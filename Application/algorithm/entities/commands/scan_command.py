from algorithm.entities.commands.command import Command


class ScanCommand(Command):
    def __init__(self, duration, object_index):
        """
        Initializes a scanning command for a specified duration and target object index.

        Args:
            duration (float): Time duration for the scan command.
            object_index (int): Index of the object to be scanned.
        """
        super().__init__(duration)  # Call the superclass constructor to initialize time.
        self.object_index = object_index  # Store the object index for future reference.

    def __str__(self):
        return f"ScanCommand(time={self.time}, object_index={self.object_index})"

    __repr__ = __str__

    def process_one_tick(self, robot):
        """
        Executes one tick of the scan command. This method updates the tick count.

        Args:
            robot: The robot instance executing the scan.
        """
        if self.total_ticks == 0:
            return  # Exit if the command has already completed.

        self.tick()  # Increment the tick counter for this command.

    def apply_on_pos(self, curr_pos):
        """
        Applies the scan command to the current position. This method is a placeholder 
        and does not modify the position since scanning does not affect physical location.

        Args:
            curr_pos: The current position of the robot.
        """
        pass  # No positional changes are made during scanning.

    def convert_to_message(self):
        """
        Converts the scan command into a message format suitable for communication.

        Returns:
            str: A simple command indicating the stop action.
        """
        command_string = 'stop'  # Message to indicate the scan has been initiated or stopped.
        return command_string  # Return the command message.
