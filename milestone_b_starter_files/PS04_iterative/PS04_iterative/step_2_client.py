import socket

class StopAndWaitSender:
    # init
    def __init__(self, host='localhost', port=12345, frame_size=256,
                 messages=[], sender_socket = None) :
        # host: Address of the receiver (default = 'localhost)
        # port: Port number to connect to (default = 12345)
        # frame_size: Maximum size of each segment (default = 256)
        # messages: List of messages to send to the receiver (default = [])
        # sender_socket: Socket for the connection to the receiver (default = None)
        self.host = host
        self.port = port
        self.frame_size = frame_size
        self.messages = messages
        self.sender_socket = sender_socket

    #########################################################################################
    # Step 2: send a message (verified by printing out message on other end)                #
    # Client includes print debugging status updates so we know what is going on throughout #
    #########################################################################################

    # connect method
        # Create a socket connection to the receiver
        # Handle connection setup with proper error handling
    def connect(self):
        self.sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Establishing connection with server at {self.host}:{self.port}")
        self.sender_socket.connect((self.host, self.port))

    # segment_message method (note: should have optional msg option, not specified in instructions. SORRY!!)
        # divides a large message into smaller segments that fit within the frame size
        # ensure each segment is properly sequenced

    # send_data
        # Send each segment of a message and wait for an acknowldgement: string 'ACK'.
        # implement timeouts (after 1 second) and retransmission for reliability
    def send_data(self):
        # iterate through each message
        for message in self.messages:
            # come  back and add logic to break up the message once we figure out segment message
            packets = [message]         # place holder so we can build the inner logic without figuring out segmenting yet
            for message in packets:
                print(f"Sending message: {message}")
                sent_bytes = self.sender_socket.send(message.encode()) # the send method returns an int of bytes sent (0 is an issue)
                print(f"Sent {sent_bytes} bytes...\n")
                if sent_bytes == 0:
                    print("Houston we have an error! Aborting...")
                    break
        print("All messages sent successfully if we reached this point.\n\n")

    # close
        # properly close the socket connection after all messages have been sent
    def close(self):
        self.sender_socket.close()



if __name__ == '__main__':
    messages = ["Hello",
                "World",
                "This is a longer message to test how the sender handles larger data frames.",
                "Short",
                "A",
                "I should make a plan before I start building any code for this course and then I should iteratively implement it while testing at every step of the way to make sure that everything is behaving the way I want. Simpler is always preferable to complex when doing initial designs."
                ]
    sender = StopAndWaitSender(messages=messages)
    sender.connect()
    sender.send_data()
    sender.close()