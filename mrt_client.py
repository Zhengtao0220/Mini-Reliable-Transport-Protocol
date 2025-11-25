# 
# Mini Reliable Transport Protocol - Client Module
# Implemented for a computer networks course at Columbia University
# Defines Client-side APIs for a custom reliable transport protocol over UDP.
#

import socket
import threading
import time
import datetime
from Segment import Segment
from Timer import Timer


class Client:
    def init(self, src_port, dst_addr, dst_port, segment_size):
        """
        initialize the client and create the client UDP channel

        arguments:
        src_port -- the port the client is using to send segments
        dst_addr -- the address of the server/network simulator
        dst_port -- the port of the server/network simulator
        segment_size -- the maximum size of a segment (including the header)
        """
        self.handshake_complete = None
        self.src_port = src_port
        self.dst_port = dst_port
        self.dst_addr = dst_addr
        self.segment_size = segment_size

        self.handshake_state = False
        self.data_transfer_state = False
        self.finish_state = False

        self.send_buffer = []
        self.send_complete = False
        self.send_timer = Timer()
        self.syn_send_timer = Timer()
        self.send_fin_timer = Timer()
        self.send_fin_ack_timer = Timer()
        self.syn_ack_received = False
        self.fin_ack_received = False
        self.fin_reached = False
        self.running = True
        self.ack_timeout = False

        self.client_isn = 0
        self.send_base = 0
        self.next_seq = 0
        self.N = 0
        self.total_packets = 0

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('', src_port))
        self.client_socket.settimeout(0.5)

        self.rcv_and_sgmnt_handler = threading.Thread(target=self.rcv_and_sgmnt_handler)
        self.rcv_and_sgmnt_handler.start()

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
            print("[Finish] client received FIN")
            self.log_event(
                self.dst_port, self.src_port, 0, 0, "FIN",
                0, "client received FIN")
            fin_ack_seg = Segment.create_seg(
                seq=0,
                ack=0,
                window=0,
                a_flag=True,
                f_flag=True,
                payload=b"")
            self.client_socket.sendto(fin_ack_seg, (self.dst_addr, self.dst_port))
            self.send_fin_ack_timer.reset_timer()
            print("[Finish] client sent FIN-ACK")
            self.log_event(
                self.src_port, self.dst_port, 0, 0, "FIN-ACK",
                0, "client sent FIN-ACK")
        else:
            print("client received FIN-ACK")
            self.log_event(
                self.dst_port, self.src_port, 0, 0, "FIN-ACK",
                0, "client received FIN-ACK")
            self.fin_ack_received = True
            self.running = False


    def rcv_and_sgmnt_handler(self):
        """
        take in input raw segment

        handle all the logic of the transport protocol
        checking ACK nums of received segments
        retransmitting segments when necessary
        """
        while self.running:
            try:
                seg_bytes, addr = self.client_socket.recvfrom(self.segment_size + Segment.HEADER_SIZE)
            except socket.timeout:
                if self.send_fin_ack_timer.is_timeout_2s():
                    print("client send fin_ack timeout, finished")
                    self.log_event(
                        self.src_port, self.dst_port, 0, 0, "FIN-ACK",
                        0, "client sent FIN-ACK timeout, closed")
                    self.running = False
                    break
                else:
                    continue

            rcv_segment = Segment.parse_seg(seg_bytes)
            if not rcv_segment["valid"]:
                print("client received corrupted seg")
                self.log_event(
                    self.dst_port, self.src_port, 0, 0, "CORRUPT",
                    0, "client received corrupted seg")
                continue

            if rcv_segment["FIN"]:
                self.handshake_state = False
                self.data_transfer_state = False
                self.process_fin(rcv_segment)
                continue

            if self.handshake_state:
                if rcv_segment["SYN"] and rcv_segment["ACK"]:
                    self.syn_send_timer.stop_timer()
                    print("[handshake] client received SYN-ACK")
                    self.log_event(
                        self.dst_port, self.src_port, int(rcv_segment["ack"]), self.client_isn + 1, "SYN-ACK",
                        0, "client received SYN-ACK")
                    self.N = int(rcv_segment["window"])
                    ack_num = int(rcv_segment["ack"])
                    ack_segment = Segment.create_seg(
                        seq=ack_num,
                        ack=self.client_isn + 1,
                        window=0,
                        a_flag=True,
                        payload=b"")
                    self.client_socket.sendto(ack_segment, (self.dst_addr, self.dst_port))
                    print("[handshake] client sent ACK")
                    self.log_event(
                        self.src_port, self.dst_port, ack_num, self.client_isn + 1, "ACK",
                        0, "client sent ACK")
                    self.handshake_state = False

                time.sleep(0.01)

            elif self.data_transfer_state:
                if rcv_segment["SYN"]:
                    self.log_event(
                        self.dst_port, self.src_port, rcv_segment["seq"], rcv_segment["ack"], "SYN",
                        0, "client received unexpected SYN during data transfer")
                    continue

                n = rcv_segment["ack"]
                print(f"[Transfer] {round(time.time() - self.start_time, 2)}: client received ACK={n}")
                self.log_event(
                    self.src_port, self.dst_port, rcv_segment["seq"], rcv_segment["ack"], "ACK",
                    0, f"client received ACK={n}")

                self.send_base = n
                if self.send_base == self.next_seq:
                    self.send_timer.stop_timer()
                else:
                    self.send_timer.reset_timer()

                if self.send_base >= self.total_packets:
                    self.data_transfer_state = False
            else:
                time.sleep(0.01)


    def connect(self):
        """
        connect to the server
        blocking until the connection is established

        it should support protection against segment loss/corruption/reordering 
        """
        self.handshake_state = True
        syn_seg = Segment.create_seg(
            seq=self.client_isn,
            ack=0,
            window=0,
            s_flag=True,
            payload=str(self.segment_size).encode())
        self.client_socket.sendto(syn_seg, (self.dst_addr, self.dst_port))
        print("[handshake] client sent SYN")
        self.log_event(
            self.src_port, self.dst_port, self.client_isn, 0, "SYN",
            str(self.segment_size).encode(), "client sent SYN")
        self.syn_send_timer.reset_timer()
        while self.handshake_state:
            if self.syn_ack_received:
                time.sleep(0.01)
                continue

            elif self.syn_send_timer.is_timeout():
                self.syn_send_timer.reset_timer()
                self.client_socket.sendto(syn_seg, (self.dst_addr, self.dst_port))
                print("[handshake] client re-sent SYN (timeout)")
                self.log_event(
                    self.src_port, self.dst_port, self.client_isn, 0, "SYN",
                    str(self.segment_size).encode(), "client re-sent SYN (timeout)")

            time.sleep(0.01)

    def send(self, data):
        """
        send a chunk of data of arbitrary size to the server
        blocking until all data is sent

        it should support protection against segment loss/corruption/reordering and flow control

        arguments:
        data -- the bytes to be sent to the server
        """
        seg_size = self.segment_size - Segment.HEADER_SIZE
        packets = [data[i:i+seg_size] for i in range(0, len(data), seg_size)]
        self.send_buffer.extend(packets)
        self.total_packets = len(self.send_buffer)

        print(f"window size ={self.N}")
        self.log(f"window size ={self.N}")
        self.send_timer.reset_timer()
        self.data_transfer_state = True
        while self.send_base < self.total_packets and self.data_transfer_state:
            if self.next_seq < self.send_base + self.N and self.next_seq < self.total_packets:
                seg = Segment.create_seg(
                    seq=self.next_seq,
                    ack=0,
                    window=self.N,
                    d_flag=True,
                    payload=self.send_buffer[self.next_seq])
                self.client_socket.sendto(seg, (self.dst_addr, self.dst_port))
                self.log_event(
                    self.src_port, self.dst_port, self.next_seq, 0, "DATA",
                    len(self.send_buffer[self.next_seq]), f"client sent packet seq={self.next_seq}")
                self.next_seq += 1

            if self.send_timer.is_timeout():
                self.send_timer.reset_timer()
                for i in range(self.send_base, self.next_seq):
                    seg = Segment.create_seg(
                        seq=i,
                        ack=0,
                        window=self.N,
                        d_flag=True,
                        payload=self.send_buffer[i])
                    self.client_socket.sendto(seg, (self.dst_addr, self.dst_port))
                    self.log_event(
                        self.src_port, self.dst_port, self.next_seq, 0, "DATA",
                        len(self.send_buffer[i]), f"client retransmitted packet seq={i}")

            time.sleep(0.01)
        return len(data)

    def close(self):
        """
        request to close the connection with the server
        blocking until the connection is closed
        """
        fin_seg = Segment.create_seg(
            seq=0,
            ack=0,
            window=0,
            f_flag=True,
            payload=b"")
        self.client_socket.sendto(fin_seg, (self.dst_addr, self.dst_port))
        print(f"[Finish] client sent FIN")
        self.log_event(
            self.src_port, self.dst_port, 0, 0, "FIN",
            0, "client sent FIN")
        self.send_fin_timer.reset_timer()
        while not self.fin_ack_received:
            if self.send_fin_timer.is_timeout():
                self.send_fin_timer.reset_timer()
                self.client_socket.sendto(fin_seg, (self.dst_addr, self.dst_port))
                print(f"[Finish] client re-sent FIN (timeout)")
                self.log_event(
                    self.src_port, self.dst_port, 0, 0, "FIN",
                    0, "client re-sent FIN")
            time.sleep(0.01)

        print("client closed")
        self.log("client closed")
        self.rcv_and_sgmnt_handler.join()
        self.client_socket.close()
        pass
