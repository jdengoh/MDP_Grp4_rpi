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
import socket
import pickle
from algorithm import settings
from algorithm.app import AlgoMinimal
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.obstacle import Obstacle

#from model import *
# from helper import command_generator

app = Flask(__name__)
CORS(app)


model = load_model()
# DATA_FILE = os.path.join(os.getcwd(), 'obstacles_data.json')
DATA_FILE ='Application/obstacles_data.json'

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DATA_FILE):
        print("exists!")
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"obstacles": []}


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

@app.route('/save_obstacle_data', methods=['POST'])
def save_obstacle_data():
    data = request.json
    current_data = load_data()
    current_data['obstacles'].append(data)
    save_data(current_data)
    return jsonify(current_data)


@app.route('/receive_obstacle_data', methods=['GET'])
def get_obstacle_data():
    data = load_data()
    print(data)
    return jsonify(data)


@app.route('/send_command_data', methods=['POST'])
def send_command_data():
    data = request.json
    print(data)
    return jsonify(data)


@app.route('/image', methods=['POST'])
def check_img():
    file = request.files['image']
    filename = file.filename
    print("THE FILENAME IS: ",filename)
    print(os.path.join('own_results/raw', filename))
    file.save(os.path.join('own_results/raw', filename))
    file_path = os.path.join('own_results/raw', filename)

    constituents = file.filename.split('_')
    # obstacle_id = constituents[1]


    # # ## Week 8 ## 
    # signal = constituents[2].strip(".jpg")
    # image_id = predict_image(filename, model, signal)

    # ## Week 9 ## 
    # # We don't need to pass in the signal anymore
    # image_id = predict_image_week_9(filename,model)

    
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
    """
    This is the main endpoint for the stitching command. Stitches the images using two different functions, in effect creating two stitches, just for redundancy purposes
    """
    img = stitch_image()
    img.show()
    img2 = stitch_image_own()
    img2.show()
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
            obstacle_params[0]*10 + 5,  # x-coordinate
            (obstacle_params[1])*10 + 5,  # y-coordinate
            Direction(obstacle_params[2]),  # direction (0, 90, 180, -90)
            obstacle_params[3]  # index (ID)
        ))
    
    print("Converted obstacles:")
    for obstacle in obstacle_list:
        print(obstacle)
    
    return obstacle_list


def run_algo(obstacle_data):
    st = time.time() # start to receive the obstacle
    obstacles = parse_obstacle_data(obstacle_data)
    app = AlgoMinimal(obstacles)
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
    print("Commands:" + str(commands))
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
