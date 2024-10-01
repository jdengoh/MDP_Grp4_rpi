import sys
sys.path.append('/home/pi/Documents/MDP_Project/')

from multiprocessing import Process, Manager
import json
import queue
import time
import os
import requests
from MDP_rpi.settings import * 

from AndroidController import AndroidController, android_msg
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

    # def jsonify(self) -> str:
    #     return json.dumps({'cat': self.cat, 'value': self.value})


class RPI:

    def __init__(self):

        self.logger = event_logger()
        self.AC = AndroidController()
        self.STMC = STM32Controller()
        self.manager = Manager()
        # self.cam = PiCamera()
        

        # pathing mode
        self.robot_mode = self.manager.Value('i', 1)

        # # Events
        self.android_dropped = self.manager.Event()  # Set when the android link drops
        # commands will be retrieved from commands queue when this event is set
        self.unpause = self.manager.Event()

        self.snap = self.manager.Event()
        

        # Movement Lock
        self.movement_lock = self.manager.Lock()

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

        self.rs_flag = False

        self.ack_count = 0
        self.near_flag = self.manager.Lock()


    
    def start(self):

        try:
            # Android Connection
            self.AC.connect()
            self.android_q.put(android_msg('info', 'Connected to RPI!'))

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
            # self.proc_snap_pic = Process(target=self.snap_pic)

            # Start Processes
            self.proc_android_recv.start()
            self.proc_android_sender.start()

            self.proc_stm32_recv.start()
            self.proc_command_follower.start()
            self.proc_rpi_action.start()
            # self.proc_snap_pic = start()


            # Logging
            self.logger.info("All Processes Successfully Started")
            self.android_q.put(android_msg('info', 'All Processes Successfully Started'))
            self.android_q.put(android_msg('mode', 'path' if self.robot_mode.value == 1 else 'manual'))
            
            # Handover control to the Reconnect Handler to watch over Android connection
            self.android_monitor()


        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.logger.info("Stopping all processes")
        self.android_q.put(android_msg('info', 'Stopping all processes'))

        self.AC.disconnect()
        self.STMC.disconnect()

        self.proc_android_recv.terminate()
        self.proc_android_sender.terminate()
        # self.proc_stm32_recv.terminate()
        # self.proc_command_follower.terminate()
        # self.proc_rpi_action.terminate()

        self.logger.info("All processes stopped")

    # def snap_pic(self):
    #     url = f"http://{API_IP}:{API_PORT}/image"
    #     self.logger.info(f"Connecting to {url}")
    #     # Initialize the PiCamera

                    
    #     # rpistr = 'raspistill -o /home/pi/captured_image.jpg'            
    #     # os.system(rpistr)

    #     # Capture image
    #     self.logger.info("Start Cam")
    #     while True:
    #         self.cam.capture('/home/pi/captured_image.jpg')
    #     self.logger.info("End Cam")


    #     # Send image to Flask server
    #     self.logger.info(f"Sending image to server")

    #     with open('/home/pi/captured_image.jpg', 'rb') as img_file:
    #         files = {'image': img_file}
    #         response = requests.post(url, files=files)

    #     # Get the response from the server
    #     if response.status_code == 200:
    #         print("200")
    #         print("Image detection result:", response.json())
            
    #     else:
    #         print("Error:", response.json())

    #     results = json.loads(response.content)
    #     return results

    def android_monitor(self):

        self.logger.info("Monitoring Android")

        while True:
            
            self.android_dropped.wait()

            self.logger.error("Android Disconnected!")

            # Stop and kill processes
            self.logger.debug("Stopping all processes")
            self.proc_android_sender.kill()
            self.proc_android_recv.kill()

            self.proc_android_recv.join()
            self.proc_android_sender.join()
            assert self.proc_android_recv.is_alive() is False
            assert self.proc_android_sender.is_alive() is False 

            self.AC.disconnect()
            self.logger.debug("Processes stopped and killed")

            # Attempt to reconnect
            self.logger.debug("Attempting to reconnect to Android")
            self.AC.connect()

            # Restart processes
            self.logger.debug("Restarting processes")
            self.proc_android_recv = Process(target=self.android_recv)
            self.proc_android_sender = Process(target=self.android_sender)

            self.proc_android_recv.start()
            self.proc_android_sender.start()

            self.logger.debug("Processes restarted")
            self.android_q.put(android_msg('info', 'You have been reconnected!'))
            self.android_q.put(AndroidMessage('mode', 'path' if self.robot_mode.value == 1 else 'manual'))

            self.android_drop.clear()

    def android_recv(self) -> None:
        
        while True:
            msg_str: Optional[str] = None
            
            try:
                msg_str = self.AC.receive()
            except OSError as e:
                self.logger.error(f"Error receiving from Android: {e}")
                self.android_dropped.set()
            
            if msg_str is None:
                continue

            self.command_q.put(msg_str) #TO IMPROVE
            self.logger.debug(f"put into command queue")


            # TO-DO
            # message: dict = json.loads(msg_str)

            # if message['cat'] == 'control':
            #     if message['value'] == 'start':

            #         self.logger.info("Received Start Command")

    def android_sender(self):
        while True:
            try:
                msg: android_msg = self.android_q.get(timeout=0.5)
            except queue.Empty:
                continue
            
            try:
                self.AC.send(msg)
            except OSError as e:
                self.logger.error(f"Error sending to Android: {e}")
                self.android_dropped.set()
            
    def command_follower(self):
        while True:
            command: str = self.command_q.get()
            self.logger.debug("wait for unpause")

            print(command)
            # Wait for unpause event to be true [Main Trigger]
            # try:
            #     self.logger.debug("wait for retrylock")
            #     self.retrylock.acquire()
            #     self.retrylock.release()
            # except:
            #     self.logger.debug("wait for unpause")
            #     self.unpause.wait()
            
            self.logger.debug("wait for movelock")
            # Acquire lock first (needed for both moving, and snapping pictures)
            self.movement_lock.acquire()
           
            # stm_32_prefixes = ("FS", "BS", "FW", "BW", "FL", "FR", "BL",
            #                   "BR", "TL", "TR", "A", "C", "DT", "STOP", "ZZ", "RS")
                              
            if command.startswith('f'):
                self.STMC.send('m')
                self.STMC.send('6')
                self.STMC.send('0')
                self.STMC.send('\r')

                

            elif command.startswith('g') or command.startswith('u'):
                self.STMC.send('u')
                self.STMC.send('\r')
                self.STMC.send('\r')
                self.STMC.send('\r')
                

            # elif command.startswith('s'):
            #     self.STMC.send('s')
            #     self.STMC.send('t')
            #     self.STMC.send('o')
            #     self.STMC.send('p')

            elif command.startswith('r'):
                self.STMC.send('r')
                self.STMC.send('9')
                self.STMC.send('0')
                self.STMC.send('\r')
            
            elif command.startswith('l'):
                self.STMC.send('l')
                self.STMC.send('9')
                self.STMC.send('0')
                self.STMC.send('\r')

            elif command.startswith('b'):
                self.STMC.send('w')
                self.STMC.send('1')
                self.STMC.send('0')
                self.STMC.send('0')
            
            elif command.startswith('s'):
                result = snap_pic()
                print("the result is is", result)
            
            
            elif command.startswith('a'):
                
                for i in range(0,3):
                    snap_pic()
                    self.STMC.send('u')
                    self.STMC.send('\r')
                    self.STMC.send('\r')
                    self.STMC.send('\r')

                    while True:
                        if self.STMC.receive() == "Stop":
                            break
                        








            else:
                raise Exception(f"Unknown command: {command}")

            # self.unpause.clear()
            self.movement_lock.release()
            self.logger.info("Commands queue finished.")
            self.android_q.put(android_msg("info", "Commands queue finished."))
            self.android_q.put(android_msg("status", "finished"))




    def rpi_action(self):
        pass
       
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

    def snap_and_rec(self, obstacle_id: str) -> None:
        """
        RPi snaps an image and calls the API for image-rec.
        The response is then forwarded back to the android
        :param obstacle_id: the current obstacle ID
        """
        
        self.logger.info(f"Capturing image for obstacle id: {obstacle_id}")
        signal = "C"
        url = f"http://{API_IP}:{API_PORT}/image"
        filename = f"{int(time.time())}_{obstacle_id}_{signal}.jpg"
        
        
        # con_file    = "PiLCConfig9.txt"
        # Home_Files  = []
        # Home_Files.append(os.getlogin())
        # config_file = "/home/" + Home_Files[0]+ "/" + con_file

        # extns        = ['jpg','png','bmp','rgb','yuv420','raw']
        # shutters     = [-2000,-1600,-1250,-1000,-800,-640,-500,-400,-320,-288,-250,-240,-200,-160,-144,-125,-120,-100,-96,-80,-60,-50,-48,-40,-30,-25,-20,-15,-13,-10,-8,-6,-5,-4,-3,0.4,0.5,0.6,0.8,1,1.1,1.2,2,3,4,5,6,7,8,9,10,11,15,20,25,30,40,50,60,75,100,112,120,150,200,220,230,239,435]
        # meters       = ['centre','spot','average']
        # awbs         = ['off','auto','incandescent','tungsten','fluorescent','indoor','daylight','cloudy']
        # denoises     = ['off','cdn_off','cdn_fast','cdn_hq']

        config = []
        with open(config_file, "r") as file:
            line = file.readline()
            while line:
                config.append(line.strip())
                line = file.readline()
            config = list(map(int,config))
        mode        = config[0]
        speed       = config[1]
        gain        = config[2]
        brightness  = config[3]
        contrast    = config[4]
        red         = config[6]
        blue        = config[7]
        ev          = config[8]
        extn        = config[15]
        saturation  = config[19]
        meter       = config[20]
        awb         = config[21]
        sharpness   = config[22]
        denoise     = config[23]
        quality     = config[24]
        
        retry_count = 0
        
        while True:
        
            retry_count += 1
        
            shutter = shutters[speed]
            if shutter < 0:
                shutter = abs(1/shutter)
            sspeed = int(shutter * 1000000)
            if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
                sspeed +=1
                
            rpistr = "libcamera-still -e " + extns[extn] + " -n -t 100 -o " + filename
            rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
            rpistr += " --shutter " + str(sspeed)
            if ev != 0:
                rpistr += " --ev " + str(ev)
            if sspeed > 1000000 and mode == 0:
                rpistr += " --gain " + str(gain) + " --immediate "
            else:    
                rpistr += " --gain " + str(gain)
                if awb == 0:
                    rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                else:
                    rpistr += " --awb " + awbs[awb]
            rpistr += " --metering " + meters[meter]
            rpistr += " --saturation " + str(saturation/10)
            rpistr += " --sharpness " + str(sharpness/10)
            rpistr += " --quality " + str(quality)
            rpistr += " --denoise "    + denoises[denoise]
            rpistr += " --metadata - --metadata-format txt >> PiLibtext.txt"

            os.system(rpistr)
            
            
            self.logger.debug("Requesting from image API")
            
            response = requests.post(url, files={"file": (filename, open(filename,'rb'))})

            if response.status_code != 200:
                self.logger.error("Something went wrong when requesting path from image-rec API. Please try again.")
                return
            

            results = json.loads(response.content)

            # Higher brightness retry
            
            if results['image_id'] != 'NA' or retry_count > 6:
                break
            elif retry_count <= 2:
                self.logger.info(f"Image recognition results: {results}")
                self.logger.info("Recapturing with same shutter speed...")
            elif retry_count <= 4:
                self.logger.info(f"Image recognition results: {results}")
                self.logger.info("Recapturing with lower shutter speed...")
                speed -= 1
            elif retry_count == 5:
                self.logger.info(f"Image recognition results: {results}")
                self.logger.info("Recapturing with lower shutter speed...")
                speed += 3
            
        ans = SYMBOL_MAP.get(results['image_id'])
        self.logger.info(f"Image recognition results: {results} ({ans})")
        return ans

    # def request_algo(self, data, robot_x=1, robot_y=1, robot_dir=0, retrying=False):
    #     """
    #     Requests for a series of commands and the path from the Algo API.
    #     The received commands and path are then queued in the respective queues
    #     """
    #     self.logger.info("Requesting path from algo...")
    #     self.android_queue.put(AndroidMessage(
    #         "info", "Requesting path from algo..."))
    #     self.logger.info(f"data: {data}")
    #     body = {**data, "big_turn": "0", "robot_x": robot_x,
    #             "robot_y": robot_y, "robot_dir": robot_dir, "retrying": retrying}
    #     url = f"http://{API_IP}:{API_PORT}/path"
    #     response = requests.post(url, json=body)

    #     # Error encountered at the server, return early
    #     if response.status_code != 200:
    #         self.android_queue.put(AndroidMessage(
    #             "error", "Something went wrong when requesting path from Algo API."))
    #         self.logger.error(
    #             "Something went wrong when requesting path from Algo API.")
    #         return

        # Parse response
        result = json.loads(response.content)['data']
        commands = result['commands']
        path = result['path']

        # Log commands received
        self.logger.debug(f"Commands received from API: {commands}")

    def stm32_recv(self) -> None:
        """
        [Child Process] Receive acknowledgement messages from STM32, and release the movement lock
        """
        while True:

            msg: str = self.STMC.receive()
            
            if msg == "Stop":
                self.snap.set()

            self.logger.info(f"{msg}")

            

            # if message.startswith("ACK"):
            #     if self.rs_flag == False:
            #         self.rs_flag = True
            #         self.logger.debug("ACK for RS00 from STM32 received.")
            #         continue
            #     try:
            #         self.movement_lock.release()
            #         try:
            #             self.retrylock.release()
            #         except:
            #             pass
            #         self.logger.debug(
            #             "ACK from STM32 received, movement lock released.")

            #         cur_location = self.path_queue.get_nowait()

            #         self.current_location['x'] = cur_location['x']
            #         self.current_location['y'] = cur_location['y']
            #         self.current_location['d'] = cur_location['d']
            #         self.logger.info(
            #             f"self.current_location = {self.current_location}")
            #         self.android_queue.put(AndroidMessage('location', {
            #             "x": cur_location['x'],
            #             "y": cur_location['y'],
            #             "d": cur_location['d'],
            #         }))

            #     except Exception:
            #         self.logger.warning("Tried to release a released lock!")
            # else:
            #     self.logger.warning(
            #         f"Ignored unknown message from STM: {message}")

            



if __name__ == "__main__":
    rpi = RPI()
    # rpi.check_api()
    rpi.start()
