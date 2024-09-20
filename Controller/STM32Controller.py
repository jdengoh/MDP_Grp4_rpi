import serial
from settings import SERIAL_PORT, BAUD_RATE

from . import BaseController


class STM32Controller(BaseController):

    def __innit__(self):
        super().__init__()
        self.serial_link = None

    def connect(self):
        self.serial_link = serial.Serial(SERIAL_PORT, BAUD_RATE)
        self.logger.info(f"Connected to STM32 on {SERIAL_PORT}")

    def disconnect(self):
        self.serial_link.close()
        self.serial_link = None
        self.logger.info(f"Disconnected from STM32 on {SERIAL_PORT}")

    def send(self, msg: str) -> None:

        self.serial_link.write(f"{msg}\n".encode('utf-8'))
        self.logger.info(f"Sent to STM32: {msg}")

    def receive(self) -> None:
        msg = self.serial_link.readline().decode('utf-8').strip()
        self.logger.info(f"Received from STM32: {msg}")
        return msg

    

