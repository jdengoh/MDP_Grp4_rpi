import math
from abc import ABC, abstractmethod

from algorithm import settings


class Command(ABC):
    def __init__(self, time):
        self.time = time  # Time in seconds in which this command is carried out.
        self.ticks = math.ceil(time * settings.FRAMES)  # Number of frame ticks that this command will take.
        self.total_ticks = self.ticks  # Keep track of original total ticks.

    def tick(self):
        self.ticks -= 1

    @abstractmethod
    def process_one_tick(self, robot):
        """
        Overriding method must call tick().
        """
        # return 0
        pass

    @abstractmethod
    def apply_on_pos(self, curr_pos):
        """
        Apply this command to a Position, such that its attributes will reflect the correct values
        after the command is done.

        This method should return itself.
        """
        pass

    @abstractmethod
    def convert_to_message(self):
        """
        Conversion to a message that is easy to send over the RPi.
        RPI needs in this format: a,b,abc,c, 1digit,1digit,3digit,1digit
        first: decides if go straight or turn, 1 is straight, 0 is turn
        second: if go straight, forward or backwards, 1 is forward, 0 is reverse
        third: distance, only applies if first argument is 1. unit in cm
        fourth: only applies if turning, 1 is turn right, 0 is turn left
        have default argument,
        """
        pass

