import socket
import cryptography
import random
import time
import threading
from datetime import datetime

import cryptography.fernet
import cryptography.hazmat
import cryptography.hazmat.primitives
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.primitives.kdf
import cryptography.hazmat.primitives.kdf.pbkdf2
from pdu import HTTPDatagram, IPHeader
import webbrowser
from pathlib import Path
import os
import os.path as path
import subprocess
import base64

class Client:
    """
    Represents an HTTP client that communicates with a server using a custom protocol via raw sockets.
    
    Attributes:
        client_ip (str): The client's IP address.
        server_ip (str): The server's IP address.
        gateway (str): The gateway address for the client.
        client_port (int): The client's source port, randomly chosen during initialization.
        server_port (int): The server's destination port.
        frame_size (int): Maximum frame size for transmitting data.
        window_size (int): Window size for Go-Back-N protocol.
        timeout (int): Socket timeout for receiving data.
        base (int): Base sequence number for the Go-Back-N protocol.
        seq_num (int): Current sequence number.
        ack_num (int): Current acknowledgment number.
    """

    def __init__(self, client_ip='127.0.0.1', server_ip='127.128.0.1', gateway='127.0.0.254', server_port=8080, frame_size=800, window_size=4, timeout=5):
        """
        Initializes the client with given IP addresses, ports, and network settings.

        Args:
            client_ip (str): Client's IP address.
            server_ip (str): Server's IP address.
            gateway (str): Client's gateway.
            server_port (int): Server's port (default: 8080).
            frame_size (int): Maximum frame size (default: 1024 bytes).
            window_size (int): Window size for Go-Back-N protocol (default: 5).
            timeout (int): Socket timeout (default: 11 seconds).
        """
        self.client_ip = client_ip
        self.client_port = random.randint(1024, 65535)  # Random client port
        self.server_ip = server_ip
        self.server_port = server_port
        self.gateway = gateway

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.client_socket.bind((self.client_ip, 0))
        self.client_socket.settimeout(timeout)

        self.frame_size = frame_size
        self.window_size = window_size
        self.timeout = timeout

        self.base = 0
        self.seq_num = 0
        self.ack_num = 0
        key = open("key.txt","rb").read()
        # print(key)
        self.key = cryptography.fernet.Fernet(key)
        # print(self.key.encrypt(b"bad"))
        # exit(1)

    def initiate_handshake(self):
        """
        Initiates a three-way handshake with the server to establish a connection.
        
        Returns:
            bool: True if the handshake is successful, False otherwise.
        """
        # Step 1: Send SYN
        syn_datagram = HTTPDatagram(
            source_ip=self.client_ip, dest_ip=self.server_ip,
            source_port=self.client_port, dest_port=self.server_port,
            seq_num=self.seq_num, ack_num=self.ack_num,
            flags=2, window_size=self.window_size, next_hop=self.gateway, data='SYN'
        )
        self.client_socket.sendto(syn_datagram.to_bytes(), (self.gateway, 0))
        self.seq_num += 1

        # Step 2: Receive SYN/ACK
        syn_ack = False
        while not syn_ack:
            try:
                frame = self.client_socket.recv(self.frame_size)
            except socket.timeout:
                return False

            datagram_fields = HTTPDatagram.from_bytes(frame)
            if datagram_fields.flags == 18 and datagram_fields.next_hop == self.client_ip:
                syn_ack = True
                self.ack_num = datagram_fields.seq_num + 1
                self.window_size = min(self.window_size, datagram_fields.window_size)
                
                # Step 3: Send ACK
                ack_datagram = HTTPDatagram(
                    source_ip=self.client_ip, dest_ip=self.server_ip,
                    source_port=self.client_port, dest_port=self.server_port,
                    seq_num=self.seq_num, ack_num=self.ack_num,
                    flags=16, window_size=self.window_size, next_hop=self.gateway, data='ACK'
                )
                self.client_socket.sendto(ack_datagram.to_bytes(), (self.gateway, 0))
                return True
        return False

    #Add option for post
    def build_request(self, resource, type="GET", data=None, timestamp=None):
        """
        Builds an HTTP GET request string.

        Args:
            resource (str): The requested resource.
            timestamp (str, optional): If-Modified-Since timestamp.

        Returns:
            str: The HTTP request as a string.
        """
        if type == "GET":
            request = f"GET {resource} HTTP/1.1\r\nHost: {self.server_ip}\r\n"
            if timestamp:
                request += f"If-Modified-Since: {timestamp}\r\n"
            request += "\r\n"
            return request

        elif type == "POST":#Check the type of the request we are sending
            request = f"POST {resource} HTTP/1.1\r\nHost: {self.server_ip}\r\nContent-Length: {len(data)}\r\n{data}\r\n"#build the request string
            request += "\r\n"
            return request#return it

    def send_request_segments(self, request):
        """
        Segments and sends the HTTP request using Go-Back-N protocol.

        Args:
            request (str): The full HTTP request string.
        """
        request_bytes = request.encode()
        max_data_length = self.frame_size - 60  # Assuming 60 bytes for headers
        segments = [request_bytes[i:i + max_data_length] for i in range(0, len(request_bytes), max_data_length)]

        flags = 24  # Set ACK and PSH bits for request
        init_seq_num = self.seq_num

        # Sending segments using Go-Back-N protocol
        while self.base < len(segments):
            for segment in segments[self.base:min(len(segments), self.base + self.window_size)]:
                segment = self.key.encrypt(segment)
                # print(str(segment))
                if self.seq_num - init_seq_num == len(segments) - 1:
                    flags = 25  # Set the FIN flag on the last segment
                new_datagram = HTTPDatagram(
                    source_ip=self.client_ip, dest_ip=self.server_ip,
                    source_port=self.client_port, dest_port=self.server_port,
                    seq_num=self.seq_num, ack_num=self.ack_num,
                    flags=flags, window_size=self.window_size, next_hop=self.gateway, data=segment.decode()
                )
                self.client_socket.sendto(new_datagram.to_bytes(), (self.gateway, 0))
                self.seq_num += 1

            # Processing acknowledgments
            startTime = time.time()
            ###Check for timeout
            while time.time()-startTime < 15:# and self.base < self.seq_num:#self.base < len(segments) and :
                try:
                    frame = self.client_socket.recv(self.frame_size)
                except socket.timeout:
                    #Remove this so that sequence number remains as the last one acknowledged
                    self.seq_num = self.base + init_seq_num  # Retransmit on timeout
                    break

                datagram_fields = HTTPDatagram.from_bytes(frame)
                # Confirm frame is meant for this application and is an ACK for the oldest sent packet
                if (datagram_fields.next_hop == self.client_ip) and (datagram_fields.ip_saddr == self.server_ip) and (datagram_fields.flags == 16):# and (datagram_fields.ack_num == self.base + init_seq_num + 1):
                    # send another segment (base + window_size) if necessary
                    if self.base + self.window_size < len(segments):
                        segment = segments[self.base + self.window_size]
                        segment = self.key.encrypt(segment)
                        if self.base == min(len(segments), self.base + self.window_size) - 1:
                            flags = 25
                        new_datagram = HTTPDatagram(source_ip=self.client_ip, dest_ip=self.server_ip, source_port=self.client_port, dest_port=self.server_port, seq_num=self.seq_num, ack_num=self.ack_num, flags=flags, window_size=self.window_size, next_hop=self.gateway, data=segment.decode())
                        datagram_bytes = new_datagram.to_bytes()
                        self.client_socket.sendto(datagram_bytes, (self.gateway, 0))
                        self.seq_num += 1
                    # increment base
                    #The ack acknowledges all packets it received using the ack number, so the one it returns is the last one it received
                    self.base = datagram_fields.ack_num  
                    break

    def process_response_segments(self):
        """
        Receives and reassembles the response segments from the server.

        Returns:
            str: The full response as a string.
        """
        received = 0
        response = ''
        flags = 24
        tricked = False
        firstsig = False

        print(self.ack_num)
        while flags not in [25, 17]:#Check for finish flags
            start_time = time.time()#start timing each window
            while time.time() - start_time < 15 and flags not in [25, 17] and received < self.window_size:  # Stop if FIN or RST flags, or received enough packets
                # print(received)
                try:
                    frame = self.client_socket.recv(self.frame_size)
                    frame_bytes = IPHeader.from_bytes(frame)
                    if frame_bytes.ip_daddr == self.client_ip:
                        datagram_fields = HTTPDatagram.from_bytes(frame)
                        if datagram_fields.next_hop == self.client_ip and datagram_fields.flags in [17, 24, 25]:
                            # print(datagram_fields.seq_num, self.ack_num)
                            if datagram_fields.seq_num == self.ack_num:
                                # print("check")
                                self.ack_num += 1
                                # print(datagram_fields.seq_num)
                                # if datagram_fields.data[:6] == 'gAAAAA' and not firstsig:
                                #     firstsig = True
                                # elif datagram_fields.data[:6] == 'gAAAAA':
                                #     continue
                                received += 1
                                print(datagram_fields.data)
                                print()
                                res = self.key.decrypt(datagram_fields.data).decode()
                                # print(res)
                                response += res
                                flags = datagram_fields.flags
                                # print(flags)

                # except Exception as e:
                except FloatingPointError as e:
                    print(f'Error while receiving response: {e}')
                    continue
            #Moved sending the ack to the outside of this loop so it only does it after a certain period of time
            # Send ACK
            ack = HTTPDatagram(
                source_ip=self.client_ip, dest_ip=datagram_fields.ip_saddr,
                source_port=self.client_port, dest_port=datagram_fields.source_port,
                seq_num=self.seq_num, ack_num=self.ack_num,
                flags=16, window_size=self.window_size, next_hop=self.gateway, data='ACK'
            )
            if not tricked and ack.ack_num > 5:#cause a retransmission
                # ack.ack_num -= 1
                tricked = True
            self.client_socket.sendto(ack.to_bytes(), (self.gateway, 0))
            print(self.ack_num)
            #Reset received count
            received = 0
        # print(response.encode())
        return response

    def close_socket(self):
        """
        Closes the client's socket.
        """
        self.client_socket.close()

    def request_resource(self, resource, timestamp=None, method="GET", data=""):
        """
        Orchestrates the resource request process: handshake, request sending, and response processing.

        Args:
            resource (str): The requested resource.
            timestamp (str, optional): If-Modified-Since timestamp.

        Returns:
            str: The server's response.
        """
        connection = self.initiate_handshake()
        if connection:
            request = self.build_request(resource, method, data, timestamp)
            # request = self.build_request(resource, method, )
            self.send_request_segments(request)
            response = self.process_response_segments()

            #File location
            myPath = '/home/cadet/index.html'
            file = open(myPath,"w")
            #Save the response in the proper format
            file.write(response.replace("\\n","\n"))
            file.close()
            #Text based web browser (from webbrowser docs on python.org)
            broswer = webbrowser.get("lynx")
            #Open the browser in the terminal
            broswer.open_new("file://" + myPath)

            print(response)
        else:
            response = "Failed to connect to the server."
        self.close_socket()
        return response


if __name__ == "__main__":
    client = Client(frame_size=2048)
    
    # Get user input for custom resource and timestamp
    resource = input("Enter the resource to request (default: /index.html): ").strip() or "/index.html"
    if_modified_since = input("Enter the If-Modified-Since timestamp (optional, format: Wed, 21 Oct 2020 07:28:00 GMT): ").strip()

    # Make the request to the server
    response = client.request_resource(resource, if_modified_since)
    
    # Print the response from the server
    print(response)