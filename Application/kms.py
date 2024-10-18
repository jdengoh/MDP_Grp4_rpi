import time
import matplotlib.pyplot as plt
import os
from typing import List
from algorithm import settings
from algorithm.entities.assets.direction import Direction
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.grid.grid import Grid

def parse_obstacle_data(data: dict) -> List[Obstacle]:
    obstacle_list = []

    for key, obstacle_params in data.items():  # Iterate over the dictionary's items
        obstacle_list.append(Obstacle(
            obstacle_params[0] + 5,  # x-coordinate
            obstacle_params[1] + 5,  # y-coordinate
            Direction(obstacle_params[2]),  # direction
            obstacle_params[3]  # index (ID)
        ))

    return obstacle_list

def run_visualizer():
    # Fill in obstacle positions with respect to lower bottom left corner.
    obstacles = {
        "0": [40, 100, 90, 0],
        "1": [70, 170, -90, 1],
        "2": [170, 100, -90, 2],
        "3": [110, 70, 180, 3],
        "4": [150, 30, 180, 4],
        "5": [150, 160, 180, 5]
    }

    st = time.time()  # Start time to receive the obstacle
    obs = parse_obstacle_data(obstacles)
    draw_grid(obs)  # Draw the grid with obstacles

    # Create a Grid object with the obstacles and visualize validity for each obstacle target grid
    for obstacle_index, _ in enumerate(obs):
        grid = Grid(obs)
        print(grid.cache.keys())
        print(obstacle_index)
        draw_validity_grid(grid, obstacle_index)  # Draw the grid showing valid and invalid areas for each target grid

    ed = time.time()
    print("Time to visualize the obstacles", ed - st)

def draw_grid(obstacles):
    """
    Function to draw the grid using Matplotlib to verify the setup.
    """
    # Create a directory for saving grid images if it doesn't exist
    output_folder = "grid"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.set_xlim(0, settings.WINDOW_SIZE[0])
    ax.set_ylim(0, settings.WINDOW_SIZE[1])
    ax.set_title("Grid Verification - Obstacle Visualization")

    # Draw nodes (default to free area)
    for x in range(0, settings.WINDOW_SIZE[0], settings.GRID_CELL_LENGTH):
        for y in range(0, settings.WINDOW_SIZE[1], settings.GRID_CELL_LENGTH):
            rect = plt.Rectangle((x, y), settings.GRID_CELL_LENGTH, settings.GRID_CELL_LENGTH, color='lightgray', fill=True, edgecolor='black')
            ax.add_patch(rect)

    # Draw obstacles with smaller safety zones
    obstacle_safety_radius = settings.OBSTACLE_SAFETY_WIDTH  # Reduced safety zone
    for obstacle in obstacles:
        # Draw safety zone
        safety_circle = plt.Circle((obstacle.x_cm * settings.SCALING_FACTOR, obstacle.y_cm * settings.SCALING_FACTOR), obstacle_safety_radius, color='yellow', alpha=0.3)
        ax.add_patch(safety_circle)
        # Draw core obstacle
        core_circle = plt.Circle((obstacle.x_cm * settings.SCALING_FACTOR, obstacle.y_cm * settings.SCALING_FACTOR), 10, color='red')
        ax.add_patch(core_circle)

    plt.gca().invert_yaxis()  # Invert y-axis to match typical grid orientation
    filename = "grid_visualization.png"
    plt.savefig(os.path.join(output_folder, filename))
    plt.show()

def draw_validity_grid(grid, obstacle_index):
    """
    Function to draw the grid using Matplotlib to show valid (free) and invalid areas for each obstacle grid.
    """
    # Create a directory for saving grid images if it doesn't exist
    output_folder = "grid"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.set_xlim(0, settings.WINDOW_SIZE[0])
    ax.set_ylim(0, settings.WINDOW_SIZE[1])
    ax.set_title(f"Grid Verification - Validity Visualization for Obstacle {obstacle_index}")

    # Draw nodes, color based on validity
    for x in range(0, settings.WINDOW_SIZE[0], settings.GRID_CELL_LENGTH):
        for y in range(0, settings.WINDOW_SIZE[1], settings.GRID_CELL_LENGTH):
            if grid.cache[obstacle_index].get((x, y)) is False:
                color = 'red'  # Invalid area
            else:
                color = 'lightgray'  # Valid area
            rect = plt.Rectangle((x, y), settings.GRID_CELL_LENGTH, settings.GRID_CELL_LENGTH, color=color, fill=True, edgecolor='black')
            ax.add_patch(rect)

    plt.gca().invert_yaxis()  # Invert y-axis to match typical grid orientation
    filename = f"validity_grid_visualization_obstacle_{obstacle_index}.png"
    plt.savefig(os.path.join(output_folder, filename))
    plt.show()

if __name__ == '__main__':
    run_visualizer()
