import itertools
import math

from collections import deque
from algorithm import configs
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.scan_command import ScanCommand
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.commands.turn_command import TurnCommand
from algorithm.entities.robot.brain.mod_a_star import ModifiedAStar

class Brain:
    def __init__(self, robot, grid):
        self.robot = robot
        self.grid = grid
        self.simple_hamiltonian = []  # Stores simplified Hamiltonian paths
        self.commands = deque()  # Command queue for the robot

    def compute_simple_hamiltonian_path(self):
        """
        Generate possible Hamiltonian paths among obstacles, minimizing travel distance.
        """
        perms = list(itertools.permutations(self.grid.obstacles))  # All possible obstacle paths
        
        def calc_distance(path):
            total_distance = 0
            last_pos = self.robot.pos
            for obstacle in path:
                target_pos = obstacle.get_nearest_valid_target(last_pos) if obstacle.valid_targets else obstacle.pos
                total_distance += abs(last_pos.x - target_pos.x) + abs(last_pos.y - target_pos.y)
                last_pos = target_pos
            return total_distance

        perms.sort(key=calc_distance)  # Sort by shortest path
        return perms

    def compress_paths(self):
        """
        Merges consecutive straight commands to minimize command count.
        """
        new_commands = deque()
        index = 0
        while index < len(self.commands):
            command = self.commands[index]
            if isinstance(command, StraightCommand):
                combined_distance = 0
                while index < len(self.commands) and isinstance(self.commands[index], StraightCommand):
                    combined_distance += self.commands[index].distance
                    index += 1
                new_commands.append(StraightCommand(combined_distance))
            else:
                new_commands.append(command)
                index += 1
        self.commands = new_commands

    def compress_paths_single(self, commands):
        """
        Reduces consecutive straight commands within a single path command list.
        """
        new_commands = deque()
        index = 0
        while index < len(commands):
            command = commands[index]
            if isinstance(command, StraightCommand):
                combined_distance = 0
                while index < len(commands) and isinstance(commands[index], StraightCommand):
                    combined_distance += commands[index].dist
                    index += 1
                new_commands.append(StraightCommand(combined_distance))
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
            consider = min(configs.NUM_HAM_PATH_CHECK, tot)
        if len(self.grid.obstacles) == 4:
            consider = min(configs.NUM_HAM_PATH_CHECK,40)
        elif len(self.grid.obstacles) > 4:
            consider = configs.NUM_HAM_PATH_CHECK

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
                        bad_sights+=1
            print(f"Obstacle {obstacle.index} has {len(valid_targets)} valid targets and {bad_sights} bad sights")
            obstacle.valid_targets = valid_targets
        
        paths = self.compute_simple_hamiltonian_path()[0:consider]
        print(f"Considering", consider, "paths")
        orders = []

        def process_path(path_index, path, curr):   
            commands = []
            order = []
            for obstacle in path:
                valid_targets = obstacle.valid_targets
                astar = ModifiedAStar(self.grid, self, curr, valid_targets)
                res = astar.start_astar(get_target=False)
                if res is None:
                    pass
                else:
                    curr = res
                    self.commands.append(ScanCommand(configs.ROBOT_SCANNING_TIME, obstacle.index))
                    order.append(obstacle.index)
            string_commands = [command.convert_to_message() for command in self.commands]
            total_dist = 0
            for command in string_commands:
                parts = command.split(",")
                if parts[0] == "1":  # move forward
                    total_dist += int(parts[2])
                if parts[0] == "0":  # turn
                    total_dist += int(200)
            
            self.commands = []
            
            return order, path_index, total_dist              
        
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
            astar = ModifiedAStar(self.grid, self, curr, target)
            p = astar.start_astar(get_target=True)
            if p is None:
                pass
            else:
                res, chose_target = p                
                targets.append(target[chose_target])
                
                curr = res
                current_pos = target[chose_target]
                target_pos = obstacle.pos
                peek_command = None
                reversed_peek_command = None
                turn_direction = None
                if target_pos.direction == Direction.TOP or target_pos.direction == Direction.BOTTOM:
                    ratio = abs(current_pos.x - target_pos.x) / abs(current_pos.y - target_pos.y)
                else:
                    ratio = abs(current_pos.y - target_pos.y) / abs(current_pos.x - target_pos.x)
                theta = math.atan(ratio)
                theta = math.degrees(theta)
                if target_pos.direction == Direction.TOP:
                    if current_pos.x > target_pos.x + configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "right"
                    elif current_pos.x < target_pos.x - configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "left"
                if target_pos.direction == Direction.BOTTOM:
                    if current_pos.x > target_pos.x + configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "left"
                    elif current_pos.x < target_pos.x - configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "right"
                if target_pos.direction == Direction.LEFT:
                    if current_pos.y > target_pos.y + configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "right"
                    elif current_pos.y < target_pos.y - configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "left"
                if target_pos.direction == Direction.RIGHT:
                    if current_pos.y > target_pos.y + configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "left"
                    elif current_pos.y < target_pos.y - configs.PEEK_HORIZONTAL_THRESHOLD:
                        turn_direction = "right"
                if turn_direction == "right":
                    peek_command = TurnCommand(-theta, False)
                    reversed_peek_command = TurnCommand(theta, True)
                else:
                    peek_command = TurnCommand(theta, False)
                    reversed_peek_command = TurnCommand(-theta, True)
                
                if peek_command is not None and reversed_peek_command is not None:
                    if abs(theta) > configs.PEEK_ANGLE_THRESHOLD:
                        self.commands.append(peek_command)
                        pass
                
                self.commands.append(ScanCommand(configs.ROBOT_SCANNING_TIME, obstacle.index))
                
                if peek_command is not None and reversed_peek_command is not None:
                    if abs(theta) > configs.PEEK_ANGLE_THRESHOLD:
                        self.commands.append(reversed_peek_command)
                        pass
        
        self.compress_paths()
        print("Number of Commands", len(self.commands))
        return orders[best_index][0], targets
