import threading
import time
import signal
import sys
from client_udp import Client
from server_udp import Server

server = None

def run_server():
    global server
    server = Server()
    server.start_server()

def run_client(resource, if_modified_since):
    client = Client()
    response = client.request_resource(resource, if_modified_since)
    if response:
        print(f"Response received: {response}")
    else:
        print("There was an error with transmitting/receiving the message.")

def signal_handler(sig, frame):
    global server
    print("\nStopping server...")
    if server:
        server.stop_server(sig, frame)
    sys.exit(0)

if __name__ == "__main__":
    # Handle SIGINT (CTRL-C) to shutdown the server gracefully
    signal.signal(signal.SIGINT, signal_handler)

    # Start the server thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    # Give the server some time to start
    time.sleep(1)

    try:
        # keep requesting user input until CTRL-C is issued
        while True:
            # Get user input for custom resource and timestamp
            resource = input("Enter the resource to request (default: /index.html): ").strip() or "/index.html"
            if_modified_since = input("Enter the If-Modified-Since timestamp (optional, format: Wed, 21 Oct 2020 07:28:00 GMT): ").strip() or None

            # Start the client thread
            client_thread = threading.Thread(target=run_client, args=(resource, if_modified_since))
            client_thread.start()

            # Wait for the client thread to finish
            client_thread.join()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
