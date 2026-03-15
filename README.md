# Computer Communications - Final Project

**Ariel University | Computer Science Department**

## 📖 Project Overview

This project simulates the complete process of accessing a web resource. It covers everything from connecting to a new network, obtaining an IP address via DHCP, resolving domain names through a local DNS server, and finally communicating with an Application Server.

The system provides a choice between standard **TCP** and a custom **Reliable UDP (RUDP)** implementation for the application layer. The Application Server functions as an AI Agent, processing user prompts using the **Gemini API**.

---

## 🛠 Tech Stack

* **Language:** Python 3.x (Recommended)
* **API:** Google GenAI (Gemini)
* **Environment:** Virtual Environment (venv)
* **Version Control:** Git (Private Repository)

---

# 🚀 Getting Started

## 1. Prerequisites

Ensure Python is installed and clone the project from the private repository:

```bash
git clone https://github.com/OmerCohen96/FinalProject_CN.git
cd FinalProject_CN
```

---

## 2. Environment Setup

To ensure the project runs on any machine, a virtual environment is used:

```bash
# Create virtual environment
python -m venv venv

# Activate environment (Windows)
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

---

## 3. API Configuration

The Application Server requires a **Gemini API Key**.

1. Obtain a key from **Google AI Studio**
2. Create a `.env` file in the project root
3. Add the following line:

```
GEMINI_API_KEY=your_actual_key_here
```

> **Note:** The `.env` file is excluded from Git to prevent credential leaks and plagiarism issues.

---

# 🚦 Execution Order

For the simulation to work correctly, start the components in the following order:

### 1️⃣ DHCP Server

Assigns local IP addresses.

```bash
python -m server.dhcp_server
```

### 2️⃣ DNS Local Server

Handles domain name resolution.

```bash
python -m server.dns_server
```

### 3️⃣ Application Server

AI-powered endpoint supporting **TCP / RUDP**.

```bash
python -m server.app_server
```

### 4️⃣ Client

Initiates the connection and sends prompts.

```bash
python -m client.client_main
```

---

# 🏗 System Architecture & RUDP

The core of this project is the **Reliable UDP (RUDP)** implementation.

Key mechanisms include:

* **Reliability**
  Packet delivery assurance using **ARQ / ACK mechanisms**

* **Congestion Control**
  Dynamic window sizing (increase/decrease)

* **Flow Control**
  Prevents receiver buffer overflow

* **Error Simulation**
  The system intentionally simulates **packet loss and latency** to test reliability.

---

# 📊 Submission Requirements

### Final ZIP

Contains:

* All source code
* `.pcap` traffic captures
* Architecture PDF document

### Architecture PDF

Includes:

* System diagrams
* Prompts used for AI interaction
* Answers to theoretical questions

### Traffic Captures

Filtered `.pcap` files demonstrating:

* Successful transmissions
* Error detection and recovery

---

> **Disclaimer:**
> Portions of this project were developed with assistance from LLM tools (**Gemini AI**).
> All AI-generated code snippets are explicitly marked in the source files.
