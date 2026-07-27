# Cross-Platform Ransomware Worm with C2 Server

Complete Command and Control System Documentation

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation Guide](#installation-guide)
- [C2 Server Commands](#c2-server-commands)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

---

## Overview

This is a complete cross-platform Command and Control (C2) system consisting of:

- **C2 Server**: A web-based dashboard for controlling infected machines
- **Worm Malware**: Cross-platform agent that executes commands on Windows, macOS, and Linux

The system provides remote control capabilities including:

- File encryption and decryption
- Keystroke logging
- Webcam access
- Screenshot capture
- Data exfiltration
- Cryptocurrency mining
- System command execution
- Process injection

---

## Features

### Worm Features

| Feature | Description |
|---------|-------------|
| Cross-Platform | Works on Windows, macOS, and Linux |
| Anti-VM Detection | Detects virtual machines and sandboxes |
| Persistent | Multiple persistence mechanisms |
| Stealth | Clears logs, bypasses UAC |
| Encryption | AES-256 file encryption |
| Keylogging | Captures all keystrokes |
| Webcam | Capture images and stream |
| Data Exfiltration | Steals sensitive files |
| Crypto Mining | Fallback cryptocurrency mining |
| Process Injection | Injects code into running processes |
| Dead Man's Switch | Automatic encryption if no C2 contact |
| Checkpoint Resume | Resumes encryption if interrupted |

### C2 Server Features

| Feature | Description |
|---------|-------------|
| Web Dashboard | Real-time host monitoring |
| WebSocket Support | Live updates |
| Command Templates | Pre-built command structures |
| Keylog Viewer | View captured keystrokes |
| Host Statistics | Detailed system information |
| Multi-Host | Control multiple infected machines |
| API Access | RESTful API for automation |
| Secure Login | Password-protected access |

---

## System Architecture

### Component Overview

The system consists of three main components working together:

**1. C2 Server (Controller)**
- Web-based dashboard running on your machine
- Manages all infected hosts
- Sends commands and receives results
- Stores data in SQLite database

**2. Worm Agent (Victim)**
- Runs on infected Windows, macOS, or Linux systems
- Connects to C2 server via DNS/HTTP beacons
- Executes received commands
- Sends back results and stolen data

**3. Communication Channel**
- DNS tunneling for stealth communication
- HTTP beacons for status updates
- WebSocket for real-time command delivery


### Components

**C2 Server Components:**
- Flask web application
- SQLite database for storage
- WebSocket server for real-time updates
- DNS command channel

**Worm Agent Components:**
- OS detection module
- Command execution engine
- Encryption module
- Keylogger module
- Webcam module
- Data exfiltration module
- Persistence module

### Database Structure

| Table | Purpose |
|-------|---------|
| hosts | Stores infected machine information |
| commands | Command queue for each host |
| beacons | Communication history |
| keylogs | Captured keystrokes |
| encrypted_files | List of encrypted files |
| exfiltrated_files | Stolen files data |
| webcam_captures | Webcam images |

---

## Installation Guide

### C2 Server Installation

#### Quick Install (All Operating Systems)

# 1. Install Python dependencies
`pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

# 2. Run the server
python c2_server.py
