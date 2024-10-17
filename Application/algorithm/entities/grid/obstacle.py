import math
import time
from algorithm import settings
from algorithm.entities.assets import colors
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.position import Position, RobotPosition
import random

class Obstacle:
    def __init__(self, x, y, direction, index):
        """
        x -> x-coordinate of the obstacle.
        y -> y-coordinate of the obstacle.
        Note x, y coordinates should not be scaled.
        direction -> Which direction the image is facing. If image is on the right side of the obstacle, RIGHT.
        """
        # Check if the coordinates are multiples of 10 with offset 5. If they are not, then they are invalid
        # obstacle coordinates.
        # This is from the assumption that all obstacles are placed centered in each grid.
        if (x - 5) % 10 != 0 or (y - 5) % 10 != 0:
            raise AssertionError("Obstacle center coordinates must be multiples of 10 with offset 5!")

        # Translate given coordinates to be in PyGame coordinates.
        self.pos = Position(x * settings.SCALING_FACTOR, y * settings.SCALING_FACTOR, direction)

        self.x_cm = x
        self.y_cm = y
        self.index = index
        self.direction = direction
        self.valid_targets = []
        
    def get_nearest_valid_target(self, pos: Position):
        best_num = 100000
        best_target = None
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
        Checks whether a given x-y coordinate is within the safety boundary of this obstacle.
        """
        # d2 = (self.pos.x - x) ** 2 + (self.pos.y - y) ** 2
        # return d2 <= settings.OBSTACLE_SAFETY_WIDTH ** 2
        if self.pos.x - settings.OBSTACLE_SAFETY_WIDTH < x < self.pos.x + settings.OBSTACLE_SAFETY_WIDTH and \
                self.pos.y - settings.OBSTACLE_SAFETY_WIDTH < y < self.pos.y + settings.OBSTACLE_SAFETY_WIDTH:
            return True
        return False

    def get_boundary_points(self):
        """
        Get points at the corner of the virtual obstacle for this image.

        Useful for checking if a point is within the boundary of this obstacle.
        """
        upper = self.pos.y + settings.OBSTACLE_SAFETY_WIDTH
        lower = self.pos.y - settings.OBSTACLE_SAFETY_WIDTH
        left = self.pos.x - settings.OBSTACLE_SAFETY_WIDTH
        right = self.pos.x + settings.OBSTACLE_SAFETY_WIDTH

        return [
            # Note that in this case, the direction does not matter.
            Position(left, lower),  # Bottom left.
            Position(right, lower),  # Bottom right.
            Position(left, upper),  # Upper left.
            Position(right, upper)  # Upper right.
        ]

    def get_all_possible_centers(self):
        sensor_width=2592
        sensor_height=1944
        focal = 3.6 #mm
        pixel_size=1.4

        ratio_w = 1024/sensor_width
        ratio_h = 1024/sensor_height
        def get_uv(horizontal,height,vertical):
            x = horizontal
            y = height
            z = vertical
            f = focal #mm
            theta = math.acos(abs(z)/math.sqrt(x*x+z*z)) # 
            deg = math.degrees(theta)
            # alpha = f/2.76 # vertical focal ratio, height
            # beta = f/3.68 # horizontal focal ratio, width
            e = 0.001
            try:
                u = f * (x/z - y*math.tan(theta)/z)
            except:
                u = f * x / z# projected horizontal on image plane
            u /= (pixel_size*e) #  projected width pixel
            
            v = f * (y/(z*math.cos(theta))) # height pixel, using height
            v /= pixel_size*e # f/z == projected_height/real_height
            
            v = 512-v*ratio_h # got flip up
            u = 512+u*ratio_w
            
            # v = 512+v
            return (u, v)


        #horizontal = 0 #horizontal distance from camera to obstacle
        #height = 120 #height of obstacle from camera
        #vertical = 250 #distance from camera to obstacle (verticle, facing)
        height = 50
        possible_centers = []
        
        for i in range(settings.GRID_NUM_GRIDS):
            for j in range(settings.GRID_NUM_GRIDS):
                x = i*settings.GRID_CELL_LENGTH
                y = j*settings.GRID_CELL_LENGTH
                cen_dis = settings.GRID_CELL_LENGTH//2
                x_mm = (x+cen_dis)*10/settings.SCALING_FACTOR
                y_mm = (y+cen_dis)*10/settings.SCALING_FACTOR
                
                # print("xmm,ymm", x_mm, y_mm, self.x_cm * 10, self.y_cm * 10)
                x_view = x_mm - self.x_cm * 10
                y_view = y_mm - self.y_cm * 10
                if self.direction == Direction.LEFT:
                    if x_view > 0:
                        continue
                elif self.direction == Direction.RIGHT:
                    if x_view < 0:
                        continue
                elif self.direction == Direction.TOP:
                    if y_view < 0:
                        continue
                elif self.direction == Direction.BOTTOM:
                    if y_view > 0:
                        continue
                x_view = abs(x_view)
                y_view = abs(y_view)
                if self.direction == Direction.TOP or self.direction == Direction.BOTTOM:
                    if y_view < (settings.OBSTACLE_SAFETY_WIDTH + settings.OBSTACLE_LENGTH) * 10 / settings.SCALING_FACTOR + 10*10:
                        continue
                    if y_view < settings.minimum_vertical:
                        continue
                    u, v = get_uv(x_view, height, y_view)
                else:
                    if x_view < (settings.OBSTACLE_SAFETY_WIDTH + settings.OBSTACLE_LENGTH) * 10 / settings.SCALING_FACTOR + 10*10:
                        continue
                    if x_view < settings.minimum_vertical:
                        continue
                    u, v = get_uv(y_view, height, x_view)
                # print(i, j, u, v, x_view, y_view)
                if (u > settings.left_pixel_threshold and u < settings.right_pixel_threshold and v > 0 and v < 1024):
                    if x_view > settings.maximum_vertical: #1m2
                        continue
                    if y_view > settings.maximum_vertical:
                        continue
                    
                    x_grid = i * settings.GRID_CELL_LENGTH + settings.GRID_CELL_LENGTH//2
                    y_grid = j * settings.GRID_CELL_LENGTH + settings.GRID_CELL_LENGTH//2
                    possible_centers.append((x_grid, y_grid))
        # print("="*50)
        # print(self.pos)
        # print(possible_centers)
        # print("="*50)
        # time.sleep(100)
        return possible_centers
                    

    def get_robot_target_pos(self):
        """
        Returns the point that the robot should target for, including the target orientation.

        Note that the target orientation is now with respect to the robot. If the robot needs to face right, then
        we use 0 degrees.

        We can store this information within a Position object.

        The object will also store the angle that the robot should face.
        """
        possible_targets = []
        upper_bound = settings.upper_bound
        lower_bound = settings.lower_bound
        lower_bound_side = settings.lower_bound_side
        upper_bound_side = settings.upper_bound_side
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
        
        valid_possible_targets = []
        for target in possible_targets:
            if target.x < 0 or target.y < 0 or target.x > settings.GRID_LENGTH or target.y > settings.GRID_LENGTH:
                pass
            else:
                valid_possible_targets.append(target)
        
        return valid_possible_targets
    