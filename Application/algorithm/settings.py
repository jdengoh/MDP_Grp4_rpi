# PyGame settings
SCALING_FACTOR = 4
FRAMES = 60
WINDOW_SIZE = 800, 800

# Connection to RPi
RPI_HOST: str = "192.168.4.16"
RPI_PORT: int = 5001

# Connection to PC
PC_HOST: str = "192.168.4.27"
PC_PORT: int = 4161

# Robot Attributes
ROBOT_LENGTH = 20 * SCALING_FACTOR
ROBOT_LEFT_TURN_RADIUS = 25 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns
ROBOT_RIGHT_TURN_RADIUS = 25 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns
ROBOT_SPEED_PER_SECOND = 50 * SCALING_FACTOR
ROBOT_LEFT_S_FACTOR = ROBOT_LENGTH / ROBOT_LEFT_TURN_RADIUS
ROBOT_RIGHT_S_FACTOR = ROBOT_LENGTH / ROBOT_RIGHT_TURN_RADIUS
ROBOT_START_POSITION = 15 * SCALING_FACTOR
ROBOT_SAFETY_DISTANCE = 15 * SCALING_FACTOR
ROBOT_SCAN_TIME = 2  # Time provided for scanning an obstacle image in seconds.

# Grid Attributes
GRID_LENGTH = 200 * SCALING_FACTOR
GRID_CELL_LENGTH = 10 * SCALING_FACTOR
GRID_START_BOX_LENGTH = 30 * SCALING_FACTOR
GRID_NUM_GRIDS = GRID_LENGTH // GRID_CELL_LENGTH

# Obstacle Attributes
OBSTACLE_LENGTH = 10 * SCALING_FACTOR
OBSTACLE_SAFETY_WIDTH = ROBOT_SAFETY_DISTANCE // 3 * 5  # With respect to the center of the obstacle

# Path Finding Attributes
PATH_TURN_COST = 99999 * ROBOT_SPEED_PER_SECOND * ROBOT_RIGHT_TURN_RADIUS
# NOTE: Higher number == Lower Granularity == Faster Checking.
# Must be an integer more than 0! Number higher than 3 not recommended.
PATH_TURN_CHECK_GRANULARITY = 1
