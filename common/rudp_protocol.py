import socket
import random
from common.packet import Packet

# State constants for Congestion Control
SLOW_START = 0
CONGESTION_AVOIDANCE = 1
FAST_RECOVERY = 2

STATE_NAMES = {
    SLOW_START: "SLOW_START",
    CONGESTION_AVOIDANCE: "CONGESTION_AVOIDANCE",
    FAST_RECOVERY: "FAST_RECOVERY"
}

class RUDPSocket:
    """
    A reliable UDP socket wrapper.
    Implements reliability features:
    1. Sequence Numbers (for ordering)
    2. ACKs (for delivery confirmation)
    3. Retransmissions (for lost packets)
    4. Dynamic Window / Congestion Control (Reno style logic)
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

        # Congestion Control Parameters (Initial State)
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
        Reliably sends data using a Sliding Window protocol over UDP.
        Blocks until all data is acknowledged by the receiver.
        """

        self.sock.settimeout(self.timeout)

        packets = self._fragment_data(data)
        total_packets = len(packets)
        base = 0 # Index of the first unacked packet (Left edge of the window)
        next_seq = 0 # Index of the next packet to be sent 

        print(f"[RUDP] Starting transfer of {total_packets} packets. Initial CWND: {self.cwnd}. State: {STATE_NAMES[self.cc_state]}")

        # [MAIN LOOP]
        # We stay here until the 'base' reaches 'total_packets', meaning everything is ACKed.
        while base < total_packets:

            # [CALCULATING WINDOW SIZE]
            # Logic: We calculate 'window_limit' which is the right edge of our current window.
            window_limit = base + int(self.cwnd) 

            # [CONDITION]: Can we send more packets right now within our quota?
            while next_seq < total_packets and next_seq < window_limit:
                pkt = packets[next_seq]
                
                # [SENDING PACKET]
                if not self._should_drop_packet(drop_probability=0):
                    self.sock.sendto(pkt.pack(), self.dest_addr)
                else:
                    print(f"[SIMULATOR] Dropped packet Seq {pkt.seq_num} deliberately.")
                
                print(f"[DEBUG] Sent Seq {pkt.seq_num} (CWND: {self.cwnd:.2f}, State: {STATE_NAMES[self.cc_state]})")
                
                # After sending, we move the 'next_seq' cursor forward, but we do NOT move the 'base' until ACKs are received.
                next_seq += 1

            
            # [WAITING FOR ACKS]
            try:
                # [RECEIVING ACKS]
                data_raw, addr = self.sock.recvfrom(1024)
                ack_pkt = Packet.unpack(data_raw)

                # [CONDITION]: Is the received packet actually an ACK?
                if ack_pkt.is_ack:

                    # [CONDITION]: Is this a NEW ACK (moving the left edge of the window)?
                    if ack_pkt.seq_num >= base:
                        print(f"[RUDP-SENDER] Received valid ACK {ack_pkt.seq_num}. Advancing base.")
                        
                        # --- Valid NEW ACK ---
                        base = ack_pkt.seq_num + 1
                        
                        # [CONDITION]: TCP RENO - Did we just receive a new ACK while in Fast Recovery?
                        if self.cc_state == FAST_RECOVERY:
                            # [EXIT FAST RECOVERY]
                            self.cwnd = self.ssthresh
                            self.cc_state = CONGESTION_AVOIDANCE
                            self.dup_acks = 0
                        else:
                            # Normal Success (Slow Start or Congestion Avoidance)
                            self._handle_success_cc()
                            print(f"[RUDP-SENDER] CWND updated to {self.cwnd:.2f}. Current State: {STATE_NAMES[self.cc_state]}")
                            self.dup_acks = 0
                            
                        # Update last ACK received to the current ACK's sequence number
                        self.last_ack_received = ack_pkt.seq_num

                    # [CONDITION]: Is this a duplicate ACK (receiver is still waiting for 'base')?
                    elif ack_pkt.seq_num == self.last_ack_received:
                        # --- Duplicate ACK ---
                        self.dup_acks += 1
                        print(f"[RUDP-SENDER] Received Duplicate ACK {ack_pkt.seq_num}. (Dup Count: {self.dup_acks})")
                        
                        # [CONDITION]: Are we already in Fast Recovery?
                        if self.cc_state == FAST_RECOVERY:
                            # [INCREMENT WINDOW] TCP RENO
                            self.cwnd += 1
                            print(f"[RUDP-SENDER] Fast Recovery: Inflating window. CWND: {self.cwnd:.2f}")

                        # [CONDITION]: Triple Duplicate ACK detected (Fast Retransmit trigger)
                        elif self.dup_acks == 3:
                            print(f"[RUDP] 3 Dup ACKs! Fast Recovery triggered for Seq {base}!")
                            
                            # From SS/CA to FAST_RECOVERY
                            self.ssthresh = max(2, int(self.cwnd / 2))
                            self.cwnd = self.ssthresh + 3
                            self.cc_state = FAST_RECOVERY

                            print(f"[RUDP-SENDER] Window cut in half! New ssthresh: {self.ssthresh}, New CWND: {self.cwnd:.2f}")
                            
                            # Retransmit ONLY the missing packet at 'base' immediately
                            resend_pkt = packets[base]
                            self.sock.sendto(resend_pkt.pack(), self.dest_addr)

            # [CONDITION]: Packet Loss / Heavy Congestion
            except socket.timeout:
                # --- Congestion Control Logic: Timeout ---
                print(f"[RUDP] Timeout! Packet lost at base index {base}. Reducing Window.")
                self._handle_timeout_cc()
                
                # [UPDATE] Simple Go-Back-N Fallback Recovery
                next_seq = base
                    
            except Exception as e:
                print(f"[RUDP] Error: {e}")
                break
        
        # [TERMINATION]
        print("[RUDP] Sending FIN packet to terminate transfer.")
        fin_pkt = Packet(seq_num=total_packets, is_fin=True)
        self.sock.sendto(fin_pkt.pack(), self.dest_addr)
        print(f"[RUDP] Transfer complete")


    def _fragment_data(self, data: bytes):
        """Splits large data into Packet objects with sequence numbers."""
        MSS = 10 # Small size for easier observation of window behavior
        fragments = [data[i:i+MSS] for i in range(0, len(data), MSS)]
        packets = []

        for i, frag in enumerate(fragments):
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
                
                # [CONDITION]: Is this a FIN packet?
                if pkt.is_fin:
                    ack_pkt = Packet(seq_num=pkt.seq_num, is_ack=True)
                    self.sock.sendto(ack_pkt.pack(), addr)
                    print("[RUDP] Received FIN. End of transmission.")
                    break
                
                # [CONDITION]: Is this a data packet?
                if not pkt.is_ack:
                    if pkt.seq_num == expected_seq:
                        received_fragments[pkt.seq_num] = pkt.data
                        expected_seq += 1
                        
                        while expected_seq in received_fragments:
                            expected_seq += 1

                    # [CONDITION] Is this an out-of-order packet?
                    elif pkt.seq_num > expected_seq:
                        if pkt.seq_num not in received_fragments:
                            received_fragments[pkt.seq_num] = pkt.data

                    # Send a cumulative ACK
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
            self.cc_state = SLOW_START
            self.cwnd += 1
        else:
            if self.cc_state == SLOW_START:
                print(f"[RUDP-SENDER] CWND crossed ssthresh ({self.ssthresh}). Transitioning to CONGESTION AVOIDANCE!")
            # Congestion Avoidance: Linear Growth
            self.cc_state = CONGESTION_AVOIDANCE
            self.cwnd += 1.0 / self.cwnd

    def _handle_timeout_cc(self):
        """
        Updates Congestion Window on Timeout (Packet Loss).
        Algorithm (Reno):
        - ssthresh drops to half of current window.
        - cwnd resets to 1.
        - dupACKcount resets to 0.
        - System goes back to Slow Start.
        """
        self.ssthresh = max(2, int(self.cwnd / 2))
        self.cwnd = 1
        self.dup_acks = 0  # CRITICAL: Reset duplicate ACKs on timeout
        self.cc_state = SLOW_START