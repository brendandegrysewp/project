import socket                   # used to send and receive messages
import signal                   # used to allow CTRL-C to shut off server
import json                     # used to easily read the provided json files
from pathlib import Path        # used to more easily handle file paths
from datetime import datetime
from urllib import response   # used to determine if a file has been changed

class Server:
    # The __init__ method will be called automatically when you initialize
    # a new instance of the Server class. This is a good spot to define any
    # attributes that would be helpful to access in all methods.
    def __init__(self, host='localhost', port=8080, resources = "resources.json"):
        # The following line of code creates a socket object for you to use.
        # AF_INET is the attribute that says this is an Internet type socket, SOCK_DGRAM says this is a UDP socket.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setblocking(False)
        self.host = host
        self.port = port
        file = open(resources)
        self.resources = json.load(file)
        file.close()
        # this specifies we will read 1024 bytes at a time. You will need it to listen for the client's messages
        self.recv_size = 1024

        self.running = True                 # this is used to end the program if you press CTRL-C, don't mess with it

        base_path = Path(__file__).parent   # this line of code determines the location of your server code so you can build paths with it

        # We recommend that you read in the resources.json file and store the data for easy reference later
        ### ADD ANY ADDITIONAL ATTRIBUTES HERE ###

    def start_server(self):
        self.server_socket.bind((self.host, self.port))     # this line of code reserves the specified port with your OS. DON'T CHANGE IT.
        print(f"Server is listening on port {self.port}...")

        while self.running:         # this line is used to exit your code with CTRL-C. DON'T CHANGE IT.
            try:

                """
                This method is the control method which will constantly listen for incoming messages.
                You need to do the following things here:
                - Check if a new messages has been received
                - Decode the message
                - Send the decoded message to the process_request method
                - Take the response generated in process_request and send it back to the client
                """
                message, clientAddress = self.server_socket.recvfrom(self.recv_size)
                message = self.process_request(message.decode())
                self.server_socket.sendto(message.encode(), clientAddress)


            except BlockingIOError:
                continue                # if there is no message go back to the top of the loop

            except KeyboardInterrupt:   # this line is there to handle CTRL-C
                break

        print("Server shutting down...")
        self.server_socket.close()      # this line returns the port that was previously bound back to the OS

    def process_request(self, msg):
        try:
            msg = msg.split("\r\n")
            print(msg)
            # This method should complete the following tasks
            # - determine if the message is a GET request
            line1 = msg[0].split(" ")
            if line1[0] != "GET" or not (line1[1] in self.resources):
                return "HTTP/1.1 404 Not Found\r\n\r\n"

            last_modified = datetime.strptime(self.resources[line1[1]]["last_modified"], "%a, %d %b %Y %H:%M:%S %Z")
            file_size = str(self.resources[line1[1]]["file_size"])
            etag = self.resources[line1[1]]["etag"]

            line2 = msg[2].split(" ")
            if line2[0] == "If-Modified-Since:":
                if datetime.strptime(msg[2], "If-Modified-Since: %a, %d %b %Y %H:%M:%S %Z") >= last_modified:
                    return 'HTTP/1.1 304 Not Modified\r\n\r\n'

            response = 'HTTP/1.1 200 OK\r\n Content-Length: ' + str(file_size) + '\r\n ETag: ' + etag + '\r\n \r\n'
            return response

        except Exception as e:
            print(e)
            return 'HTTP/1.1 400 Bad Request\r\n\r\n'

        #     - If not, you should treat it as a 400 Bad Request response.
        # - determine if the requested resource is valid
        #     - If yes, determine the file size, etag, and last modified time
        #     - Check if there is an "If-Modified-Since" header
        #         -If yes, compare the time in the header to the last modified time.
        #             - If the file is newer it should be treated as a 200 OK response
        #             - If the file is older it should be treated as a 304 Not Modified response
        #         -If no, it should be treated as a 200 OK response
        #     - IF the resource is not valid, it should be treated as a 404 Not Found response.

        # - build the response message (you can build additional helper methods if you desire)
        #     - A 200 OK response should include the response code, the file size, and the ETag. Here is an example 200 OK response:

        #         HTTP/1.1 200 OK\r\n
        #         Content-Length: 1234\r\n
        #         ETag: abc123\r\n
        #         \r\n

        # if ():

        #     - Here is an example 304 Not Modified response:

        #         HTTP/1.1 304 Not Modified\r\n
        #         \r\n

        #     - Here is an example 404 Not Found response:

        #         HTTP/1.1 404 Not Found\r\n
        #         \r\n
            
        #     - Finally, an example 400 Bad Request response:

        #         HTTP/1.1 400 Bad Request\r\n
        #         \r\n

                
        #     - Please note the additional \r\n following every response. Why is this there?
            
        # - return the response message back to start_server

    def stop_server(self, signum, frame):
        self.running = False



# the following lines allow your code to run on its own. They will NOT be called by the autograder
# so do not add any code below.
if __name__== "__main__":
    server = Server()
    signal.signal(signal.SIGINT, server.stop_server)    # this line of code captures your CTRL-C input to turn off the server
    server.start_server()
