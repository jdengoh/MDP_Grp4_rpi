import itertools
from collections import deque
import multiprocessing
import math
from multiprocessing.pool import ThreadPool
from algorithm import settings
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.scan_command import ScanCommand
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.commands.turn_command import TurnCommand
from algorithm.entities.robot.brain.mod_a_star import ModifiedAStar


class Brain:
    def __init__(self, robot, grid):
        self.robot = robot
        self.grid = grid

        # Compute simple Hamiltonian paths for all obstacles
        self.simple_hamiltonian = []

        # Create all the commands required to finish the course.
        self.commands = deque()
        print("Brain initialized for robot")

    def compute_simple_hamiltonian_path(self):
        """
        Get the Hamiltonian Path to all points with the best possible effort.
        This is a simple calculation where we assume that we travel directly to the next obstacle.
        """
        # Generate all possible permutations for the image obstacles
        perms = list(itertools.permutations(self.grid.obstacles))

        def calc_distance(path):
            targets = [self.robot]

            dist = 0
            lst_target = targets[0].pos
            for i in range(len(path)):
                obstacle = path[i]
                if len(obstacle.valid_targets) == 0:
                    nxt_target = obstacle.pos  # obstacle itself
                else:
                    nxt_target = obstacle.get_nearest_valid_target(lst_target)

                dist += abs(lst_target.x - nxt_target.x) + abs(lst_target.y - nxt_target.y)
                lst_target = nxt_target
            return dist

        perms.sort(key=calc_distance)
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

    def compress_paths_single(self, commands):
        """
        Compress similar commands into one command.

        Helps to reduce the number of commands.
        """
        print("Compressing commands... ", end="")
        index = 0
        new_commands = deque()
        while index < len(commands):
            command = commands[index]
            if isinstance(command, StraightCommand):
                new_length = 0
                while index < len(commands) and isinstance(commands[index], StraightCommand):
                    new_length += commands[index].dist
                    index += 1
                command = StraightCommand(new_length)
                new_commands.append(command)
            else:
                new_commands.append(command)
                index += 1
        return new_commands

    def plan_path(self):
        print("-" * 40)
        print("STARTING PATH COMPUTATION...")
        if len(self.grid.obstacles) < 4:
            tot = 1
            for i in range(1, len(self.grid.obstacles) + 1):
                tot *= i
            consider = min(settings.NUM_HAM_PATH_CHECK, tot)
        if len(self.grid.obstacles) == 4:
            consider = min(settings.NUM_HAM_PATH_CHECK, 40)
        elif len(self.grid.obstacles) > 4:
            consider = settings.NUM_HAM_PATH_CHECK

        valid_targets = []
        for obstacle in self.grid.obstacles:
            possible_targets = obstacle.get_robot_target_pos()
            valid_targets = []
            bad_sights = 0
            for possible_target in possible_targets:
                if self.grid.check_valid_position(possible_target):
                    if self.grid.check_valid_sight(possible_target, obstacle):
                        valid_targets.append(possible_target)
                    else:
                        bad_sights += 1
            print(f"Obstacle {obstacle.index} has {len(valid_targets)} valid targets and {bad_sights} bad sights")
            obstacle.valid_targets = valid_targets

        paths = self.compute_simple_hamiltonian_path()[0:consider]
        print(f"Considering {consider} paths")
        orders = []

        def process_path(path_index, path, curr):
            commands = []
            order = []
            print(f"Processing path {path_index}...")  # Debug: Start processing a path

            for obstacle in path:
                valid_targets = obstacle.valid_targets
                target_index = obstacle.index  # Use the obstacle index to select the appropriate cache

                # Updated to pass target_index
                astar = ModifiedAStar(self.grid, self, curr, valid_targets, target_index)

                res = astar.start_astar(get_target=False)

                if res is None:
                    print(f"Warning: No path found to obstacle {obstacle.index}. Skipping.")  # Debug: No path found
                else:
                    print(f"Path found to obstacle {obstacle.index}.")  # Debug: Path found
                    curr = res
                    # Only append commands if a path is successfully found
                    self.commands.append(ScanCommand(settings.ROBOT_SCAN_TIME, obstacle.index))
                    order.append(obstacle.index)

            if order:
                string_commands = [command.convert_to_message() for command in self.commands]
                total_dist = 0
                for command in string_commands:
                    parts = command.split(",")
                    if parts[0] == "1":  # straight
                        total_dist += int(parts[2])
                    if parts[0] == "0":  # turn
                        total_dist += int(200)

                commands = self.compress_paths_single(self.commands)
                print(f"Processed path {path_index} with length {len(commands)} and order of recognition",
                      order)  # Debug: Path processed summary
            else:
                print(f"No valid paths were found for path {path_index}. Commands will not be processed.")

            self.commands = []  # Clear commands to avoid unintended reuse
            return order, path_index, total_dist

        def call_back(result):
            orders.append(result)

        def custom_error_callback(error):
            print(f'Got error: {error}')

        if settings.multi_threading:
            pool = ThreadPool(processes=settings.NUM_THREADS)

            for i, path in enumerate(paths):
                pool.apply_async(process_path, args=(i, path, self.robot.pos.copy()), callback=call_back,
                                 error_callback=custom_error_callback)

            # Close the pool and wait for all processes to finish
            pool.close()
            pool.join()
        else:
            for i, path in enumerate(paths):
                orders.append(process_path(i, path, self.robot.pos.copy()))

        shortest = 10000
        for item in orders:
            if item[2] < shortest:
                shortest = item[2]
                best_index = item[1]

        self.simple_hamiltonian = paths[best_index]
        self.commands.clear()
        targets = []

        curr = self.robot.pos.copy()  # We use a copy rather than get a reference.
        for obstacle in self.simple_hamiltonian:
            target = obstacle.get_robot_target_pos()
            astar = ModifiedAStar(self.grid, self, curr, target,obstacle.index)
            p = astar.start_astar(get_target=True)
            if p is None:
                pass
            else:
                res, chose_target = p
                targets.append(target[chose_target])

                curr = res
                current_pos = target[chose_target]
                target_pos = obstacle.pos
                peak_command = None
                reverse_peak_command = None
                right_or_left = None
                if target_pos.direction == Direction.TOP or target_pos.direction == Direction.BOTTOM:
                    ratio = abs(current_pos.x - target_pos.x) / abs(current_pos.y - target_pos.y)
                else:
                    ratio = abs(current_pos.y - target_pos.y) / abs(current_pos.x - target_pos.x)
                theta = math.atan(ratio)
                theta = math.degrees(theta)
                if target_pos.direction == Direction.TOP:
                    if current_pos.x > target_pos.x + settings.peak_horizontal_tolerance:
                        right_or_left = "right"
                    elif current_pos.x < target_pos.x - settings.peak_horizontal_tolerance:
                        right_or_left = "left"
                if target_pos.direction == Direction.BOTTOM:
                    if current_pos.x > target_pos.x + settings.peak_horizontal_tolerance:
                        right_or_left = "left"
                    elif current_pos.x < target_pos.x - settings.peak_horizontal_tolerance:
                        right_or_left = "right"
                if target_pos.direction == Direction.LEFT:
                    if current_pos.y > target_pos.y + settings.peak_horizontal_tolerance:
                        right_or_left = "right"
                    elif current_pos.y < target_pos.y - settings.peak_horizontal_tolerance:
                        right_or_left = "left"
                if target_pos.direction == Direction.RIGHT:
                    if current_pos.y > target_pos.y + settings.peak_horizontal_tolerance:
                        right_or_left = "left"
                    elif current_pos.y < target_pos.y - settings.peak_horizontal_tolerance:
                        right_or_left = "right"
                if right_or_left == "right":
                    peak_command = TurnCommand(-theta, False)
                    reverse_peak_command = TurnCommand(theta, True)
                else:
                    peak_command = TurnCommand(theta, False)
                    reverse_peak_command = TurnCommand(-theta, True)

                # add a peak turn
                if peak_command is not None and reverse_peak_command is not None:
                    if abs(theta) > settings.angle_peak_threshold:
                        self.commands.append(peak_command)
                        pass

                self.commands.append(ScanCommand(settings.ROBOT_SCAN_TIME, obstacle.index))

                if peak_command is not None and reverse_peak_command is not None:
                    if abs(theta) > settings.angle_peak_threshold:
                        self.commands.append(reverse_peak_command)
                        pass
                # add a reverse peak turn

        self.compress_paths()
        print("length of commands", len(self.commands))
        return orders[best_index][0], targets