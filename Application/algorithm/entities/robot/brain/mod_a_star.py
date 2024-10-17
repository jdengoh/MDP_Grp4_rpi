import math
import time
from queue import PriorityQueue
from typing import List, Tuple

from algorithm import settings
from algorithm.entities.commands.command import Command
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.commands.turn_command import TurnCommand
from algorithm.entities.grid.grid import Grid
from algorithm.entities.grid.node import Node
from algorithm.entities.grid.position import RobotPosition

class ModifiedAStar:
    def __init__(self, grid, brain, start: RobotPosition, possible_ends: List[RobotPosition]):
        # We use a copy of the grid rather than use a reference
        # to the exact grid.
        self.grid = grid
        self.nodes = self.grid.nodes
        self.cache = self.grid.cache
        self.brain = brain

        self.start = start
        self.possible_ends = possible_ends
        self.possible_xy = [end.xy() for end in possible_ends]

    def get_neighbours(self, pos: RobotPosition) -> List[Tuple[Node, RobotPosition, int, Command]]:
        """
        Get movement neighbours from this position.

        Note that all values in the Position object (x, y, direction) are all with respect to the grid!

        We also expect the return Positions to be with respect to the grid.
        """
        # We assume the robot will always make a full 90-degree turn to the next neighbour, and that it will travel
        # a fix distance of 10 when travelling straight.
        neighbours = []

        # Check travel straights.
        straight_dist = settings.UNIT_STRAIGHT * settings.SCALING_FACTOR
        straight_commands = [
            StraightCommand(straight_dist),
            StraightCommand(-straight_dist),
        ]
        for c in straight_commands:
            # Check if doing this command does not bring us to any invalid position.
            after, p = self.check_valid_command(c, pos) #! Heavy, pos is current position, c is command, after is new position
            if after:
                travel_weight = c.dist
                neighbours.append((after, p, straight_dist, c))

        # Check turns
        turn_penalty = settings.PATH_TURN_COST
        turn_commands = [
            TurnCommand(90, False),  # Forward right turn
            TurnCommand(-90, False),  # Forward left turn
            TurnCommand(90, True),  # Reverse with wheels to right.
            TurnCommand(-90, True),  # Reverse with wheels to left.
        ]
        for c in turn_commands:
            # Check if doing this command does not bring us to any invalid position.
            after, p = self.check_valid_command(c, pos) #! Heavy
            if after:
                neighbours.append((after, p, turn_penalty, c))
        return neighbours

    def check_valid_position(self, pos):
        x = int(pos.x)
        y = int(pos.y)
        if self.cache.get((x, y)) is not None:
            return self.cache[(x, y)]
        else:
            return False

    def check_valid_command(self, command: Command, p: RobotPosition):
        """
        Checks if a command will bring a point into any invalid position.

        If invalid, we return None for both the resulting grid location and the resulting position.
        """
        # Check specifically for validity of turn command.
        p = p.copy()
        if isinstance(command, TurnCommand):
            p_c = p.copy()
            original_direction = p_c.direction
            for tick in range(command.ticks // settings.PATH_TURN_CHECK_GRANULARITY):
                tick_command = TurnCommand(command.angle / (command.ticks // settings.PATH_TURN_CHECK_GRANULARITY),
                                           command.rev)
                tick_command.apply_on_pos(p_c, original_direction)
                x = int(p_c.x)
                y = int(p_c.y)
                if self.cache.get((x, y)) is not None:
                    v1 = self.cache[(x, y)]
                else:
                    v1 = False
                col_num = x // settings.GRID_CELL_LENGTH
                row_num = settings.GRID_NUM_GRIDS - (y // settings.GRID_CELL_LENGTH) - 1
                if row_num < 0 or col_num < 0 or row_num >= len(self.nodes) or col_num >= len(self.nodes[0]):
                    v2 = None
                else:
                    v2 = self.nodes[row_num][col_num]
                if not (v1 and v2):
                    return None, None
        if isinstance(command, TurnCommand):
            command.apply_on_pos(p, p.direction)
        else:
            command.apply_on_pos(p)
        x = int(p.x)
        y = int(p.y)
        if self.cache.get((x, y)) is not None:
            v1 = self.cache[(x, y)]
        else:
            v1 = False
        after = self.grid.get_coordinate_node(*p.xy())
        if v1 and after:
            after.pos.direction = p.direction
            return after.copy(), p
        # ! Check valid position is heavy
        return None, None

    def heuristic(self, curr_pos: RobotPosition):
        """
        Measure the difference in distance between the provided position and the
        end position.
        """
        t = 10000
        for i in range(len(self.possible_xy)):
            x_d = self.possible_xy[i][0] - curr_pos.x
            y_d = self.possible_xy[i][1] - curr_pos.y
            t = min(t, abs(x_d) + abs(y_d))
        return t
    

    def start_astar(self, get_target=False):
        frontier = PriorityQueue()  # Store frontier nodes to travel to.
        backtrack = dict()  # Store the sequence of nodes being travelled.
        cost = dict()  # Store the cost to travel from start to a node.

        # We can check what the goal node is
        goal_nodes = []
        for end in self.possible_ends:
            goal_node = self.grid.get_coordinate_node(*end.xy()).copy()  # Take note of copy!
            goal_node.pos.direction = end.direction  # Set the required direction at this node.
            goal_nodes.append(goal_node)

        # Add starting node set into the frontier.
        start_node: Node = self.grid.get_coordinate_node(*self.start.xy()).copy()  # Take note of copy!
        start_node.direction = self.start.direction  # Make the node know which direction the robot is facing.

        offset = 0  # Used to tie-break.
        frontier.put((0, offset, (start_node, self.start)))  # Extra time parameter to tie-break same priority.
        cost[start_node] = 0
        backtrack[start_node] = (None, None)  # Parent, Command
        
        while not frontier.empty():  # While there are still nodes to process.
            priority, _, (current_node, current_position) = frontier.get()
            for i, goal_node in enumerate(goal_nodes):
                if current_node.x == goal_node.x and current_node.y == goal_node.y and current_node.direction == goal_node.pos.direction:
                    self.extract_commands(backtrack, goal_node)
                    if not get_target:
                        return current_position
                    else:
                        return current_position, i

            for new_node, new_pos, weight, c in self.get_neighbours(current_position):
                new_cost = cost.get(current_node) + weight

                if new_node not in backtrack or new_cost < cost[new_node]:
                    offset += 1
                    priority = new_cost + self.heuristic(new_pos)

                    frontier.put((priority, offset, (new_node, new_pos)))
                    backtrack[new_node] = (current_node, c)
                    cost[new_node] = new_cost
        return None

    def extract_commands(self, backtrack, goal_node):
        """
        Extract required commands to get to destination.
        """
        commands = []
        curr = goal_node
        while curr:
            curr, c = backtrack.get(curr, (None, None))
            if c:
                commands.append(c)
        commands.reverse()
        self.brain.commands.extend(commands)
