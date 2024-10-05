import socket
import pickle


class RPiServer:
    """
    Used as the server in the RPi.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket()

        self.__data = []
        self.conn, self.address = None, None

    def start(self):
        print(f"Creating server at {self.host}:{self.port}")
        self.socket.bind((self.host, self.port))
        self.socket.settimeout(10)
        self.socket.listen()
        print("Listening for connection...")

        try:
            self.conn, self.address = self.socket.accept()
        except socket.timeout:
            print('Socket timed out. No connection received.')
            return None
        print(f"Connection from {self.address}")

    def receive_data(self):
        assert self.conn is not None and self.address is not None
        d = self.conn.recv(2048)
        return pickle.loads(d)

    def close(self):
        print("Closing socket.")
        self.socket.close()
