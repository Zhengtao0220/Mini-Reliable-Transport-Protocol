# CSEE 4119 Spring 2025, Assignment 2 Testing File
## Zhengtao Hu
## UNI: zh2651


Before starting testing, I need to mention the nature of my GBN algorithm.
When the difference of next ACK# received and the previous ACK# is greater than the window size, then the transmission will be in a deadlock and it will stop
e.g. the ACK prev = 1, and window size is 4, then the next ACK received must be smaller than 6 in order for the code to run.
Therefore, I implement the min window size to be 4 so that it won't crash the case when I receive ACK = 1 and 3 in a roll and my program stops because of my window size = 2 which is too small.
In reality, I understand window size should be always updated, but since the nature of this assignment, I will set a min value for N.


##Test case 1:
Testing code with no loss or corruption
loss.txt:
0 0.0 0.0
5 0.0 0.0
10 0.0 0.0
15 0.0 0.0
20 0.0 0.0
...
run with bufferSize = 2048, segmentSize = 512
call close() on the server side
Observed handshake complete
Observed all data is sent delivered correctly
Observed finish complete
Segments are sent 4 at a time, which equals window size = 4


##Test case 2:
Testing code for handshake for high data corruption case
loss.txt:
0 0.0 0.01
5 0.0 0.01
10 0.0 0.01
15 0.0 0.01
20 0.0 0.01
...
run connect() and accept() only
run with bufferSize = 2048, segmentSize = 512
Observed 3-Way handshake is completed as expected (ignore the case of waiting for an implict ACK)
SYN is re-sent and triggering the sending of SYN-ACK


##Test case 3:
Testing code for varying network condition and with a different window size
loss.txt:
0 0.2 0.0001
5 0.2 0.0001
10 0.2 0.0001
15 0.4 0.0005
20 0.4 0.0005
...
run with bufferSize = 3072, segmentSize = 512
call close() on the server side
Observed handshake complete
Observed all data is sent delivered correctly
Observed finish complete
Segments are sent 6 at a time, which equals window size = 6
The sending in the beginning is faster and slow down after around 10s


##Test case 4:
Testing code with extreme data loss condition
loss.txt:
0 0.8 0.0
5 0.8 0.0
10 0.8 0.0
15 0.8 0.0
20 0.8 0.0
...
run with bufferSize = 2048, segmentSize = 512
call close() on the server side
Observed handshake complete
Observed all data is sent delivered correctly
Observed finish complete
Segments are sent 4 at a time, which equals window size = 4
Log file shows there are many out of order but ACK are correctly sent back:
e.g.
03:11:26.136 50005 60006 10 0 DATA 504 "server received out-of-order seg, seq=10"
03:11:26.136 60006 50005 0 7 ACK 0 "server sent ACK for out-of-order seg, ack=7"


##Test case 5:
Testing code with extreme data corruption
loss.txt:
0 0.0 0.001
5 0.0 0.001
10 0.0 0.001
15 0.0 0.001
20 0.0 0.001
...
run with bufferSize = 2048, segmentSize = 512
call close() on the server side
Observed handshake complete
Observed all data is sent delivered correctly
Observed finish complete
Segments are sent 4 at a time, which equals window size = 4
Log file shows there are many corruption but they are ignored
And ACKs are correctly sent back:
e.g.
03:16:52.936 50005 60006 0 0 CORRUPT 0 "server received corrupted seg"
03:16:52.965 50005 60006 0 0 CORRUPT 0 "server received corrupted seg"
03:16:53.001 50005 60006 0 0 CORRUPT 0 "server received corrupted seg"
03:16:53.409 50005 60006 1 0 DATA 504 "server received valid seg, seq=1"
03:16:53.409 60006 50005 0 2 ACK 0 "server sent ACK for valid seg, ack=1"

03:16:53.391 50011 50005 5 0 DATA 504 "client retransmitted packet seq=1"
03:16:53.391 50011 50005 5 0 DATA 504 "client retransmitted packet seq=2"
03:16:53.391 50011 50005 5 0 DATA 504 "client retransmitted packet seq=3"
03:16:53.391 50011 50005 5 0 DATA 504 "client retransmitted packet seq=4"
03:16:53.409 50011 50005 0 2 ACK 0 "client received ACK=2"
03:16:53.416 50011 50005 5 0 DATA 504 "client sent packet seq=5"
03:16:53.918 50011 50005 6 0 DATA 504 "client retransmitted packet seq=2"
03:16:53.918 50011 50005 6 0 DATA 504 "client retransmitted packet seq=3"
03:16:53.918 50011 50005 6 0 DATA 504 "client retransmitted packet seq=4"
03:16:53.919 50011 50005 6 0 DATA 504 "client retransmitted packet seq=5"


##Test case 6:
Testing code with multiple send()
loss.txt:
0 0.4 0.0002
5 0.4 0.0002
10 0.4 0.0002
15 0.4 0.0002
20 0.4 0.0002
...
run with bufferSize = 2048, segmentSize = 512
call send() twice

sent = client.send(data)
    print(f">> sent {sent} bytes of data")
sent1 = client.send(data)
    print(f">> sent {sent} bytes of data")
where len(data) = 4000

Observed handshake complete
Observed all data is sent delivered correctly
Observed finish complete
Segments are sent 4 at a time, which equals window size = 4
When the first send is complete, the program proceed with the next seq# and ACK without reset, which is the expected behavior. The first send complete does not block the second one.


##Test case 7:
Testing code with multiple receive()
loss.txt:
0 0.4 0.0002
5 0.4 0.0002
10 0.4 0.0002
15 0.4 0.0002
20 0.4 0.0002
...
run with bufferSize = 5120, segmentSize = 1024
call receive() twice

received = server.receive(client, 4000)
    received1 = server.receive(client, 4000)
    received = received + received1

Observed handshake complete
Observed all data is sent delivered correctly
Observed finish complete
Segments are sent 5 at a time, which equals window size = 5
When the first receive is complete, the program proceed with the next seq# and ACK without reset, which is the expected behavior. The first receive complete does not block the second one.


##Test case 8:
Testing code with close() on the server side
loss.txt:
0 0.4 0.0002
5 0.4 0.0002
10 0.4 0.0002
15 0.4 0.0002
20 0.4 0.0002
...
run with bufferSize = 5120, segmentSize = 1024
run connect(), accept(), and close() in app_server only

Observed handshake complete
Observed finish complete
When FIN-ACK is not received, Server will keep re-sending FIN to stimulate client to send FIN-ACK. client stop when it does not receive further FIN for 2s.


##Test case 9:
Testing code with close() on the client side
loss.txt:
0 0.4 0.0002
5 0.4 0.0002
10 0.4 0.0002
15 0.4 0.0002
20 0.4 0.0002
...
run with bufferSize = 5120, segmentSize = 1024
run connect(), accept(), and close() in app_client only

Observed handshake complete
Observed finish complete
Similar to what happened on test case 8 but just with the client server reversed.
