from socket import *
from datagram import Datagram
import random

class RClient:
    def __init__(self, client_ip='127.0.0.2', server_ip='127.42.0.1', server_port = 8080, timeout=1):
        self.client_ip = client_ip
        self.server_ip = server_ip
        self.server_port = server_port
        self.timeout = timeout

        self.client_socket = socket(AF_INET, SOCK_RAW, IPPROTO_TCP)
        
        self.client_socket.bind((self.client_ip, 0))
        self.client_socket.settimeout(self.timeout)
        self.client_port = random.randint(49152, 65535)
        self.seq_num = 0
        self.ack_num = 0

    def process_request(self):
        try:
            request = f"GET not_found.html HTTP/1.1\r\nHost: {self.server_ip}\r\n\r\n"
            print(f"Sending request: {request}")
            new_datagram = Datagram(source_ip=self.client_ip, dest_ip=self.server_ip, source_port = self.client_port, dest_port = self.server_port, seq_num = self.seq_num, ack_num = self.ack_num, flags=24, window_size = 10, data=request)
            new_datagram_bytes = new_datagram.to_bytes()
            self.client_socket.sendto(new_datagram_bytes, (self.server_ip, self.server_port))
            self.seq_num += 1
        except Exception as e:
            print(e)