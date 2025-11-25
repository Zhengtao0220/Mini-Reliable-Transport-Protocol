# CSEE 4119 Spring 2025 – Assignment 2 Design
**Name:** Zhengtao Hu  
**UNI:** zh2651  

## Message Types

- **SYN**  
  Initiated by the client to start a connection. Its payload carries the client’s segment size.

- **SYN-ACK**  
  Sent by the server in response to a SYN. It includes the server’s initial sequence number and the advertised window size.

- **ACK**  
  Used to acknowledge the receipt of segments.

- **DATA**  
  Segments carrying the actual payload. The DATA flag is set, and the segment is numbered with a sequence number.

- **FIN**  
  Sent by either side to signal the intent to terminate the connection.

- **FIN-ACK**  
  Sent in response to a FIN to acknowledge the termination request.

---

## Connection Establishment – 3-Way Handshake

In this protocol, the 3-way handshake uses **SYN**, **SYN-ACK**, and **ACK**, followed by **DATA**:

- Application calls: `connect()` (client) and `accept()` (server).

Protocol steps:

1. **Client → Server:** send `SYN` (retransmit if timeout).  
2. **Server → Client:** upon receiving `SYN`, send `SYN-ACK`.  
3. **Client → Server:** upon receiving `SYN-ACK`, send `ACK` and end handshake.  
4. **Server:** handshake ends once it receives the `ACK` (or a `DATA` segment that serves as an implicit ACK).

---

## Data Transfer

- Application calls: `send()` (client) and `receive()` (server).
- Uses **Go-Back-N (GBN)** to handle:
  - Data loss
  - Out-of-order delivery

**Window size (N)** is decided during the handshake:  
\[
N = \frac{\text{bufferSize}}{\text{segmentSize}}
\]

Segments within the sliding window can be in flight at the same time. ACKs advance the window.

---

## Connection Termination

Termination uses **FIN** and **FIN-ACK**:

- Application calls: `close()` on either side (do **not** call `close()` on both sides).

Protocol steps:

1. **Side 1** calls `close()` and sends `FIN` (retransmit if timeout).  
2. **Side 2** responds with `FIN-ACK` when it receives `FIN`, and starts a 2s timeout countdown. It finishes when the timeout expires.  
3. **Side 1** finishes when it receives `FIN-ACK`.

---

## Segment Loss

- Whenever a segment (SYN, DATA, FIN, etc.) is sent, the program starts a timer.
- If the expected ACK is not received before the timer expires, the segment is **retransmitted**.

Examples:

- **Handshake:**  
  If the client does not receive a `SYN-ACK`, it retransmits the `SYN` after timeout.

- **Data transfer:**  
  Segments within the current sliding window are retransmitted upon timeout if their ACKs are not received.

- **Finish:**  
  If a `FIN-ACK` is not received before timeout, the `FIN` segment is retransmitted until the acknowledgment is received.

---

## Data Corruption

**Checksum (CRC32):**

- When each segment is created, it includes a **CRC32 checksum**.
- On receipt, the checksum is recomputed and compared against the transmitted value.
- If they disagree, the segment is marked **invalid**.
- Every invalid segment is **ignored** as soon as one side receives it:
  - No ACK is generated for invalid segments.

---

## Out-of-Order Delivery

- Each segment carries a **sequence number**.
- A global variable (e.g., “next expected sequence number”) tracks the expected incoming sequence number.

Behavior:

- When an ACK is sent during data transfer, the **next expected sequence number** is incremented.
- Only the segment that matches the **expected** sequence number is accepted and placed into the data buffer.
- If the incoming segment’s sequence number **does not** match the expected one:
  - The receiver sends an ACK for the **last correctly received** segment.
  - This informs the sender to retransmit missing or out-of-order segments.

---

## High Link Latency

### Timeout

- Timeouts trigger retransmissions when ACKs are delayed under high latency.
- This ensures reliability even when round-trip times are large.

### Sliding Window

- The sliding window enables **pipelining**:
  - Multiple segments can be transmitted before waiting for ACKs.
- This helps maintain throughput even when RTT is high.

---

## Flow Control

- Window size \( N \) is decided during the handshake:
  \[
  N = \frac{\text{bufferSize}}{\text{segmentSize}}
  \]
- The sender maintains:
  - **`send_base`** – sequence number of the earliest unacknowledged segment.
  - **`next_seq`** – sequence number for the next new segment.

Sending rule:

- The sender transmits new segments only if the number of unacknowledged segments is **within the window limit**.

The **advertised window** from the server tells the client how many segments can be in transit before it must wait for ACKs.
