# SC2079 MDP - Group 4 RPI and Algo Code

Hi! Welcome to our group's RPI and Algo repository. We did our best to clean up the code after our project ended, so hopefully it is as organised as it can be for your reference.

## Overview

Hi! Welcome to our group's RPI and Algo repository. We did our best to clean up the code after our project ended, so hopefully it is as organised as it can be for your reference.

You can find our group's video [here](https://www.youtube.com/watch?v=ft0QzwhuB7s)!

This repository's Controller folder will be hosted on the RPI itself. It will serve as an orchestrator to facilitate the connection between the STM board, Android and Algorithm.

The Application folder will be hosted on another laptop, this is where we will be running both the algorithm and image inference server.

## RPI

We used Python's `multiprocessing` library to manage the concurrent processes.

A `queue` system was used to ensure that all commands are received and executed in correct sequence.

Most importantly, proper `lock` management is needed to ensure processes will not try to access the same resource at once.


## Image Rec and Inference Server
We utilized a YOLOv5 model trained on a dataset of more than 2,000 images, which were collected in collaboration with other groups. Annotation was done using roboflow.

A Flask server was deployed as our inference server to:
1. receive images captured by the RPI camera.
2. perform object detection using our trained model.
3. return the detection results to the RPI for further processing.

## Important Links and Acknowledgement

Our work was only made possible thanks to the following resources (really really grateful for it). Below are the links!

### References
https://github.com/pyesonekyaw/CZ3004-SC2079-MDP-RaspberryPi


### Bluetooth Troubleshoot
https://www.reddit.com/r/learnpython/comments/6wnutb/python_353raspberry_pi_cant_import_bluetooth/
