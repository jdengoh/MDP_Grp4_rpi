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

def obstacle_optimizer(obstacles: dict) -> dict:
    # Obstacle Optimizer
    print("Old Obstacles:", obstacles)
    
    # Iterate over each obstacle
    for key, value in obstacles.items():
        x, y, direction, _ = value
        # Check the direction and apply changes based on conditions
        if direction == 180 and x in [40, 50]:  # If direction is left (180), and x is 40 or 50
            x = 60  # Set x to 60
        elif direction == 0 and x in [150, 160]:  # If direction is right (0), and x is 150 or 160
            x = 140  # Set x to 140
        elif direction == 90 and y in [150, 160]:  # If direction is up (90), and y is 150 or 160
            y = 140  # Set y to 140
        elif direction == -90 and y in [40, 50]:  # If direction is down (-90), and y is 40 or 50
            y = 60  # Set y to 60
        
        # Update the obstacle values in the dictionary
        obstacles[key] = [x, y, direction, value[3]]

    print("New obstacles:", obstacles)
    return obstacles

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
    
    obstacles = obstacle_optimizer(obstacles)
    
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
    
    # Command optimization
    i = 0
    while i < len(commands) - 3:  # Need at least 4 elements to form the pattern LFxxx -> P -> LBxxx -> LF090
        # Check for LFxxx -> P -> LBxxx -> LF090 case
        if commands[i].startswith('LF') and commands[i + 1] == 'P' and commands[i + 2].startswith('LB') and commands[i + 3] == 'LF090':
            # Extract the number from LBxxx and make sure LFxxx and LBxxx have matching distances
            try:
                dist1 = int(commands[i][2:])  # LFxxx -> extract xxx
                dist2 = int(commands[i + 2][2:])  # LBxxx -> extract xxx
                if dist1 == dist2:  # Ensure distances match
                    # Replace LBxxx with modified LFxxx
                    new_command = commands[i][:2] + str(90 - dist2).zfill(3)  # LFxxx becomes LF(90-xxx)
                    commands[i + 2] = new_command
                    # Remove LF090
                    commands.pop(i + 3)
                    continue  # Stay on the current index to check for adjacent sequences
            except ValueError:
                pass  # Skip if there is a non-numeric value

        # Check for RFxxx -> P -> RBxxx -> RF090 case
        elif commands[i].startswith('RF') and commands[i + 1] == 'P' and commands[i + 2].startswith('RB') and commands[i + 3] == 'RF090':
            try:
                dist1 = int(commands[i][2:])  # RFxxx -> extract xxx
                dist2 = int(commands[i + 2][2:])  # RBxxx -> extract xxx
                if dist1 == dist2:  # Ensure distances match
                    # Replace RBxxx with modified RFxxx
                    new_command = commands[i][:2] + str(90 - dist2).zfill(3)  # RFxxx becomes RF(90-xxx)
                    commands[i + 2] = new_command
                    # Remove RF090
                    commands.pop(i + 3)
                    continue  # Stay on the current index to check for adjacent sequences
            except ValueError:
                pass  # Skip if there is a non-numeric value

        i += 1
    
    print("Nommands:" + str(commands))
    print("Order: ", order)
    
    ed = time.time()
    print("time to received the commands from beginning of received obstacles", ed-st)


if __name__ == '__main__':
    run_simulator()