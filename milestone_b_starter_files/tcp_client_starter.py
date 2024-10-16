import socket
import random
import time
from datetime import datetime
from datagram import Datagram

class Client:
    """
    A class that implements a TCP client using raw sockets.

    Attributes:
        client_ip (str): The IP address of the client.
        server_ip (str): The IP address of the server.
        server_port (int): The port number of the server.
        frame_size (int): The maximum size of each frame in bytes.
        window_size (int): The size of the TCP window for flow control (number of segments allowed).
        timeout (int): The timeout duration for socket operations in seconds.
        client_socket (socket.socket): The raw socket used for communication.
        base (int): The base sequence number for tracking sent messages.
        seq_num (int): The current sequence number for outgoing messages.
        ack_num (int): The current acknowledgment number for incoming messages.
    """

    def __init__(self, client_ip='127.0.0.2', server_ip='127.128.0.1', server_port=8080, frame_size=1024, window_size = 5, timeout=5):
        """
        Initializes the Client with specified parameters.

        Args:
            client_ip (str): IP address for the client.
            server_ip (str): IP address for the server.
            server_port (int): Port number for the server.
            frame_size (int): Maximum size of each frame in bytes.
            window_size (int): Size of the TCP window in number of segments.
            timeout (int): Timeout duration for socket operations in seconds.
        """

        # Establish the raw socket
        self.client_ip = client_ip
        self.client_port = random.randint(1024, 65535)  # Arbitrary client port for example purposes
        self.server_ip = server_ip
        self.server_port = server_port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.client_socket.bind((self.client_ip, 0))
        
        # Manage the settings to control transport layer services
        self.frame_size = frame_size
        self.window_size = window_size

        self.timeout = timeout
        self.client_socket.settimeout(timeout)
        
        self.base = 0
        self.seq_num = 0
        self.ack_num = 0

        ### ADD ANY ADDITIONAL ATTRIBUTES YOU REQUIRE HERE
        
    def initiate_handshake(self):
        """
        Initiates a TCP connection via a 3-way handshake.

        Returns:
            bool: True if the handshake was successful, False otherwise.
        """
        ### Establish a connection with the server via 3-way handshake
        ## 1. Send SYN 
        try:
            request = f"SYN\r\n\r\n"
            print(f"Sending request: {request}")
            new_datagram = Datagram(source_ip=self.client_ip, dest_ip=self.server_ip, source_port = self.client_port, dest_port = self.server_port, seq_num = self.seq_num, ack_num = self.ack_num, flags=24, window_size = 10, data=request)
            new_datagram_bytes = new_datagram.to_bytes()
            self.client_socket.sendto(new_datagram_bytes, (self.server_ip, self.server_port))
        except:
            return False
        ## 2. Recieve SYN/ACK
        ack = None
        try:
            ack = Datagram.from_bytes(self.client_socket.recv(self.frame_size))
            # ack = self.client_socket.recv(self.frame_size)
            if "SYNA" not in ack.data:#temp fix
                print((ack.data))
                return False
        except Exception as e:
            print(e)
            return False
        ## 3. Send ACK
        try:
            request = f"ACK\r\n\r\n"
            print(f"Sending request: {request}")
            new_datagram = Datagram(source_ip=self.client_ip, dest_ip=self.server_ip, source_port = self.client_port, dest_port = self.server_port, seq_num = self.seq_num, ack_num = self.ack_num, flags=24, window_size = 10, data=request)
            new_datagram_bytes = new_datagram.to_bytes()
            self.client_socket.sendto(new_datagram_bytes, (self.server_ip, self.server_port))
        except:
            return False
        return True

    def build_request(self, resource, timestamp=None):
        """
        Builds an HTTP GET request for the specified resource.
        DO NOT MODIFY THIS METHOD.

        Args:
            resource (str): The resource to request.
            timestamp (str): Optional timestamp for conditional requests.

        Returns:
            str: The constructed HTTP GET request.
        """
        request = f"GET {resource} HTTP/1.1\r\nHost: {self.server_ip}\r\n"
        if timestamp:
            request += f"If-Modified-Since: {timestamp}\r\n"
        request += "\r\n"

        return request

    def send_request_segments(self, request):
        """
        Sends the request segments using the Go-Back-N protocol.

        Args:
            request (str): The HTTP request to send.
        """
        
        ### Segment the request (segments no larger than frame_size)
        res = []
        split = len(request) // self.frame_size
        if len(request) % self.frame_size > 0:
            split += 1
        for d in range(split):
            res.append(request[(self.frame_size*d):(self.frame_size*(d+1))])

        ### Send the request segments using Go-Back-N (use Datagram class to encapsulate the segments)
        ## Start by sending all datagrams in the window          
        for message in res:
            for seq_num in range(self.window_size):
                print(f"Sending message: {message}")
                new_datagram = Datagram(source_ip=self.client_ip, dest_ip=self.server_ip, source_port = self.client_port, dest_port = self.server_port, seq_num = self.seq_num, ack_num = self.ack_num, flags=24, window_size = 10, data=message)
                new_datagram_bytes = new_datagram.to_bytes()
                sent_bytes = self.client_socket.sendto(new_datagram_bytes, (self.server_ip, self.server_port))
                self.seq_num += 1
                print(f"Sent {sent_bytes} bytes...\n")
                if sent_bytes == 0:
                    print("Houston we have an error! Aborting...")
                    break
                # listen for responses
                ack = None
                try:
                    ack = self.client_socket.recv(self.frame_size).decode()
                
                except socket.timeout:
                    print("Timed out!\n")
                    """
                    This is probably a great place to do something to determine
                    if you should retransmit or not. There are multiple
                    solutions to this, but the easiest is just to go back 
                    to the top of your loop (nest it in a while loop that you break
                    when you get an 'ACK'). Good luck!
                    """

                except Exception as e:
                    print(e)
                # this print statement confirms we can send and receive
                print(ack)
            self.base += self.window_size
        ## process the acknowledgements
        # If ack is good: increment base and transmit another packet
        # If ack is duplicate: ignore ack
        # If timeout: adjust seq_num; retransmit segments in window from base

        pass

    def process_response_segments(self):
        """
        Processes incoming response segments from the server.

        Returns:
            str: The complete response from the server.
        """
        ### Implement the Go-Back-N receiver functions and reassemble the response message from the received segments.
        ## Receive segments until end of message (use Datagram class to access header values)
        # If the seg_num of each segment matches the previous ack_num, send an acknowledgement.
        # Otherwise, send a duplicate acknowledgement.
        ### Return the full response

        pass

    def close_socket(self):
        """
        Closes the client socket.
        DO NOT MODIFY THIS METHOD.
        """
        self.client_socket.close()

    def request_resource(self, resource, timestamp=None):
        """
        Control method that uses the others to request a resource 
        from the server and return the response. DO NOT MODIFY THIS METHOD.

        Args:
            resource (str): The resource to request.
            timestamp (str): Optional timestamp for conditional requests.

        Returns:
            str: The server's response.
        """
        response = ''
        # Establish a connection
        connected = self.initiate_handshake()
        if connected:
            # Build the request segments
            request = self.build_request(resource, timestamp)
            # Send the request seqments
            self.send_request_segments(request)
            # Process the response segments
            response = self.process_response_segments()
        # Close the socket
        self.close_socket()
        # Return the response
        return response

### Note: this is for your testing / debugging purposes and will not be used by the Autograder.
if __name__ == "__main__":
    client = Client(frame_size=64)
    
    # Get user input for custom resource and timestamp.
    resource = input("Enter the resource to request (default: /index.html): ").strip() or "/index.html"
    if_modified_since = input("Enter the If-Modified-Since timestamp (optional, format: Wed, 21 Oct 2020 07:28:00 GMT): ").strip()

    response = client.request_resource(resource, if_modified_since)

