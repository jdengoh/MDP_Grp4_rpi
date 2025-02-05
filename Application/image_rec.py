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
    pt_path = os.path.join(current_path, 'best (19).pt')

    model = torch.hub.load(yolo5_path,
                           'custom',
                           path=pt_path,
                           source='local')
    return model

def predict_image(image, model):
    try:
        # Load the image
        img = Image.open(image)

        # Predict the image using the model
        pred_output = model(img)
        
        pred_output.save('runs')
        print(pred_output)

        # Convert the pred_output to a pandas dataframe and calculate the height, width, and area of the bounding box
        df_predictions = pred_output.pandas().xyxy[0]
        df_predictions['box_height'] = df_predictions['ymax'] - df_predictions['ymin']
        df_predictions['box_width'] = df_predictions['xmax'] - df_predictions['xmin']
        df_predictions['box_area'] = df_predictions['box_height'] * df_predictions['box_width']

        df_predictions = df_predictions.sort_values('box_area', ascending=False)

        pred_list = df_predictions

        print()
        print("************** PRED LIST **************")
        print(pred_list)
        print("****************************************")
        pred = 'NA'

        # If only one prediction, select it
        if len(pred_list) == 1:
            print("*********** Case 1: only 1 PRED ***********")
            pred = pred_list.iloc[0]
            print("*******************************************")

        # If more than one label is detected, apply further logic to select the best prediction
        elif len(pred_list) > 1:
            pred_shortlist = []
            current_area = pred_list.iloc[0]['box_area']
            
            # Filter by confidence and area
            for _, row in pred_list.iterrows():
                print("************** Case 2: ITERROWS TIME **************")
                if row['name'] != 'Bullseye' and (row['confidence'] > 0.8 or \
                                                  (row['name'] in ['F', 'G', 'H', 'Y', 'V'] and row['confidence'] >= 0.75) or \
                                                    (row['name'] == 'One' and current_area * 0.6 <= row['box_area'])):
                    print("=============== APPENDING STHING ===============")
                    print(row)
                    print("===============================================")
                    pred_shortlist.append(row)
                    current_area = row['box_area']
                    print("+++++++++++++++ APPENDING STHING +++++++++++++++")
# ------------------------------------------------------------------------------------------------------------ #
            print("=============== PRED SHORTLIST ===============")
            print(pred_shortlist)
            pred = 'NA'
            print("==============================================")

            # Check if both 'five' and 'circle' are in the prediction list
            five_pred = next((row for row in pred_shortlist if row['name'] == 'five'), None)
            circle_pred = next((row for row in pred_shortlist if row['name'] == 'circle'), None)

            if five_pred and circle_pred:
                # If both are detected, compare their confidence
                confidence_diff = abs(five_pred['confidence'] - circle_pred['confidence'])
                if confidence_diff < 0.20:
                    # If the confidence difference is less than 0.20, predict 'five'
                    pred = five_pred
                    print("************** Choosing 'five' based on confidence difference **************")
            else:
                if len(pred_shortlist) == 1:
                    print("************** ENTERING IF(pred_shortlist == 1) **************")
                    pred = pred_shortlist[0]
                    print("**************************************************************")

                else:
                    print("************** ENTERING ELSE **************")

                    pred_shortlist.sort(key=lambda x: x['xmin'])

                    fake_con = -1
                    for i in range(len(pred_shortlist)):
                        if 250 < pred_shortlist[i]['xmin'] < 774:
                            if pred_shortlist[i]['confidence'] > fake_con:
                                pred = pred_shortlist[i]
                                fake_con = pred_shortlist[i]['confidence']
                            else:
                                continue
                    if isinstance(pred, str):
                        pred_shortlist.sort(key=lambda x: x['box_area'])
                        pred = pred_shortlist[0]

        # Draw the selected bounding box on the image
        if not isinstance(pred, str):
            draw(np.array(img), pred['xmin'], pred['ymin'], pred['xmax'], pred['ymax'], pred['name'])
            print(f"Selected prediction: {pred['name']}")
        
        # Return the selected prediction as per the logic
        id_list = {
            "NA": 'NA', "Bullseye": 10, "one": 11, "two": 12, "three": 13, "four": 14,
            "five": 15, "six": 16, "seven": 17, "eight": 18, "nine": 19, "A": 20,
            "B": 21, "C": 22, "D": 23, "E": 24, "F": 25, "G": 26, "H": 27,
            "S": 28, "T": 29, "U": 30, "V": 31, "W": 32, "X": 33, "Y": 34,
            "Z": 35, "Up": 36, "Down": 37, "Right": 38, "Left": 39,
            "up": 36, "down": 37, "right": 38, "left": 39, "circle": 40
        }
        if not isinstance(pred, str):
            image_id = str(id_list[pred['name']])
        else:
            image_id = 'NA'
        print(f"Final result: {image_id}")
        return [image_id, pred['name']]
    
    except Exception as e:
        print(f"Error occurred during prediction: {traceback.format_exc()}")
        print(f"Final result: NA")
        return ['NA', 'NA']

def draw(img,x1,y1,x2,y2,label):

    col = (40,255,18)
    t_col = (0,0,0)

    id_list = {
    "NA": 'NA', "Bullseye": 10, "one": 11, "two": 12, "three": 13, "four": 14,
    "five": 15, "six": 16, "seven": 17, "eight": 18, "nine": 19, "A": 20,
    "B": 21, "C": 22, "D": 23, "E": 24, "F": 25, "G": 26, "H": 27,
    "S": 28, "T": 29, "U": 30, "V": 31, "W": 32, "X": 33, "Y": 34,
    "Z": 35, "Up": 36, "Down": 37, "Right": 38, "Left": 39,
    "up": 36, "down": 37, "right": 38, "left": 39, "circle": 40
    }
    
    label = label + "-" + str(id_list[label])

    x1 = int(x1)
    x2 = int(x2)
    y1 = int(y1)
    y2 = int(y2)

    # Save the raw image
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2.imwrite(f"results/raw/raw_image_{label}_{str(int(time.time()))}.jpg", img)

    # Draw the bounding box
    img = cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)

    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)

    img = cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), col, -1)
    if label == "circle":
        label="stop"
    img = cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, t_col, 1)

    cv2.imwrite(f"own_results/annotated/annotated_image_{label}_{str(int(time.time()))}.jpg", img)

def stitch_image():
    # Initialize path to save stitched image
    fold = 'runs'
    final_path = os.path.join(fold, f'final_image_{int(time.time())}.jpeg')

    image_paths = glob.glob(os.path.join('own_results/annotated/', "*.jpg"))

    results = [Image.open(x) for x in image_paths]

    width, height = zip(*(i.size for i in results))

    # 2 rows of images
    num_images_per_row = len(results) // 2 + len(results) % 2

    total_width = max(width) * num_images_per_row
    max_height = max(height) * 2

    final_stitch = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    y_offset = 0

    # Stitch the images together in 2 rows
    for i, im in enumerate(results):
        final_stitch.paste(im, (x_offset, y_offset))
        x_offset += im.size[0]
        if (i + 1) % num_images_per_row == 0:
            x_offset = 0
            y_offset += im.size[1]

    final_stitch.save(final_path)

    # Move original results to "originals" subdirectory
    for img in image_paths:
        shutil.move(img, os.path.join(
            "own_results", "old", os.path.basename(img)))

    return final_stitch