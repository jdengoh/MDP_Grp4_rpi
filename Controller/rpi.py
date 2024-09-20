from multiprocessing import Process, Manager



from communication.android_controller import AndroidController
from communication.event_logger import event_logger



class RPI:

    def __init__(self):

        self.logger = event_logger()
        self.AC = AndroidController()

        # self.manager = Manager()

        # path mode
        # self.robot_mode = self.manager.Value('i', 1)



    def run(self):
        while True:




    def start(self):
        self.AC.connect()
        self.AC.send("Hello")



start_rpi = RPI()
start_rpi.start()