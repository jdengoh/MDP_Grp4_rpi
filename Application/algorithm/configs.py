# For Simulator
SCALING_FACTOR = 4  # Scale factor for distances and object sizes
FRAMES = 60  # Frames per second for PyGame rendering
WINDOW_SIZE = (800, 800)  # Simulation window dimensions (width, height)

# Robot Movement Params
UNIT_STRAIGHT = 10  # Base unit distance in cm for robot's straight movements
ROBOT_LENGTH = 25 * SCALING_FACTOR  # Length of robot

# Indoor Turning Radii
ROBOT_LEFT_TURN_RADIUS_X = 29 * SCALING_FACTOR  # Left turn radius, x-axis
ROBOT_LEFT_TURN_RADIUS_Y = 16 * SCALING_FACTOR  # Left turn radius, y-axis
ROBOT_RIGHT_TURN_RADIUS_X = 33 * SCALING_FACTOR  # Right turn radius, x-axis
ROBOT_RIGHT_TURN_RADIUS_Y = 19 * SCALING_FACTOR  # Right turn radius, y-axis

# Outdoor Turning Radii
# ROBOT_LEFT_TURN_RADIUS_X = 32 * SCALING_FACTOR  # Left turn radius, x-axis
# ROBOT_LEFT_TURN_RADIUS_Y = 18 * SCALING_FACTOR  # Left turn radius, y-axis
# ROBOT_RIGHT_TURN_RADIUS_X = 35 * SCALING_FACTOR  # Right turn radius, x-axis
# ROBOT_RIGHT_TURN_RADIUS_Y = 21 * SCALING_FACTOR  # Right turn radius, y-axis

# Robot Speed and Safety
ROBOT_SPEED = 50 * SCALING_FACTOR  # Robot speed in cm/s
ROBOT_LEFT_TURN_FACTOR = (ROBOT_LENGTH / ROBOT_LEFT_TURN_RADIUS_X + ROBOT_LENGTH / ROBOT_LEFT_TURN_RADIUS_Y) / 2
ROBOT_RIGHT_TURN_FACTOR = (ROBOT_LENGTH / ROBOT_RIGHT_TURN_RADIUS_X + ROBOT_LENGTH / ROBOT_RIGHT_TURN_RADIUS_Y) / 2
ROBOT_X_START_POSITION = 15 * SCALING_FACTOR  # Starting X position of the robot
ROBOT_Y_START_POSITION = 15 * SCALING_FACTOR  # Starting Y position of the robot
ROBOT_SAFETY_DISTANCE = 15 * SCALING_FACTOR  # Minimum safe distance from obstacles
ROBOT_SCANNING_TIME = 2  # Time for scanning obstacle images, in seconds

# Grid Configuration
GRID_LENGTH = 200 * SCALING_FACTOR  # Length of the grid area
GRID_CELL_LENGTH = 5 * SCALING_FACTOR  # Size of each grid cell
GRID_START_BOX_LENGTH = 30 * SCALING_FACTOR  # Initial grid size where the robot begins
GRID_NUM_GRIDS = GRID_LENGTH // GRID_CELL_LENGTH  # Total number of grid cells across the grid

# Obstacle Properties
OBSTACLE_LENGTH = 10 * SCALING_FACTOR  # Length of obstacles
OBSTACLE_SAFETY_WIDTH = 25 * SCALING_FACTOR  # Safe width added to the obstacle area
OBSTACLE_TARGET_DISTANCE = 32 * SCALING_FACTOR  # Distance from obstacle for target positioning

# Pathfinding Settings
PATH_TURN_COST = 99999 * ROBOT_SPEED * (ROBOT_RIGHT_TURN_RADIUS_X + ROBOT_RIGHT_TURN_RADIUS_Y) / 2
TURN_GRANULARITY = 3  # Precision of turn checking, values above 3 may reduce accuracy

# Threading Configuration for Processing
NUM_THREADS = 1  # Number of threads for pathfinding computations
NUM_HAM_PATH_CHECK = 5  # Number of hamiltonian paths to consider

# Boundary Parameters for Path Detection
BOUND_LOWER = 3
BOUND_UPPER = 10
BOUND_LOWER_SIDE = 5
BOUND_UPPER_SIDE = 10

# Pixel and Angle Thresholds for Obstacle Detection
PEEK_HORIZONTAL_THRESHOLD = 15  # Horizontal tolerance for peek detection
VERTICAL_MIN = 500  # Minimum allowable vertical threshold in mm
VERTICAL_MAX = 700  # Maximum allowable vertical threshold in mm
PEEK_ANGLE_THRESHOLD = 8  # Threshold angle in degrees for detecting peaks
PIXEL_LEFT_THRESHOLD = 200  # Pixel threshold for left boundary detection
PIXEL_RIGHT_THRESHOLD = 800  # Pixel threshold for right boundary detection