import time
from algorithm.entities.grid.grid import Grid
from algorithm.entities.robot.robot import Robot

class AlgoPathPlanner:
    """
    Minimal application to generate a path and transmit commands based on obstacles in the grid.
    """
    def __init__(self, obstacles):
        """
        Initializes the grid and robot based on the provided obstacles.

        Args:
            obstacles (list): List of obstacles to be used for grid and path planning.
        """
        start_time = time.time()  # Start timer for initialization
        self.grid = Grid(obstacles)  # Create grid with specified obstacles
        self.robot = Robot(self.grid)  # Initialize the robot within this grid
        print("Initialization time (grid and robot setup):", time.time() - start_time)

    def execute(self):
        """
        Executes the path planning and returns the order of navigation steps.

        Returns:
            list: Ordered path of waypoints or grid cells to navigate.
        """
        print("Starting path calculation...")
        start_time = time.time()  # Start timer for path calculation

        # Calculate path based on grid obstacles, returning order and target locations
        order, targets = self.robot.brain.plan_path()
        print("Path calculation time:", time.time() - start_time)

        self.targets = targets  # Store calculated targets for further use if needed
        print("Path calculation complete.")
        return order