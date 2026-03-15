import socket
import time
import struct
import threading
import random
from common.packet import Packet

# State constants for Congestion Control
SLOW_START = 0
CONGESTION_AVOIDANCE = 1

class RUDPSocket:
    """
    A reliable UDP socket wrapper
    """

    def __init__(self, port=0, timeout=2.0):
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if port != 0:
            self.sock.bind(('0.0.0.0', port))

        self.sock.settimeout(timeout)
        self.dest_addr = None
        self.timeout = timeout

        # --- Reliability & Windowing ---
        self.seq_num = 0
        self.expected_ack = 0

        # Congestion Control Parameters
        self.cwnd = 1.0         # Congestion Window (starts at 1 packet)
        self.ssthresh = 64      # Slow Start Threshold
        self.cc_state = SLOW_START
        self.dup_acks = 0       # Counter for duplicate ACKs
        self.last_ack_received = -1


    def set_destination(self, addr):
        """Sets the target address for sending data."""
        self.dest_addr = addr

    def _should_drop_packet(self, drop_probability=0.15):
        """Simulates network packet loss for testing purposes."""
        return random.random() < drop_probability

    def send_data(self, data: bytes):
        """
        
        """

        self.sock.settimeout(self.timeout)

        packets = self._fragment_data(data)
        total_packets = len(packets)
        base = 0 # Index of the first unacked packet
        next_seq = 0 # Index of the next packet to send

        print(f"[RUDP] Starting transfer of {total_packets} packets. Initial CWND: {self.cwnd}")

        while base < total_packets:
            # 1. Send packets within the window
            # We can send as long as 'next_seq' is within the window defined by 'base + cwnd'
            window_limit = base + int(self.cwnd) # Window limit is the upper bound of the last packet in the sequence we are allowed to send

            while next_seq < total_packets and next_seq < window_limit:
                pkt = packets[next_seq]
                
                # Network Simulator: Decide whether to drop or send
                if not self._should_drop_packet(drop_probability=0.30):
                    self.sock.sendto(pkt.pack(), self.dest_addr)
                else:
                    print(f"[SIMULATOR] Dropped packet Seq {pkt.seq_num} deliberately.")

                print(f"[DEBUG] Sent Seq {pkt.seq_num} (CWND: {self.cwnd:.2f})")
                next_seq += 1

            # 2. Wait for ACKs 
            try:
                # Try to recieve an ack
                data_raw, addr = self.sock.recvfrom(1024)
                ack_pkt = Packet.unpack(data_raw)

                if ack_pkt.is_ack:
                    if ack_pkt.seq_num >= base:
                        # Valid new ack
                        # Calculate how many packets were acknowledged
                        acked_count = ack_pkt.seq_num - base + 1
                        base = ack_pkt.seq_num + 1
                        # --- Congestion Control Logic: Successful ACK ---
                        self._handle_success_cc()
                        self.dup_acks = 0
                        self.last_ack_received = ack_pkt.seq_num

                    elif ack_pkt.seq_num == self.last_ack_received:
                        # Duplicate ACK
                        self.dup_acks += 1
                        # Fast Retransmit: If we receive 3 duplicate ACKs, we assume a packet loss and retransmit the missing packet
                        if self.dup_acks == 3:
                            print(f"[RUDP] Fast Retransmit triggered for Seq {base}!")
                            # Halve the window and resend immediately
                            self.ssthresh = max (2, int(self.cwnd / 2))
                            self.cwnd = self.ssthresh

                            # Resend the missing packet immediately
                            resend_pkt = packets[base]
                            self.sock.sendto(resend_pkt.pack(), self.dest_addr)
                            self.dup_acks = 0 # Reset after fast retransmit

            except socket.timeout:
                # --- Congestion Control Logic: Timeout ---
                print(f"[RUDP] Timeout! Packet lost at base index {base}. Reducing Window.")
                self._handle_timeout_cc()
                
                # Go-Back-N (Simplification): Resend from 'base'
                # In a real implementation, we might reset next_seq to base
                next_seq = base
                    
            except Exception as e:
                print(f"[RUDP] Error: {e}")
                break
        
        # Send FIN packet to terminate transfer
        print("[RUDP] Sending FIN packet to terminate transfer.")
        fin_pkt = Packet(seq_num=total_packets, is_fin=True)
        self.sock.sendto(fin_pkt.pack(), self.dest_addr)
        print(f"[RUDP] Transfer complete")


    def _fragment_data(self, data: bytes):
        """Splits large data into Packet objects with sequence numbers."""
        MSS = 5 # Max Segment Size (Safe for UDP MTU)
        fragments = [data[i:i+MSS] for i in range(0, len(data), MSS)]
        packets = []

        for i, frag in enumerate(fragments):
            # Creates a Packet. Note: In a real connection, seq_num should persist.
            # For this simple implementation, we reset seq_num per message or handle it globally.
            p = Packet(seq_num=i, data=frag)
            packets.append(p)

        return packets
    

    def receive_data(self) -> bytes:
        """
        Listens for packets, reassembles them in order, and handles ACKs.
        Returns the full data when a FIN packet is received.
        """
        received_fragments = {}
        expected_seq = 0
        
        print("[RUDP] Waiting for incoming data...")
        self.sock.settimeout(None)  # Block until data arrives
        
        while True:
            try:
                data_raw, addr = self.sock.recvfrom(2048)
                self.dest_addr = addr  # Update destination for ACKs
                pkt = Packet.unpack(data_raw)
                
                # If it's a FIN packet, acknowledge it and finish
                if pkt.is_fin:
                    ack_pkt = Packet(seq_num=pkt.seq_num, is_ack=True)
                    self.sock.sendto(ack_pkt.pack(), addr)
                    print("[RUDP] Received FIN. End of transmission.")
                    break
                    
                if not pkt.is_ack:
                    # Store data if it's the expected next sequence
                    if pkt.seq_num == expected_seq:
                        received_fragments[pkt.seq_num] = pkt.data
                        expected_seq += 1
                        
                        # Process any buffered out-of-order packets
                        while expected_seq in received_fragments:
                            expected_seq += 1
                            
                    elif pkt.seq_num > expected_seq:
                        # Buffer out-of-order packet
                        if pkt.seq_num not in received_fragments:
                            received_fragments[pkt.seq_num] = pkt.data

                    if expected_seq > 0:
                        ack_pkt = Packet(seq_num=expected_seq - 1, is_ack=True)
                        self.sock.sendto(ack_pkt.pack(), addr)
                            
            except Exception as e:
                print(f"[RUDP] Receive error: {e}")
                break
                
        # Reassemble the payload
        sorted_keys = sorted(received_fragments.keys())
        full_data = b"".join([received_fragments[k] for k in sorted_keys])
        self.sock.settimeout(self.timeout)
        return full_data
    

    def _handle_success_cc(self):
        """
        Updates Congestion Window (cwnd) on successful ACK.
        Algorithm:
        - If in Slow Start: cwnd = cwnd + 1 (Exponential growth)
        - If in Congestion Avoidance: cwnd = cwnd + 1/cwnd (Linear growth)
        """
        if self.cwnd < self.ssthresh:
            # Slow Start: Exponential Growth
            self.cwnd += 1
        else:
            # Congestion Avoidance: Linear Growth
            self.cwnd += 1.0 / self.cwnd

    def _handle_timeout_cc(self):
        """
        Updates Congestion Window on Timeout (Packet Loss).
        Algorithm (Tahoe/Reno simplified):
        - ssthresh drops to half of current window.
        - cwnd resets to 1.
        - System goes back to Slow Start.
        """
        self.ssthresh = max (2, int(self.cwnd / 2))
        self.cwnd = 1
        self.cc_state = SLOW_START
