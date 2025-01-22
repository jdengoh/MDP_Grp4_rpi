import math
from collections import deque
from typing import List

from algorithm import configs
from algorithm.entities.grid.node import Node
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.grid.position import Position


class Grid:
    def __init__(self, obstacles: List[Obstacle]):
        """
        Initializes a Grid instance with a list of obstacles.
        
        Parameters:
        obstacles (List[Obstacle]): A list of Obstacle objects that define the grid's boundaries.
        """
        self.obstacles = obstacles  # Store obstacles within the grid.
        self.cache = dict()  # Initialize a cache for quick position validity checks.
        self.fill_cache()  # Populate the cache based on obstacle positions.
        self.nodes = self.generate_nodes()  # Create nodes representing grid positions.

    def fill_cache(self):
        """
        Fill the cache with valid and invalid positions based on obstacles and grid boundaries.
        Positions are marked as invalid if they are within the safety radius of any obstacle.
        """
        # Initially assume all positions are valid.
        for x in range(800):
            for y in range(800):
                self.cache[(x, y)] = True

        # Mark positions around obstacles as invalid based on the safety radius.
        for obstacle in self.obstacles:
            obstacle_x = obstacle.pos.x
            obstacle_y = obstacle.pos.y
            safety_radius = configs.OBSTACLE_SAFETY_WIDTH

            # Iterate through the grid points and invalidate those within the safety radius.
            for x in range(800):
                for y in range(800):
                    distance = math.sqrt((x - obstacle_x) ** 2 + (y - obstacle_y) ** 2)
                    if distance < safety_radius:
                        self.cache[(x, y)] = False

        # Check positions near the grid border to ensure they are valid.
        for x in range(800):
            for y in range(800):
                # Adjust border validity to allow slight overextension for robots.
                if (y < configs.GRID_CELL_LENGTH or y > configs.GRID_LENGTH - configs.GRID_CELL_LENGTH) or \
                   (x < configs.GRID_CELL_LENGTH or x > configs.GRID_LENGTH - configs.GRID_CELL_LENGTH):
                    self.cache[(x, y)] = False

                # Explicitly mark edge positions as valid.
                if x < 30 or x > 770 or y < 30 or y > 770:
                    self.cache[(x, y)] = True

    def generate_nodes(self):
        """
        Create a grid of Node objects based on the specified grid size and cell dimensions.
        
        Returns:
        deque: A deque of rows, each containing Node objects representing the grid.
        """
        nodes = deque()  # Initialize a deque to hold rows of nodes.
        for i in range(configs.GRID_NUM_GRIDS):
            row = deque()  # Create a new row for nodes.
            for j in range(configs.GRID_NUM_GRIDS):
                # Calculate the center coordinates for the node in the grid.
                x = (configs.GRID_CELL_LENGTH // 2) + (configs.GRID_CELL_LENGTH * j)
                y = (configs.GRID_CELL_LENGTH // 2) + (configs.GRID_CELL_LENGTH * i)
                # Create a new Node, marking it occupied based on its validity.
                new_node = Node(x, y, not self.check_valid_position(Position(x, y)))
                row.append(new_node)  # Add the new node to the row.
            nodes.appendleft(row)  # Add the row of nodes to the grid.
        return nodes  # Return the complete grid of nodes.

    def get_coordinate_node(self, x, y):
        """
        Retrieve the Node object that corresponds to the specified grid coordinates.
        
        Parameters:
        x (int): The x-coordinate in grid terms.
        y (int): The y-coordinate in grid terms.

        Returns:
        Node or None: The corresponding Node object, or None if out of bounds.
        """
        col_num = math.floor(x / configs.GRID_CELL_LENGTH)
        row_num = configs.GRID_NUM_GRIDS - math.floor(y / configs.GRID_CELL_LENGTH) - 1
        try:
            return self.nodes[row_num][col_num]  # Return the corresponding node.
        except IndexError:
            return None  # Return None if the coordinates are out of bounds.

    def copy(self):
        """
        Create and return a copy of the current grid with the same obstacle configuration.
        
        Returns:
        Grid: A new Grid instance that is a copy of the current one.
        """
        nodes = []  # List to hold the copied node rows.
        for row in self.nodes:
            new_row = [col.copy() for col in row]  # Copy each node in the row.
            nodes.append(new_row)  # Add the copied row to the list.
        new_grid = Grid(self.obstacles)  # Create a new Grid with the same obstacles.
        new_grid.nodes = nodes  # Assign the copied nodes to the new grid.
        return new_grid  # Return the copied grid.

    def check_valid_position(self, pos: Position):
        """
        Determine if a given position is valid within the grid.
        
        Parameters:
        pos (Position): The Position object representing the coordinates to check.

        Returns:
        bool: True if the position is valid; False otherwise.
        """
        # Check the cache for the validity of the specified position.
        if self.cache.get((int(pos.x), int(pos.y))) is not None:
            return self.cache[(int(pos.x), int(pos.y))]
        else:
            return False  # Return False if the position is not found in the cache.

    def check_valid_sight(self, view, target_obstacle):
        """
        Assess if the target position can be seen from the current viewing position, considering obstacles.
        
        Parameters:
        view: The current position being viewed from.
        target_obstacle: The obstacle being targeted.

        Returns:
        bool: True if the target can be seen; False otherwise.
        """
        obstructed = False  # Initialize obstruction status.
        view_x_cm = view.x // configs.SCALING_FACTOR  # Convert view position to centimeters.
        view_y_cm = view.y // configs.SCALING_FACTOR  # Convert view position to centimeters.

        # Gather all obstacles except the target one.
        potential_obstructed_obstacles = [ob for ob in self.obstacles if ob != target_obstacle]

        # Check each obstacle to determine if it blocks the view.
        for obstacle in potential_obstructed_obstacles:
            if obstacle.check_within_boundary(view.x, view.y):
                obstructed = True  # Mark as obstructed if within boundary.

            # Calculate distance from view to the segment connecting target and obstacle.
            distance = self.distance_to_segment(view_x_cm, view_y_cm, target_obstacle.x_cm, target_obstacle.y_cm, obstacle.x_cm, obstacle.y_cm)
            if distance < 15:  # If too close, mark as obstructed.
                obstructed = True
            
            if obstructed:  # Break if already marked as obstructed.
                break
        
        return not obstructed  # Return True if not obstructed, False otherwise.

    def distance_to_segment(self, x_view, y_view, x_target, y_target, x_obstacle, y_obstacle):
        """
        Calculate the distance from a point (x_obstacle, y_obstacle) to the line segment 
        formed by (x_view, y_view) and (x_target, y_target).

        Returns:
        float: The distance from the obstacle point to the line segment.
        """
        # Calculate the length of the line segment.
        segment_length = math.sqrt((x_target - x_view) ** 2 + (y_target - y_view) ** 2)
        
        # If the segment length is zero, return the distance to the view point.
        if segment_length == 0:
            return math.sqrt((x_obstacle - x_view) ** 2 + (y_obstacle - y_view) ** 2)

        # Calculate the components of the vector from the view point to the obstacle.
        dx = x_obstacle - x_view
        dy = y_obstacle - y_view
        
        # Calculate the projection of the vector onto the line segment.
        t = max(0, min(segment_length, (dx * (x_target - x_view) + dy * (y_target - y_view)) / (segment_length ** 2)))
        
        # Calculate the nearest point on the segment to the obstacle.
        nearest_point_x = x_view + t * (x_target - x_view)
        nearest_point_y = y_view + t * (y_target - y_view)
        
        # Calculate the distance from the obstacle to the nearest point on the segment.
        distance = math.sqrt((x_obstacle - nearest_point_x) ** 2 + (y_obstacle - nearest_point_y) ** 2)
        
        return distance  # Return the calculated distance.

    def within_threshold(self, x_view, y_view, x_target, y_target, x_obstacle, y_obstacle, threshold):
        """
        Check if the distance from the obstacle to the line segment formed by 
        (x_view, y_view) and (x_target, y_target) is within the specified threshold.
        
        Parameters:
        threshold (float): The distance threshold for consideration.

        Returns:
        bool: True if within the threshold; False otherwise.
        """
        # Use the distance_to_segment function to get the distance.
        distance = self.distance_to_segment(x_view, y_view, x_target, y_target, x_obstacle, y_obstacle)
        return distance <= threshold  # Return True if distance is within threshold.
