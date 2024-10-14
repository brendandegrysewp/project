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
    # Step 2: listen for messages and just print them out to confirm receipt   #
    ############################################################################

    # make a start method
    def start(self):
        # create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set timeout 
        self.server_socket.settimeout(10)
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
        
        try:
            # loop forever
            while True:
                # receive messages
                message = connection.recv(self.frame_size).decode()
                # if nothing came through get out of the infinite loop
                if not message:
                    print("Nothing received, terminating loop.")
                    break
                # print out received messages
                print(f"Message received: {message}")

        # if it breaks it is super helpful to know why
        except Exception as e:
            print(f"Exception occurred: {e}")

            # respond with 'ACK'

            # optionally make it so server doesn't respond to test timeout        
        finally:
            # close everything
            connection.close()
            self.server_socket.close()

# make a main statement for testing
        

if __name__ == "__main__":
    server = StopAndWaitServer()
    server.start()