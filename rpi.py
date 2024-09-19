from multiprocessing import Process, Manager



from communication.android_controller import AndroidController
from communication.event_logger import event_logger



class RPI:

    def __init__(self):

        self.logger = event_logger()
        self.AC = AndroidController()


    def run(self):
        while True:
            self.controller.receive()
            self.controller.send('Hello from RPI')



    def start(self):
        self.AC.connect()