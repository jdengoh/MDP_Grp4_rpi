from algorithm import settings
from algorithm.entities.assets import colors
from algorithm.entities.grid.position import Position


class Node:
    def __init__(self, x, y, occupied, direction=None):
        """
        x and y coordinates are in terms of the grid.
        """
        self.pos = Position(x, y, direction)
        self.occupied = occupied
        self.x = x
        self.y = y
        self.direction = direction

    def __str__(self):
        return f"Node({self.pos})"

    __repr__ = __str__

    def __eq__(self, other):
        return self.pos.xy_dir() == other.pos.xy_dir()

    def __hash__(self):
        return hash(self.pos.xy_dir())

    def copy(self):
        """
        Return a copy of this node.
        """
        return Node(self.pos.x, self.pos.y, self.occupied, self.pos.direction)