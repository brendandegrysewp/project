############################################################################
# Step 0: Make a plan for the client                                       #
############################################################################

# make class StopAndWaitSender
    
    # init
        # host: Address of the receiver (default = 'localhost)
        # port: Port number to connect to (default = 12345)
        # frame_size: Maximum size of each segment (default = 256)
        # messages: List of messages to send to the receiver (default = [])
        # sender_socket: Socket for the connection to the receiver (default = None)

    
    # connect method
        # Create a socket connection to the receiver
        # Handle connection setup with proper error handling

    # segment_message method (note: should have optional msg option, not specified in instructions. SORRY!!)
        # divides a large message into smaller segments that fit within the frame size
        # ensure each segment is properly sequenced

    # send_data
        # Send each segment of a message and wait for an acknowldgement: string 'ACK'.
        # implement timeouts (after 1 second) and retransmission for reliability

    # close
        # properly close the socket connection after all messages have been sent



# make a main statement for testing