import socket
from datetime import datetime

class Client:
    # The __init__ method will be called automatically when you initialize
    # a new instance of the Client class. This is a good spot to define any
    # attributes that would be helpful to access in all methods.
    def __init__(self, server_host='localhost', server_port=8080):
        # The following line of code creates a socket object for you to use.
        # AF_INET is the attribute that says this is an Internet type socket, SOCK_DGRAM says this is a UDP socket.
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
        self.server_host = server_host
        self.server_port = server_port
        # this specifies we will read 1024 bytes at a time. You will need it to listen for the server's response.
        self.recv_size = 1024

        ### ADD ANY ADDITIONAL ATTRIBUTES YOU THINK YOU NEED BELOW HERE ###

    # This method has been provided to you to create a properly formatted GET request
    def build_request(self, resource, timestamp=None):
        request = f"GET {resource} HTTP/1.1\r\nHost: localhost\r\n"
        if timestamp:
            request += f"If-Modified-Since: {if_modified_since}\r\n"
        request += "\r\n"

        return request

    def send_request(self, request):

        """
        You need to do the following things in this method (or with helper methods)
        - encode the request
        - use the socket object from the __init__ to send the request to the correct address (also specified in __init__)
        Your solution should be resilient to errors. In other words you should use a try / except block to avoid your code failing from an exception.
        """
        ### YOUR CODE GOES HERE ###
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            self.client_socket.send(request.encode())
        except:
            print("Operation failed")
        pass

    def process_response(self):#, ):
        """
        This method should listen for any response from the server after you send a request.
        It should do the following
        - receive any incoming response from the socket object
        - return the decoded response
        """
        response = self.client_socket.recv(self.recv_size)
        return response.decode()
    
    def close_socket(self):
        """
        This method simply needs to close the existing socket object. (1 line of code is all you need)
        """
        ### YOUR CODE GOES HERE ###
        self.client_socket.close()
        #pass

    # control method that calls all of the others
    def request_resource(self, resource, timestamp=None):

        
        #This method is what the Web-app (and Autograder) will call to send a message.
        #It should do the following by calling the appropriate methods defined above
        #- build the request
        request = self.build_request(resource, timestamp)
        #- send the request
        self.send_request(request)
        #- process the request response
        response = self.process_response()
        #- close the socket
        self.close_socket()
        #- return the response 
        return response
        pass

if __name__ == "__main__":
    client = Client()
    
    # Get user input for custom resource and timestamp. Note, this is for your testing / debugging purposes and will not be used by the Autograder.
    resource = input("Enter the resource to request (default: /index.html): ").strip() or "/index.html"
    if_modified_since = input("Enter the If-Modified-Since timestamp (optional, format: Wed, 21 Oct 2020 07:28:00 GMT): ").strip()

    response = client.request_resource(resource, if_modified_since)
    if response:
        print(f"Response received: {response}")
    else:
        print("There was an error with transmitting / receiving the message.")
