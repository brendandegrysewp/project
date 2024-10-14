import socket

class StopAndWaitServer:
    # init
    def __init__(self, host='localhost', port=12345, frame_size=256,
                 messages=[]) :
        # host: Address of the receiver (default = 'localhost)
        # port: Port number to connect to (default = 12345)
        # frame_size: Maximum size of each segment (default = 256)
        # messages: List of messages to send to the receiver (default = [])
        # sender_socket: Socket for the connection to the receiver (default = None)
        self.host = host
        self.port = port
        self.frame_size = frame_size
        messages = messages

    ############################################################################
    # step 1: confirm we can establish a connection, print out the address     #
    ############################################################################

    # make a start method
    def start(self):
        # create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set timeout 
        self.server_socket.settimeout(5)
        # bind socket
        self.server_socket.bind((self.host, self.port))
        # listen for connections
        self.server_socket.listen()
        print(f"Listening for connections on port {self.port}.")
        # accept connections
        connection, client_address = self.server_socket.accept()
        # print out status
        print("Connection request accepted.")
        print(f"Connection from {client_address}")

        # close everything
        connection.close()
        self.server_socket.close()




        # note that we didn't bother doing the infinite loop for initial testing

            # loop forever

            # receive messages

            # print out received messages

            # respond with 'ACK'

            # optionally make it so server doesn't respond to test timeout



# make a main statement for testing
        

if __name__ == "__main__":
    server = StopAndWaitServer()
    server.start()