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

        # pathing mode
        self.robot_mode = self.manager.Value('i', 1)

        # # Events
        self.android_dropped = self.manager.Event()  # Set when the android link drops
        # commands will be retrieved from commands queue when this event is set
        self.unpause = self.manager.Event()

        # Movement Lock
        # self.movement_lock = self.manager.Lock()

        self.rpi_action_q = self.manager.Queue() # Messages that need to be processed by RPi
        self.android_q = self.manager.Queue()
        self.command_q = self.manager.Queue()

        # Initialise Empty Processes
        self.proc_android_recv = None
        self.proc_stm32_recv = None
        self.proc_android_sender = None
        self.proc_command_follower = None
        # self.proc_rpi_action = None

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
            # self.proc_stm32_recv = Process(target=self.stm32_recv)
            self.proc_command_follower = Process(target=self.command_follower)
            self.proc_rpi_action = Process(target=self.rpi_action)

            # Start Processes
            self.proc_android_recv.start()
            self.proc_android_sender.start()

            # self.proc_stm32_recv.start()
            self.proc_command_follower.start()
            self.proc_rpi_action.start()

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
            self.unpause.wait()
            self.movement_lock.acquire()
            stm_32_prefixes = ("STOP", "ZZ", "UL", "UR", "PL", "PR", "RS", "OB")
            if command.startswith(stm32_prefixes):
                self.stm_link.send(command)
            elif command == "FIN":
                self.unpause.clear()
                self.movement_lock.release()
                self.logger.info("Commands queue finished.")
                self.android_queue.put(AndroidMessage("info", "Commands queue finished."))
                self.android_queue.put(AndroidMessage("status", "finished"))
                self.rpi_action_queue.put(PiAction(cat="stitch", value=""))
            else:
                raise Exception(f"Unknown command: {command}")


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


if __name__ == "__main__":
    rpi = RPI()
    # rpi.check_api()
    rpi.start()

