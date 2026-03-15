import os
import socket
from google import genai
from common.rudp_protocol import RUDPSocket
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY is missing. Check your .env file.")
    exit(1)

# Initialize the new genai client
client = genai.Client(api_key=api_key)


def handle_prompt_with_gemini(prompt_text):
    """Helper function to contact Gemini API"""
    print("[APP SERVER] Contacting Gemini API...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text)
        return response.text
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"
    

def run_tcp_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(('0.0.0.0', 5555))
    server_sock.listen(5)
    print("[APP SERVER] AI Proxy Server is running on TCP port 5555...")

    while True:
        conn, addr = server_sock.accept()
        print(f"\n[APP SERVER] Received connection from {addr}")
        try:
            prompt_bytes = conn.recv(4096)
            if prompt_bytes:
                prompt_text = prompt_bytes.decode('utf-8')
                print(f"[APP SERVER] Received (TCP): {prompt_text}")

                answer_text = handle_prompt_with_gemini(prompt_text)

                print(f"[APP SERVER] Sending response back via TCP...")
                conn.sendall(answer_text.encode('utf-8'))
        except Exception as e:
            print(f"[APP SERVER] TCP Error: {e}")
        finally:
            conn.close()


def run_rudp_server():
    server_sock = RUDPSocket(port=5555)
    print("[APP SERVER] AI Proxy Server is running on RUDP port 5555...")
    while True:
        prompt_bytes = server_sock.receive_data()
        if not prompt_bytes:
            continue
            
        prompt_text = prompt_bytes.decode('utf-8')
        print(f"\n[APP SERVER] Received (RUDP): {prompt_text}")

        answer_text = handle_prompt_with_gemini(prompt_text)

        print(f"[APP SERVER] Sending response back via RUDP...")
        server_sock.send_data(answer_text.encode('utf-8'))


def main():
    print("=== AI Proxy Server ===")
    choice = input("Select protocol - (1) TCP or (2) RUDP: ").strip()

    if choice == '1':
        run_tcp_server()
    elif choice == '2':
        run_rudp_server()
    else:
        print("Invalid choice. Please select 1 for TCP or 2 for RUDP.")


if __name__ == "__main__":
    main()