from typing import List
from abc import ABC, abstractmethod

import time

from algorithm import settings
from algorithm.entities.assets import colors
from algorithm.entities.grid.grid import Grid
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.robot.robot import Robot

import os

class AlgoMinimal():
    """
    Minimal app to just calculate a path and then send the commands over.
    """
    def __init__(self, obstacles):
        st = time.time()
        self.grid = Grid(obstacles)
        self.robot = Robot(self.grid)
        print("time to create grid and robot", time.time()-st)

    def execute(self):
        # Calculate path
        print("Calculating path...")
        st = time.time()
        order, targets = self.robot.brain.plan_path() # change change change change change change change change change change change change
        print("time to calculate path", time.time()-st)
        self.targets = targets
        print("Done!")
        return order # change change change change change change change change change change change change
