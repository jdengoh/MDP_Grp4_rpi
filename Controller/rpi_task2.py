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
        self.ack_count = 0
        self.first_image = 'NA'
        self.second_image = 'NA'
    
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

                if msg['cat'] == 'control':
                    if msg['value'] == 'start':
                        if not self.check_api():
                            self.logger.error("Android_R - API is down! Start command aborted.")
                            self.android_q.put(android_msg('error', "API is down, start command aborted."))
                        
                        self.clear_queues()
                        result = snap_pic()

                        print("RESULT IS: ", result)
                        if result == '38':
                            self.first_image = 'right'
                        else:
                            self.first_image = 'left'

                        self.logger.info(f"First image is: {self.first_image}")

                        if self.first_image == 'left':
                            self.command_q.put("X000")
                            self.command_q.put("W20")
                            self.command_q.put("U111")

                        elif self.first_image == 'right':
                            self.command_q.put("X000")
                            self.command_q.put("W20")
                            self.command_q.put("U222")

                        self.logger.info("Start command received, starting robot")
                        self.android_q.put(android_msg('status', 'running'))
                        self.unpause.set()

            except:
                self.logger.error(f"Android_R - Error parsing JSON: {msg_str}")
                if msg_str.startswith('P'):
                    self.unpause.set()
                    self.command_q.put(msg_str)

                elif msg_str.startswith('m'):
                    self.unpause.set()
                    self.command_q.put(msg_str)

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
            
            if msg.startswith("STAR"):
                self.logger.info("STM32_RECV: 'STAR' from STM32 received.")
                
            elif msg.startswith("DONE"):
                time.sleep(1)
                self.logger.info("STM32_RECV: 'DONE' from STM32 received.")
                self.ack_count += 1
                try:
                    self.movement_lock.release()
                    self.logger.debug("STM32_RECV: movement_lock released from 'DONE'")
                except Exception:
                    self.logger.warning("STM32_RECV: Tried to release a released lock!")

                if self.ack_count == 3:
                    time.sleep(1)
                    result_2 = snap_pic()

                    if result_2 == '38':
                        self.second_image = 'right'
                    else:
                        self.second_image= 'left'
                    
                    self.logger.info(f"Second image is: {self.second_image}")

                    self.clear_queues()
                    if self.second_image == 'left':
                        self.command_q.put("?000")
                        self.command_q.put("W20")
                        self.command_q.put("l77")
                        self.command_q.put("q000")
                        self.command_q.put("fin")
                                            
                    elif self.second_image == 'right':
                        self.command_q.put("?000")
                        self.command_q.put("W20")
                        self.command_q.put("r77")
                        self.command_q.put("o000")
                        self.command_q.put("fin")
            else:
                self.logger.warning(
                    f"Ignored unknown message from STM: {msg}")
            
    def command_follower(self):
        while True:
            command: str = self.command_q.get()
            self.logger.debug("Comm_F - wait for unpause")
            self.unpause.wait()  
            self.logger.debug("Comm_F - wait for movelock")
            self.movement_lock.acquire()
            self.logger.debug("Comm_F - movelock acquired")
            time.sleep(0.5)
                  
            if command.startswith('X'):
                self.STMC.send('x')
                self.STMC.send(command[1])
                self.STMC.send(command[2])
                self.STMC.send(command[3])
                self.STMC.send('\r')

            elif command.startswith('?'):
                self.STMC.send('x')
                self.STMC.send(command[1])
                self.STMC.send(command[2])
                self.STMC.send(command[3])            
            
            elif command.startswith('W'):
                self.STMC.send('w')
                self.STMC.send(command[1])
                self.STMC.send(command[2])
                self.STMC.send('\r')
            
            elif command.startswith('U'):
                self.STMC.send('u')
                self.STMC.send(command[1])
                self.STMC.send(command[2])
                self.STMC.send(command[3])

            elif command.startswith('q'):
                self.STMC.send('q')
                self.STMC.send(command[1])
                self.STMC.send(command[2])
                self.STMC.send(command[3])

            elif command.startswith('o'):
                self.STMC.send('o')
                self.STMC.send(command[1])
                self.STMC.send(command[2])
                self.STMC.send(command[3])   

            elif command.startswith('l77'):
                self.STMC.send('l')
                self.STMC.send('7')
                self.STMC.send('8')
                self.STMC.send('\r')    

            elif command.startswith('r77'):
                self.STMC.send('r')
                self.STMC.send('7')
                self.STMC.send('9')
                self.STMC.send('\r')           
            
            elif command.startswith('K'):
                self.STMC.send('k')
                self.STMC.send('9')
                self.STMC.send('0')
                self.STMC.send('\r')
           
            elif command.startswith("fin"):
                self.unpause.clear()
                self.movement_lock.release()
                self.logger.info("Commands queue finished.")
                self.android_q.put(android_msg(
                    "info", "Commands queue finished."))
                self.android_q.put(android_msg("status", "finished"))
                self.rpi_action_q.put(PiAction(cat="stitch", value=""))
                self.request_stitch()
                self.logger.info("Stitch completed!")
            else:
                raise Exception(f"Unknown command: {command}")


    def rpi_action(self):
        while True:
            action: PiAction = self.rpi_action_q.get()
            self.logger.info(
                f"PiAction retrieved from queue: {action.cat} {action.value}")
        
            if action.cat == "snap":
                result = snap_pic()
                self.android_q.put(android_result(action.value, result))
                print("the result is", result)
                time.sleep(0.5)
                self.movement_lock.release()
       
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

 
    def request_stitch(self):
        url = f"http://{API_IP}:{API_PORT}/stitch"
        response = requests.get(url)

        if response.status_code != 200:
            self.android_q.put(android_msg("Error", "Stitch error!"))
            self.logger.error("Stitch error!")
            return

        self.logger.info("Stich complete!")
        self.android_q.put(android_msg("info", "Stich complete!"))

    def clear_queues(self):
        while not self.command_q.empty():
            self.command_q.get()

if __name__ == "__main__":
    rpi = RPI()
    rpi.start()
