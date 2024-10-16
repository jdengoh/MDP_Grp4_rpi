import torch
import pathlib
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath
import torch
import cv2

# Path to your custom YOLOv5 model
model_path = './best (4).pt'

#"C:\Users\hp\Downloads\use.pt"

# "C:\Users\hp\Downloads\best (1).pt"
# "C:\Users\hp\Downloads\best (4).pt"

# Load your YOLOv5 model
print("Loading model...")
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)
print("Model loaded successfully.")

# Open a video capture for the live camera feed (default webcam, `0`)
cap = cv2.VideoCapture(0)  # If using an external camera, change '0' to '1' or the appropriate camera index

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    # Capture frame-by-frame from the camera
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Failed to capture image.")
        break

    # Perform object detection on the current frame
    results = model(frame)

    # Render the results (bounding boxes, labels, etc.) on the frame
    result_frame = results.render()[0]

    # Display the frame with detection results
    cv2.imshow('YOLOv5 Live Feed Detection', result_frame)

    # Press 'q' to quit the live feed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close any open OpenCV windows
cap.release()
cv2.destroyAllWindows()
