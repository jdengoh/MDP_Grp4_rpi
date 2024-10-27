import math
from abc import ABC, abstractmethod

from algorithm import configs


class Command(ABC):
    def __init__(self, duration):
        """
        Initializes a command with a specified duration.

        Args:
            duration (float): The time in seconds for which this command will be active.
        """
        self.time = duration  # Duration of the command in seconds.
        self.ticks = math.ceil(duration * configs.FRAMES)  # Calculate total ticks based on frames per second.
        self.total_ticks = self.ticks  # Store the original total ticks for reference.

    def tick(self):
        """Decrement the tick count by one to indicate the passage of time."""
        self.ticks -= 1  # Reduce the remaining ticks by one.

    @abstractmethod
    def process_one_tick(self, robot):
        """
        Process the command for one tick. This method should be implemented by subclasses.

        Args:
            robot: The robot instance that will execute this command.
        """
        # This method must call tick() to manage command timing.
        pass

    @abstractmethod
    def apply_on_pos(self, curr_pos):
        """
        Apply the command to a given position. This method should update the position's attributes
        to reflect any changes after executing the command.

        Args:
            curr_pos: The current position of the robot.

        Returns:
            Command: Returns itself for chaining or further processing.
        """
        pass

    @abstractmethod
    def convert_to_message(self):
        """
        Convert the command into a format suitable for transmission over the Raspberry Pi (RPi).

        The format required by the RPi is: a,b,abc,c, where:
        - a: 1 for moving straight, 0 for turning.
        - b: 1 for moving forward, 0 for reverse (only if moving straight).
        - abc: distance in centimeters (only if moving straight).
        - c: 1 for turning right, 0 for turning left (only if turning).
        """
        pass
