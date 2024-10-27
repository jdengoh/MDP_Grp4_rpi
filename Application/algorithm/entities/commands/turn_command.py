import math
from algorithm import configs
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.command import Command
from algorithm.entities.grid.position import Position, RobotPosition


class TurnCommand(Command):
    def __init__(self, angle, rev):
        """
        Initializes the turn command with the specified angle and rotation direction.
        
        Parameters:
        angle (float): The angle to turn, in degrees.
        rev (bool): Indicates if the turn is in reverse. 
                    A negative angle will always result in a clockwise rotation.

        The time to complete the turn is calculated based on the angle and robot's specifications.
        """
        # Calculate the time required for the turn based on the angle and direction of rotation.
        if (angle < 0 and rev) or (angle >= 0 and not rev):
            time = abs((math.radians(angle) * configs.ROBOT_LENGTH) /
                        (configs.ROBOT_SPEED * configs.ROBOT_LEFT_TURN_FACTOR))
        else:
            time = abs((math.radians(angle) * configs.ROBOT_LENGTH) /
                        (configs.ROBOT_SPEED * configs.ROBOT_RIGHT_TURN_FACTOR))
        super().__init__(time)

        self.angle = angle  # Angle to turn in degrees
        self.rev = rev  # Reverse flag for the turn direction

    def __str__(self):
        """Returns a string representation of the TurnCommand object."""
        return f"TurnCommand({self.angle:.2f} degrees, {self.total_ticks} ticks, rev={self.rev})"

    __repr__ = __str__

    def process_one_tick(self, robot, original_direction):
        """
        Processes a single tick of the turn command.
        
        This method updates the robot's direction based on the angle and the total ticks.
        """
        if self.total_ticks == 0:
            return  # No ticks left to process

        self.tick()  # Update the tick count
        angle_per_tick = self.angle / self.total_ticks
        robot.turn(angle_per_tick, self.rev, original_direction)  # Execute the turn for this tick

    def apply_on_pos(self, curr_pos: Position, original_direction: Direction):
        """
        Updates the current position based on the turn command.

        The new position is calculated using the turning radius and the angle to turn.
        
        Parameters:
        curr_pos (Position): The current position of the robot.
        original_direction (Direction): The original direction of the robot.
        """
        # Ensure correct types for parameters
        assert isinstance(curr_pos, RobotPosition), "Cannot apply turn command on non-robot positions!"
        assert isinstance(original_direction, Direction), "Original direction must be a Direction enum!"
        
        # Calculate changes in x and y coordinates based on the angle and current position
        x_change_1 = configs.ROBOT_RIGHT_TURN_RADIUS_X * (math.sin(math.radians(curr_pos.angle + self.angle)) -
                                                            math.sin(math.radians(curr_pos.angle)))
        y_change_1 = configs.ROBOT_RIGHT_TURN_RADIUS_Y * (math.cos(math.radians(curr_pos.angle + self.angle)) -
                                                            math.cos(math.radians(curr_pos.angle)))

        x_change_2 = configs.ROBOT_RIGHT_TURN_RADIUS_Y * (math.sin(math.radians(curr_pos.angle + self.angle)) -
                                                            math.sin(math.radians(curr_pos.angle)))
        y_change_2 = configs.ROBOT_RIGHT_TURN_RADIUS_X * (math.cos(math.radians(curr_pos.angle + self.angle)) -
                                                            math.cos(math.radians(curr_pos.angle)))

        # Determine the movement based on the angle and direction of rotation
        if (self.angle < 0 and self.rev) or (self.angle >= 0 and not self.rev):
            # Turning right while moving forward or left while moving backward
            if (self.angle >= 0 and not self.rev):
                if original_direction == Direction.TOP or original_direction == Direction.BOTTOM:
                    curr_pos.x += x_change_1
                    curr_pos.y -= y_change_1
                elif original_direction == Direction.RIGHT or original_direction == Direction.LEFT:
                    curr_pos.x += x_change_2
                    curr_pos.y -= y_change_2
            if (self.angle < 0 and self.rev):
                if original_direction == Direction.RIGHT or original_direction == Direction.LEFT:
                    curr_pos.x += x_change_1
                    curr_pos.y -= y_change_1
                elif original_direction == Direction.TOP or original_direction == Direction.BOTTOM:
                    curr_pos.x += x_change_2
                    curr_pos.y -= y_change_2

        else:  # Wheels to the right while moving forward or backward
            if not self.rev:
                if original_direction == Direction.TOP or original_direction == Direction.BOTTOM:
                    curr_pos.x -= x_change_1
                    curr_pos.y += y_change_1
                elif original_direction == Direction.RIGHT or original_direction == Direction.LEFT:
                    curr_pos.x -= x_change_2
                    curr_pos.y += y_change_2
            else:
                if original_direction == Direction.LEFT or original_direction == Direction.RIGHT:
                    curr_pos.x -= x_change_1
                    curr_pos.y += y_change_1
                elif original_direction == Direction.TOP or original_direction == Direction.BOTTOM:
                    curr_pos.x -= x_change_2
                    curr_pos.y += y_change_2

        # Update the current angle of the robot and normalize it
        curr_pos.angle += self.angle
        if curr_pos.angle < -180:
            curr_pos.angle += 360  # Normalize angle to [0, 360)
        elif curr_pos.angle >= 180:
            curr_pos.angle -= 360  # Normalize angle to (-180, 180]

        # Update the Position's direction based on the new angle
        if 45 <= curr_pos.angle <= 135:
            curr_pos.direction = Direction.TOP
        elif -45 < curr_pos.angle < 45:
            curr_pos.direction = Direction.RIGHT
        elif -135 <= curr_pos.angle < -45:
            curr_pos.direction = Direction.BOTTOM
        else:
            curr_pos.direction = Direction.LEFT

        return self

    def convert_to_message(self):
        """
        Converts the turn command to a message format suitable for sending over the Raspberry Pi.

        The message format is: [a,b,cde,f]
        - a: 0 for turn, 1 for straight
        - b: 0 for backward, 1 for forward (only applicable if going straight)
        - cde: distance in cm (only applies if going straight)
        - f: 0 for left turn, 1 for right turn (only applicable if turning)
        
        Returns:
        str: The formatted command string.
        """
        if self.angle > 0 and not self.rev:  # Forward left turn
            if self.angle < 70:
                t = int(self.angle)
                command_string = f"0,1,{t:03d},0"  # Zero-padded to three digits
            else:
                command_string = "0,1,090,0"  # Default value for larger angles
            return command_string
        elif self.angle > 0 and self.rev:  # Backward left turn
            if self.angle < 70:
                t = int(self.angle)
                command_string = f"0,0,{t:03d},1"
            else:
                command_string = "0,0,090,1"  # Default value for larger angles
            return command_string
        elif self.angle < 0 and not self.rev:  # Forward right turn
            if abs(self.angle) < 70:
                t = int(abs(self.angle))
                command_string = f"0,1,{t:03d},1"
            else:
                command_string = "0,1,090,1"
            return command_string
        else:  # Backward right turn
            if abs(self.angle) < 70:
                t = int(abs(self.angle))
                command_string = f"0,0,{t:03d},0"
            else:
                command_string = "0,0,090,0"
            return command_string
