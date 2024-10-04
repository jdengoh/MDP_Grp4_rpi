from algorithm import settings
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.command import Command
from algorithm.entities.grid.position import Position


class StraightCommand(Command):
    def __init__(self, dist):
        """
        Specified distance is scaled. Do not divide the provided distance by the scaling factor!
        """
        # Calculate the time needed to travel the required distance.
        time = abs(dist / settings.ROBOT_SPEED_PER_SECOND)
        super().__init__(time)

        self.dist = dist

    def __str__(self):
        return f"StraightCommand(dist={self.dist / settings.SCALING_FACTOR}, {self.total_ticks} ticks)"

    __repr__ = __str__

    def process_one_tick(self, robot):
        if self.total_ticks == 0:
            return

        self.tick()
        distance = self.dist / self.total_ticks
        robot.straight(distance)
        # print(distance)
        # return distance

    def apply_on_pos(self, curr_pos: Position):
        """
        Apply this command onto a current Position object.
        """
        if curr_pos.direction == Direction.RIGHT:
            curr_pos.x += self.dist
        elif curr_pos.direction == Direction.TOP:
            curr_pos.y += self.dist
        elif curr_pos.direction == Direction.BOTTOM:
            curr_pos.y -= self.dist
        else:
            curr_pos.x -= self.dist

        return self

    def convert_to_message(self):
        # MESSAGE: fXXXX for forward, bXXXX for backward.
        # XXXX is the distance in decimal in centimeters.

        # Note that the distance is now scaled.
        # Therefore, we need to de-scale it.
        """
        Conversion to a message that is easy to send over the RPi.
        RPI needs in this format: a,b,abc,c, 1digit,1digit,3digit,1digit
        first: decides if go straight or turn, 1 is straight, 0 is turn
        second: if go straight, forward or backwards, 1 is forward, 0 is reverse
        third: distance, only applies if first argument is 1. unit in cm
        fourth: only applies if turning, 1 is turn right, 0 is turn left
        have default argument,
        """
        descaled_distance = int(self.dist // settings.SCALING_FACTOR)
        # Check if forward or backward.
        if descaled_distance < 0:
            # It is a backward command.
            command_string = "1,0," + '{:0>3}'.format(abs(descaled_distance)) + ",0"
            # return f"b{abs(descaled_distance):04}"
            return command_string
        # Else, it is a forward command.
        # return f"f{descaled_distance:04}"
        command_string = "1,1," + '{:0>3}'.format(descaled_distance) + ",0"
        return command_string
