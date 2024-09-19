import json
import os
import socket
import bluetooth

# from communication.link import Link


class AndroidController(link):

    def __innit__(self):
        super().__init__()
        self.client_socket = None
        self.server_socket = None


    def conncet(self):
        self.logger.info('Activating Bluetooth Connection')

        try:
            os.system("sudo hciconfig hci0 piscan")

            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", bluetooth.PORT_ANY))
            self.server_socket.listen(1)

            port = self.server_socket.getsockname()[1]
            # uuid = pass
        
            bluetooth.advertise_service(self.server_socket, 
                                        "AndroidController", 
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

    def send(self, msg: str) -> None:
        try:
            self.client_socket.send(f"{msg.jsonify()}\n".econde("utf-8"))
            self.logger.debug(f"Sent to Android: {{msg.jsonify()}}")

        except Exception as e:
            self.logger.error(f"Error sending message to Android: {e}")
            raise e
        
    def receive(self) -> None:
        try:
            data = self.client_socket.recv(1024)
            self.logger.debug(f"Received from Android: {data.decode('utf-8')}")

        except Exception as e:
            self.logger.error(f"Error receiving message from Android: {e}")
            raise e 