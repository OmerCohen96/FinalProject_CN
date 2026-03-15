import socket
import json
import time
import random
from common.rudp_protocol import RUDPSocket

def get_dhcp_ip(mac_address, dhcp_addr=('127.0.0.1', 6767)):
    """
    Simulates the DORA process to obtain an IP address from the DHCP server.
    """
    print("\n--- Starting DHCP Process (DORA) ---")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    try:
        # 1. DISCOVER
        discover_msg = {"type": "DISCOVER", "mac": mac_address}
        sock.sendto(json.dumps(discover_msg).encode('utf-8'), dhcp_addr)
        print("[CLIENT DHCP] Sent DISCOVER")
        
        # 2. OFFER
        data, _ = sock.recvfrom(1024)
        offer_msg = json.loads(data.decode('utf-8'))
        if offer_msg.get("type") != "OFFER":
            return None
            
        offered_ip = offer_msg.get("ip")
        print(f"[CLIENT DHCP] Received OFFER: {offered_ip}")
        
        # 3. REQUEST
        request_msg = {"type": "REQUEST", "mac": mac_address, "ip": offered_ip}
        sock.sendto(json.dumps(request_msg).encode('utf-8'), dhcp_addr)
        print(f"[CLIENT DHCP] Sent REQUEST for {offered_ip}")
        
        # 4. ACK
        data, _ = sock.recvfrom(1024)
        ack_msg = json.loads(data.decode('utf-8'))
        if ack_msg.get("type") == "ACK":
            print(f"[CLIENT DHCP] Received ACK. My new IP is: {offered_ip}\n")
            return offered_ip
            
    except socket.timeout:
        print("[CLIENT DHCP] DHCP Server timeout.")
    except Exception as e:
        print(f"[CLIENT DHCP] Error: {e}")
    finally:
        sock.close()
        
    return None


def get_dns_resolution(domain, dns_addr=('127.0.0.1', 5353)):
    """Resolves a domain name to an IP and Port using the DNS server."""
    print(f"\n--- Starting DNS Resolution for {domain} ---")

    # Comunicate with the DNS server using UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    try:
        query = {"domain": domain}
        sock.sendto(json.dumps(query).encode('utf-8'), dns_addr)
        print(f"[CLIENT DNS] Sent query for {domain}")
        
        data, _ = sock.recvfrom(1024)
        response = json.loads(data.decode('utf-8'))
        
        if response.get("status") == "OK":
            ip = response.get("ip")
            port = response.get("port")
            print(f"[CLIENT DNS] Received resolution: {ip}:{port}")
            return (ip, port)
        else:
            print(f"[CLIENT DNS] Domain not found.")
    except Exception as e:
        print(f"[CLIENT DNS] Error: {e}")
    finally:
        sock.close()
    return None


def main():

    # Simulate getting an IP address via DHCP
    my_mac = f"00:1A:2B:3C:4D:{random.randint(10, 99)}"

    # Phase 1: DHCP to get an IP address

    my_virtual_ip = get_dhcp_ip(my_mac)
    if not my_virtual_ip:
        print("Failed to obtain IP from DHCP. Cannot proceed.")
        return
    

    # Phase 2: DNS to resolve AI server address

    target_domain = "ai-server.local"
    resolved_addr = get_dns_resolution(target_domain)
    if not resolved_addr:
        print("Failed to resolve DNS. Exiting.")
        return
    
    server_ip, server_port = resolved_addr

    # Phase 3: Protocol Selection (TCP / RUDP)

    print("\n--- Protocol Selection ---")
    mode = input("Choose protocol - (1) TCP or (2) RUDP: ").strip()

    # Phase 4: Recieve user prompt and send to app server

    prompt = input("Enter your question for the AI: ")
    if not prompt.strip():
        print("Empty prompt. Exiting.")
        return
    
    # Embed the Virtual IP to show we are using it
    full_payload = f"[Virtual IP: {my_virtual_ip}] {prompt}"

    # Phase 5: Communication Logic

    if mode == '1':
        # TCP MODE
        print("\n[CLIENT] Sending prompt via TCP...")
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.settimeout(15.0)  # AI can take a few seconds to respond
            tcp_sock.connect((server_ip, server_port))
            tcp_sock.sendall(full_payload.encode('utf-8'))
            
            print("\n[CLIENT] Waiting for AI response...")
            # We use a larger buffer to receive the whole text in TCP
            response_bytes = tcp_sock.recv(65535) 
            if response_bytes:
                print("\n" + "="*40)
                print("RESPONSE FROM AI (TCP):")
                print(response_bytes.decode('utf-8', errors='replace'))
                print("="*40 + "\n")
            tcp_sock.close()
        except Exception as e:
            print(f"[CLIENT] TCP Error: {e}")
            
    elif mode == '2':
        # RUDP MODE
        print("\n[CLIENT] Sending prompt via RUDP...")
        client_sock = RUDPSocket(timeout=2.0)
        client_sock.set_destination((server_ip, server_port))
        client_sock.send_data(full_payload.encode('utf-8'))
        
        print("\n[CLIENT] Waiting for AI response...")
        response_bytes = client_sock.receive_data()
        
        if response_bytes:
            print("\n" + "="*40)
            print("RESPONSE FROM AI (RUDP):")
            print(response_bytes.decode('utf-8', errors='replace'))
            print("="*40 + "\n")
        else:
            print("[CLIENT] No response received.")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()