import os
import socket
from google import genai
from common.rudp_protocol import RUDPSocket
from dotenv import load_dotenv

# ==========================================
# SYSTEM CONFIGURATION & API SETUP
# ==========================================
# Load environment variables from the .env file to prevent API key leakage.
# This ensures credentials are not hardcoded or pushed to version control.
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY is missing. Check your .env file.")
    exit(1)

# Initialize the Google GenAI client securely using the loaded key.
client = genai.Client(api_key=api_key)


def handle_prompt_with_gemini(prompt_text):
    """
    Acts as the AI Proxy logic.
    Receives a decoded string prompt, forwards it to the Google Gemini API
    via an external HTTPS request, and returns the generated text.
    """
    print("[APP SERVER] Contacting Gemini API...")
    try:
        # Using the gemini-2.5-flash model for fast, standard text generation
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text
        )
        return response.text
    except Exception as e:
        # Fallback error message to send back to the client instead of crashing the server
        return f"Error communicating with AI: {str(e)}"
    

def run_tcp_server():
    """
    Runs the Application Server in standard TCP mode.
    Provides a reliable, stream-based connection using the OS's native network stack.
    """
    # [TRANSPORT LAYER] Create a standard TCP IPv4 socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind to all available network interfaces on port 5555
    server_sock.bind(('0.0.0.0', 5555))
    # Listen for incoming connections (backlog of 5)
    server_sock.listen(5)
    print("[APP SERVER] AI Proxy Server is running on TCP port 5555...")

    # [MAIN LOOP] Wait for and handle clients sequentially
    while True:
        # Block and wait for a new client TCP connection
        conn, addr = server_sock.accept()
        print(f"\n[APP SERVER] Received connection from {addr}")
        try:
            # Receive up to 4KB of prompt data. 
            # Note: For our simulation, 4KB is sufficient for a text prompt.
            # In a heavy production environment, a dynamic receiving loop until EOF is preferred.
            prompt_bytes = conn.recv(4096)
            if prompt_bytes:
                prompt_text = prompt_bytes.decode('utf-8')
                print(f"[APP SERVER] Received (TCP): {prompt_text}")

                # [APPLICATION LOGIC] Pass the payload to the AI handler
                answer_text = handle_prompt_with_gemini(prompt_text)

                print(f"[APP SERVER] Sending response back via TCP...")
                # Send the entire AI response back to the client over the reliable stream
                conn.sendall(answer_text.encode('utf-8'))
        except Exception as e:
            print(f"[APP SERVER] TCP Error: {e}")
        finally:
            # [TEARDOWN] Always close the connection socket after serving the request
            conn.close()


def run_rudp_server():
    """
    Runs the Application Server using our custom Reliable UDP protocol.
    Abstracts the underlying UDP mechanics so the application layer 
    treats it almost identically to a standard reliable stream.
    """
    # Initialize our custom RUDP socket listening on port 5555
    server_sock = RUDPSocket(port=5555)
    print("[APP SERVER] AI Proxy Server is running on RUDP port 5555...")
    
    # [MAIN LOOP] Process RUDP sessions sequentially
    while True:
        # Block and wait for a complete, reassembled payload from the RUDP stack
        prompt_bytes = server_sock.receive_data()
        if not prompt_bytes:
            continue
            
        prompt_text = prompt_bytes.decode('utf-8')
        print(f"\n[APP SERVER] Received (RUDP): {prompt_text}")

        # [APPLICATION LOGIC] Pass the payload to the AI handler
        answer_text = handle_prompt_with_gemini(prompt_text)

        print(f"[APP SERVER] Sending response back via RUDP...")
        # Hand the payload back to the RUDP stack for fragmentation and reliable delivery
        server_sock.send_data(answer_text.encode('utf-8'))


def main():
    """
    Entry point of the server. Allows the administrator to explicitly 
    choose the transport protocol before starting the listener loop.
    """
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