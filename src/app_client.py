#
# Mini Reliable Transport (MRT) - Example Application Client
#
# Simple example client application that uses the MRT client APIs.
# It parses command-line arguments, establishes a connection to the server,
# sends the contents of a local file, and then cleanly closes the connection.
#
# Developed as part of a computer networks project at Columbia University as testing purpose
#

import sys
from mrt_client import Client

# parse input arguments
# <client_port> <network_addr> <network_port> <segment_size>
# example: 50000 127.0.0.1 51000 1460
if __name__ == '__main__':

    client_port = int(sys.argv[1]) # the port the client is using to send segments
    server_addr = sys.argv[2] # the address of the server/network simulator
    server_port = int(sys.argv[3]) # the port of the server/network simulator
    segment_size = int(sys.argv[4]) # the maximum size of a segment (including the header)

    # initialize and connect to the server
    client = Client()
    client.init(client_port, server_addr, server_port, segment_size)
    client.connect()

    #client.close() [testing]
    
    # open a file and send it to the server
    with open("data.txt", "rb") as f:
        data = f.read(8000)
    sent = client.send(data)
    print(f">> sent {sent} bytes of data")

    # close the connection
    client.close()
