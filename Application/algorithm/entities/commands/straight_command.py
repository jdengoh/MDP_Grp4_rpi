from algorithm import configs
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.command import Command
from algorithm.entities.grid.position import Position


class StraightCommand(Command):
    def __init__(self, distance):
        """
        Initializes a command to move straight a specified distance.

        Args:
            distance (float): The distance to move, which should not be scaled down.
        """
        # Calculate the time required to travel the specified distance using the robot's speed.
        time = abs(distance / configs.ROBOT_SPEED)
        super().__init__(time)

        self.distance = distance  # Store the original distance value.

    def __str__(self):
        return f"StraightCommand(distance={self.distance / configs.SCALING_FACTOR:.2f}, ticks={self.total_ticks})"

    __repr__ = __str__

    def process_one_tick(self, robot):
        """
        Processes a single tick of the command, moving the robot forward by a portion of the total distance.

        Args:
            robot: The robot instance to move.
        """
        if self.total_ticks == 0:
            return  # No movement if the command is complete.

        self.tick()  # Advance the tick count.
        distance_per_tick = self.distance / self.total_ticks  # Calculate distance to move in this tick.
        robot.straight(distance_per_tick)  # Move the robot straight by the calculated distance.

    def apply_on_pos(self, curr_pos: Position):
        """
        Updates the robot's current position based on its direction and the distance to move.

        Args:
            curr_pos (Position): The current position of the robot.

        Returns:
            self: The current instance of StraightCommand for chaining.
        """
        # Update the position based on the current direction.
        if curr_pos.direction == Direction.RIGHT:
            curr_pos.x += self.distance
        elif curr_pos.direction == Direction.TOP:
            curr_pos.y += self.distance
        elif curr_pos.direction == Direction.BOTTOM:
            curr_pos.y -= self.distance
        else:  # Direction.LEFT
            curr_pos.x -= self.distance

        return self  # Return the command instance for potential chaining.

    def convert_to_message(self):
        """
        Converts the command into a string format suitable for communication with the Raspberry Pi.

        Returns:
            str: Formatted message representing the command.
        """
        # De-scale the distance to convert it into centimeters.
        descaled_distance = int(self.distance // configs.SCALING_FACTOR)

        # Prepare the command message based on the movement direction.
        if descaled_distance < 0:
            # If the distance is negative, it indicates a backward movement.
            command_string = f"1,0,{abs(descaled_distance):03},0"
        else:
            # If positive, it indicates a forward movement.
            command_string = f"1,1,{descaled_distance:03},0"

        return command_string  # Return the constructed command message.
