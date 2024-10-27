from algorithm.entities.grid.position import Position

class Node:
    def __init__(self, x, y, occupied, direction=None):
        """
        Initializes a grid node with specified coordinates and occupancy status.
        
        Parameters:
        x (int): The x-coordinate of the node in the grid.
        y (int): The y-coordinate of the node in the grid.
        occupied (bool): Indicates if the node is currently occupied.
        direction (optional): The direction associated with the node, if applicable.
        """
        self.pos = Position(x, y, direction)
        self.occupied = occupied
        self.x = x 
        self.y = y 
        self.direction = direction 

    def __str__(self):
        return f"Node({self.pos})"  # String representation of the node.

    __repr__ = __str__  # Allow for consistent representation in collections.

    def __eq__(self, other):
        """
        Compares this node with another node for equality.
        
        Two nodes are considered equal if their positions and directions match.
        """
        return self.pos.xy_direction() == other.pos.xy_direction()  # Compare based on position and direction.

    def __hash__(self):
        """
        Generates a hash value for the node based on its position and direction.
        This is useful for using nodes in sets or as dictionary keys.
        """
        return hash(self.pos.xy_direction())  # Use the position's XY coordinates for hashing.

    def copy(self):
        """
        Creates and returns a duplicate of this node.
        
        The new node will have the same coordinates and occupancy status as the original.
        """
        return Node(self.pos.x, self.pos.y, self.occupied, self.pos.direction)  # Create a new node with identical properties.
