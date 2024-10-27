from queue import PriorityQueue
from typing import List, Tuple

from algorithm import configs
from algorithm.entities.commands.command import Command
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.commands.turn_command import TurnCommand
from algorithm.entities.grid.node import Node
from algorithm.entities.grid.position import RobotPosition

class ModifiedAStar:
    def __init__(self, grid, brain, start: RobotPosition, possible_ends: List[RobotPosition]):
        # Create a copy of the grid to work with rather than modifying the original grid directly
        self.grid = grid
        self.nodes = self.grid.nodes
        self.cache = self.grid.cache  # Cache to store already evaluated nodes
        self.brain = brain

        self.start = start
        self.possible_ends = possible_ends
        self.possible_xy = [end.xy_coords() for end in possible_ends]  # List of possible endpoint coordinates

    def get_neighbours(self, pos: RobotPosition) -> List[Tuple[Node, RobotPosition, int, Command]]:
        """
        Retrieves valid neighboring positions for a given robot position on the grid.
        Coordinates returned here are relative to the grid.
        """
        neighbours = []  # Store valid neighboring nodes

        # Straight-line moves in both forward and reverse directions
        straight_dist = configs.UNIT_STRAIGHT * configs.SCALING_FACTOR
        straight_commands = [StraightCommand(straight_dist), StraightCommand(-straight_dist)]
        
        # Test all straight-line moves and add to neighbors if valid
        for command in straight_commands:
            next_node, next_position = self.check_valid_command(command, pos)
            if next_node:
                neighbours.append((next_node, next_position, straight_dist, command))

        # Turn commands with penalties for different directional adjustments
        turn_penalty = configs.PATH_TURN_COST
        turn_commands = [
            TurnCommand(90, False),   # 90-degree right turn (forward)
            TurnCommand(-90, False),  # 90-degree left turn (forward)
            TurnCommand(90, True),    # 90-degree right turn (reverse)
            TurnCommand(-90, True)    # 90-degree left turn (reverse)
        ]

        # Test all turn commands and add to neighbors if valid
        for command in turn_commands:
            next_node, next_position = self.check_valid_command(command, pos)
            if next_node:
                neighbours.append((next_node, next_position, turn_penalty, command))

        return neighbours

    def check_valid_command(self, command: Command, pos: RobotPosition):
        """
        Verifies if executing a command from the current position results in a valid grid position.
        Returns None if the resulting position is invalid.
        """
        # Check specifically for validity of turn command.
        pos = pos.copy()
        if isinstance(command, TurnCommand):
            pos_copy = pos.copy()
            original_direction = pos_copy.direction
            for tick in range(command.ticks // configs.TURN_GRANULARITY):
                tick_command = TurnCommand(command.angle / (command.ticks // configs.TURN_GRANULARITY),
                                           command.rev)
                tick_command.apply_on_pos(pos_copy, original_direction)
                x = int(pos_copy.x)
                y = int(pos_copy.y)
                if self.cache.get((x, y)) is not None:
                    v1 = self.cache[(x, y)]
                else:
                    v1 = False
                col_num = x // configs.GRID_CELL_LENGTH
                row_num = configs.GRID_NUM_GRIDS - (y // configs.GRID_CELL_LENGTH) - 1
                if row_num < 0 or col_num < 0 or row_num >= len(self.nodes) or col_num >= len(self.nodes[0]):
                    v2 = None
                else:
                    v2 = self.nodes[row_num][col_num]
                if not (v1 and v2):
                    return None, None
        if isinstance(command, TurnCommand):
            command.apply_on_pos(pos, pos.direction)
        else:
            command.apply_on_pos(pos)
        x = int(pos.x)
        y = int(pos.y)
        if self.cache.get((x, y)) is not None:
            v1 = self.cache[(x, y)]
        else:
            v1 = False
        after = self.grid.get_coordinate_node(*pos.xy_coords())
        if v1 and after:
            after.pos.direction = pos.direction
            return after.copy(), pos
        # ! Check valid position is heavy
        return None, None
    
    def is_within_bounds(self, x: int, y: int) -> bool:
        """Checks if coordinates are within the grid boundaries."""
        col_num = x // configs.GRID_CELL_LENGTH
        row_num = configs.GRID_NUM_GRIDS - (y // configs.GRID_CELL_LENGTH) - 1
        return 0 <= row_num < len(self.nodes) and 0 <= col_num < len(self.nodes[0])

    def heuristic(self, curr_pos: RobotPosition):
        """
        Heuristic function to estimate cost from current position to nearest endpoint.
        """
        min_dist = float('inf')
        for x, y in self.possible_xy:
            min_dist = min(min_dist, abs(x - curr_pos.x) + abs(y - curr_pos.y))
        return min_dist

    def start_astar(self, get_target=False):
        """Runs the A* algorithm to find the optimal path to the nearest endpoint."""
        frontier = PriorityQueue()
        backtrack = {}
        cost = {}
        
        goal_nodes = [self.grid.get_coordinate_node(*end.xy_coords()).copy() for end in self.possible_ends]
        for goal, end in zip(goal_nodes, self.possible_ends):
            goal.pos.direction = end.direction

        start_node = self.grid.get_coordinate_node(*self.start.xy_coords()).copy()
        start_node.direction = self.start.direction

        frontier.put((0, 0, (start_node, self.start)))
        cost[start_node] = 0
        backtrack[start_node] = (None, None)
        offset = 0  # To avoid tie-breaking issues with PriorityQueue

        while not frontier.empty():
            priority, _, (current_node, current_position) = frontier.get()
            
            for i, goal_node in enumerate(goal_nodes):
                if (current_node.x == goal_node.x and current_node.y == goal_node.y and
                        current_node.direction == goal_node.pos.direction):
                    self.extract_commands(backtrack, goal_node)
                    return (current_position, i) if get_target else current_position

            for next_node, next_position, weight, command in self.get_neighbours(current_position):
                new_cost = cost[current_node] + weight

                if next_node not in cost or new_cost < cost[next_node]:
                    offset += 1
                    frontier.put((new_cost + self.heuristic(next_position), offset, (next_node, next_position)))
                    backtrack[next_node] = (current_node, command)
                    cost[next_node] = new_cost

        return None

    def extract_commands(self, backtrack, goal_node):
        """
        Retrieves the sequence of commands from the backtrack dictionary to reach the goal node.
        """
        commands = []
        current = goal_node
        while current:
            current, command = backtrack.get(current, (None, None))
            if command:
                commands.append(command)
        commands.reverse()
        self.brain.commands.extend(commands)