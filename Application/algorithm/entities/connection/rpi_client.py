import pickle
import socket


class RPiClient:
    """
    Used for connecting to...
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.socket.settimeout(5)

    def connect(self):
        self.socket.connect((self.host, self.port))

    def send_message(self, obj):
        self.socket.sendall(pickle.dumps(obj))

    def receive_data(self):
        d=self.socket.recv(2048)
        return pickle.loads(d)

    def close(self):
        self.socket.close()
