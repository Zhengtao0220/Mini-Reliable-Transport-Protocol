# 
# Mini Reliable Transport Protocol - Server Module
# Implemented for a computer networks course at Columbia University
# Defines Server-side APIs for a custom reliable transport protocol over UDP.
#

import socket
import threading
import queue
import time
import datetime
from Segment import Segment
from Timer import Timer


class Server:
    def init(self, src_port, receive_buffer_size):
        """
        initialize the server, create the UDP connection, and configure the receive buffer

        arguments:
        src_port -- the port the server is using to receive segments
        receive_buffer_size -- the maximum size of the receive buffer
        """
        self.src_port = src_port
        self.receive_buffer_size = receive_buffer_size

        self.handshake_state = False
        self.data_transfer_state = False
        self.finish_state = False

        self.server_isn = 0
        self.client_addr = None
        self.syn_ack_segment = None
        self.nextseqnum = 0
        self.syn_ack_timer = Timer()
        self.send_fin_timer = Timer()
        self.send_fin_ack_timer = Timer()
        self.running = True

        self.fin_reached = False
        self.fin_ack_received = False
        self.ack_timeout = True

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', src_port))
        self.server_socket.settimeout(0.5)

        self.rcv_buffer = queue.Queue()
        self.data_buffer = bytearray()

        self.rcv_thread = threading.Thread(target=self.rcv_handler)
        self.sgmnt_thread = threading.Thread(target=self.sgmnt_handler)
        self.rcv_thread.start()
        self.sgmnt_thread.start()

        self.log_file_name = f"log_{src_port}.txt"
        self.log_file = open(self.log_file_name, "a")
        self.start_time = time.time()
        pass

    def log(self, message):
        """
        write a line of log

        arguments:
        message -- the message to write
        """
        self.log_file.write(message + "\n")
        self.log_file.flush()

    def log_event(self, src_port, dst_port, seq, ack, seg_type, payload_length, extra=""):
        """
        write a line of formatted log

        arguments:
        src_port, dst_port, seq, ack, seg_type, payload_length, extra="" -- input info
        """
        now = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"{now} {src_port} {dst_port} {seq} {ack} {seg_type} {payload_length}"
        if extra:
            log_line += f' "{extra}"'
        self.log(log_line)

    def process_fin(self, segment):
        """
        check the finish segment and respond with ACK

        arguments:
        segment: FIN segment
        """
        if not segment["ACK"]:
            self.fin_reached = True
            print("[Finish] server received FIN")
            self.log_event(
                self.client_addr[1], self.src_port, 0, 0, "FIN",
                0, "server received FIN")
            fin_ack_seg = Segment.create_seg(
                seq=0,
                ack=0,
                window=0,
                a_flag=True,
                f_flag=True,
                payload=b"")
            self.server_socket.sendto(fin_ack_seg, self.client_addr)
            self.send_fin_ack_timer.reset_timer()
            print("[Finish] server sent FIN-ACK")
            self.log_event(
                self.src_port, self.client_addr[1], 0, 0, "FIN-ACK",
                0, "server sent FIN-ACK")
        else:
            print("server received FIN-ACK, server closed")
            self.log_event(
                self.client_addr[1], self.src_port, 0, 0, "FIN-ACK",
                0, "server received FIN-ACK, server closed")
            self.fin_ack_received = True

    def rcv_handler(self):
        """
        take in input raw segment

        all data in this buffer should be in order and intact
        handle all the logic of the transport protocol
        """
        while self.running:
            try:
                seg_bytes, client_addr = self.server_socket.recvfrom(self.receive_buffer_size)
            except socket.timeout:
                    continue
            print(f"{round(time.time() - self.start_time, 2)}: received seg from:", client_addr)
            self.rcv_buffer.put((seg_bytes, client_addr))
            time.sleep(0.01)

    def sgmnt_handler(self):
        """
        take in input raw segment

        handle all the logic of the transport protocol
        checking ACK nums of received segments
        retransmitting segments when necessary
        """
        while self.running:
            if self.send_fin_ack_timer.is_timeout_2s():
                print("server send fin_ack timout, finished")
                self.log("server send fin_ack timout, finished")
                self.fin_ack_received = True
                break

            if not self.rcv_buffer.empty():
                seg_bytes, client_addr = self.rcv_buffer.get()
                curr_segment = Segment.parse_seg(seg_bytes)
                if not curr_segment["valid"]:
                    print("server received corrupted seg")
                    self.log_event(
                        client_addr[1], self.src_port, 0, 0, "CORRUPT",
                        0, "server received corrupted seg")
                    continue

                if curr_segment["FIN"]:
                    self.handshake_state = False
                    self.data_transfer_state = False
                    self.process_fin(curr_segment)
                    continue

                if self.handshake_state:
                    if curr_segment["SYN"] and not curr_segment["ACK"] and not curr_segment["FIN"]:
                        print("[handshake] server received SYN from:", client_addr)
                        self.log_event(
                            client_addr[1], self.src_port, curr_segment["seq"], 0, "SYN",
                            len(curr_segment["payload"]), "server received SYN")
                        self.client_addr = client_addr
                        client_isn = curr_segment["seq"]
                        client_segment_size = int(curr_segment["payload"].decode().strip())
                        self.N = self.receive_buffer_size // client_segment_size
                        if self.N < 4:
                            self.N = 4
                        self.syn_ack_segment = Segment.create_seg(
                            seq=self.server_isn,
                            ack=client_isn + 1,
                            window=self.N,
                            a_flag=True,
                            s_flag=True,
                            payload=b""
                        )
                        self.server_socket.sendto(self.syn_ack_segment, client_addr)
                        print("[handshake] server sent SYN-ACK")
                        self.log_event(
                            self.src_port, client_addr[1], self.server_isn, client_isn + 1, "SYN-ACK",
                            0, "server sent SYN-ACK")
                    elif curr_segment["ACK"] and not curr_segment["SYN"] and not curr_segment["FIN"]:
                        print("[handshake] server received ACK:", client_addr)
                        self.log_event(
                            client_addr[1], self.src_port, curr_segment["seq"], curr_segment["ack"], "ACK",
                            len(curr_segment["payload"]), "server received ACK")
                        self.syn_ack_timer.stop_timer()
                        self.nextseqnum = 0
                        self.handshake_state = False

                    elif curr_segment["DATA"] or curr_segment["FIN"]:
                        print("[handshake] server received implicit ACK")
                        self.log_event(
                            client_addr[1], self.src_port, curr_segment["seq"], curr_segment["ack"], "DATA",
                            len(curr_segment["payload"]), "server received implicit ACK")
                        self.syn_ack_timer.stop_timer()
                        self.nextseqnum = 0
                        self.handshake_state = False

                    time.sleep(0.01)

                elif self.data_transfer_state:
                    seq_num = curr_segment["seq"]
                    if curr_segment["valid"] and seq_num == self.nextseqnum:
                        self.log_event(
                            client_addr[1], self.src_port, curr_segment["seq"], curr_segment["ack"], "DATA",
                            len(curr_segment["payload"]), f"server received valid seg, seq={seq_num}")
                        self.data_buffer.extend(curr_segment["payload"])
                        ack_nextseqnum = Segment.create_seg(seq=0,
                                                            ack=self.nextseqnum + 1,
                                                            window=0,
                                                            a_flag=True,
                                                            payload=b"")
                        self.server_socket.sendto(ack_nextseqnum, client_addr)
                        print(f"[Transfer]: server sent ACK for data seq: {self.nextseqnum + 1}")
                        self.log_event(
                            self.src_port, client_addr[1], 0, self.nextseqnum + 1, "ACK",
                            0, f"server sent ACK for valid seg, ack={self.nextseqnum}")
                        self.nextseqnum += 1

                    elif curr_segment["valid"] and seq_num < self.nextseqnum:
                        print(f"[Transfer] server received duplicate seg with seq: {seq_num} from {client_addr}")
                        self.log_event(
                            client_addr[1], self.src_port, curr_segment["seq"], curr_segment["ack"], "DATA",
                            len(curr_segment["payload"]), f"server received duplicate seg, seq={seq_num}")
                        ack_seg = Segment.create_seg(seq=0,
                                                     ack=self.nextseqnum,
                                                     window=0,
                                                     a_flag=True,
                                                     payload=b"")
                        self.server_socket.sendto(ack_seg, client_addr)
                        print(f"[Transfer] {round(time.time() - self.start_time, 2)}: server sent ACK for data seq: {self.nextseqnum}")
                        self.log_event(
                            self.src_port, client_addr[1], 0, self.nextseqnum, "ACK",
                            0, f"server sent ACK for duplicate seg, ack={self.nextseqnum}")

                    elif curr_segment["valid"]:
                        print(f"[Transfer] {round(time.time() - self.start_time, 2)}: server received out of order seg")
                        self.log_event(
                            client_addr[1], self.src_port, curr_segment["seq"], curr_segment["ack"], "DATA",
                            len(curr_segment["payload"]), f"server received out of order seg, seq={seq_num}")
                        ack_seg = Segment.create_seg(seq=0,
                                                     ack=self.nextseqnum,
                                                     window=0,
                                                     a_flag=True,
                                                     payload=b"")
                        self.server_socket.sendto(ack_seg, client_addr)
                        print(f"[Transfer] {round(time.time() - self.start_time, 2)}: server sent ACK for data seq: {self.nextseqnum}")
                        self.log_event(self.src_port, client_addr[1], 0, self.nextseqnum, "ACK",
                                       0, f"server sent ACK for out-of-order seg, ack={self.nextseqnum}")
                    time.sleep(0.01)

                else:
                    time.sleep(0.01)

    def accept(self):
        """
        accept a client request
        blocking until a client is accepted

        it should support protection against segment loss/corruption/reordering 

        return:
        the connection to the client 
        """
        self.handshake_state = True
        while self.handshake_state:
            time.sleep(0.01)

        print("3-way handshake completed on server.", self.client_addr)
        self.log("3-way handshake completed on server.")
        return self.client_addr

    def receive(self, conn, length):
        """
        receive data from the given client
        blocking until the requested amount of data is received
        
        it should support protection against segment loss/corruption/reordering 
        the client should never overwhelm the server given the receive buffer size

        arguments:
        conn -- the connection to the client
        length -- the number of bytes to receive

        return:
        data -- the bytes received from the client, guaranteed to be in its original order
        """
        data = bytearray()
        if conn != self.client_addr:
            print("Address disagree")

        self.data_transfer_state = True
        while len(data) < length:
            if len(self.data_buffer) > 0:
                needed = length - len(data)
                data.extend(self.data_buffer[:needed])
                self.data_buffer = self.data_buffer[needed:]
            time.sleep(0.01)

        print("server returning data of length:", len(data))
        self.log(f"server returning data of length: {len(data)}")
        return bytes(data)

    def close(self):
        """
        close the server and the client if it is still connected
        blocking until the connection is closed
        """
        fin_seg = Segment.create_seg(
            seq=0,
            ack=0,
            window=0,
            f_flag=True,
            payload=b"")
        self.server_socket.sendto(fin_seg, self.client_addr)
        print(f"[Finish] server sent FIN")
        self.log_event(
            self.src_port, self.client_addr[1], 0, 0, "FIN",
            0, "server sent FIN")
        self.send_fin_timer.reset_timer()
        while not self.fin_ack_received:
            if self.send_fin_timer.is_timeout():
                self.send_fin_timer.reset_timer()
                self.server_socket.sendto(fin_seg, self.client_addr)
                print(f"[Finish] server re-sent FIN (timeout)")
                self.log_event(
                    self.src_port, self.client_addr[1], 0, 0, "FIN",
                    0, "server re-sent FIN")
            time.sleep(0.01)

        self.running = False
        print("server closed")
        self.log("server closed")
        self.rcv_thread.join()
        self.sgmnt_thread.join()
        self.server_socket.close()
        pass
