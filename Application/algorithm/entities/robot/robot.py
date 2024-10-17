import datetime

from algorithm import settings
from algorithm.entities.assets import colors
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.command import Command
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.commands.turn_command import TurnCommand
from algorithm.entities.grid.position import RobotPosition
from algorithm.entities.robot.brain.brain import Brain


class Robot:
    def __init__(self, grid):
        # Note that we assume the robot starts always facing the top.
        # This value will never change, but it will not affect us as the robot uses a more fine-tuned internal
        # angle tracker.
        # self.pos = RobotPosition(settings.ROBOT_START_POSITION,
                                #  settings.ROBOT_START_POSITION,
                                #  Direction.TOP,
                                #  90)
        self.pos = RobotPosition(settings.ROBOT_START_POSITION_X,
                                 settings.ROBOT_START_POSITION_Y,
                                 Direction.TOP,
                                 90)
        self._start_copy = self.pos.copy()

        self.brain = Brain(self, grid)
        self.path_hist = []  # Stores the history of the path taken by the robot.


    def get_current_pos(self):
        return self.pos

    def convert_all_commands(self):
        """
        Convert the list of command objects to corresponding list of messages.
        """
        print("Converting commands to string...", end="")
        string_commands = [command.convert_to_message() for command in self.brain.commands]
        total_dist = 0
        print("srtring commands", string_commands)
        modified_commands=[]
        for command in string_commands:
            tmpcmd = ""
            print(command)
            parts = command.split(",")
            # if (parts[0]!="stop"): print(parts[0]+","+parts[1]+","+parts[2]+","+parts[3])
            if parts[0] == "1": # straight
                total_dist += int(parts[2])

                tmpcmd = tmpcmd+"S"
                
                if parts[1] == "0": # reverse
                    tmpcmd = tmpcmd + "B"
                elif parts[1] == "1": # forward
                    tmpcmd = tmpcmd + "F"

                tmpcmd = tmpcmd + parts[2]

            if parts[0] == "0": # turn
                total_dist += int(100)

                if parts[3] == "0": # turn left
                    tmpcmd = tmpcmd + "L"
                elif parts[3] == "1": # turn right
                    tmpcmd = tmpcmd + "R"

                if parts[1] == "0": # reverse
                    tmpcmd = tmpcmd + "B"
                elif parts[1] == "1": # forward
                    tmpcmd = tmpcmd + "F"
                
                tmpcmd = tmpcmd + parts[2]

            if command == "stop":
                tmpcmd = "P"
            
            # if "LF" in tmpcmd or "RF" in tmpcmd:
            #     modified_commands.append("SF008")
            modified_commands.append(tmpcmd)
                
        string_commands.append("finish")
        modified_commands.append("finish")
        print("total_dist =", total_dist)
        return modified_commands
        return string_commands

    def turn(self, d_angle, rev, original_direction):
        """
        Turns the robot by the specified angle, and whether to do it in reverse or not.
        Take note that the angle is in radians.

        A negative angle will always cause the robot to be rotated in a clockwise manner, regardless
        of the value of rev.

        x_new = x + R(sin(∆θ + θ) − sin θ)
        y_new = y − R(cos(∆θ + θ) − cos θ)
        θ_new = θ + ∆θ
        R is the turning radius.

        Take note that:
            - +ve ∆θ -> rotate counter-clockwise
            - -ve ∆θ -> rotate clockwise

        Note that ∆θ is in radians.
        """
        TurnCommand(d_angle, rev).apply_on_pos(self.pos, original_direction)

    def straight(self, dist):
        """
        Make a robot go straight.

        A negative number indicates that the robot will move in reverse, and vice versa.
        """
        StraightCommand(dist).apply_on_pos(self.pos)
