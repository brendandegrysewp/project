import socket
import json
from pathlib import Path
from datetime import datetime
from datagram import Datagram

class Server:
    """
    A class that implements a TCP server using raw sockets.

    Attributes:
        server_ip (str): The IP address of the server.
        server_port (int): The port number of the server.
        server_socket (socket.socket): The raw socket used for communication.
        frame_size (int): The maximum size of each frame.
        resources (dict): A dictionary storing resources available to the server.
        window_size (int): The size of the TCP window for flow control (number of segments).
        timeout (int): The timeout duration for socket operations in seconds.
        base (int): The base sequence number for tracking sent messages.
        seq_num (int): The current sequence number for outgoing messages.
        ack_num (int): The current acknowledgment number for incoming messages.
    """

    def __init__(self, server_ip='127.128.0.1', server_port=8080, frame_size=1024, window_size=4, timeout=5):

        # Establish the raw socket
        self.server_ip = server_ip
        self.server_port = server_port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.server_socket.bind((self.server_ip, 0))

        # Read and store the resources available to the server
        base_path = Path(__file__).parent
        resources_path = base_path / 'resources.json'
        with open(resources_path, 'r') as f:
            self.resources = json.load(f)

        # Manage the settings to control transport layer services
        self.frame_size = frame_size
        self.window_size = window_size
        self.timeout = timeout
        self.base = 0
        self.seq_num = 0
        self.ack_num = 0

        ### ADD ANY ADDITIONAL ATTRIBUTES YOU REQUIRE HERE

    def accept_handshake(self):
        """
        Accepts a TCP connection via a 3-way handshake.

        Returns:
            bool: True if the handshake was successful, False otherwise.
        """
        ### Process a request for connection with the server via 3-way handshake
        ## 1. Receive SYN
        SYN = None
        try:
            SYN = Datagram.from_bytes(self.server_socket.recv(self.frame_size))
            if "SYN" not in SYN.data :
                print("Didn't receive SYN")
                print(SYN)
                return False
        except Exception as e:
            print(e)
            return False
        ## 2. Send SYN/ACK       
        try:
            request = f"SYNACK\r\n\r\n"
            print(f"Sending request: {request}")
            new_datagram = Datagram(source_ip=self.server_ip, dest_ip=SYN.ip_saddr, source_port = self.server_port, dest_port = SYN.source_port, seq_num = self.seq_num, ack_num = self.ack_num, flags=24, window_size = 10, data=request)
            new_datagram_bytes = new_datagram.to_bytes()
            self.server_socket.sendto(new_datagram_bytes, (SYN.ip_saddr, SYN.source_port))
        except Exception as e:
            print(e)
            return False
        ## 3. Receive ACK
        ack = None
        try:
            ack = Datagram.from_bytes(self.server_socket.recv(self.frame_size))
            if "ACK" not in ack.data:
                return False
        except Exception as e:
            print(e)
            return False
        return True

    def receive_request_segments(self):
        """
        Receives request segments from the client.

        Returns:
            tuple: A tuple containing the request string, source port, and source IP.
        """

        ### Implement the Go-Back-N receiver functions and reassemble the request message from the received segments.
        ## Receive segments until end of message (use Datagram class to access header values)
        ## If the seg_num of each segment matches the previous ack_num, send an acknowledgement.
        ## Otherwise, send a duplicate acknowledgement.
        ### Return the full request, source port, and source IP.

        pass


    def process_request(self, request, dest_port, dest_ip):
        """
        Processes the received request and sends an appropriate response.

        Args:
            request (str): The HTTP request to process.
            dest_port (int): The destination port for the response.
            dest_ip (str): The destination IP for the response.
        """

        request_lines = request.split('\r\n')
        first_line = request_lines[0].split()
        method = first_line[0]
        resource = first_line[1]
        modified_since = None

        # Determine the response message based on the HTTP Request.

        if method != "GET":
            # Invalid response
            data = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid Request"
            flags = 17
        elif resource not in self.resources:
            # Not found response
            data = "HTTP/1.1 404 Not Found\r\n\r\nResource Not Found"
            flags = 17
        else:
            # Check for If-Modified-Since header line
            for line in request_lines[1:]:
                if line.startswith("If-Modified-Since:"):
                    modified_since = line.split(":", 1)[1].strip()
                    break
            resource_info = self.resources[resource]

            # If header line exists, compare dates to determine response type
            if modified_since:
                modified_since_time = datetime.strptime(modified_since, "%a, %d %b %Y %H:%M:%S GMT")
                last_modified_time = datetime.strptime(resource_info['last_modified'], "%a, %d %b %Y %H:%M:%S GMT")
                if last_modified_time <= modified_since_time:
                    data = "HTTP/1.1 304 Not Modified\r\n\r\n"
                    flags = 17
            else:
                data = resource_info['data'].encode()
                data = f"HTTP/1.1 200 OK\r\nContent-Length: {len(data)}\r\n\r\n" + data.decode()
                flags = 24

        ### Segment the response (segments no larger than frame_size)

        ### Send the response segments using Go-Back-N (use Datagram class to encapsulate the segments)
        ## Start by sending all datagrams in the window          
        ## process the acknowledgements
        # If ack is good: increment base and transmit another packet
        # If ack is duplicate: ignore ack
        # If timeout: adjust seq_num; retransmit segments in window from base

    def reset_connection(self):
        """
        Resets the connection parameters for the server.
        """
        ### Re-initialize the appropriate settings to control transport layer services
        pass

    def close_server(self):
        """
        Closes the server socket.
        DO NOT MODIFY THIS METHOD.
        """
        self.server_socket.close()

    def run_server(self, request_list=None):
        """
        Runs the server to accept and process incoming requests.
        DO NOT MODIFY THIS METHOD.

        Args:
            request_list (list): Optional list to store requests received.
        """
        connected = self.accept_handshake()
        if connected:
            request, port, ip = self.receive_request_segments()
            if request_list is not None:
                request_list.append(request)
            self.process_request(request, port, ip)
        self.reset_connection()

if __name__ == "__main__":
     server = Server(frame_size=64)
     server.run_server()
