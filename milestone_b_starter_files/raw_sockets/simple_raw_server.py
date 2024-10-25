import time
import socket
from datagram import Datagram

class Server:
    def __init__(self, server_ip='127.128.0.1', server_port=8080, timeout=5):

        self.server_ip = server_ip
        self.server_port = server_port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.server_socket.bind((self.server_ip, 0))

        self.timeout = timeout

        # Keep track of sequence numbers and ack numbers
        self.seq_num = 0
        self.ack_num = 0

    def process_request(self):
        print("Server started, waiting for request...")
        # receive the request 
        # Note that this method is blocking when timeout is not set (i.e. code execution stops until a frame is received.)
        request_bytes = self.server_socket.recv(1024)
        print("Request received... converting from binary...")
        # convert and display the request
        request = Datagram.from_bytes(request_bytes)
        print(request)
        print(f"Source IP: {request.ip_saddr}")           
        print(f"Source Port: {request.source_port}")
        print(f"Dest IP: {request.ip_daddr}")
        print(f"Dest Port: {request.dest_port}")
        print(f"Request Data: {request.data}")

        # simulate send an acknowledgement for the request
        print("Acknowledgement number incremented.")
        self.ack_num += 1

        # Simulate delay (uncomment to show client timeout)
        # time.sleep(2)

        # send a 404 response
        print()
        print()
        response = "HTTP/1.1 404 Not Found\r\n\r\nResource Not Found"
        print(f"Response: {response}")
        print("Converting response to binary...")
        response_datagram = Datagram(source_ip=self.server_ip, dest_ip=request.ip_saddr, source_port=self.server_port, dest_port=request.source_port, seq_num=self.seq_num, ack_num=self.ack_num, flags=24, window_size=10, data=response)
        response_datagram_bytes = response_datagram.to_bytes()
        self.server_socket.sendto(response_datagram_bytes, (request.ip_saddr, request.source_port))
        self.seq_num += 1
        print("Response sent. Sequence number incremented.")


if __name__ == "__main__":
    server = Server()
    server.process_request()


