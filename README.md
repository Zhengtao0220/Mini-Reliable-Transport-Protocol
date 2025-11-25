# CSEE 4119 Spring 2025, Assignment 2
## Zhengtao Hu
## UNI: zh2651


#Code Structure
##mrt_server.py and mrt_client.py:
- In the code, all global variables, multi-threads, and socket connections are initialized in the init() function.
- Both mrt_server and mrt_client will each establish a UDP socket connection, and the connections are constantly being maintained.
- The application layer functions: app_server.py and app_client.py will call the functions written in mrt_server.py and mrt_client.py.
- My implementation uses a finite state machine like if else statements structure in my threads.
- When messages are transferred and processed between server and client, the current state will be updated so that server and client will know
when to do handshakes, data transferring, and finishing the transfers.

mrt_server:
basic function is included in the previous section
- rcv_handler thread: it continuously receives UDP segments and puts them into a queue.
- rcv_buffer: the queue which receive the raw segments, updated in rcv_handler
- sgmnt_handler thread: it processes the queued segments.
- data_buffer: the bytearray which only accept in-order and valid segment, updated in data_buffer
- accept(): set server to handshake state, and accept a client request.
- receive(): set server to data transfer state, receving data from client.
- close(): send finish signal to client, informs both server and client to switch to finish state.

mrt_client:
- rcv_and_sgmnt_handler: listens for incoming segments and processes them
- connect(): set client to handshake state, and try to connect to server.
- send(): set client to data transfer state, send data to client.
- close(): send finish signal to server, informs both client and server to switch to finish state.

##Segement.py:
- It computes and parses the header of a segment, and it contain create_seg() and parse_seg()
- Each segment will have an 8-byte header which includes:
0: seq#
1: ack#
2: window_size(N)
3: a flag byte, with bit 4:ACK flag, 3:SYN flag, 2:DATA flag, 1:FIN flag
4-7: a 4-byte checksum calculated over the header using csc32
- when create header, header = bytes([seq, ack, window, flags_byte]) + checksum_bytes
- when create header, its checksum is computed over the temporary header (with zeros) concatenated with the payload.
- when parse header, its checksum is computed over the temporary header (with zeros), and it will compare the checksum value in the checksum field
- when parse header, the result of checksum comparing will return as "valid" which indicate if a segment is corrupted.
- when parse header, it can also return values for seq, ack, window, and flags_byte.

##Timer.py:
- It is the timer class for mrt_server and mrt_client.
- When a timer is initialized, it is in the stop state, which means checking if it is timeout will always return False.
- reset_timer() will reset and start the timer
- is_timeout() and is_timeout_2s() will return True after 0.5s and 2s, False otherwise
- stop_timer() will always make the return of is_timeout functions to be False


#Compilation and Usage
##preparation:
- Make sure mrt_client.py, mrt_server.py, app_client.py, app_server.py, network.py, Segment.py, Timer.py in the same directory
- Create a loss txt file in which each row is formatted as '5 .1 .001':
meaning loss rate = 10% and bit error rate = .1% 5s after the client is connected.

##Usage:
- Run the network.py using command formatted as below:
network.py <networkPort> <clientAddr> <clientPort> <serverAddr> <serverPort> <lossFile>
- Run the app_server.py using command formatted as below:
app_server.py <serverPort> <bufferSize>
- Run the app_client.py using command formatted as below:
app_client.py <clientPort> <networkAddr> <networkPort> <segmentSize>

where:
1. bufferSize > segmentSize
2. networkPort, clientPort, and serverPort in range: [49152 - 65535]
3. clientAddr and serverAddr can be 127.0.0.1

Example run:
python3 network.py 50005 127.0.0.1 50011 127.0.0.1 60006 loss.txt
python3 app_server.py 60006 2048
python3 app_client.py 50011 127.0.0.1 50005 512

A log flie in format will be produced after the run
<time> <src_port> <dst_port> <seq> <ack> <type> <payload_length> + 'my own comments'


#MRT Protocol
My code uses:
3-Way Handshake: SYN, SYN-ACK, ACK, DATA
Call function connect() and accept()
1. client send a SYN (re-send if timeout)
2. server reply a SYN-ACK if it received a SYN
3. client reply an ACK if it received a SYN-ACK, and end handshake
4. server receive the ACK (or DATA as implicit ACK), and end handshake

Data transfer: DATA
Call function send() and receive()
Use GBN to transfer and handle data loss and out of order
Window size(N) is decided in handshake stage, which N = bufferSize // segmentSize

Finish: FIN, FIN-ACK
Call close() on either side (don't call both)
side 1: send FIN (re-send if timeout)
side 2: send back FIN-ACK if received FIN, start the 2s timout countdown. Finish when timeout.
side 1: Finish if received FIN-ACK

More detail of MRT Protocol in DESIGN.md
