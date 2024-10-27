import os
import time
from matplotlib import pyplot as plt
from typing import List
from algorithm import configs
from algorithm.app import AlgoPathPlanner
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.obstacle import Obstacle

def get_relative_pos(obstacles, targets):
    """
    Calculate the relative position of each obstacle to a target based on the direction.
    """
    results = []
    for i in range(len(obstacles)):
        ob = obstacles[i]
        target = targets[i]
        ob_x = ob.x_cm 
        ob_y = ob.y_cm
        camera_x = target.x // configs.SCALING_FACTOR
        camera_y = target.y // configs.SCALING_FACTOR

        # Calculate horizontal and vertical distances based on obstacle direction
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
    """
    Parse obstacle data into Obstacle instances, adjusting x and y positions.
    """
    obstacle_list = []
    for key, obstacle_params in data.items():
        obstacle_list.append(Obstacle(
            obstacle_params[0] + 5,  # Adjusted x-coordinate
            obstacle_params[1] + 5,  # Adjusted y-coordinate
            Direction(obstacle_params[2]),  # Direction
            obstacle_params[3]  # ID/index
        ))
    return obstacle_list

def obstacle_optimizer(obstacles: dict) -> dict:
    """
    Optimize obstacle positions based on specific conditions.
    """
    print("Original Obstacles:", obstacles)
    for key, value in obstacles.items():
        x, y, direction, _ = value
        
        # Adjust positions based on direction and coordinates
        if direction == 180 and x in [40, 50]:
            x = 60
        elif direction == 0 and x in [150, 160]:
            x = 140
        elif direction == 90 and y in [150, 160]:
            y = 140
        elif direction == -90 and y in [40, 50]:
            y = 60
        
        obstacles[key] = [x, y, direction, value[3]]
    print("Optimized Obstacles:", obstacles)
    return obstacles

def command_optimizer(commands: list) -> list:
    """
    Optimize commands by removing redundant patterns in command sequences.
    """
    print("Original Commands:", commands)
    i = 0
    while i < len(commands) - 3:
        # Optimize LFxxx -> P -> LBxxx -> LF090 sequence
        if commands[i].startswith('LF') and commands[i + 1] == 'P' and commands[i + 2].startswith('LB') and commands[i + 3] == 'LF090':
            try:
                dist1 = int(commands[i][2:])
                dist2 = int(commands[i + 2][2:])
                if dist1 == dist2:
                    new_command = commands[i][:2] + str(90 - dist2).zfill(3)
                    commands[i + 2] = new_command
                    commands.pop(i + 3)
                    continue
            except ValueError:
                pass

        # Optimize RFxxx -> P -> RBxxx -> RF090 sequence
        elif commands[i].startswith('RF') and commands[i + 1] == 'P' and commands[i + 2].startswith('RB') and commands[i + 3] == 'RF090':
            try:
                dist1 = int(commands[i][2:])
                dist2 = int(commands[i + 2][2:])
                if dist1 == dist2:
                    new_command = commands[i][:2] + str(90 - dist2).zfill(3)
                    commands[i + 2] = new_command
                    commands.pop(i + 3)
                    continue
            except ValueError:
                pass

        i += 1
    print("Optimized Commands:", commands)
    return commands

def draw_validity_grid(grid):
    """
    Display the grid using Matplotlib, marking valid and invalid areas for obstacles.
    """
    output_folder = "grid"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.set_xlim(0, configs.WINDOW_SIZE[0])
    ax.set_ylim(0, configs.WINDOW_SIZE[1])
    ax.set_title("Grid Validation - Obstacle Visualization")

    for x in range(0, configs.WINDOW_SIZE[0], configs.GRID_CELL_LENGTH):
        for y in range(0, configs.WINDOW_SIZE[1], configs.GRID_CELL_LENGTH):
            color = 'red' if grid.cache.get((x, y)) is False else 'lightgray'
            rect = plt.Rectangle((x, y), configs.GRID_CELL_LENGTH, configs.GRID_CELL_LENGTH, color=color, fill=True, edgecolor='black')
            ax.add_patch(rect)

    plt.gca().invert_yaxis()
    filename = "validity_grid_visualization_obstacle.png"
    plt.savefig(os.path.join(output_folder, filename))
    plt.show()

def run_simulator():
    """
    Main function to set up and run the simulator with obstacle optimization and command execution.
    """
    obstacles = {
        "0": [10, 160, 0, 0],
        "1": [50, 110, -90, 1],
        "2": [70, 40, 90, 2],
        "3": [110, 130, 0, 3],
        "4": [150, 20, 180, 4],
        "5": [160, 190, -90, 5],
        "6": [190, 90, 180, 6],
    }

    obstacles = obstacle_optimizer(obstacles)
    
    start_time = time.time()
    parsed_obstacles = parse_obstacle_data(obstacles)
    app = AlgoPathPlanner(parsed_obstacles)
    order = app.execute()
    
    commands = app.robot.convert_all_commands()
    commands = command_optimizer(commands)
    print("Obstacle Order: ", order)
    
    end_time = time.time()
    print("Execution Time:", end_time - start_time)

if __name__ == '__main__':
    run_simulator()