############################################################################
# Step 0: Make a plan for the server                                       #
############################################################################

# Make class for StopAndWaitServer
    # init method

        # host: Address of the receiver (default = 'localhost)
        # port: Port number to connect to (default = 12345)
        # frame_size: Maximum size of each segment (default = 256)
        # messages: List of messages to send to the receiver (default = [])
        # server_socket: Socket for the connection to the receiver (default = None) 


    # make a start method
        # create socket

        # bind socket

        # set timeout 

        # listen for connections

        # loop forever
            # accept connections

            # print out status

            # receive messages

            # print out received messages

            # respond with 'ACK'

            # optionally make it so server doesn't respond to test timeout

    # close everything

# make a main statement for testing