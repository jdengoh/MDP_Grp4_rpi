import json
import os
import socket
import bluetooth
from typing import Optional
from BaseController import BaseController

class android_msg:
    def __init__(self, cat: str, msg: str):

        self._cat = cat
        self.msg = msg

    def get_cat(self) -> str:
        return self._cat
    
    def get_msg(self) -> str:
        return self.msg
    
    def jsonify(self) -> str:
        return json.dumps({'cat': self._cat, 
                           'msg': self.msg})

class AndroidController(BaseController):

    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.server_socket = None


    def connect(self):
        self.logger.info('Activating Bluetooth Connection')

        try:
            os.system("sudo hciconfig hci0 piscan")

            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", bluetooth.PORT_ANY))
            self.server_socket.listen(1)

            port = self.server_socket.getsockname()[1]
            # uuid = pass
        
            bluetooth.advertise_service(self.server_socket, 
                                        "MDPGroup4", 
                                        # service_id=uuid, 
                                        service_classes=[bluetooth.SERIAL_PORT_CLASS], 
                                        profiles=[bluetooth.SERIAL_PORT_PROFILE])
            
            self.logger.info(f"Waiting for connection on RFCOMM channel {port}")
            
            self.client_socket, client_info = self.server_socket.accept()
            self.logger.info(f"Accepted connection from {client_info}")

        except Exception as e:
            self.logger.error(f"Error establishing connection: {e}")
            self.server_socket.close()
            self.server_socket = None

    def disconnect(self):
        try:
            self.logger.info("Deactivating Bluetooth Connection")
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
            self.client_socket = None
            self.server_socket.close()
            self.server_socket = None
            self.logger.info("Disconnected from Android")

        except Exception as e:
            self.logger.error(f"Error disconnecting from Android: {e}")
            raise e

    def send(self, msg:android_msg) -> None:
        try:
            self.client_socket.send(f"{msg.jsonify()}\n".encode("utf-8"))
            self.logger.debug(f"Sent to Android: {msg.jsonify()}")

        except Exception as e:
            self.logger.error(f"Error sending message to Android: {e}")
            raise e
        
    def receive(self) -> Optional[str]:
        try:
            data = self.client_socket.recv(1024)
            message = data.strip().decode('utf-8')
            self.logger.debug(f"Received from Android: {data.decode('utf-8')}")
            return message

        except Exception as e:
            self.logger.error(f"Error receiving message from Android: {e}")
            raise e 
        
