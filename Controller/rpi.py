from multiprocessing import Process, Manager
import json
import queue
import time
import os
import requests

from AndroidController import AndroidController, android_msg
from LogsController import event_logger
from STM32Controller import STM32Controller
# from consts import SYMBOL_MAP





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
            # --- --- ---

            # Define Processes
            self.proc_android_recv = Process(target=self.android_recv)
            self.proc_android_sender = Process(target=self.android_sender)
            # self.proc_stm32_recv = Process(target=self.stm32_recv)
            # self.proc_command_follower = Process(target=self.command_follower)
            # self.proc_rpi_action = Process(target=self.rpi_action)

            # Start Processes
            self.proc_android_recv.start()
            self.proc_android_sender.start()

            # self.proc_stm32_recv.start()
            # self.proc_command_follower.start()
            # self.proc_rpi_action.start()

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
            



if __name__ == "__main__":
    rpi = RPI()
    rpi.start()




