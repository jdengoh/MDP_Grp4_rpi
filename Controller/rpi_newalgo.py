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

        self.android_dropped = self.manager.Event()
        self.unpause = self.manager.Event()        

        self.rpi_action_q = self.manager.Queue()
        self.android_q = self.manager.Queue()
        self.command_q = self.manager.Queue()
        self.path_q = self.manager.Queue()

        self.proc_android_recv = None
        self.proc_stm32_recv = None
        self.proc_android_sender = None
        self.proc_command_follower = None
        self.proc_rpi_action = None

        self.movement_lock = self.manager.Lock()

        self.start_flag = False
        self.success_obstacles = self.manager.list()
        self.failed_obstacles = self.manager.list()
        self.obstacles = self.manager.dict()
        self.current_location = self.manager.dict()
        self.failed_attempt = False
    
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
                self.logger.info("STM32_RECV: 'DONE' from STM32 received.")
                try:
                    self.movement_lock.release()
                    self.logger.debug("STM32_RECV: movement_lock released from 'DONE'")

                except Exception:
                    self.logger.warning("STM32_RECV: Tried to release a released lock!")

            elif msg.startswith("ACK"):
                if self.start_flag == False:
                    self.start_flag = True
                    self.logger.info("STM32_RECV: 'ACK' from STM32 received.")
                    continue
                
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

            if command.startswith('SF'):
                int_portion = int(command[2:])
                speed = str(int_portion)
                if int_portion < 100:
                    self.STMC.send('m')
                    self.STMC.send(speed[0])
                    self.STMC.send(speed[1])
                    self.STMC.send('\r')
                else:
                    self.STMC.send('m')
                    self.STMC.send(speed[0])
                    self.STMC.send(speed[1])
                    self.STMC.send(speed[2])

            elif command.startswith('RF'):
                self.STMC.send('r')
                self.STMC.send(command[3])
                self.STMC.send(command[4])
                self.STMC.send('\r')
            
            elif command.startswith('LF'):
                self.STMC.send('l')
                self.STMC.send(command[3])
                self.STMC.send(command[4])
                self.STMC.send('\r')

            elif command.startswith('SB'):
                int_portion = int(command[2:])
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
                self.STMC.send(command[3])
                self.STMC.send(command[4])
                self.STMC.send('\r')

            elif command.startswith('RB'):
                self.STMC.send('k')
                self.STMC.send(command[3])
                self.STMC.send(command[4])
                self.STMC.send('\r')
            
            elif command.startswith('P'):
                print("gonna try and snap pic")
                self.rpi_action_q.put(PiAction(cat="snap", value=command[1:]))

            elif command.startswith("fin"):
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
            
            elif action.cat == "snap":
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

    def request_algo(self, data):

        self.logger.info("Requesting path from algo...")
        self.android_q.put(android_msg(
            "info", "Requesting path from algo..."))
        self.logger.info(f"data: {data}")

        url = f"http://{API_IP}:{API_PORT}/algo"
        response = requests.post(url, json=data)

        if response.status_code != 200:
            self.android_q.put(android_msg(
                "error", "Something went wrong when requesting path from Algo API."))
            self.logger.error(
                "Something went wrong when requesting path from Algo API.")
            return
        
        result = json.loads(response.content)
        commands = result.get('commands', [])
        order = result.get('order', [])
        print(order)
        
        id_index = 0

        for i, command in enumerate(commands):
            if command == 'P' and id_index < len(order):
                commands[i] = f'P{order[id_index]}'
                id_index += 1

        self.logger.debug(f"Commands received from API: {commands}")
        
        self.clear_queues()
        for c in commands:
            self.logger.info(f"Command Queue input: {c}")
            self.command_q.put(c)
        
        self.android_q.put(android_msg("status", "Algo Received!"))

    def request_stitch(self):
        """Sends a stitch request to the image recognition API to stitch the different images together"""
        url = f"http://{API_IP}:{API_PORT}/stitch"
        response = requests.get(url)

        if response.status_code != 200:
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
    rpi.start()
