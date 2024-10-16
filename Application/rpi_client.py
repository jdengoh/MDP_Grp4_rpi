import sys
sys.path.append('/home/pi/Documents/MDP_Project/')
from MDP_rpi.settings import * 

import json
import requests
from picamera import PiCamera
import time


# Flask server URL

def snap_pic():
    url = f"http://{API_IP}:{API_PORT}/image"
    print(url)
    # Initialize the PiCamera
    camera = PiCamera()

    # Capture image
    image_filename = f"/home/pi/{int(time.time())}.jpg"
    camera.start_preview()
    time.sleep(2)  # Camera warm-up time
    camera.capture(image_filename)
    camera.stop_preview()

    # Send image to Flask server
    print("Sending image to server...")
    with open('/home/pi/captured_image.jpg', 'rb') as img_file:
        files = {'image': img_file}
        response = requests.post(url, files=files)
        print("SENT SUCCESSFUL")

    # Get the response from the server
    if response.status_code == 200:
        # print("200")
        print("rpi_client - Image detection result:", response.json())
        
    else:
        print("Error:", response.json())


    camera.close()
    results = response.json()
    print(results)

    return results['image_id']

# results = snap_pic()
# print (results)