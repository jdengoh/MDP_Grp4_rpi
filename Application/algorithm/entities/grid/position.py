from algorithm import configs
from algorithm.entities.assets.direction import Direction


class Position:
    def __init__(self, x, y, direction: Direction = None):
        """
        Initializes Position with x, y coordinates and an optional direction.
        
        Args:
            x (int): X-coordinate on the grid
            y (int): Y-coordinate on the grid
            direction (Direction, optional)
        """
        self.x = x
        self.y = y
        self.direction = direction

    def __str__(self):
        """
        Returns a formatted string representation of the position with scaled x, y coordinates.
        """
        scaled_x = self.x // configs.SCALING_FACTOR
        scaled_y = self.y // configs.SCALING_FACTOR
        return f"Position({scaled_x}, {scaled_y}, direction={self.direction})"

    __repr__ = __str__

    def xy_coords(self):
        """
        Returns the true, unscaled (x, y) coordinates of this Position.

        Returns:
            tuple: A tuple containing (x, y) coordinates.
        """
        return self.x, self.y

    def xy_direction(self):
        """
        Returns the coordinates and direction as a tuple.

        Returns:
            tuple: Contains (x, y, direction).
        """
        return *self.xy_coords(), self.direction

    def copy(self):
        """
        Creates a copy of this Position instance.

        Returns:
            Position: A new instance with the same x, y, and direction values.
        """
        return Position(self.x, self.y, self.direction)

    def get_scaled_xy_direction(self):
        """
        Provides the scaled-down (x, y) coordinates and direction for telemetry purposes.

        Returns:
            tuple: A tuple containing scaled (x, y) and direction as a cardinal string.
        """
        scaled_x = self.x // configs.SCALING_FACTOR
        scaled_y = self.y // configs.SCALING_FACTOR
        
        direction_map = {
            Direction.TOP: 'N',
            Direction.RIGHT: 'E',
            Direction.BOTTOM: 'S',
            Direction.LEFT: 'W'
        }

        return scaled_x, scaled_y, direction_map.get(self.direction)


class RobotPosition(Position):
    def __init__(self, x, y, direction: Direction = None, angle=None):
        """
        Initializes RobotPosition with x, y coordinates, direction, and an optional angle.
        
        Args:
            x (int): X-coordinate of the robot.
            y (int): Y-coordinate of the robot.
            direction (Direction, optional): Cardinal direction.
            angle (int, optional): The robot's angle in degrees.
        """
        super().__init__(x, y, direction)
        self.angle = angle if angle is not None else direction.value if direction else None

    def __str__(self):
        """
        Returns a formatted string representation of the robot's position including angle.
        """
        return f"RobotPosition({super().__str__()}, angle={self.angle})"

    __repr__ = __str__

    def copy(self):
        """
        Creates a copy of this RobotPosition instance.

        Returns:
            RobotPosition: A new instance with the same x, y, direction, and angle values.
        """
        return RobotPosition(self.x, self.y, self.direction, self.angle)