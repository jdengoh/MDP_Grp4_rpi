import serial
from BaseController import BaseController


class STM32Controller(BaseController):

    def __init__(self):

        super().__init__()
        self.serial_link = None

    def connect(self): 
        # SERIAL_PORT = '/dev/ttyS0' # WHEN DISCONNECTED
        SERIAL_PORT = '/dev/ttyUSB0'
        BAUD_RATE = 115200
        self.serial_link = serial.Serial(SERIAL_PORT, BAUD_RATE)
        self.logger.info(f"Connected to STM32 on {SERIAL_PORT}")

    def disconnect(self):
        self.serial_link.close()
        self.serial_link = None
        self.logger.info(f"Disconnected from STM32 on {SERIAL_PORT}")

    def send(self, msg: str) -> None:
        # Send message to STM32
        self.serial_link.write(f"{msg}".encode('utf-8'))
        self.logger.info(f"Sent to STM32: {msg}")

    def receive(self) -> None:
        # Read 4 bytes from serial link
        msg = self.serial_link.read(4).decode('utf-8')
        self.logger.info(f"Received from STM32: {msg}")
        return msg

    

