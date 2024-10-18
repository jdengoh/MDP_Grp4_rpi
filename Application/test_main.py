import sys
import time
import requests
from typing import List
from algorithm import settings
from algorithm.app import AlgoMinimal
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.obstacle import Obstacle

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
        
        # print(" get relative pos", ob, target, ob.direction)
        # print(f"realtive position camera {camera_x} {camera_y}, obstacle {ob_x}, {ob_y}")
        results.append([horizontal*10, vertical*10])
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
    # (x-coordinate, y-coordinate, Direction, index)
    obstacles = {
        "0": [0, 130, -90, 0],
        "1": [0, 190, 0, 1],
        "2": [70, 50, -90, 2], # problematic one
        "3": [80, 140, 0, 3],
        "4": [130, 80, 180, 4],
        "5": [190, 0, 90, 5],
        "6": [190, 190, -90, 6]
    }
    # obstacles = {
    #     "0": [40, 100, 90, 0],
    #     "1": [70, 170, -90, 1],
    #     "2": [170, 100, -90, 2],
    #     "3": [110, 70, 180, 3],
    #     "4": [150, 30, 180, 4],
    #     "5": [150, 160, 180, 5]
    # }
    
    st = time.time() # start to receive the obstacle
    obs = parse_obstacle_data(obstacles)
    app = AlgoMinimal(obs)
    order = app.execute() # [] all are based 1, but might in different order, for e.g: [8,4,3,1] and missing some as well
    # obstacles_ordered = []
    # for index in order:
    #     for obstacle in obstacles:
    #         if index == obstacle.index:
    #             obstacles_ordered.append(obstacle)
    # print("obstacle after ordered", obstacles_ordered)
    # targets = get_relative_pos(obstacles_ordered, app.targets)
    commands = app.robot.convert_all_commands()
    print("Commands:" + str(commands))
    print("Order: ", order)
    
    ed = time.time()
    print("time to received the commands from beginning of received obstacles", ed-st)


if __name__ == '__main__':
    run_simulator()