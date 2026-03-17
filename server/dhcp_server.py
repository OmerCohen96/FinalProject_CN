import socket
import json

class DHCPServer:
    """
    DHCP (Dynamic Host Configuration Protocol) Server Simulation.
    Implements the standard DORA process:
    - [D]ISCOVER: Client broadcasts to find a DHCP server.
    - [O]FFER: Server proposes an available IP address.
    - [R]EQUEST: Client formally requests the offered IP.
    - [A]CKNOWLEDGE: Server confirms the IP allocation.
    """
    def __init__(self, host='127.0.0.1', port=6767):
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        
        # IP Pool for DHCP (10 IPs for simplicity)
        self.ip_pool = [f"192.168.1.{i}" for i in range(100, 110)]
        self.allocated_ips = {}  # Maps MAC Address -> Allocated IP

    def start(self):
        print(f"[DHCP SERVER] Listening on UDP port {self.address[1]}...")
        
        while True:
            try:
                data, client_addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                msg_type = message.get("type")
                client_mac = message.get("mac")

                # Ignore malformed packets immediately
                if not msg_type or not client_mac:
                    continue 

                # ==========================================
                # PHASE 1: [D]ISCOVER -> [O]FFER
                # ==========================================
                if msg_type == "DISCOVER":
                    print(f"\n[DHCP] Received DISCOVER from MAC: {client_mac}")
                    
                    # [LOGIC FIX] Check if the client already has an IP allocated (e.g., client rebooted)
                    # This prevents IP leakage where the server assigns a new IP every time the same client connects.
                    if client_mac in self.allocated_ips:
                        offered_ip = self.allocated_ips[client_mac]
                        print(f"[DHCP] MAC known. Re-offering previous IP: {offered_ip}")
                    elif self.ip_pool:
                        # Offer the first available IP from the pool. 
                        # We do NOT remove it from the pool yet, because the client hasn't formally requested it.
                        offered_ip = self.ip_pool[0]
                    else:
                        print("[DHCP] No available IPs to offer.")
                        continue # Skip sending an offer if pool is empty

                    response = {"type": "OFFER", "ip": offered_ip, "mac": client_mac}
                    self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)
                    print(f"[DHCP] Sent OFFER: {offered_ip}")

                # ==========================================
                # PHASE 2: [R]EQUEST -> [A]CK / NACK
                # ==========================================
                elif msg_type == "REQUEST":
                    requested_ip = message.get("ip")
                    print(f"[DHCP] Received REQUEST for IP: {requested_ip} from MAC: {client_mac}")
                    
                    # [CONDITION] Does the client already own this exact IP?
                    if client_mac in self.allocated_ips and self.allocated_ips[client_mac] == requested_ip:
                        response = {"type": "ACK", "ip": requested_ip, "mac": client_mac}
                        self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)
                        print(f"[DHCP] Sent ACK (IP already owned). IP {requested_ip} remains allocated to {client_mac}")
                    
                    # [CONDITION] Is the IP available in the pool?
                    elif requested_ip in self.ip_pool:
                        # Formally allocate: remove from pool and map to the specific MAC
                        self.ip_pool.remove(requested_ip)
                        self.allocated_ips[client_mac] = requested_ip
                        
                        response = {"type": "ACK", "ip": requested_ip, "mac": client_mac}
                        self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)
                        print(f"[DHCP] Sent ACK. IP {requested_ip} successfully allocated to {client_mac}")
                    
                    # [CONDITION] IP is neither owned by this MAC nor available in the pool
                    else:
                        response = {"type": "NACK", "mac": client_mac}
                        self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)
                        print(f"[DHCP] Sent NACK for IP {requested_ip}")

            # Catch JSON parsing errors specifically to prevent server crash on bad packets
            except json.JSONDecodeError:
                print("[DHCP SERVER] Received invalid JSON data. Ignoring.")
            except Exception as e:
                print(f"[DHCP SERVER] Error: {e}")

if __name__ == "__main__":
    server = DHCPServer()
    server.start()