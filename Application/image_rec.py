import os
import shutil
import time
import glob
import torch
from PIL import Image
import cv2
import random
import string
import numpy as np
import random
import traceback
from torchvision import transforms
import pandas



def load_model():
    current_path = os.path.dirname(os.path.abspath(__file__))
    yolo5_path = os.path.join(current_path, 'yolov5')
    pt_path = os.path.join(current_path, 'best (9).pt')

    model = torch.hub.load(yolo5_path,
                           'custom',
                           path=pt_path,
                           source='local')
    return model

def predict_image(image, model, signal='C'):
    try:
        # Load the image
        img = Image.open(image)

        # Predict the image using the model
        results = model(img)
        
        results.save('runs')
        print(results)

        # Convert the results to a pandas dataframe and calculate the height, width, and area of the bounding box
        df_results = results.pandas().xyxy[0]
        df_results['bboxHt'] = df_results['ymax'] - df_results['ymin']
        df_results['bboxWt'] = df_results['xmax'] - df_results['xmin']
        df_results['bboxArea'] = df_results['bboxHt'] * df_results['bboxWt']

        # Sort by bounding box area, largest first
        df_results = df_results.sort_values('bboxArea', ascending=False)

        # Filter out 'Bullseye' and initialize prediction to 'NA'
        pred_list = df_results
        pred = 'NA'

        # If only one prediction, select it
        if len(pred_list) == 1:
            pred = pred_list.iloc[0]
        # If more than one label is detected, apply further logic to select the best prediction
        elif len(pred_list) > 1:
            pred_shortlist = []
            current_area = pred_list.iloc[0]['bboxArea']
            
            # Filter by confidence and area
            for _, row in pred_list.iterrows():
                if row['name'] != 'Bullseye' and row['confidence'] > 0.7 and \
                        ((current_area * 0.8 <= row['bboxArea']) or \
                        (row['name'] == 'One' and current_area * 0.6 <= row['bboxArea'])):
                    pred_shortlist.append(row)
                    current_area = row['bboxArea']

            # Select based on the signal and other conditions
            # if len(pred_shortlist) == 1:
            pred = pred_shortlist[0]
            # else:
            #     pred_shortlist.sort(key=lambda x: x['xmin'])

            #     if signal == 'L':
            #         pred = pred_shortlist[0]
            #     elif signal == 'R':
            #         pred = pred_shortlist[-1]
            #     else:  # 'C' for central
            #         for i in range(len(pred_shortlist)):
            #             if 250 < pred_shortlist[i]['xmin'] < 774:
            #                 pred = pred_shortlist[i]
            #                 break
            #         if isinstance(pred, str):
            #             pred_shortlist.sort(key=lambda x: x['bboxArea'])
            #             pred = pred_shortlist[-1]

        # Draw the selected bounding box on the image
        if not isinstance(pred, str):
            draw_own_bbox(np.array(img), pred['xmin'], pred['ymin'], pred['xmax'], pred['ymax'], pred['name'])
            print(f"Selected prediction: {pred['name']}")
        
        # Return the selected prediction as per the logic
        name_to_id = {
            "NA": 'NA', "Bullseye": 10, "one": 11, "two": 12, "three": 13, "four": 14,
            "five": 15, "six": 16, "seven": 17, "eight": 18, "nine": 19, "A": 20,
            "B": 21, "C": 22, "D": 23, "E": 24, "F": 25, "G": 26, "H": 27,
            "S": 28, "T": 29, "U": 30, "V": 31, "W": 32, "X": 33, "Y": 34,
            "Z": 35, "Up": 36, "Down": 37, "Right": 38, "Left": 39,
            "Up Arrow": 36, "Down Arrow": 37, "right": 38, "Left Arrow": 39, "Stop": 40
        }
        if not isinstance(pred, str):
            image_id = str(name_to_id[pred['name']])
        else:
            image_id = 'NA'
        print(f"Final result: {image_id}")
        return [image_id, pred['name']]
    
    except Exception as e:
        print(f"Error occurred during prediction: {traceback.format_exc()}")
        print(f"Final result: NA")
        return ['NA', 'NA']

def draw_own_bbox(img,x1,y1,x2,y2,label,color=(36,255,12),text_color=(0,0,0)):
    """
    Draw bounding box on the image with text label and save both the raw and annotated image in the 'own_results' folder

    Inputs
    ------
    img: numpy.ndarray - image on which the bounding box is to be drawn

    x1: int - x coordinate of the top left corner of the bounding box

    y1: int - y coordinate of the top left corner of the bounding box

    x2: int - x coordinate of the bottom right corner of the bounding box

    y2: int - y coordinate of the bottom right corner of the bounding box

    label: str - label to be written on the bounding box

    color: tuple - color of the bounding box

    text_color: tuple - color of the text label

    Returns
    -------
    None

    """
    name_to_id = {
        "NA": 'NA',
        "Bullseye": 'NA',
        "one": 11,
        "two": 12,
        "three": 13,
        "four": 14,
        "five": 15,
        "six": 16,
        "seven": 17,
        "eight": 18,
        "nine": 19,
        "A": 20,
        "B": 21,
        "C": 22,
        "D": 23,
        "E": 24,
        "F": 25,
        "G": 26,
        "H": 27,
        "S": 28,
        "T": 29,
        "U": 30,
        "V": 31,
        "W": 32,
        "X": 33,
        "Y": 34,
        "Z": 35,
        "Up": 36,
        "Down": 37,
        "Right": 38,
        "Left": 39,
        "Up Arrow": 36,
        "Down Arrow": 37,
        "right": 38,
        "Left Arrow": 39,
        "Stop": 40
    }
    # Reformat the label to {label name}-{label id}
    label = label + "-" + str(name_to_id[label])
    # Convert the coordinates to int
    x1 = int(x1)
    x2 = int(x2)
    y1 = int(y1)
    y2 = int(y2)
    # Create a random string to be used as the suffix for the image name, just in case the same name is accidentally used
    rand = str(int(time.time()))

    # Save the raw image
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2.imwrite(f"results/raw/raw_image_{label}_{rand}.jpg", img)

    # Draw the bounding box
    img = cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    # For the text background, find space required by the text so that we can put a background with that amount of width.
    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    # Print the text  
    img = cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), color, -1)
    img = cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)
    # Save the annotated image
    cv2.imwrite(f"own_results/annotated/annotated_image_{label}_{rand}.jpg", img)

# def live_rec():
#     model = load_model()
    
#         # Open a video capture for the live camera feed (default webcam, `0`)
#     cap = cv2.VideoCapture(0)  # If using an external camera, change '0' to '1' or the appropriate camera index

#     # Check if the camera opened successfully
#     if not cap.isOpened():
#         print("Error: Could not open video stream.")
#         exit()

#     while True:
#         # Capture frame-by-frame from the camera
#         ret, frame = cap.read()
        
#         if not ret:
#             print("Error: Failed to capture image.")
#             break

#         # Perform object detection on the current frame
#         results = model(frame)

#         # Render the results (bounding boxes, labels, etc.) on the frame
#         result_frame = results.render()[0]

#         # Display the frame with detection results
#         cv2.imshow('YOLOv5 Live Feed Detection', result_frame)

#         # Press 'q' to quit the live feed
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     # Release the camera and close any open OpenCV windows
#     cap.release()
#     cv2.destroyAllWindows()

# live_rec()

# model = load_model()

# predict_image('2024-09-24-125015.jpg', model)



def stitch_image():
    """
    Stitches the images in the folder together and saves it into runs/stitched folder in 2 rows
    """
    # Initialize path to save stitched image
    imgFolder = 'runs'
    stitchedPath = os.path.join(imgFolder, f'stitched-{int(time.time())}.jpeg')

    # Find all files that ends with ".jpg" (this won't match the stitched images as we name them ".jpeg")
    # imgPaths = glob.glob(os.path.join(imgFolder+"/detect/*/", "*.jpg"))
    imgPaths = glob.glob(os.path.join('own_results/annotated/', "*.jpg"))
    # Open all images
    images = [Image.open(x) for x in imgPaths]
    # Get the width and height of each image
    width, height = zip(*(i.size for i in images))

    # Calculate the number of images per row (half of the total images)
    num_images_per_row = len(images) // 2 + len(images) % 2

    # Calculate the total width and max height of the stitched image
    total_width = max(width) * num_images_per_row
    max_height = max(height) * 2

    # Create a new blank image with the calculated dimensions
    stitchedImg = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    y_offset = 0

    # Stitch the images together in 2 rows
    for i, im in enumerate(images):
        stitchedImg.paste(im, (x_offset, y_offset))
        x_offset += im.size[0]
        if (i + 1) % num_images_per_row == 0:
            x_offset = 0
            y_offset += im.size[1]

    # Save the stitched image to the path
    stitchedImg.save(stitchedPath)

    # Move original images to "originals" subdirectory
    for img in imgPaths:
        shutil.move(img, os.path.join(
            "own_results", "old", os.path.basename(img)))

    return stitchedImg
   

def stitch_image_own():
    """
    Stitches the images in the folder together and saves it into own_results folder in 2 rows

    Basically similar to stitch_image() but with different folder names and slightly different drawing of bounding boxes and text
    """
    imgFolder = 'own_results'
    stitchedPath = os.path.join(imgFolder, f'stitched-{int(time.time())}.jpeg')

    imgPaths = glob.glob(os.path.join(imgFolder, "annotated", "annotated_image_*.jpg"))
    imgTimestamps = [imgPath.split("_")[-1][:-4] for imgPath in imgPaths]
    
    sortedByTimeStampImages = sorted(zip(imgPaths, imgTimestamps), key=lambda x: x[1])

    images = [Image.open(x[0]) for x in sortedByTimeStampImages]
    width, height = zip(*(i.size for i in images))

    # Calculate the number of images per row (half of the total images)
    num_images_per_row = len(images) // 2 + len(images) % 2

    # Calculate the total width and max height of the stitched image
    total_width = max(width) * num_images_per_row
    max_height = max(height) * 2

    # Create a new blank image with the calculated dimensions
    stitchedImg = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    y_offset = 0

    # Stitch the images together in 2 rows
    for i, im in enumerate(images):
        stitchedImg.paste(im, (x_offset, y_offset))
        x_offset += im.size[0]
        if (i + 1) % num_images_per_row == 0:
            x_offset = 0
            y_offset += im.size[1]

    # Save the stitched image to the path
    stitchedImg.save(stitchedPath)

    return stitchedImg