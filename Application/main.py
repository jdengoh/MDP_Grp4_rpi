import time
from flask import Flask,request, jsonify
from flask_cors import CORS

#from model import *
# from helper import command_generator

app = Flask(__name__)
CORS(app)

model = None

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


@app.route('/image', methods=['POST'])
def check_img():
    file = request.files['image']
    filename = file.filename

    file.save(os.path.join('uploads', filename))

    constituents = file.filename.split('_')
    obstacle_id = constituents[1]


    # # ## Week 8 ## 
    # signal = constituents[2].strip(".jpg")
    # image_id = predict_image(filename, model, signal)

    # ## Week 9 ## 
    # # We don't need to pass in the signal anymore
    # image_id = predict_image_week_9(filename,model)

    image_id = predict_image(filename,model)

    result = {
        "obstacle_id": obstacle_id,
        image_id: image_id
    }

    return jsonfiy(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

