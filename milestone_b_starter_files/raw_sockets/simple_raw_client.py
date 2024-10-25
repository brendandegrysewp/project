import socket
import random
from datagram import Datagram

class Client:
    def __init__(self, client_ip='127.0.0.7', server_ip='127.128.0.1',
                 server_port = 8080, timeout=1):
        self.client_ip = client_ip
        self.client_port = random.randint(49152, 65535)

        self.server_ip = server_ip
        self.server_port = server_port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                           socket.IPPROTO_TCP)
        self.client_socket.bind((self.client_ip, 0))

        self.client_socket.settimeout(timeout)

        self.seq_num = 0
        self.ack_num = 0

    def process_request(self):
        request = f"GET not_found.html HTTP/1.1\r\nHost: {self.server_ip}\r\n\r\n"
        print(f"Sending request: {request}")
        # use the Datagram class to format the datagram        
        new_datagram = Datagram(source_ip=self.client_ip, dest_ip=self.server_ip,
                                source_port=self.client_port, dest_port=self.server_port,
                                seq_num=self.seq_num, ack_num=self.ack_num, 
                                flags=24, window_size=10, data=request)
        
        new_datagram_bytes = new_datagram.to_bytes()
        self.client_socket.sendto(new_datagram_bytes, (self.server_ip, self.server_port))
        self.seq_num += 1

        # receive the response
        try:
            response_bytes = self.client_socket.recv(1024)
            # make the bytes readable
            response = Datagram.from_bytes(response_bytes)
            # display the response
            print("Response received - ")
            print(response)
            print(f"Source IP: {response.ip_saddr}")           
            print(f"Source Port: {response.source_port}")
            print(f"Dest IP: {response.ip_daddr}")
            print(f"Dest Port: {response.dest_port}")
            print(f"Response Data: {response.data}")
            # simulate sending an ACK for the response
            self.ack_num += 1

        except socket.timeout:
            # Define what to do if a timeout occurs
            print('Timout occurred prior to receiving the response.')


if __name__ == "__main__":
    client = Client()
    client.process_request()
