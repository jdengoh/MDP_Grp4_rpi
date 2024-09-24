import os
import time
from flask import Flask, jsonify, send_file, request
from picamera import PiCamera

app = Flask(__name__)

# Configure the camera
camera = PiCamera()

# Endpoint to capture the image and send it to the PC
@app.route('/capture-image', methods=['GET'])
def capture_image():
    try:
        image_filename = f"/home/pi/{int(time.time())}.jpg"
        camera.start_preview()
        time.sleep(2)  # Allow the camera to warm up
        camera.capture(image_filename)
        camera.stop_preview()

        return send_file(image_filename, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint to receive the image recognition result from the PC
@app.route('/receive-result', methods=['POST'])
def receive_result():
    try:
        data = request.json
        result = data.get("recognized_object", "Unknown")
        confidence = data.get("confidence", 0.0)

        # Log the result or take some action
        print(f"Received result: {result} with confidence: {confidence}")

        return jsonify({"status": "success", "message": "Result received"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
