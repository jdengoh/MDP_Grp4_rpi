import math
from algorithm import configs
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.position import Position, RobotPosition

class Obstacle:
    def __init__(self, x, y, direction, index):
        """
        Initializes the obstacle with its coordinates and direction.
        x, y: coordinates (should be multiples of 10 with offset 5).
        direction: the direction the image is facing (e.g., RIGHT).
        """
        if (x - 5) % 10 != 0 or (y - 5) % 10 != 0:
            raise AssertionError("Obstacle center coordinates must be multiples of 10 with offset 5!")

        # Translate to PyGame coordinates.
        self.pos = Position(x * configs.SCALING_FACTOR, y * configs.SCALING_FACTOR, direction)
        self.x_cm = x
        self.y_cm = y
        self.index = index
        self.direction = direction
        self.valid_targets = []
        
    def get_nearest_valid_target(self, pos: Position):
        best_target = None
        best_num = float('inf')
        for target in self.valid_targets:
            dis = abs(pos.x - target.x) + abs(pos.y - target.y)
            if best_num > dis:
                best_num = dis
                best_target = target
        return best_target
    
    def __str__(self):
        return f"Obstacle({self.pos})"

    __repr__ = __str__

    def check_within_boundary(self, x, y):
        """
        Checks if the given coordinates are within the obstacle's safety boundary.
        """
        return (self.pos.x - configs.OBSTACLE_SAFETY_WIDTH < x < self.pos.x + configs.OBSTACLE_SAFETY_WIDTH and
                self.pos.y - configs.OBSTACLE_SAFETY_WIDTH < y < self.pos.y + configs.OBSTACLE_SAFETY_WIDTH)

    def get_boundary_points(self):
        """
        Returns corner points of the obstacle's virtual boundary.
        """
        upper = self.pos.y + configs.OBSTACLE_SAFETY_WIDTH
        lower = self.pos.y - configs.OBSTACLE_SAFETY_WIDTH
        left = self.pos.x - configs.OBSTACLE_SAFETY_WIDTH
        right = self.pos.x + configs.OBSTACLE_SAFETY_WIDTH

        return [
            Position(left, lower),  # Bottom left
            Position(right, lower),  # Bottom right
            Position(left, upper),  # Upper left
            Position(right, upper)  # Upper right
        ]

    def get_all_possible_centers(self):
        """
        Calculates all possible centers based on sensor parameters and obstacle properties.
        """
        height = 50
        possible_centers = []

        for i in range(configs.GRID_NUM_GRIDS):
            for j in range(configs.GRID_NUM_GRIDS):
                x = i * configs.GRID_CELL_LENGTH
                y = j * configs.GRID_CELL_LENGTH
                cen_dis = configs.GRID_CELL_LENGTH // 2
                x_mm = (x + cen_dis) * 10 / configs.SCALING_FACTOR
                y_mm = (y + cen_dis) * 10 / configs.SCALING_FACTOR
                
                x_view = x_mm - self.x_cm * 10
                y_view = y_mm - self.y_cm * 10
                
                if ((self.direction == Direction.LEFT and x_view > 0) or
                    (self.direction == Direction.RIGHT and x_view < 0) or
                    (self.direction == Direction.TOP and y_view < 0) or
                    (self.direction == Direction.BOTTOM and y_view > 0)):
                    continue
                
                x_view = abs(x_view)
                y_view = abs(y_view)
                
                if (self.direction in {Direction.TOP, Direction.BOTTOM}):
                    if (y_view < (configs.OBSTACLE_SAFETY_WIDTH + configs.OBSTACLE_LENGTH) * 10 / configs.SCALING_FACTOR + 100):
                        continue
                    if y_view < configs.VERTICAL_MIN:
                        continue
                    u, v = self.get_uv(x_view, height, y_view)
                else:
                    if (x_view < (configs.OBSTACLE_SAFETY_WIDTH + configs.OBSTACLE_LENGTH) * 10 / configs.SCALING_FACTOR + 100):
                        continue
                    if x_view < configs.VERTICAL_MIN:
                        continue
                    u, v = self.get_uv(y_view, height, x_view)

                if (configs.PIXEL_LEFT_THRESHOLD < u < configs.PIXEL_RIGHT_THRESHOLD and 0 < v < 1024):
                    if (x_view > configs.VERTICAL_MAX or y_view > configs.VERTICAL_MAX):
                        continue
                    
                    x_grid = i * configs.GRID_CELL_LENGTH + configs.GRID_CELL_LENGTH // 2
                    y_grid = j * configs.GRID_CELL_LENGTH + configs.GRID_CELL_LENGTH // 2
                    possible_centers.append((x_grid, y_grid))

        return possible_centers

    def get_uv(self, horizontal, height, vertical):
        """
        Computes the image pixel coordinates from 3D world coordinates.
        """
        f = 3.6  # mm
        pixel_size = 1.4
        e = 0.001
        x, y, z = horizontal, height, vertical
        
        theta = math.acos(abs(z) / math.sqrt(x ** 2 + z ** 2))
        try:
            u = f * (x / z - y * math.tan(theta) / z) / (pixel_size * e)
        except ZeroDivisionError:
            u = f * x / z / (pixel_size * e)  # projected width pixel
            
        v = f * (y / (z * math.cos(theta))) / (pixel_size * e)  # height pixel
        v = 512 - v * (1024 / 1944)  # flip up
        u = 512 + u * (1024 / 2592)
        
        return u, v

    def get_robot_target_pos(self):
        """
        Returns valid target positions for the robot based on possible centers.
        """
        possible_targets = []
        possible_centers = self.get_all_possible_centers()
        for center in possible_centers:
            if self.pos.direction == Direction.TOP:
                possible_targets.append(RobotPosition(center[0], center[1], Direction.BOTTOM))
            elif self.pos.direction == Direction.BOTTOM:
                possible_targets.append(RobotPosition(center[0], center[1], Direction.TOP))
            elif self.pos.direction == Direction.LEFT:
                possible_targets.append(RobotPosition(center[0], center[1], Direction.RIGHT))
            else:
                possible_targets.append(RobotPosition(center[0], center[1], Direction.LEFT))
        
        return [target for target in possible_targets if 0 <= target.x <= configs.GRID_LENGTH and 0 <= target.y <= configs.GRID_LENGTH]
