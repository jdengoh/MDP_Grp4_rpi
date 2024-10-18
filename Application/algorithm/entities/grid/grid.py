import math
from collections import deque
from typing import List

import time
# from line_profiler import profile

from algorithm import settings
from algorithm.entities.assets import colors
from algorithm.entities.grid.node import Node
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.grid.position import Position


class Grid:
    def __init__(self, obstacles: List[Obstacle]):
        self.obstacles = obstacles
        self.cache = dict()
        self.fill_cache()
        self.nodes = self.generate_nodes()

    # @profile
    def fill_cache(self):
        for x in range(800):
            for y in range(800):
                # Safe is true
                self.cache[(x, y)] = True

        for obstacle in self.obstacles:
            obstacle_x = obstacle.pos.x
            obstacle_y = obstacle.pos.y
            safety_radius = settings.OBSTACLE_SAFETY_WIDTH

            # Iterate through the grid points and mark those within the safety radius as invalid
            for x in range(800):
                for y in range(800):
                    distance = ((x - obstacle_x) ** 2 + (y - obstacle_y) ** 2) ** 0.5
                    if distance < safety_radius:
                        self.cache[(x,y)]=False

        # Check if position too close to the border.
        # NOTE: We allow the robot to overextend the border a little!
        # We do this by setting the limit to be GRID_CELL_LENGTH rather than ROBOT_SAFETY_DISTANCE
        if (y < settings.GRID_CELL_LENGTH or
            y > settings.GRID_LENGTH - settings.GRID_CELL_LENGTH) or \
                (x < settings.GRID_CELL_LENGTH or
                x > settings.GRID_LENGTH - settings.GRID_CELL_LENGTH):
            self.cache[(x, y)] = False

    def generate_nodes(self):
        """
        Generate the nodes for this grid.
        """
        nodes = deque()
        for i in range(settings.GRID_NUM_GRIDS):
            row = deque()
            for j in range(settings.GRID_NUM_GRIDS):
                x, y = (settings.GRID_CELL_LENGTH // 2 + settings.GRID_CELL_LENGTH * j), \
                       (settings.GRID_CELL_LENGTH // 2 + settings.GRID_CELL_LENGTH * i)
                new_node = Node(x, y, not self.check_valid_position(Position(x, y)))
                row.append(new_node)
            nodes.appendleft(row)
        return nodes

    def get_coordinate_node(self, x, y):
        """
        Get the corresponding Node object that contains specified x, y coordinates.

        Note that the x-y coordinates are in terms of the grid, and must be scaled properly.
        """
        col_num = math.floor(x / settings.GRID_CELL_LENGTH)
        row_num = settings.GRID_NUM_GRIDS - math.floor(y / settings.GRID_CELL_LENGTH) - 1
        try:
            return self.nodes[row_num][col_num]
        except IndexError:
            return None

    def copy(self):
        """
        Return a copy of the grid.
        """
        nodes = []
        for row in self.nodes:
            new_row = []
            for col in row:
                new_row.append(col.copy())
            nodes.append(new_row)
        new_grid = Grid(self.obstacles)
        new_grid.nodes = nodes
        return new_grid
    
    def check_valid_position(self, pos: Position):
        """
        Check if a current position can be here.
        """
        # Check if position is inside any obstacle.
        # if any(obstacle.check_within_boundary(*pos.xy()) for obstacle in self.obstacles):
        #     return False
        if self.cache.get((int(pos.x), int(pos.y))) is not None:
            return self.cache[(int(pos.x), int(pos.y))]
        else:

            return False
    
    def check_valid_sight(self, view, target_obstacle):
        """
        Check if a target position can be seen from the current position.
        """
        valid_views = []
        potential_obstructred_obstacles = [ob for ob in self.obstacles if ob != target_obstacle]
        # checking if the target obstacle can be seen from the current position, obstructed by other obstacles
        obstructed = False
        view_x_cm = view.x // settings.SCALING_FACTOR
        view_y_cm = view.y // settings.SCALING_FACTOR
        for ob in potential_obstructred_obstacles:
            if ob.check_within_boundary(view.x, view.y):
                obstructed = True
            
            dis = self.distance_to_segment(view_x_cm, view_y_cm, target_obstacle.x_cm, target_obstacle.y_cm, ob.x_cm, ob.y_cm)
            # print(f"Distance to segment: {dis}, ", view_x_cm, view_y_cm, target_obstacle.x_cm, target_obstacle.y_cm, ob.x_cm, ob.y_cm)
            if dis < 15:
                obstructed = True
            if obstructed:
                break
        
        return not obstructed

    def distance_to_segment(self, x_view, y_view, x_target, y_target, x_obstacle, y_obstacle):
        """
        Calculate the distance from a point (x_obstacle, y_obstacle) to the line segment formed by
        (x_view, y_view) and (x_target, y_target).
        """
        # Calculate the length of the line segment
        segment_length = math.sqrt((x_target - x_view)**2 + (y_target - y_view)**2)
        
        # If the segment length is 0, return the distance to one of the points
        if segment_length == 0:
            return math.sqrt((x_obstacle - x_view)**2 + (y_obstacle - y_view)**2)

        # Calculate the components of the vector from the view point to the obstacle
        dx = x_obstacle - x_view
        dy = y_obstacle - y_view
        
        # Calculate the projection of the vector onto the line segment
        t = max(0, min(segment_length, (dx * (x_target - x_view) + dy * (y_target - y_view)) / (segment_length ** 2)))
        # print("projection", t)
        # Calculate the nearest point on the segment to the obstacle
        nearest_point_x = x_view + t * (x_target - x_view)
        nearest_point_y = y_view + t * (y_target - y_view)
        # print(f"Nearest point: {nearest_point_x}, {nearest_point_y}")
        
        # Calculate the distance between the obstacle and the nearest point on the segment
        distance = math.sqrt((x_obstacle - nearest_point_x)**2 + (y_obstacle - nearest_point_y)**2)
        
        return distance

    def within_threshold(self, x_view, y_view, x_target, y_target, x_obstacle, y_obstacle, threshold):
        """
        Check if the distance from the obstacle (x_obstacle, y_obstacle) to the line segment formed by
        (x_view, y_view) and (x_target, y_target) is within the given threshold.
        """
        distance = distance_to_segment(x_view, y_view, x_target, y_target, x_obstacle, y_obstacle)
        return distance <= threshold
    