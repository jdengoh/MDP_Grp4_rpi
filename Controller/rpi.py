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


if __name__ == "__main__":
    rpi = RPI()
    # rpi.check_api()
    rpi.start()

