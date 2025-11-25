#
# Mini Reliable Transport - Segment Definition
# Defines the MRT segment format
# Encapsulates sequence/ack numbers, window size, flags, and payload.
#

import zlib


class Segment:
    HEADER_SIZE = 8

    @staticmethod
    def compute_checksum(packet: bytes) -> int:
        """
        compute the checksum

        arguments:
        packet -- the segment converted to bytes
        """
        return zlib.crc32(packet) & 0xffffffff

    @staticmethod
    def create_seg(seq, ack, window, a_flag=False, s_flag=False, f_flag=False, d_flag=False, payload=b''):
        """"
        create a segment with a header and payload.

        arguments:
        seq -- the sequence number
        ack -- the acknowledgment number
        window -- the window size
        a_flag -- boolean flag for ACK
        s_flag --  boolean flag for SYN
        f_flag --  boolean flag for FIN
        d_flag --  boolean flag for DATA
        payload -- the payload

        returns:
        bytes -- segment as a bytes object.
        """
        seq = seq % 256
        ack = ack % 256
        window = window % 256

        flags_byte = 0
        if a_flag:
            flags_byte |= (1 << 4)
        if s_flag:
            flags_byte |= (1 << 3)
        if f_flag:
            flags_byte |= (1 << 2)
        if d_flag:
            flags_byte |= (1 << 1)

        temp_header = bytes([seq, ack, window, flags_byte]) + b"\x00\x00\x00\x00"
        temp_segment = temp_header + payload
        checksum = Segment.compute_checksum(temp_segment)
        checksum_bytes = checksum.to_bytes(4, byteorder='big')

        header = temp_header[:4] + checksum_bytes
        return header + payload

    @staticmethod
    def parse_seg(seg_bytes):
        """
        parse a segment
        the checksum is verified by computing the checksum again

        arguments:
        seg_bytes -- The complete segment as a bytes object

        returns:
        dict: a dictionary containing:
            - seq: the sequence number
            - ack: the acknowledgment number
            - window: the window size
            - checksum: the checksum value extracted from the header
            - ACK: boolean flag for ACK
            - SYN: boolean flag for SYN
            - FIN: boolean flag for FIN
            - DATA: boolean flag for DATA
            - payload: the payload
            - valid: boolean which indicate if the segment's checksum is correct
        """
        if len(seg_bytes) < Segment.HEADER_SIZE:
            raise ValueError("Segment too short to contain 5-byte header")

        header = seg_bytes[:Segment.HEADER_SIZE]
        payload = seg_bytes[Segment.HEADER_SIZE:]

        seq = header[0]
        ack = header[1]
        window = header[2]
        flags_byte = header[3]
        checksum_bytes = header[4:8]
        checksum = int.from_bytes(checksum_bytes, byteorder='big')

        header_zero = header[:4] + b"\x00\x00\x00\x00"
        computed_checksum = Segment.compute_checksum(header_zero + payload)
        valid = (computed_checksum == checksum)

        a_flag = bool((flags_byte >> 4) & 1)
        s_flag = bool((flags_byte >> 3) & 1)
        f_flag = bool((flags_byte >> 2) & 1)
        d_flag = bool((flags_byte >> 1) & 1)

        return {
            "seq": seq,
            "ack": ack,
            "window": window,
            "checksum": checksum,
            "ACK": a_flag,
            "SYN": s_flag,
            "FIN": f_flag,
            "DATA": d_flag,
            "payload": payload,
            "valid": valid
        }
