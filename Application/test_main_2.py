import sys
import time
import pygame
from typing import List
from algorithm import settings
from algorithm.entities.assets import colors
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.grid.grid import Grid  # Import Grid class
from algorithm.entities.robot.robot import Robot
from algorithm.entities.commands.turn_command import TurnCommand
from abc import ABC, abstractmethod


class AlgoApp(ABC):
    def __init__(self, obstacles: List[Obstacle]):
        self.grid = Grid(obstacles)
        self.robot = Robot(self.grid)

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def execute(self):
        pass


class AlgoSimulator(AlgoApp):
    """
    Run the Algo using a GUI simulator.
    """

    def __init__(self, obstacles: List[Obstacle]):
        super().__init__(obstacles)

        self.running = False
        self.size = self.width, self.height = settings.WINDOW_SIZE
        self.screen = self.clock = None
        self.command_index = 0
        self.previous_position = None

    def init(self):
        """
        Set initial values for the app.
        """
        pygame.init()
        self.running = True

        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()

        # Inform user that it is finding path...
        pygame.display.set_caption("Calculating path...")
        font = pygame.font.SysFont("arial", 35)
        text = font.render("Calculating path...", True, colors.TAN)
        text_rect = text.get_rect()
        text_rect.center = settings.WINDOW_SIZE[0] / 2, settings.WINDOW_SIZE[1] / 2
        self.screen.blit(text, text_rect)
        pygame.display.flip()

        # Calculate the path.
        self.robot.brain.plan_path()
        pygame.display.set_caption("Simulating path!")  # Update the caption once done.
        self.previous_position = (int(self.robot.get_current_pos().x), int(self.robot.get_current_pos().y))

    def settle_events(self):
        """
        Process Pygame events.
        """
        for event in pygame.event.get():
            # On quit, stop the game loop. This will stop the app.
            if event.type == pygame.QUIT:
                self.running = False

    def do_updates(self):
        commands = list(self.robot.brain.commands)

        if self.command_index < len(commands):
            command = commands[self.command_index]
            if isinstance(command, TurnCommand):
                command.apply_on_pos(self.robot.get_current_pos(), self.robot.get_current_pos().direction)
            else:
                command.apply_on_pos(self.robot.get_current_pos())
            self.command_index += 1

    def render(self):
        """
        Render the screen.
        """
        self.screen.fill(colors.TAN, None)

        # Draw obstacles and robot
        self.grid.draw(self.screen)
        self.robot.draw(self.screen)

        # Draw path line
        current_position = (int(self.robot.get_current_pos().x), int(self.robot.get_current_pos().y))
        if self.previous_position:
            pygame.draw.line(self.screen, colors.GREEN, self.previous_position, current_position,
                             2)  # Draw line showing path
        self.previous_position = current_position

        # Really render now
        pygame.display.flip()

    def execute(self):
        """
        Initialise the app and start the game loop.
        """
        self.init()
        while self.running:
            # Check for Pygame events.
            self.settle_events()
            # Do required updates.
            self.do_updates()

            # Render the new frame.
            self.render()

            self.clock.tick(settings.FRAMES // 3)  # Slow down the simulation by reducing frames per second


def parse_obstacle_data(data: dict) -> List[Obstacle]:
    obstacle_list = []

    for key, obstacle_params in data.items():  # Iterate over the dictionary's items
        obstacle_list.append(Obstacle(
            obstacle_params[0],  # x-coordinate
            obstacle_params[1],  # y-coordinate
            Direction(obstacle_params[2]),  # direction
            obstacle_params[3]  # index (ID)
        ))

    return obstacle_list


def run_simulator_with_visualisation():
    # Define obstacle positions with respect to the lower bottom left corner.
    obstacles = {
        "0": [45, 105, 90, 0],
        "1": [75, 175, -90, 1],
        "2": [175, 105, -90, 2],
        "3": [115, 75, 180, 3],
        "4": [155, 35, 180, 4],
        "5": [155, 165, 180, 5]
    }

    obs = parse_obstacle_data(obstacles)
    simulator = AlgoSimulator(obs)
    simulator.execute()


if __name__ == '__main__':
    run_simulator_with_visualisation()
