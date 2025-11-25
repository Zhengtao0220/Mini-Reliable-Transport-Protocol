# CSEE 4119 Spring 2025, Assignment 2 Design File
## Zhengtao Hu
## UNI: zh2651


##Message Type
SYN:Initiated by the client to start a connection. Its payload carries the client’s segment size.

SYN-ACK:Sent by the server in response to a SYN. It includes the server’s initial sequence number and the advertised window size.

ACK:Used to acknowledge the receipt of segments.

DATA:Segments carrying the actual payload. The DATA flag is set, and the segment is numbered with a sequence number.

FIN:Sent by either side to signal the intent to terminate the connection.

FIN-ACK: Sent in response to a FIN to acknowledge the termination request.

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


##Segment loss
- When a segment (can be SYN, DATA, FIN...) is sent, the program start a timer. 
If the expected ack is not received before the timer expires, it will retransmit the segment.
e.g. 
During handshake: if client did not receive an SYN-ACK, it will re-sent SYN after timeout
During data transfer: segments within the current sliding window are retransmitted upon timeout.
During finish: If a FIN-ACK is not received and it timeouts, the FIN segment is retransmitted until an acknowledgment is received.


##Data Corruption
Checksum:
- When each segment is created, it will include a CRC32 checksum.
- The checksum is recomputed and compared against the transmitted value
- If they disagree, the segment will be marked as invalid.
- Every invalid segment will be ignored as soon as one side receives it, and there will no ACK generated for these invalid segment


##Out-of-Order Delivery
- Each segment carries a sequence number, a global variable 'next sequence number' will keep track of the incoming segment's sequence number.
- If an ACK is sent during data transfer, the next sequence number will += 1
- Only the segment that matches the expected next sequence number are accepted and put into the data buffer
- If the incoming seg's sequence number disagrees the expected one, the receiver sends an ACK for the last correctly received segment. This will inform the sender to retransmit any out-of-order segments.


##High Link Latency
Timeout:
The timeout can trigger retransmission in high latency case when ACKs are delayed.

Sliding window:
The sliding window allows pipeline to happen. Multiple segments can be transited in one row, which helps maintain throughput even if round-trip times are high.


##Flow Control
- Window size(N) is decided in handshake stage, which N = bufferSize // segmentSize
- The sender maintains a send_base (the seq# of the earliest unacknowledged segment) and next_seq (the next sequence number to use). The sender only transmits new segments if the number of these unacknowledged segments is within the window limit.
- The advertised window from the server informs the client how many segments can be in transit before waiting for an ACK.
