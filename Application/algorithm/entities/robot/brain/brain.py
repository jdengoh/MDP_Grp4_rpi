import itertools
from collections import deque

from algorithm import settings
from algorithm.entities.commands.scan_command import ScanCommand
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.robot.brain.mod_a_star import ModifiedAStar


class Brain:
    def __init__(self, robot, grid):
        self.robot = robot
        self.grid = grid

        # Compute simple Hamiltonian paths for all obstacles
        self.simple_hamiltonian = []

        # Create all the commands required to finish the course.
        self.commands = deque()

    def compute_simple_hamiltonian_path(self):
        """
        Get the Hamiltonian Path to all points with the best possible effort.
        This is a simple calculation where we assume that we travel directly to the next obstacle.
        """
        # Generate all possible permutations for the image obstacles
        perms = list(itertools.permutations(self.grid.obstacles))
        
        # Get the path that has the least distance travelled.
        def calc_distance(path):
            # Create all target points, including the start.
            targets = [self.robot.pos.xy_pygame()]
            for obstacle in path:
                targets.append(obstacle.pos.xy_pygame())

            dist = 0
            for i in range(len(targets) - 1):
                # dist += math.sqrt(((targets[i][0] - targets[i + 1][0]) ** 2) +
                #                   ((targets[i][1] - targets[i + 1][1]) ** 2))
                dist += abs(targets[i][0] - targets[i + 1][0]) + abs(targets[i][1] - targets[i + 1][1])
            return dist
        
        perms.sort(key=calc_distance);
        print("Found simple hamiltonian paths")
        return perms

    def compress_paths(self):
        """
        Compress similar commands into one command.

        Helps to reduce the number of commands.
        """
        print("Compressing commands... ", end="")
        index = 0
        new_commands = deque()
        while index < len(self.commands):
            command = self.commands[index]
            if isinstance(command, StraightCommand):
                new_length = 0
                while index < len(self.commands) and isinstance(self.commands[index], StraightCommand):
                    new_length += self.commands[index].dist
                    index += 1
                command = StraightCommand(new_length)
                new_commands.append(command)
            else:
                new_commands.append(command)
                index += 1
        self.commands = new_commands
        print("Done!")

    def plan_path(self):
        print("-" * 40)
        print("STARTING PATH COMPUTATION...")
        if len(self.grid.obstacles) <= 4:
            consider = 20 #20
        elif len(self.grid.obstacles) > 4:
            consider = 5 #for testing, use 50 normally
        paths = self.compute_simple_hamiltonian_path()[0:consider]
        print(f"Considering", consider, "paths")
        print()
        orders = []

        def calc_actual_distance(path):

            string_commands = [command.convert_to_message() for command in self.commands]
            total_dist = 0
            for command in string_commands:
                parts = command.split(",")
                if parts[0] == "1":  # straight
                    total_dist += int(parts[2])
                if parts[0] == "0":  # turn
                    total_dist += int(100)
            string_commands.append("finish")
            return total_dist

        index = 0
        for path in paths:
            self.simple_hamiltonian = path
            self.commands.clear()
            order = []

            print()
            print("Path {}:".format(index + 1))

            curr = self.robot.pos.copy()  # We use a copy rather than get a reference.
            for obstacle in self.simple_hamiltonian:
                target = obstacle.get_robot_target_pos()
                print(f"Planning {curr} to {target}")
                res = ModifiedAStar(self.grid, self, curr, target).start_astar()
                if res is None:
                    print(f"\tNo path found from {curr} to {obstacle}")
                else:
                    print("\tPath found.")
                    curr = res
                    self.commands.append(ScanCommand(settings.ROBOT_SCAN_TIME, obstacle.index))
                    order.append(obstacle.index)
            orders.append((order, index, calc_actual_distance(paths[index])))
            index += 1

        shortest = 10000
        for item in orders:
            if item[2] < shortest:
                shortest = item[2]
                best_index = item[1]

        # clear commands, input commands for shortest path
        self.simple_hamiltonian = paths[best_index]
        self.commands.clear()

        curr = self.robot.pos.copy()  # We use a copy rather than get a reference.
        for obstacle in self.simple_hamiltonian:
            target = obstacle.get_robot_target_pos()
            print(f"Planning {curr} to {target}")
            res = ModifiedAStar(self.grid, self, curr, target).start_astar()
            if res is None:
                print(f"\tNo path found from {curr} to {obstacle}")
            else:
                print("\tPath found.")
                curr = res
                self.commands.append(ScanCommand(settings.ROBOT_SCAN_TIME, obstacle.index))

        self.compress_paths()
        print(best_index)
        print("-" * 40)
        return orders[best_index][0]
