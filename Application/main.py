import os
import sys
sys.path.append('/home/pi/Documents/MDP_Project/Application')
import time
import json
from flask import Flask,request, jsonify
from flask_cors import CORS
from image_rec import predict_image, load_model

import sys
import time
from typing import List
import socket
import pickle
from algorithm import settings
from algorithm.app import AlgoSimulator, AlgoMinimal
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
    os.path
    file.save(os.path.join('Application/own_results/raw', filename))
    file_path = os.path.join('Application/own_results/raw', filename)

    constituents = file.filename.split('_')
    # obstacle_id = constituents[1]


    # # ## Week 8 ## 
    # signal = constituents[2].strip(".jpg")
    # image_id = predict_image(filename, model, signal)

    # ## Week 9 ## 
    # # We don't need to pass in the signal anymore
    # image_id = predict_image_week_9(filename,model)

    
    image_results = predict_image(filename,model)

    result = {
        # "obstacle_id": obstacle_id,
        "image_id" : image_results[0],
        "result"   : image_results[1]
    }

    print(result)
    return jsonify(result)

@app.route('/algo', methods=['POST'])
def algo():
    data = request.json['obstacles']
    print("Data Received by algo\n" + str(data))
    order_and_commands = run_algo(data)
    print("Order and commands: " + str(order_and_commands))
    return jsonify(order_and_commands)


def run_algo(obstacle_data):
    obstacles = parse_obstacle_data(obstacle_data)
    algo = AlgoMinimal(obstacles)
    algo.init()
    order = algo.execute()
    commands = algo.robot.convert_all_commands()
    print("Commands converted: " + str(commands))
    print("Order: " + str(order))
    order_and_commands = {
        "order": order,
        "commands": commands,
        "path_hist": None
    }
    return order_and_commands


def parse_obstacle_data(data: dict) -> List[Obstacle]:
    obstacle_list = []
    
    for key, obstacle_params in data.items():  # Iterate over the dictionary's items
        obstacle_list.append(Obstacle(
            obstacle_params[0]*10 + 5,  # x-coordinate
            (20-obstacle_params[1]-1)*10 + 5,  # y-coordinate
            Direction(obstacle_params[2]),  # direction (0, 90, 180, -90)
            obstacle_params[3]  # index (ID)
        ))
    
    print("Converted obstacles:")
    for obstacle in obstacle_list:
        print(obstacle)
    
    return obstacle_list


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
