import sys
sys.path.append('/home/pi/Documents/MDP_Project/')

from multiprocessing import Process, Manager
import json
import queue
import time
import os
import requests
from MDP_rpi.settings import * 

from AndroidController import AndroidController, android_msg, android_result
from LogsController import event_logger
from STM32Controller import STM32Controller
from MDP_rpi.Application.rpi_client import snap_pic
# from consts import SYMBOL_MAP

class PiAction:
    def __init__(self, cat: str, value: str):
        self.cat = cat
        self.value = value

    def get_cat(self):
        return self.cat

    def get_value(self):
        return self.value

class RPI:

    def __init__(self):

        self.logger = event_logger()
        self.AC = AndroidController()
        self.STMC = STM32Controller()
        self.manager = Manager()        

 
        # # Events
        self.android_dropped = self.manager.Event()  # Set when the android link drops
        self.unpause = self.manager.Event()        

        # Movement Lock
        self.rpi_action_q = self.manager.Queue() # Messages that need to be processed by RPi
        self.android_q = self.manager.Queue()
        self.command_q = self.manager.Queue()
        self.path_q = self.manager.Queue()

        # Initialise Empty Processes
        self.proc_android_recv = None
        self.proc_stm32_recv = None
        self.proc_android_sender = None
        self.proc_command_follower = None
        self.proc_rpi_action = None

        self.movement_lock = self.manager.Lock()

        # Data
        self.rs_flag = False
        self.success_obstacles = self.manager.list()
        self.failed_obstacles = self.manager.list()
        self.obstacles = self.manager.dict()
        self.current_location = self.manager.dict()
        self.failed_attempt = False
    
    def start(self):

        try:
            # Android Connection
            self.AC.connect()
            self.android_q.put(android_msg('info', 
                                           'Connected to RPI!'))
            # STM Connection
            self.STMC.connect()
            # Image Rec
            self.check_api()

            # Define Processes
            self.proc_android_recv = Process(target=self.android_recv)
            self.proc_android_sender = Process(target=self.android_sender)
            self.proc_stm32_recv = Process(target=self.stm32_recv)
            self.proc_command_follower = Process(target=self.command_follower)
            self.proc_rpi_action = Process(target=self.rpi_action)

            # Start Processes
            self.proc_android_recv.start()
            self.proc_android_sender.start()
            self.proc_stm32_recv.start()
            self.proc_command_follower.start()
            self.proc_rpi_action.start()


            # Logging
            self.logger.info("START - All Processes Successfully Started")
            self.android_q.put(android_msg("info", "All Processes Successfully Started"))
            # self.android_q.put(android_msg("mode", "path" if self.robot_mode.value == 1 else "manual"))
            
            # Handover control to the Reconnect Handler to watch over Android connection
            self.android_monitor()


        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.AC.disconnect()
        self.STMC.disconnect()
        self.logger.info("STOP - All processes stopped")

    def android_monitor(self):

        self.logger.info("Android_M - Watching Android Connection")

        while True:

            # Wait for Android to drop
            self.android_dropped.wait()

            self.logger.error("Android_M - Android Disconnected!")

            # Stop and kill processes
            self.logger.debug("Android_M - Stopping all processes")
            self.proc_android_sender.kill()
            self.proc_android_recv.kill()

            self.proc_android_recv.join()
            self.proc_android_sender.join()
            assert self.proc_android_recv.is_alive() is False
            assert self.proc_android_sender.is_alive() is False 

            self.AC.disconnect()
            self.logger.debug("Android_M - Processes stopped and killed")

            # Attempt to reconnect
            self.logger.debug("Android_M - Attempting to reconnect to Android")
            self.AC.connect()

            # Restart processes
            self.logger.debug("Android_M - Restarting processes")
            self.proc_android_recv = Process(target=self.android_recv)
            self.proc_android_sender = Process(target=self.android_sender)

            self.proc_android_recv.start()
            self.proc_android_sender.start()

            self.logger.debug("Android_M - Processes restarted")
            self.android_q.put(android_msg("info", "You have been reconnected!"))
            self.android_q.put(android_msg("mode", "path"))

            self.android_drop.clear()

    def android_recv(self) -> None:
        
        while True:
            msg_str: Optional[str] = None
            
            try:
                msg_str = self.AC.receive()
            except OSError as e:
                self.android_dropped.set()
                self.logger.error(f"Android_R - Error receiving from Android: {e}")
            
            if msg_str is None:
                continue

            try:
                msg: dict = json.loads(msg_str)
                if msg['cat'] == 'obstacles':
                    self.rpi_action_q.put(PiAction('obstacles', msg['value']))
                    self.logger.info(f"Android_R - Obstacles added to RPI Action Queue: {msg}")
                elif msg['cat'] == 'control':
                    if msg['value'] == 'start':
                        if not self.check_api():
                            self.logger.error("Android_R - API is down! Start command aborted.")
                            self.android_q.put(android_msg(
                                'error', "API is down, start command aborted."))

                        if not self.command_q.empty():
                            self.logger.info("Android_R - Command queue status: ok")
                            # no gyro reset
                            self.unpause.set()
                            self.logger.info(
                                "Android_R - Start command received, starting robot on path!")
                            # self.android_q.put(android_msg(
                            #     'info', 'Starting robot on path!'))
                            self.android_q.put(
                                {"status":"running"})
                        else:
                            self.logger.warning(
                                "Android_R - The command queue is empty, please set obstacles.")
                            self.android_q.put(android_msg(
                                "error", "Command queue is empty, did you set obstacles?"))



            except:
                self.logger.error(f"Android_R - Error parsing JSON: {msg_str}")
                if msg_str.startswith('P'):
                    self.unpause.set()
                    self.command_q.put(msg_str) #TO IMPROVE
                elif msg_str.startswith('m'):
                    self.unpause.set()
                    self.command_q.put(msg_str) #TO IMPROVE
                elif msg_str.startswith('fin'):
                    self.request_stitch()
                continue

    def android_sender(self):
        while True:
            try:
                msg: android_msg = self.android_q.get(timeout=0.5)
            except queue.Empty:
                continue
            
            try:
                if type(msg) == android_msg or type(msg) == android_result:
                    self.AC.send(msg)
                else:
                    self.AC.send_generic(msg)
            except OSError as e:
                self.logger.error(f"Android_S - Error sending to Android: {e}")
                self.android_dropped.set()

    def stm32_recv(self) -> None:

        while True:
            msg: str = self.STMC.receive()
            
            # if msg == "Stop":
            # if msg.startswith("Stop"):
            #     self.snap.set()
            # self.logger.info(f"{msg}")
            if msg.startswith("STAR"):
                self.logger.info("STM32_RECV: 'STAR' from STM32 received.")
                # reset, but no need do anything

            elif msg.startswith("DONE"):
                self.logger.info("STM32_RECV: 'DONE' from STM32 received.")
                try:
                    self.movement_lock.release()
                    self.logger.debug("STM32_RECV: movement_lock released from 'DONE'")
                    try:
                        self.retrylock.release()
                        self.logger.debug("STM32_RECV: rety_lock released")

                    except:
                        pass


                    # cur_location = self.path_queue.get_nowait()

                    # self.current_location['x'] = cur_location['x']
                    # self.current_location['y'] = cur_location['y']
                    # self.current_location['d'] = cur_location['d']
                    # self.logger.info(
                    #     f"self.current_location = {self.current_location}")
                    # self.android_queue.put(android_msg('location', {
                    #     "x": cur_location['x'],
                    #     "y": cur_location['y'],
                    #     "d": cur_location['d'],
                    # }))

                except Exception:
                    self.logger.warning("STM32_RECV: Tried to release a released lock!")

            elif msg.startswith("ACK"): # TO CHECK
                if self.rs_flag == False:
                    self.rs_flag = True
                    self.logger.info("STM32_RECV: 'DONE' from STM32 received.")
                    continue
                
            else:
                self.logger.warning(
                    f"Ignored unknown message from STM: {msg}")
            
    def command_follower(self):
        while True:
            command: str = self.command_q.get()
            self.logger.debug("Comm_F - wait for unpause")

            # try:
            #     self.logger.debug("wait for retrylock")
            #     self.retrylock.acquire()
            #     self.retrylock.release()
            # except:
            self.unpause.wait()
            
            self.logger.debug("Comm_F - wait for movelock")
            # Acquire lock first (needed for both moving, and snapping pictures)
            self.movement_lock.acquire()
            self.logger.debug("Comm_F - movelock acquired")
            # stm_32_prefixes = ("FS", "BS", "FW", "BW", "FL", "FR", "BL",
            #                   "BR", "TL", "TR", "A", "C", "DT", "STOP", "ZZ", "RS")
                              
            # pre = ['S', 'B', 'L', 'R'] # todo

            if command.startswith('S/'):
                # command[2:4]
                int_portion = int(command[2:])  # This will be 20 (integer)
                # str_portion = str(int_portion).zfill(3)
                speed = str(int_portion)
                if int_portion <= 100:
                    self.STMC.send('m')
                    self.STMC.send(speed[0])
                    self.STMC.send(speed[1])
                    self.STMC.send('\r')
                else:
                    self.STMC.send('m')
                    self.STMC.send(speed[0])
                    self.STMC.send(speed[1])
                    self.STMC.send(speed[2])

            elif command.startswith('R/'):
                self.STMC.send('r')
                self.STMC.send('9')
                self.STMC.send('0')
                self.STMC.send('\r')
            
            elif command.startswith('L/'):
                self.STMC.send('l')
                self.STMC.send('9')
                self.STMC.send('0')
                self.STMC.send('\r')

            elif command.startswith('SB'):
                int_portion = int(command[2:])  # This will be 20 (integer)
                # str_portion = str(int_portion).zfill(3)
                speed = str(int_portion)
                if int_portion <= 100:
                    self.STMC.send('w')
                    self.STMC.send(speed[0])
                    self.STMC.send(speed[1])
                    self.STMC.send('\r')
                else:
                    self.STMC.send('w')
                    self.STMC.send(speed[0])
                    self.STMC.send(speed[1])
                    self.STMC.send(speed[2])

            elif command.startswith('LB'):
                self.STMC.send('t')
                self.STMC.send('9')
                self.STMC.send('0')
                self.STMC.send('\r')

            elif command.startswith('RB'):
                self.STMC.send('k')
                self.STMC.send('9')
                self.STMC.send('0')
                self.STMC.send('\r')
           
            
            elif command.startswith('P'):
                print("gonna try and snap pic")
                self.rpi_action_q.put(PiAction(cat="snap", value=command[1:]))
                   # PiAction(cat="snap", value=obstacle_id_with_signal))

            elif command.startswith("fin"): #(MY RETRYYY FUNCTON)
                self.unpause.clear()
                self.movement_lock.release()
                self.logger.info("Commands queue finished.")
                self.android_q.put(android_msg(
                    "info", "Commands queue finished."))
                self.android_q.put(android_msg("status", "finished"))
                self.rpi_action_q.put(PiAction(cat="stitch", value=""))
                self.request_stitch()
                self.logger.info("Stitch completed!.")


            else:
                raise Exception(f"Unknown command: {command}")

            # self.unpause.clear()
            # self.movement_lock.release()
            # self.logger.info("Commands queue finished.")
            # self.android_q.put(android_msg("info", "Commands queue finished."))
            # self.android_q.put(android_msg("status", "finished"))

    def rpi_action(self):
        while True:
            action: PiAction = self.rpi_action_q.get()
            self.logger.info(
                f"PiAction retrieved from queue: {action.cat} {action.value}")
            if action.cat == "obstacles":
                temp_obstacles = {}
                for obs in action.value['obstacles']:
                    if obs['direction'] == "E":
                        obs['direction'] = 0
                    elif obs['direction'] == "N":
                        obs['direction'] = 90
                    elif obs['direction'] == "W":
                        obs['direction'] = 180
                    elif obs['direction'] == "S":
                        obs['direction'] = -90
                    temp_obstacles[obs['id']-1] = [obs['x'],\
                                                obs['y'], \
                                                obs['direction'], \
                                                obs['id']]
                self.obstacles["obstacles"] = temp_obstacles
                print(self.obstacles)
                self.request_algo(dict(self.obstacles))
            
            # NOT YET IMPLEMENTED
            elif action.cat == "snap":
                result = snap_pic()
                self.android_q.put(android_result(action.value, result))
                print("the result is", result)
                time.sleep(0.5)
                self.movement_lock.release()

            #     self.snap_and_rec(obstacle_id_with_signal=action.value)
            # elif action.cat == "stitch":
            #     self.request_stitch()
       
    def check_api(self) -> bool:
        url = f"http://{API_IP}:{API_PORT}/status"
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                self.logger.debug("API is up!")
                return True
        except ConnectionError:
            self.logger.warning("API Connection Error")
            return False
        except requests.Timeout:
            self.logger.warning("API Timeout")
            return False
        except Exception as e:
            self.logger.warning(f"API Exception: {e}")
            return False

    # def snap_and_rec(self, obstacle_id: str) -> None:
    #     """
    #     RPi snaps an image and calls the API for image-rec.
    #     The response is then forwarded back to the android
    #     :param obstacle_id: the current obstacle ID
    #     """
        
    #     self.logger.info(f"Capturing image for obstacle id: {obstacle_id}")
    #     signal = "C"
    #     url = f"http://{API_IP}:{API_PORT}/image"
    #     filename = f"{int(time.time())}_{obstacle_id}_{signal}.jpg"
        
        
    #     # con_file    = "PiLCConfig9.txt"
    #     # Home_Files  = []
    #     # Home_Files.append(os.getlogin())
    #     # config_file = "/home/" + Home_Files[0]+ "/" + con_file

    #     # extns        = ['jpg','png','bmp','rgb','yuv420','raw']
    #     # shutters     = [-2000,-1600,-1250,-1000,-800,-640,-500,-400,-320,-288,-250,-240,-200,-160,-144,-125,-120,-100,-96,-80,-60,-50,-48,-40,-30,-25,-20,-15,-13,-10,-8,-6,-5,-4,-3,0.4,0.5,0.6,0.8,1,1.1,1.2,2,3,4,5,6,7,8,9,10,11,15,20,25,30,40,50,60,75,100,112,120,150,200,220,230,239,435]
    #     # meters       = ['centre','spot','average']
    #     # awbs         = ['off','auto','incandescent','tungsten','fluorescent','indoor','daylight','cloudy']
    #     # denoises     = ['off','cdn_off','cdn_fast','cdn_hq']

    #     config = []
    #     with open(config_file, "r") as file:
    #         line = file.readline()
    #         while line:
    #             config.append(line.strip())
    #             line = file.readline()
    #         config = list(map(int,config))
    #     mode        = config[0]
    #     speed       = config[1]
    #     gain        = config[2]
    #     brightness  = config[3]
    #     contrast    = config[4]
    #     red         = config[6]
    #     blue        = config[7]
    #     ev          = config[8]
    #     extn        = config[15]
    #     saturation  = config[19]
    #     meter       = config[20]
    #     awb         = config[21]
    #     sharpness   = config[22]
    #     denoise     = config[23]
    #     quality     = config[24]
        
    #     retry_count = 0
        
    #     while True:
        
    #         retry_count += 1
        
    #         shutter = shutters[speed]
    #         if shutter < 0:
    #             shutter = abs(1/shutter)
    #         sspeed = int(shutter * 1000000)
    #         if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
    #             sspeed +=1
                
    #         rpistr = "libcamera-still -e " + extns[extn] + " -n -t 100 -o " + filename
    #         rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
    #         rpistr += " --shutter " + str(sspeed)
    #         if ev != 0:
    #             rpistr += " --ev " + str(ev)
    #         if sspeed > 1000000 and mode == 0:
    #             rpistr += " --gain " + str(gain) + " --immediate "
    #         else:    
    #             rpistr += " --gain " + str(gain)
    #             if awb == 0:
    #                 rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
    #             else:
    #                 rpistr += " --awb " + awbs[awb]
    #         rpistr += " --metering " + meters[meter]
    #         rpistr += " --saturation " + str(saturation/10)
    #         rpistr += " --sharpness " + str(sharpness/10)
    #         rpistr += " --quality " + str(quality)
    #         rpistr += " --denoise "    + denoises[denoise]
    #         rpistr += " --metadata - --metadata-format txt >> PiLibtext.txt"

    #         os.system(rpistr)
            
            
    #         self.logger.debug("Requesting from image API")
            
    #         response = requests.post(url, files={"file": (filename, open(filename,'rb'))})

    #         if response.status_code != 200:
    #             self.logger.error("Something went wrong when requesting path from image-rec API. Please try again.")
    #             return
            

    #         results = json.loads(response.content)

    #         # Higher brightness retry
            
    #         if results['image_id'] != 'NA' or retry_count > 6:
    #             break
    #         elif retry_count <= 2:
    #             self.logger.info(f"Image recognition results: {results}")
    #             self.logger.info("Recapturing with same shutter speed...")
    #         elif retry_count <= 4:
    #             self.logger.info(f"Image recognition results: {results}")
    #             self.logger.info("Recapturing with lower shutter speed...")
    #             speed -= 1
    #         elif retry_count == 5:
    #             self.logger.info(f"Image recognition results: {results}")
    #             self.logger.info("Recapturing with lower shutter speed...")
    #             speed += 3
            
    #     ans = SYMBOL_MAP.get(results['image_id'])
    #     self.logger.info(f"Image recognition results: {results} ({ans})")
    #     return ans

    def request_algo(self, data, robot_x=1, robot_y=1, robot_dir=0, retrying=False):

        self.logger.info("Requesting path from algo...")
        self.android_q.put(android_msg(
            "info", "Requesting path from algo..."))
        self.logger.info(f"data: {data}")
        # body = {**data, "big_turn": "0", "robot_x": robot_x,
        #         "robot_y": robot_y, "robot_dir": robot_dir, "retrying": retrying}

        url = f"http://{API_IP}:{API_PORT}/algo"
        response = requests.post(url, json=data) # ERROR IS HERE

        # Error encountered at the server, return early
        if response.status_code != 200:
            self.android_q.put(android_msg(
                "error", "Something went wrong when requesting path from Algo API."))
            self.logger.error(
                "Something went wrong when requesting path from Algo API.")
            return
        
        result = json.loads(response.content)
        #print("Full result:", result)
        commands = result.get('commands', [])
        order = result.get('order', [])
        print(order)
        
        id_index = 0

        for i, command in enumerate(commands):
            if command == 'P' and id_index < len(order):
                commands[i] = f'P{order[id_index]}'
                id_index += 1

        path_hist = result.get('path_hist')

        # Parse response
        # result = json.loads(response.content)['data']
        # commands = result['commands']
        # path = result['path']
        # Log commands received
        self.logger.debug(f"Commands received from API: {commands}")
        
        self.clear_queues()
        for c in commands:
            self.logger.info(f"Command Queue input: {c}")
            self.command_q.put(c)
        
        self.android_q.put(android_msg("status", "Algo Received!"))
        # for p in path[1:]:  # ignore first element as it is the starting position of the robot
        #     self.path_queue.put(p)

    def request_stitch(self):
        """Sends a stitch request to the image recognition API to stitch the different images together"""
        url = f"http://{API_IP}:{API_PORT}/stitch"
        response = requests.get(url)

        # If error, then log, and send error to Android
        if response.status_code != 200:
            # Notify android
            self.android_q.put(android_msg(
                "error", "Something went wrong when requesting stitch from the API."))
            self.logger.error(
                "Something went wrong when requesting stitch from the API.")
            return

        self.logger.info("Images stitched!")
        self.android_q.put(android_msg("info", "Images stitched!"))

    def clear_queues(self):
        """Clear both command and path queues"""
        while not self.command_q.empty():
            self.command_q.get()

if __name__ == "__main__":
    rpi = RPI()
    # rpi.check_api()
    rpi.start()
