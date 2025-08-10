# Author: Daniel Solano
# Student ID: A00151824
# Task: Assessment 1 - Task 1 Chatting Application

## START OF CODE ##

# 1. IMPORT LIBRARIES

import pika      # lets us talk to RabbitMQ (our messaging middleware)
import threading # so we can listen and type/send messages simultaneously
import sys       # to get username and room info from the command line
from datetime import datetime # to add timestamps to messages
import os  # allows us to run system-level commands like clearing the screen


# 2. GET USERNAME & ROOM FROM CMD

username = sys.argv[1] if len(sys.argv) > 1 else "User" # Get username and room from command line arguments.
room = sys.argv[2] if len(sys.argv) > 2 else "room" # If no username or room given, use default values.

# 2.1 CLEAR THE CONSOLE WINDOW

os.system('cls' if os.name == 'nt' else 'clear')  # Windows uses 'cls', Unix-like systems use 'clear'

# 2.2 SHOW WELCOME BANNER

print("=======================================")
print("  Welcome to the Chat Room! v.3.4.0")
print("=======================================\n")
print(f"Listening in [{room}] as [{username}]...type a message and hit Enter to start chatting!\n")

# 3. CONNECT TO RABBITMQ SERVER

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))  # Connect to RabbitMQ running on local machine
channel = connection.channel()  # Create a communication channel to send/receive messages

# 4. DECLARE EXCHANGE (CHAT ROOM)

channel.exchange_declare(exchange=room, exchange_type='direct')  # Declare a direct exchange named after the room for message routing based on keys

# 5. DECLARE USER QUEUE

queue_name = f"{username}_{room}"  # Create a unique queue name combining username and room for this user's messages
channel.queue_declare(queue=queue_name)  # Declare this queue so RabbitMQ can deliver messages here

# 6. BIND QUEUE TO EXCHANGE WITH ROUTING KEY

channel.queue_bind(exchange=room, queue=queue_name, routing_key='all')  # Bind queue to allow all users to receive broadcast messages

# 7. DEFINE CALLBACK TO HANDLE RECEIVED MESSAGES

def receive_messages(ch, method, properties, body):
    decoded = body.decode()
    if decoded.find(f"{username}:") != -1:  # Print message replacing username with [You] for current user
        print(decoded.replace(f"{username}:", "You:"))
    else:
        print(decoded) # When a message arrives from other user, decode and print it to the console

# 8. START LISTENING FUNCTION ON BACKGROUND THREAD

def start_listening():
    channel.basic_consume(queue=queue_name, on_message_callback=receive_messages, auto_ack=True)  # Start consuming messages from the queue
    channel.start_consuming()  # Blocking call that keeps listening for new messages

# 9. RUN LISTENER IN SEPARATE THREAD

threading.Thread(target=start_listening, daemon=True).start()  # Run the listener in background so user input is not blocked

# 10. MAIN LOOP: READ INPUT AND SEND MESSAGE

while True:
    text = input()  # Wait for user to type a message
    timestamp = datetime.now().strftime('%H:%M:%S')  # Get current time to add a timestamp
    msg = f"\n\t[{timestamp}] {username}: {text}"  # Format message to include timestamp and username
    channel.basic_publish(exchange=room, routing_key='all', body=msg)  # Send message to the exchange with routing key 'all' to broadcast

## END OF CODE ##