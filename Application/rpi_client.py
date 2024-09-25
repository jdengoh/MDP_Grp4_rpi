import sys
sys.path.append('/home/pi/Documents/MDP_Project/')
from MDP_rpi.settings import * 

import requests
from picamera import PiCamera
import time


# Flask server URL


url = f"http://{API_IP}:{API_PORT}/image"
print(url)
# Initialize the PiCamera
camera = PiCamera()

# Capture image
camera.start_preview()
time.sleep(2)  # Camera warm-up time
camera.capture('/home/pi/captured_image.jpg')
camera.stop_preview()

# Send image to Flask server
print("Sending image to server...")
with open('/home/pi/captured_image.jpg', 'rb') as img_file:
    files = {'image': img_file}
    response = requests.post(url, files=files)

# Get the response from the server
if response.status_code == 200:
    print("200")
    print("Image detection result:", response.json())
else:
    print("Error:", response.json())