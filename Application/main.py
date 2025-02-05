import os
import sys
sys.path.append('/home/pi/Documents/MDP_Project/Application')
import time
import json
from flask import Flask,request, jsonify
from flask_cors import CORS
from image_rec import predict_image, load_model, stitch_image, stitch_image_own

import sys
import time
from typing import List
from algorithm import configs
from algorithm.app import AlgoPathPlanner
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.grid.grid import Grid
from matplotlib import pyplot as plt


#from model import *
# from helper import command_generator

app = Flask(__name__)
CORS(app)


model = load_model()
# DATA_FILE = os.path.join(os.getcwd(), 'obstacles_data.json')
# DATA_FILE ='Application/obstacles_data.json'

# def save_data(data):
#     with open(DATA_FILE, 'w') as f:
#         json.dump(data, f)

# def load_data():
#     if os.path.exists(DATA_FILE):
#         print("exists!")
#         with open(DATA_FILE, 'r') as f:
#             return json.load(f)
#     return {"obstacles": []}

def draw_validity_grid(grid):
    """
    Function to draw the grid using Matplotlib to show valid (free) and invalid areas for each obstacle grid.
    """
    # Create a directory for saving grid images if it doesn't exist
    output_folder = "grid"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.set_xlim(0, configs.WINDOW_SIZE[0])
    ax.set_ylim(0, configs.WINDOW_SIZE[1])
    ax.set_title(f"Grid Verification - Validity Visualization")

    # Draw nodes, color based on validity
    for x in range(0, configs.WINDOW_SIZE[0], configs.GRID_CELL_LENGTH):
        for y in range(0, configs.WINDOW_SIZE[1], configs.GRID_CELL_LENGTH):
            if grid.cache.get((x, y)) is False:
                color = 'red'  # Invalid area
            else:
                color = 'lightgray'  # Valid area
            rect = plt.Rectangle((x, y), configs.GRID_CELL_LENGTH, configs.GRID_CELL_LENGTH, color=color, fill=True, edgecolor='black')
            ax.add_patch(rect)

    plt.gca().invert_yaxis()  # Invert y-axis to match typical grid orientation
    filename = f"validity_grid_visualization_obstacle.png"
    plt.savefig(os.path.join(output_folder, filename))
    plt.show()
@app.route('/', methods=['GET'])
def home():
    return "<h1>Hello from RPI!</h1>"

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'ok'})


# @app.route('/path', methods=['POST'])
# def path_finding():
    
#     data = request.json
#     obstacles = content['obstacles']

# @app.route('/save_obstacle_data', methods=['POST'])
# def save_obstacle_data():
#     data = request.json
#     current_data = load_data()
#     current_data['obstacles'].append(data)
#     save_data(current_data)
#     return jsonify(current_data)


# @app.route('/receive_obstacle_data', methods=['GET'])
# def get_obstacle_data():
#     data = load_data()
#     print(data)
#     return jsonify(data)


# @app.route('/send_command_data', methods=['POST'])
# def send_command_data():
#     data = request.json
#     print(data)
#     return jsonify(data)


@app.route('/image', methods=['POST'])
def check_img():
    file = request.files['image']
    filename = file.filename
    # print("THE FILENAME IS: ",filename)
    # print(os.path.join('own_results/raw', filename))
    file.save(os.path.join('own_results/raw', filename))
    file_path = os.path.join('own_results/raw', filename)

    image_results = predict_image(file_path,model)

    result = {
        # "obstacle_id": obstacle_id,
        "image_id" : image_results[0],
        "result"   : image_results[1]
    }

    print(result)
    return jsonify(result)

@app.route('/stitch', methods=['get'])
def stitch():
    img = stitch_image()
    img.show()
    return jsonify({"result": "ok"})
@app.route('/algo', methods=['POST'])
def algo():
    data = request.json['obstacles']
    print("Data Received by algo\n" + str(data))
    order_and_commands = run_algo(data)
    print("Order and commands: " + str(order_and_commands))
    return jsonify(order_and_commands)


def get_relative_pos(obstacles, targets):
    results = []
    for i in range(len(obstacles)):
        ob = obstacles[i]
        target = targets[i]
        ob_x = ob.x_cm 
        ob_y = ob.y_cm
        camera_x = target.x // configs.SCALING_FACTOR
        camera_y = target.y // configs.SCALING_FACTOR
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
            obstacle_params[0]*10 + 5,  # x-coordinate
            (obstacle_params[1])*10 + 5,  # y-coordinate
            Direction(obstacle_params[2]),  # direction (0, 90, 180, -90)
            obstacle_params[3]  # index (ID)
        ))
    
    print("Converted obstacles:")
    for obstacle in obstacle_list:
        print(obstacle)
    
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

def command_optimizer(commands: list) -> list:
     # Remove unnecessary commands by merging LFxxx -> P -> LBxxx -> LF090 and RFxxx -> P -> RBxxx -> RF090 sequences
    print("Old Commands:" + str(commands))
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
    print("New Commands:" + str(commands))
    return commands

def run_algo(obstacle_data):
    st = time.time() # start to receive the obstacle
    
    # Obstacle Optimizer
    obstacle_data = obstacle_optimizer(obstacle_data)
    
    obstacles = parse_obstacle_data(obstacle_data)
    app = AlgoPathPlanner(obstacles)
    grid = Grid(obstacles)
    # draw_validity_grid(grid)
    order = app.execute() # [] all are based 1, but might in different order, for e.g: [8,4,3,1] and missing some as well
    # obstacles_ordered = []
    # for index in order:
    #     for obstacle in obstacles:
    #         if index == obstacle.index:
    #             obstacles_ordered.append(obstacle)
    print("order", order)
    # print("obstacle after ordered", obstacles_ordered)
    # targets = get_relative_pos(obstacles_ordered, app.targets)
    commands = app.robot.convert_all_commands()
    commands = command_optimizer(commands)
    print("Order: " + str(order))
    
    ed = time.time()
    print("Time to received the commands from beginning of received obstacles", ed-st)
    
    order_and_commands = {
        "order": order,
        "commands": commands,
        "path_hist": None
    }
    return order_and_commands


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
