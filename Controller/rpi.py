from multiprocessing import Process, Manager
import json
import queue
import time
import os
import requests

from AndroidController import AndroidController, android_msg
from LogsController import event_logger
from STM32Controller import STM32Controller
from consts import SYMBOL_MAP





class RPI:

    def __init__(self):

        self.logger = event_logger()
        self.AC = AndroidController()
        self.STMC = STM32Controller()
        

        self.manager = Manager()

        # pathing mode
        self.robot_mode = self.manager.Value('i', 1)

        # # Events
        # self.android_dropped = self.manager.Event()  # Set when the android link drops
        # # commands will be retrieved from commands queue when this event is set
        # self.unpause = self.manager.Event()

        self.rpi_action_q = self.manager.Queue() # Messages that need to be processed by RPi
        self.android_q = self.manager.Queue()
        self.command_q = self.manager.Queue()

        # self.proc_recv_android = None
        # self.proc_recv_stm32 = None
        # self.proc_android_sender = None
        # self.proc_command_follower = None
        # self.proc_rpi_action = None

        # self.ack_count = 0
        # self.near_flag = self.manager.Lock()


    
    def start(self):

        try:

            self.AC.connect()
            self.android_queue.put(android_msg('info', 'Connected to RPI!'))

            self.STMC.connect()

def run(self):
        while True:
            pass

start_rpi = RPI()
start_rpi.start()