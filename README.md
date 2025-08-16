Date: August 2025
Task: Web-Based MSN-Style Messaging Platform
Technology Stack: Python Flask, RabbitMQ, SQLite, Socket.IO
Reference Implementation: https://blog.chatengine.io/fullstack-chat/python-javascript

 Project Structure
A3-projectbased
│
├── 01_start_rabbitmq.bat              # Start RabbitMQ Docker container
├── 02_open_rabbitmq_dashboard.bat     # Open RabbitMQ management dashboard
├── 03_launch_chat_app.bat             # Launch original CLI chat (Task 1)
├── 04_run_web_chat.bat               # Launch web-based chat application
├── app.py                            # Flask backend server
├── chat_app.py                       # Original CLI chat application
├── requirements.txt                  # Python dependencies
├── chat.db                          # SQLite database (auto-generated)
└── README.md                        # This documentation

##Installation & Setup

Prerequisites:

Windows 10/11 (x64)
Python 3.8+ with pip
Docker Desktop (running)
Internet connection (for initial setup)

Quick Start

Clone/Download the project files to your local machine
Start RabbitMQ Server

# manually run:
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management ( In the terminal-powershell)

Launch Web Application
# manually run:
pip install -r requirements.txt (split the terminal)
python app.py

Access the Chat

Open browser to: http://localhost:5000
Login with test credentials (see below)



Test User Accounts
Username: alice    | Password: password123 | Display: Alice Johnson
Username: bob      | Password: password123 | Display: Bob Smith  
Username: carol    | Password: password123 | Display: Carol Davis

##Usage Guide
Logging In

Navigate to http://localhost:5000
Enter username and password from test accounts
Click "Sign In" to access the chat platform

Chatting

Select Room: Use dropdown to switch between chat rooms
View Contacts: Left sidebar shows online users with status indicators
Send Messages: Type in bottom input field and press Enter or click Send
View History: Previous messages load automatically when joining rooms
Notifications: Pop-up alerts appear for new messages from other users

Room Management

General Chat: Default public room for casual conversation
Random: Off-topic discussions and random chat
Tech Talk: Technology and programming discussions
Gaming: Video game conversations and coordinatio
