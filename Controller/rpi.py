from multiprocessing import Process, Manager


from AndroidController import AndroidController
from AndroidController import android_msg
from LogsController import event_logger



class RPI:

    def __init__(self):

        self.logger = event_logger()
        self.AC = AndroidController()

        # self.manager = Manager()

        # path mode
        # self.robot_mode = self.manager.Value('i', 1)



    def run(self):
        while True:
            pass

    def start(self):
        self.AC.connect()
        print("can connect?")

        self.AC.send(android_msg(cat="greeting", msg="Hello"))



start_rpi = RPI()
start_rpi.start()