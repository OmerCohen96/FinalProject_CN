import socket
import json

class DNSServer:
    def __init__(self, host='127.0.0.1', port=5353):
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        
        # Simple DNS Records Table
        self.dns_records = {
            "ai-server.local": {"ip": "127.0.0.1", "port": 5555}
        }

    def start(self):
        print(f"[DNS SERVER] Listening on UDP port {self.address[1]}...")
        
        while True:
            try:
                data, client_addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                domain = message.get("domain")
                
                print(f"\n[DNS] Received query for domain: {domain}")
                
                if domain in self.dns_records:
                    response = {
                        "status": "OK",
                        "ip": self.dns_records[domain]["ip"],
                        "port": self.dns_records[domain]["port"]
                    }
                    print(f"[DNS] Resolved {domain} to {response['ip']}:{response['port']}")
                else:
                    response = {"status": "NOT_FOUND"}
                    print(f"[DNS] Domain {domain} not found.")
                    
                self.sock.sendto(json.dumps(response).encode('utf-8'), client_addr)

            except Exception as e:
                print(f"[DNS SERVER] Error: {e}")

if __name__ == "__main__":
    server = DNSServer()
    server.start()