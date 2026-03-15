import socket
import json

class DHCPServer:
    def __init__(self, host='127.0.0.1', port=6767):
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        
        # IP Pool for DHCP (10 IPs for simplicity)
        self.ip_pool = [f"192.168.1.{i}" for i in range(100, 110)]
        self.allocated_ips = {}  # MAC Address -> IP

    def start(self):
        print(f"[DHCP SERVER] Listening on UDP port {self.address[1]}...")
        
        while True:
            try:
                data, client_addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                msg_type = message.get("type")
                client_mac = message.get("mac")

                if msg_type == "DISCOVER":
                    print(f"\n[DHCP] Received DISCOVER from MAC: {client_mac}")
                    if self.ip_pool:
                        # Offer the first available IP from the pool
                        offered_ip = self.ip_pool[0]
                        response = {"type": "OFFER", "ip": offered_ip, "mac": client_mac}
                        self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)
                        print(f"[DHCP] Sent OFFER: {offered_ip}")
                    else:
                        print("[DHCP] No available IPs to offer.")

                elif msg_type == "REQUEST":
                    requested_ip = message.get("ip")
                    print(f"[DHCP] Received REQUEST for IP: {requested_ip} from MAC: {client_mac}")
                    
                    if requested_ip in self.ip_pool:
                        # If the requested IP is still available, allocate it to the client
                        self.ip_pool.remove(requested_ip)
                        self.allocated_ips[client_mac] = requested_ip
                        
                        response = {"type": "ACK", "ip": requested_ip, "mac": client_mac}
                        self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)
                        print(f"[DHCP] Sent ACK. IP {requested_ip} successfully allocated to {client_mac}")
                    else:
                        # The requested IP is not available (either already allocated or not in the pool)
                        response = {"type": "NACK", "mac": client_mac}
                        self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)
                        print(f"[DHCP] Sent NACK for IP {requested_ip}")

            except Exception as e:
                print(f"[DHCP SERVER] Error: {e}")

if __name__ == "__main__":
    server = DHCPServer()
    server.start()