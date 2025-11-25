#
# Mini Reliable Transport (MRT) - Example Application Server
#
# Simple example server application that uses the MRT server APIs.
# It listens for incoming MRT connections, accepts a single client, receives
# a fixed amount of data, and compares the received payload with a source file
# to verify correctness of the protocol implementation.
#
# Developed as part of a computer networks project at Columbia University as testing purpose
#

import sys
from mrt_server import Server

# parse input arguments
# <server_port> <buffer_size>
# example: 60000 4096
if __name__ == '__main__':
    listen_port = int(sys.argv[1]) # port to listen for incoming connections
    buffer_size = int(sys.argv[2]) # buffer size for receiving segments

    # listening for incoming connection
    server = Server()
    server.init(listen_port, buffer_size)

    # accept a connection from a client
    client = server.accept()
    print(f">> client accept: {client}")

    # [testing]
    #server.close()

    # receive 8000 bytes data from client
    received = server.receive(client, 4000)
    received1 = server.receive(client, 4000)
    received = received + received1
    
    # read the first 8000 bytes of the original file
    with open("data.txt", "rb") as f:
        input = f.read(8000)
        
    # [testing]
    '''
    with open("data.txt", "rb") as f:
        input = f.read(4000)
    input = input + input
    '''

    # compare the received file with the original file
    if input != received:
        print(f">> received {len(received)} bytes but not the same as input file")
    else:
        print(f">> received {len(received)} bytes successfully")
    
    # close the server and other un-closed clients
    server.close()
