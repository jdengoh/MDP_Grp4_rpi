import math

from algorithm import settings
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.command import Command
from algorithm.entities.grid.position import Position, RobotPosition


class TurnCommand(Command):
    def __init__(self, angle, rev):
        """
        Angle to turn and whether the turn is done in reverse or not. Note that this is in degrees.

        Note that negative angles will always result in the robot being rotated clockwise.
        """

        if (angle < 0 and rev) or (angle >= 0 and not rev):
            time = abs((math.radians(angle) * settings.ROBOT_LENGTH) /
                   (settings.ROBOT_SPEED_PER_SECOND * settings.ROBOT_LEFT_S_FACTOR))
        else:
            time = abs((math.radians(angle) * settings.ROBOT_LENGTH) /
                   (settings.ROBOT_SPEED_PER_SECOND * settings.ROBOT_RIGHT_S_FACTOR))
        super().__init__(time)

        self.angle = angle
        self.rev = rev

    def __str__(self):
        return f"TurnCommand({self.angle:.2f}degrees, {self.total_ticks} ticks, rev={self.rev})"

    __repr__ = __str__

    def process_one_tick(self, robot, original_direction):
        if self.total_ticks == 0:
            return

        self.tick()
        angle = self.angle / self.total_ticks
        robot.turn(angle, self.rev, original_direction)

    def apply_on_pos(self, curr_pos: Position, original_direction: Direction):
        """
        x_new = x + R(sin(∆θ + θ) − sin θ)
        y_new = y − R(cos(∆θ + θ) − cos θ)
        θ_new = θ + ∆θ
        R is the turning radius.

        Take note that:
            - +ve ∆θ -> rotate counter-clockwise
            - -ve ∆θ -> rotate clockwise

        Note that ∆θ is in radians.
        """
        assert isinstance(curr_pos, RobotPosition), print("Cannot apply turn command on non-robot positions!")
        assert isinstance(original_direction, Direction), print("Original direction must be a Direction enum!")
        x_change_1 = settings.ROBOT_RIGHT_TURN_RADIUS_X * (math.sin(math.radians(curr_pos.angle + self.angle)) -
                                                    math.sin(math.radians(curr_pos.angle)))
        y_change_1 = settings.ROBOT_RIGHT_TURN_RADIUS_Y * (math.cos(math.radians(curr_pos.angle + self.angle)) -
                                                    math.cos(math.radians(curr_pos.angle)))
        
        x_change_2 = settings.ROBOT_RIGHT_TURN_RADIUS_Y * (math.sin(math.radians(curr_pos.angle + self.angle)) -
                                                    math.sin(math.radians(curr_pos.angle)))
        y_change_2 = settings.ROBOT_RIGHT_TURN_RADIUS_X * (math.cos(math.radians(curr_pos.angle + self.angle)) -
                                                        math.cos(math.radians(curr_pos.angle)))

        if (self.angle < 0 and self.rev) or (self.angle >= 0 and not self.rev):
            # Wheels to left moving backwards or forwards.
            # ! Right turns
            if (self.angle >= 0 and not self.rev):
                if original_direction == Direction.TOP:
                    curr_pos.x += x_change_1
                    curr_pos.y -= y_change_1
                elif original_direction == Direction.BOTTOM:
                    curr_pos.x += x_change_1
                    curr_pos.y -= y_change_1
                elif original_direction == Direction.RIGHT:
                    curr_pos.x += x_change_2
                    curr_pos.y -= y_change_2
                elif original_direction == Direction.LEFT:
                    curr_pos.x += x_change_2
                    curr_pos.y -= y_change_2
            if (self.angle < 0 and self.rev):
                if original_direction == Direction.RIGHT:
                    curr_pos.x += x_change_1
                    curr_pos.y -= y_change_1
                elif original_direction == Direction.LEFT:
                    curr_pos.x += x_change_1
                    curr_pos.y -= y_change_1
                elif original_direction == Direction.TOP:
                    curr_pos.x += x_change_2
                    curr_pos.y -= y_change_2
                elif original_direction == Direction.BOTTOM:
                    curr_pos.x += x_change_2
                    curr_pos.y -= y_change_2
                
        else:  # Wheels to right moving backwards forwards.
            if (not self.rev):
                if original_direction == Direction.TOP:
                    curr_pos.x -= x_change_1
                    curr_pos.y += y_change_1
                elif original_direction == Direction.BOTTOM:
                    curr_pos.x -= x_change_1
                    curr_pos.y += y_change_1
                elif original_direction == Direction.RIGHT:
                    curr_pos.x -= x_change_2
                    curr_pos.y += y_change_2
                elif original_direction == Direction.LEFT:
                    curr_pos.x -= x_change_2
                    curr_pos.y += y_change_2
            else:
                if original_direction == Direction.LEFT:
                    curr_pos.x -= x_change_1
                    curr_pos.y += y_change_1
                elif original_direction == Direction.RIGHT:
                    curr_pos.x -= x_change_1
                    curr_pos.y += y_change_1
                elif original_direction == Direction.TOP:
                    curr_pos.x -= x_change_2
                    curr_pos.y += y_change_2
                elif original_direction == Direction.BOTTOM:
                    curr_pos.x -= x_change_2
                    curr_pos.y += y_change_2
                
            
        
                
        curr_pos.angle += self.angle

        if curr_pos.angle < -180:
            curr_pos.angle += 2 * 180
        elif curr_pos.angle >= 180:
            curr_pos.angle -= 2 * 180

        # Update the Position's direction.
        # if 0 < curr_pos.angle <= 90:
        #     curr_pos.direction = Direction.TOP
        # elif -90 < curr_pos.angle <= 0:
        #     curr_pos.direction = Direction.RIGHT
        # elif 0 < curr_pos.angle <= -90:
        #     curr_pos.direction = Direction.BOTTOM
        # else:
        #     curr_pos.direction = Direction.LEFT
        if 45 <= curr_pos.angle <= 3 * 45:
            curr_pos.direction = Direction.TOP
        elif -45 < curr_pos.angle < 45:
            curr_pos.direction = Direction.RIGHT
        elif -45 * 3 <= curr_pos.angle <= -45:
            curr_pos.direction = Direction.BOTTOM
        else:
            curr_pos.direction = Direction.LEFT
        return self

    def convert_to_message(self):
        """
        Conversion to a message that is easy to send over the RPi.
        RPI needs in this format: [a,b,cde,f],
        a: decides if go straight or turn, 1 is straight, 0 is turn
        b: if go straight, forward or backwards, 1 is forward, 0 is reverse
        cde: distance, only applies if first argument is 1. unit in cm
        f: only applies if turning, 1 is turn right, 0 is turn left
        have default argument,
        """
        if self.angle > 0 and not self.rev:
            # This is going forward left.
            if self.angle < 70:
                t = int(self.angle)
                if t >= 10:
                    command_string = f"0,1,0{t},0"
                else:
                    command_string = f"0,1,00{t},0"
            else:
                command_string = "0,1,090,0"
            return command_string
            # return "l0090"  # Note the smaller case L.
        elif self.angle > 0 and self.rev:
            if self.angle < 70:
                t = int(self.angle)
                if t >= 10:
                    command_string = f"0,0,0{t},1"
                else:
                    command_string = f"0,0,00{t},1"
            # This is going backward and with the wheels to the right.
            else:
                command_string = "0,0,090,1"
            return command_string
            # return "R0090"
        elif self.angle < 0 and not self.rev:
            if abs(self.angle < 70):
                t = int(abs(self.angle))
                if t >= 10:
                    command_string = f"0,1,0{t},1"
                else:
                    command_string = f"0,1,00{t},1"
            # This is going backward and with the wheels to the right.
            else:
            # This is going forward right.
                command_string = "0,1,090,1"
            return command_string
            # return "r0090"
        else:
            # This is going backward and with the wheels to the left.
            if abs(self.angle < 70):
                t = int(abs(self.angle))
                if t >= 10:
                    command_string = f"0,0,0{t},0"
                else:
                    command_string = f"0,0,00{t},0"
            # This is going backward and with the wheels to the right.
            else:
                command_string = "0,0,090,0"
            return command_string
            # return "L0090"