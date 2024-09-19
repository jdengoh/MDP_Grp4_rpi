from abc import ABC, abstractmethod
import Controller.event_logger as event_logger

class BaseController(ABC):

    def __init__(self):
        self.logger = event_logger()

    def send(self, msg: str) -> None:
        pass

    def receive(self) -> None:
        pass