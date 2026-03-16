import socket
import json

class DNSServer:
    """
    DNS (Domain Name System) Server Simulation.
    Acts as the local directory for the network, translating human-readable
    domain names (e.g., 'ai-server.local') into physical IP addresses and ports.
    Uses UDP, which is the standard transport protocol for DNS queries due to
    its low overhead and speed.
    """
    
    # Fix Port For DNS Server is 53 but we will use 5353 to avoid permission issues.
    def __init__(self, host='127.0.0.1', port=5353):
        self.address = (host, port)
        
        # [TRANSPORT LAYER] Creating a UDP socket (SOCK_DGRAM)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        
        # [STATE] Simple DNS Records Table (A-Record / SRV-Record simulation)
        # Maps a logical domain name to its physical routing details.
        self.dns_records = {
            "ai-server.local": {"ip": "127.0.0.1", "port": 5555}
        }

    def start(self):
        print(f"[DNS SERVER] Listening on UDP port {self.address[1]}...")
        
        # [MAIN LOOP] Continuously listen for incoming DNS queries
        while True:
            try:
                # 1. Receive query from any client
                data, client_addr = self.sock.recvfrom(1024)
                
                # 2. Decode and parse the JSON payload
                message = json.loads(data.decode('utf-8'))
                domain = message.get("domain")
                
                # Ignore empty or malformed requests
                if not domain:
                    continue
                    
                print(f"\n[DNS] Received query for domain: {domain}")
                
                # 3. [RESOLUTION LOGIC] Check if the requested domain exists in our records
                if domain in self.dns_records:
                    # Domain found -> Return OK status with routing info
                    response = {
                        "status": "OK",
                        "ip": self.dns_records[domain]["ip"],
                        "port": self.dns_records[domain]["port"]
                    }
                    print(f"[DNS] Resolved {domain} to {response['ip']}:{response['port']}")
                else:
                    # Domain not found -> Return NOT_FOUND error status (NXDOMAIN simulation)
                    response = {"status": "NOT_FOUND"}
                    print(f"[DNS] Domain {domain} not found.")
                    
                # 4. Send the resolution response back to the client
                self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)

            # [EXCEPTION HANDLING] Prevent server crash on bad JSON format
            except json.JSONDecodeError:
                print("[DNS SERVER] Received invalid JSON data. Ignoring.")
            except Exception as e:
                print(f"[DNS SERVER] Error: {e}")

if __name__ == "__main__":
    server = DNSServer()
    server.start()