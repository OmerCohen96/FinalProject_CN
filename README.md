# Computer Communications - Final Project

**Ariel University | Computer Science Department**

## 📖 Project Overview

This project simulates a complete end-to-end network communication process. It covers establishing a connection to a local network, dynamically obtaining an IP address via a DHCP simulation, resolving domain names through a local DNS server, and finally, querying an Application Server.

The system provides a dynamic choice between standard **TCP** and a custom-built **Reliable UDP (RUDP)** implementation for the application layer. The Application Server acts as an AI Proxy, securely processing user queries using the **Google Gemini API**.

---

## 🛠 Tech Stack

* **Language:** Python 3.x
* **API:** Google GenAI (Gemini 2.5 Flash)
* **Environment:** Python Virtual Environment (venv)
* **Architecture:** Client-Server / Separation of Concerns

---

## 📂 Project Structure

* `client/` - Contains the client application (DHCP, DNS resolution, and AI querying).
* `server/` - Contains the App Server, DHCP Server, and DNS Server.
* `common/` - Contains the core network infrastructure (RUDP Protocol and Packet classes).

---

# 🚀 Getting Started

## 1. Prerequisites & Environment Setup

Clone the project and set up an isolated virtual environment to avoid dependency conflicts:

```bash
# Clone the repository
git clone https://github.com/OmerCohen96/FinalProject_CN.git
cd FinalProject_CN

# Create virtual environment
python -m venv venv

# Activate environment (Windows)
.\venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 2. API Configuration (Google Gemini)

The Application Server requires a valid Gemini API Key to process queries. Follow these exact steps to generate and configure your key securely:

**Step A: Get the API Key**

1. Navigate to https://aistudio.google.com/
2. Sign in with your Google account.
3. On the left navigation panel, click on **"Get API key"**.
4. Click the **"Create API key"** button (you may need to create a new project or select an existing one).
5. Copy the generated API key to your clipboard.

**Step B: Configure the Project**

1. Open the root directory of the cloned project (`FinalProject_CN`).
2. Create a new, plain text file and name it exactly: `.env` (Notice the dot at the beginning).
3. Open the `.env` file and paste your key in the following format (without quotes or spaces around the equal sign):

```
GEMINI_API_KEY=your_copied_api_key_here
```

4. Save the file.

> **Security Note:** The `.env` file is explicitly ignored by `.gitignore` to prevent credential leaks. Never commit your API key to a public repository.

---

# 🚦 Execution Order

For the network simulation to function correctly, you must open **four separate terminal windows** (ensure the `venv` is activated in all of them) and start the components in this exact order:

### 1️⃣ DHCP Server (Terminal 1)

Assigns virtual local IP addresses to connecting clients.

```bash
python -m server.dhcp_server
```

### 2️⃣ DNS Local Server (Terminal 2)

Handles domain name resolution (`ai-server.local`).

```bash
python -m server.dns_server
```

### 3️⃣ Application Server (Terminal 3)

The AI-powered endpoint. You will be prompted to select TCP or RUDP listening mode.

```bash
python -m server.app_server
```

### 4️⃣ Client (Terminal 4)

Initiates the DORA process, resolves the DNS, and connects to the app server.

```bash
python -m client.client_main
```

---

# 🏗 System Architecture & RUDP Implementation

The technical core of this project is the custom **Reliable UDP (RUDP)** protocol, built on top of `socket.SOCK_DGRAM`.

It strictly implements **TCP Reno** congestion control principles:

* **Reliability:** Ensures packet delivery and ordering using Sequence Numbers and Cumulative ACKs.
* **Congestion Control (Dynamic Window):** Implements *Slow Start* (exponential growth) and *Congestion Avoidance* (linear growth) based on network conditions.
* **Fast Recovery & Fast Retransmit:** Detects 3 duplicate ACKs to immediately retransmit lost packets without waiting for a full timeout, dynamically inflating the congestion window.
* **Error Simulation:** Includes an internal mechanism (`_should_drop_packet`) to deliberately drop packets and simulate network jitter/loss, proving the protocol's recovery capabilities.

> **Disclaimer:**
> Portions of this project (specifically syntax completion, boilerplate generation, and debugging assistance) were developed with the assistance of LLM tools. The theoretical application, architecture, and TCP Reno state-machine enforcement were strictly human-directed.
