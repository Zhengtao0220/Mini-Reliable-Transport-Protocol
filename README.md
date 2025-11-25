# CSEE 4119 Spring 2025 – Assignment 2
**Name:** Zhengtao Hu  
**UNI:** zh2651  

This project implements a mini reliable transport (MRT) protocol over UDP with:

- 3-way handshake (SYN, SYN-ACK, ACK)
- Go-Back-N sliding window for data transfer
- Timers and retransmissions
- CRC32-based corruption detection
- Flow control using an advertised window
- Support for varying loss/corruption conditions via a loss configuration file

---

## Code Structure

### `mrt_server.py` and `mrt_client.py`

- All global variables, multithreading, and socket connections are initialized in an `init()` function.
- Both MRT server and client:
  - Establish a UDP socket.
  - Maintain the connection for the lifetime of the protocol.
- Application-level code (`app_server.py` and `app_client.py`) calls into the functions implemented in `mrt_server.py` and `mrt_client.py`.
- The implementation uses a **finite state machine** implemented with `if` / `else` structures inside threads.
- As messages are transferred and processed between server and client, the **current state** is updated so each side knows when to:
  - Perform handshake
  - Transfer data
  - Finish the connection

#### `mrt_server.py`

(Protocol behavior is described in more detail in `DESIGN.md`.)

Key components:

- **`rcv_handler` thread**  
  Continuously receives UDP segments and puts them into a queue.

- **`rcv_buffer`**  
  A queue that stores raw incoming segments, updated by `rcv_handler`.

- **`sgmnt_handler` thread**  
  Processes segments taken from the receive queue.

- **`data_buffer`**  
  A `bytearray` that only accepts **in-order** and **valid** segments.

- **`accept()`**  
  Sets the server to the handshake state and accepts a client request.

- **`receive()`**  
  Sets the server to the data-transfer state and receives data from the client.

- **`close()`**  
  Sends a finish signal (`FIN`) to the client and switches both server and client into the finish state.

#### `mrt_client.py`

Key components:

- **`rcv_and_sgmnt_handler`**  
  Listens for incoming segments and processes them (similar to the server’s receive + segment handling).

- **`connect()`**  
  Puts the client into the handshake state and attempts to connect to the server.

- **`send()`**  
  Puts the client into the data-transfer state and sends data to the server.

- **`close()`**  
  Sends a finish signal (`FIN`) to the server and switches both sides into the finish state.

---

### `Segment.py`

Defines the segment header format and helper functions:

- Functions:
  - `create_seg()`
  - `parse_seg()`

Each segment has an **8-byte header** containing:

1. `seq` – sequence number  
2. `ack` – acknowledgment number  
3. `window` – window size \( N \)  
4. `flags_byte` – bit flags:
   - bit 4: ACK flag  
   - bit 3: SYN flag  
   - bit 2: DATA flag  
   - bit 1: FIN flag  
5. bytes 4–7: a 4-byte checksum (CRC32) calculated over the header and payload

Header creation:

- A temporary header with zeros in the checksum field is concatenated with the payload.
- CRC32 is computed over this data.
- The final header is:
  ```text
  header = bytes([seq, ack, window, flags_byte]) + checksum_bytes
