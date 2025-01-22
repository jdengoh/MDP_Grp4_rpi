from algorithm import configs
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.commands.turn_command import TurnCommand
from algorithm.entities.grid.position import RobotPosition
from algorithm.entities.robot.brain.brain import Brain

class Robot:
    def __init__(self, grid):
        """
        Initializes the Robot's starting position and brain module for path planning.

        Args:
            grid (Grid): Grid in which the robot operates and calculates paths.
        """
        # Set initial position facing 'TOP' direction with a default 90-degree orientation
        self.pos = RobotPosition(configs.ROBOT_X_START_POSITION,
                                 configs.ROBOT_Y_START_POSITION,
                                 Direction.TOP,
                                 90)
        self._start_copy = self.pos.copy()  # Save a copy of the starting position
        self.brain = Brain(self, grid)  # Initialize robot's brain with grid info
        self.path_hist = []  # Store the history of path taken for tracking

    def get_current_pos(self):
        """
        Returns the current position of the robot.
        
        Returns:
            RobotPosition: Current position including coordinates and direction.
        """
        return self.pos

    def convert_all_commands(self):
        """
        Converts a list of robot command objects into their respective command strings for execution.
        
        Returns:
            list: List of strings representing each command, formatted for robot's movement system.
        """
        string_commands = [command.convert_to_message() for command in self.brain.commands]
        total_dist = 0
        modified_commands = []

        for command in string_commands:
            tmpcmd = ""
            parts = command.split(",")
            
            # Handle straight commands
            if parts[0] == "1":  # Command for moving straight
                total_dist += int(parts[2])
                tmpcmd = "S" + ("B" if parts[1] == "0" else "F") + parts[2]

            # Handle turn commands
            elif parts[0] == "0":  # Command for turning
                total_dist += 100  # Increment total distance by assumed value for turn
                tmpcmd = ("L" if parts[3] == "0" else "R") + ("B" if parts[1] == "0" else "F") + parts[2]

            # Handle stop command
            elif command == "stop":
                tmpcmd = "P"

            modified_commands.append(tmpcmd)

        modified_commands.append("finish")  # Mark the end of commands
        print("Total Distance Travelled by Robot =", total_dist, "cm")
        return modified_commands

    def turn(self, d_angle, rev, original_direction):
        """
        Rotates the robot by a specified angle, with an option to reverse.

        Args:
            d_angle (float): The rotation angle in radians.
            rev (bool): True to reverse direction after turning.
            original_direction (Direction): The initial direction before the turn.
        """
        # Apply a turn command to update the robot's position based on angle and direction
        TurnCommand(d_angle, rev).apply_on_pos(self.pos, original_direction)

    def straight(self, dist):
        """
        Moves the robot straight by a specified distance. +ve and -ve allowed

        Args:
            dist (int): The distance to move in cm.
        """
        StraightCommand(dist).apply_on_pos(self.pos)