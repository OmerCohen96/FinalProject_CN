import struct
from typing import Tuple


class Packet:
    """A minimal packet format used by both client and server.

    Header fields are intentionally explicit (booleans, not bit-packed) to keep
    the protocol easy to read and explain during an academic code review.

    Layout (network byte order):
        seq_num (uint32)
        is_ack (bool)
        is_sin (bool)
        is_dynamic (bool)
        is_config (bool)
        is_fin (bool)          # explicit termination marker
        max_msg_size (uint32)
        payload_len (uint32)
    """

    # I: uint32, ?: bool
    HEADER_FORMAT = '!I?????II'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(
        self,
        seq_num: int,
        *,
        is_ack: bool = False,
        is_sin: bool = False,
        is_dynamic: bool = False,
        is_config: bool = False,
        is_fin: bool = False,
        max_msg_size: int = 0,
        data: bytes = b'',
    ):
        self.seq_num = int(seq_num)
        self.is_ack = bool(is_ack)
        self.is_sin = bool(is_sin)
        self.is_dynamic = bool(is_dynamic)
        self.is_config = bool(is_config)
        self.is_fin = bool(is_fin)
        self.max_msg_size = int(max_msg_size)
        self.data = data if data is not None else b''
        self.payload_len = len(self.data)

    def pack(self) -> bytes:
        """Serialize packet to bytes."""
        header = struct.pack(
            self.HEADER_FORMAT,
            self.seq_num,
            self.is_ack,
            self.is_sin,
            self.is_dynamic,
            self.is_config,
            self.is_fin,
            self.max_msg_size,
            self.payload_len,
        )
        return header + self.data

    @classmethod
    def unpack_header(cls, header_bytes: bytes) -> Tuple[int, bool, bool, bool, bool, bool, int, int]:
        """Unpack header bytes and return all header fields."""
        if len(header_bytes) != cls.HEADER_SIZE:
            raise ValueError(f"Header length mismatch: expected {cls.HEADER_SIZE}, got {len(header_bytes)}")
        return struct.unpack(cls.HEADER_FORMAT, header_bytes)

    @classmethod
    def unpack(cls, packet_bytes: bytes) -> 'Packet':
        """Parse a full packet (header + payload) into a Packet instance."""
        if len(packet_bytes) < cls.HEADER_SIZE:
            raise ValueError("Packet too short")

        header = packet_bytes[:cls.HEADER_SIZE]
        seq_num, is_ack, is_sin, is_dynamic, is_config, is_fin, max_msg_size, payload_len = struct.unpack(
            cls.HEADER_FORMAT, header
        )

        expected_len = cls.HEADER_SIZE + payload_len
        if len(packet_bytes) != expected_len:
            raise ValueError(f"Packet length mismatch: expected {expected_len}, got {len(packet_bytes)}")

        payload = packet_bytes[cls.HEADER_SIZE:expected_len]
        return cls(
            seq_num,
            is_ack=is_ack,
            is_sin=is_sin,
            is_dynamic=is_dynamic,
            is_config=is_config,
            is_fin=is_fin,
            max_msg_size=max_msg_size,
            data=payload,
        )

    def __repr__(self) -> str:
        flags = []
        if self.is_sin:
            flags.append("SIN")
        if self.is_ack:
            flags.append("ACK")
        if self.is_config:
            flags.append("CONFIG")
        if self.is_fin:
            flags.append("FIN")
        if self.is_dynamic:
            flags.append("DYN")
        flags_str = "|".join(flags) if flags else "DATA"
        return f"<Packet seq={self.seq_num} flags={flags_str} payload_len={self.payload_len} max_msg={self.max_msg_size}>"
