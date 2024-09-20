from abc import ABC, abstractmethod
from LogsController import event_logger
from typing import Optional


class BaseController(ABC):

    def __init__(self):
        self.logger = event_logger()

    def send(self, msg: str) -> None:
        pass

    def receive(self) -> Optional[str]:
        pass