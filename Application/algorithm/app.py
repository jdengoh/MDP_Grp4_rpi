import sys
import time
import requests
from typing import List
from algorithm import settings
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.grid.grid import Grid
from algorithm.entities.robot.robot import Robot


class AlgoMinimal:
    """
    Minimal app to just calculate a path and then send the commands over.
    """

    def __init__(self, obstacles):
        st = time.time()
        self.grid = Grid(obstacles)
        self.robot = Robot(self.grid)
        print("time to create grid and robot", time.time() - st)

    def execute(self):
        # Calculate path
        print("Calculating path...")
        st = time.time()
        order, targets = self.robot.brain.plan_path()
        print("time to calculate path", time.time() - st)
        self.targets = targets
        self.order = order
        if not order:
            print("Warning: The path planning returned an empty order. Debugging needed.")
        else:
            print("Order of obstacles visited:", order)
        print("Done!")
        return order


def get_relative_pos(obstacles, targets):
    results = []
    for i in range(len(obstacles)):
        ob = obstacles[i]
        target = targets[i]
        ob_x = ob.x_cm
        ob_y = ob.y_cm
        camera_x = target.x // settings.SCALING_FACTOR
        camera_y = target.y // settings.SCALING_FACTOR
        if ob.direction == Direction.TOP:
            horizontal = camera_x - ob_x
            vertical = abs(camera_y - ob_y)
        elif ob.direction == Direction.BOTTOM:
            horizontal = ob_x - camera_x
            vertical = abs(camera_y - ob_y)
        elif ob.direction == Direction.LEFT:
            horizontal = camera_y - ob_y
            vertical = abs(camera_x - ob_x)
        elif ob.direction == Direction.RIGHT:
            horizontal = ob_y - camera_y
            vertical = abs(camera_x - ob_x)

        results.append([horizontal * 10, vertical * 10])
    return results


def parse_obstacle_data(data: dict) -> List[Obstacle]:
    obstacle_list = []

    for key, obstacle_params in data.items():  # Iterate over the dictionary's items
        obstacle_list.append(Obstacle(
            obstacle_params[0] + 5,  # x-coordinate
            obstacle_params[1] + 5,  # y-coordinate
            Direction(obstacle_params[2]),  # direction
            obstacle_params[3]  # index (ID)
        ))

    return obstacle_list


def run_simulator():
    # Fill in obstacle positions with respect to lower bottom left corner.
    obstacles = {
        "0": [40, 100, 90, 0],
        "1": [70, 170, -90, 1],
        "2": [170, 100, -90, 2],
        "3": [110, 70, 180, 3],
        "4": [150, 30, 180, 4],
        "5": [150, 160, 180, 5]
    }

    st = time.time()  # Start time to receive the obstacle
    obs = parse_obstacle_data(obstacles)
    app = AlgoMinimal(obs)
    order = app.execute()  # Get the order of obstacles visited
    if not order:
        print("Warning: The order of obstacles visited is empty. Check if path planning logic is correct.")
    commands = app.robot.convert_all_commands()
    print("Commands:" + str(commands))
    print("Order:", order)

    ed = time.time()
    print("Time to receive the commands from beginning of received obstacles", ed - st)


if __name__ == '__main__':
    run_simulator()