from flask import Flask, render_template, request, jsonify, session, redirect, url_for  # Web framework
from flask_socketio import SocketIO, emit, join_room, leave_room  # Real-time WebSocket communication
import sqlite3      # simple database for storing users and messages
import hashlib      # For password hashing
import pika         # RabbitMQ client (same as original CLI chat)
import threading    # For background tasks
import json         # Message formatting
import os           # System operations
from datetime import datetime  # Timestamps for messages
import uuid         # Unique identifiers

# INITIALIZE FLASK WEB APPLICATION
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # For session management
socketio = SocketIO(app, cors_allowed_origins="*")   # Enable WebSocket with CORS

# DATABASE SETUP - CREATE TABLES FOR USERS, MESSAGES, AND ROOMS
def init_db():
    """Initialize SQLite database with required tables and test users"""
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    # Create users table - stores login credentials and display information
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 display_name TEXT NOT NULL,
                 status TEXT DEFAULT 'Online',
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create messages table - stores all chat messages with timestamps
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 room_name TEXT NOT NULL,
                 username TEXT NOT NULL,
                 message TEXT NOT NULL,
                 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create rooms table - keeps track of available chat rooms
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT UNIQUE NOT NULL,
                 created_by TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create default test users for demonstration (password: password123)
    try:
        c.execute("INSERT INTO users (username, password, display_name) VALUES (?, ?, ?)",
                 ('alice', hashlib.md5('password123'.encode()).hexdigest(), 'Alice Johnson'))
        c.execute("INSERT INTO users (username, password, display_name) VALUES (?, ?, ?)",
                 ('bob', hashlib.md5('password123'.encode()).hexdigest(), 'Bob Smith'))
        c.execute("INSERT INTO users (username, password, display_name) VALUES (?, ?, ?)",
                 ('carol', hashlib.md5('password123'.encode()).hexdigest(), 'Carol Davis'))
    except sqlite3.IntegrityError:
        pass  # Users already exist in database
    
    conn.commit()
    conn.close()

# RABBITMQ INTEGRATION - SAME MIDDLEWARE AS ORIGINAL CLI CHAT
# Reference: Extends functionality from Task 1 chat_app.py
class RabbitMQManager:
    """Manages RabbitMQ connections and operations - same setup as CLI chat"""
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        """Connect to RabbitMQ server (same as original chat_app.py)"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            print("Connected to RabbitMQ")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
    
    def create_room_exchange(self, room_name):
        """Create direct exchange for chat room (same pattern as CLI app)"""
        if self.channel:
            self.channel.exchange_declare(exchange=room_name, exchange_type='direct')
    
    def send_message(self, room_name, message_data):
        """Publish message to room exchange with routing key 'all'"""
        if self.channel:
            self.channel.basic_publish(
                exchange=room_name,
                routing_key='all',
                body=json.dumps(message_data)
            )

rabbitmq_manager = RabbitMQManager()  # Initialize RabbitMQ connection

# HELPER FUNCTIONS FOR DATABASE OPERATIONS
def get_user(username):
    """Retrieve user information from database"""
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def save_message(room_name, username, message):
    """Save chat message to database for persistence"""
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (room_name, username, message) VALUES (?, ?, ?)",
             (room_name, username, message))
    conn.commit()
    conn.close()

def get_room_messages(room_name, limit=50):
    """Load previous messages from database (same as message history feature)"""
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("""SELECT m.username, u.display_name, m.message, m.timestamp 
                 FROM messages m 
                 JOIN users u ON m.username = u.username 
                 WHERE m.room_name = ? 
                 ORDER BY m.timestamp DESC LIMIT ?""", (room_name, limit))
    messages = c.fetchall()
    conn.close()
    return list(reversed(messages))

def get_online_users():
    """Get all users for contact list display (simplified for demo)"""
    # In production, this would track actual online status
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT username, display_name, status FROM users")
    users = c.fetchall()
    conn.close()
    return users

# WEB ROUTES - HANDLE HTTP REQUESTS
@app.route('/')
def index():
    """Main page - redirect to login or chat based on session"""
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user authentication with simple login form"""
    if request.method == 'POST':
        # Handle login form submission via AJAX
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'})
        
        # Check credentials 
        user = get_user(username)
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        if user and user[2] == hashed_password:
            # Create session for authenticated user
            session['username'] = username
            session['display_name'] = user[3]
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    # Display login form with MSN-style design
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MSN Chat - Login</title>
        <style>
            body { font-family: Tahoma, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 0; height: 100vh; display: flex; align-items: center; justify-content: center; }
            .login-container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); width: 300px; text-align: center; }
            .logo { color: #0078d4; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #0078d4; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #106ebe; }
            .test-users { margin-top: 20px; font-size: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🟢 MSN Chat</div>
            <h2>Welcome Back!</h2>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Username" required>
                <input type="password" id="password" placeholder="Password" required>
                <button type="submit">Sign In</button>
            </form>
            <div class="test-users">
                <strong>Test Users:</strong><br>
                alice / password123<br>
                bob / password123<br>
                carol / password123
            </div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const result = await response.json();
                if (result.success) {
                    window.location.href = '/chat';
                } else {
                    alert(result.message);
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/chat')
def chat():
    """Main chat interface - MSN Messenger style layout"""
    # Redirect to login if not authenticated
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Return complete MSN-style chat interface HTML
    # Inspired by: https://blog.chatengine.io/fullstack-chat/python-javascript
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MSN Chat</title>
        <meta charset="utf-8">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: Tahoma, sans-serif; font-size: 11px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; overflow: hidden; }
            
            .msn-container { display: flex; height: 100vh; }
            
            .contact-list { width: 250px; background: linear-gradient(to bottom, #e1ecff 0%, #c7ddff 100%); border-right: 1px solid #8bb8ff; display: flex; flex-direction: column; }
            .contact-header { background: linear-gradient(to bottom, #4d90fe 0%, #2c5aa0 100%); color: white; padding: 8px; text-align: center; font-weight: bold; }
            .user-info { padding: 10px; border-bottom: 1px solid #b4ccff; }
            .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
            .status-online { background: #52c41a; }
            .status-away { background: #faad14; }
            .status-busy { background: #f5222d; }
            .contacts { flex-grow: 1; overflow-y: auto; }
            .contact { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #d4e2ff; display: flex; align-items: center; }
            .contact:hover { background: #d4e2ff; }
            .contact.active { background: #b4ccff; }
            
            .chat-area { flex-grow: 1; display: flex; flex-direction: column; background: white; }
            .chat-header { background: linear-gradient(to bottom, #4d90fe 0%, #2c5aa0 100%); color: white; padding: 8px 12px; display: flex; justify-content: between; align-items: center; }
            .room-controls { display: flex; align-items: center; gap: 10px; }
            .room-select { padding: 4px; border: none; border-radius: 3px; }
            .logout-btn { background: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 10px; }
            .logout-btn:hover { background: #c82333; }
            
            .messages { flex-grow: 1; padding: 10px; overflow-y: auto; background: white; }
            .message { margin-bottom: 8px; }
            .message-time { color: #666; font-size: 10px; }
            .message-user { font-weight: bold; color: #0066cc; }
            .message-text { margin-left: 5px; }
            
            .input-area { padding: 10px; border-top: 1px solid #ddd; display: flex; gap: 5px; }
            .message-input { flex-grow: 1; padding: 8px; border: 1px solid #ccc; border-radius: 3px; }
            .send-button { padding: 8px 15px; background: #0078d4; color: white; border: none; border-radius: 3px; cursor: pointer; }
            .send-button:hover { background: #106ebe; }
            
            .notification { position: fixed; top: 20px; right: 20px; background: #fffbe6; border: 1px solid #ffd666; padding: 10px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 1000; }
        </style>
    </head>
    <body>
        <div class="msn-container">
            <div class="contact-list">
                <div class="contact-header">Contacts</div>
                <div class="user-info">
                    <div><span class="status-indicator status-online"></span><strong id="currentUser"></strong></div>
                    <div style="font-size: 10px; color: #666;">Online</div>
                </div>
                <div class="contacts" id="contactsList"></div>
            </div>
            
            <div class="chat-area">
                <div class="chat-header">
                    <div>
                        <span style="font-weight: bold;">Chat Room: </span>
                        <span id="currentRoom">general</span>
                    </div>
                    <div class="room-controls">
                        <select class="room-select" id="roomSelect">
                            <option value="general">General Chat</option>
                            <option value="random">Random</option>
                            <option value="tech">Tech Talk</option>
                            <option value="gaming">Gaming</option>
                        </select>
                        <button class="logout-btn" onclick="logout()">Logout</button>
                    </div>
                </div>
                
                <div class="messages" id="messages"></div>
                
                <div class="input-area">
                    <input type="text" class="message-input" id="messageInput" placeholder="Type your message here..." maxlength="500">
                    <button class="send-button" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            let currentRoom = 'general';
            let username = '';
            let displayName = '';
            
            // Initialize
            document.addEventListener('DOMContentLoaded', function() {
                fetchUserInfo();
                fetchContacts();
                joinRoom(currentRoom);
                
                document.getElementById('messageInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') sendMessage();
                });
                
                document.getElementById('roomSelect').addEventListener('change', function() {
                    const newRoom = this.value;
                    switchRoom(newRoom);
                });
            });
            
            async function fetchUserInfo() {
                try {
                    const response = await fetch('/api/user-info');
                    const data = await response.json();
                    username = data.username;
                    displayName = data.display_name;
                    document.getElementById('currentUser').textContent = displayName;
                } catch (error) {
                    console.error('Error fetching user info:', error);
                }
            }
            
            async function fetchContacts() {
                try {
                    const response = await fetch('/api/contacts');
                    const contacts = await response.json();
                    const contactsList = document.getElementById('contactsList');
                    contactsList.innerHTML = '';
                    
                    contacts.forEach(contact => {
                        const contactDiv = document.createElement('div');
                        contactDiv.className = 'contact';
                        contactDiv.innerHTML = `
                            <span class="status-indicator status-${contact[2].toLowerCase()}"></span>
                            <span>${contact[1]}</span>
                        `;
                        contactsList.appendChild(contactDiv);
                    });
                } catch (error) {
                    console.error('Error fetching contacts:', error);
                }
            }
            
            function joinRoom(roomName) {
                socket.emit('join_room', {room: roomName});
                loadRoomMessages(roomName);
            }
            
            function switchRoom(newRoom) {
                socket.emit('leave_room', {room: currentRoom});
                currentRoom = newRoom;
                document.getElementById('currentRoom').textContent = newRoom;
                document.getElementById('roomSelect').value = newRoom;
                joinRoom(newRoom);
                document.getElementById('messages').innerHTML = '';
            }
            
            async function loadRoomMessages(roomName) {
                try {
                    const response = await fetch(`/api/messages/${roomName}`);
                    const messages = await response.json();
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';
                    
                    messages.forEach(msg => {
                        displayMessage(msg[0], msg[1], msg[2], msg[3], false);
                    });
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                } catch (error) {
                    console.error('Error loading messages:', error);
                }
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message) {
                    socket.emit('send_message', {
                        room: currentRoom,
                        message: message
                    });
                    input.value = '';
                }
            }
            
            function displayMessage(msgUsername, displayName, message, timestamp, isNew = false) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                
                const time = new Date(timestamp).toLocaleTimeString();
                const userLabel = msgUsername === username ? 'You' : displayName;
                
                messageDiv.innerHTML = `
                    <span class="message-time">[${time}]</span>
                    <span class="message-user">${userLabel}:</span>
                    <span class="message-text">${message}</span>
                `;
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
                if (isNew && msgUsername !== username) {
                    showNotification(`New message from ${displayName}`, message);
                }
            }
            
            function showNotification(title, message) {
                const notification = document.createElement('div');
                notification.className = 'notification';
                notification.innerHTML = `<strong>${title}</strong><br>${message}`;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 3000);
            }
            
            function logout() {
                fetch('/logout', {method: 'POST'})
                    .then(() => window.location.href = '/login');
            }
            
            // Socket events
            socket.on('message', function(data) {
                displayMessage(data.username, data.display_name, data.message, data.timestamp, true);
            });
            
            socket.on('user_joined', function(data) {
                const messagesDiv = document.getElementById('messages');
                const joinDiv = document.createElement('div');
                joinDiv.className = 'message';
                joinDiv.innerHTML = `<em style="color: #666;">${data.display_name} joined the room</em>`;
                messagesDiv.appendChild(joinDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                fetchContacts(); // Refresh contacts
            });
            
            socket.on('user_left', function(data) {
                const messagesDiv = document.getElementById('messages');
                const leaveDiv = document.createElement('div');
                leaveDiv.className = 'message';
                leaveDiv.innerHTML = `<em style="color: #666;">${data.display_name} left the room</em>`;
                messagesDiv.appendChild(leaveDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                fetchContacts(); // Refresh contacts
            });
        </script>
    </body>
    </html>
    '''

@app.route('/logout', methods=['POST'])
def logout():
    """Clear user session and logout"""
    session.clear()
    return jsonify({'success': True})

# API ENDPOINTS - PROVIDE DATA TO FRONTEND
@app.route('/api/user-info')
def user_info():
    """Get current user information for frontend display"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'username': session['username'],
        'display_name': session['display_name']
    })

@app.route('/api/contacts')
def contacts():
    """Get list of all users for contact list (MSN friends list)"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    users = get_online_users()
    return jsonify(users)

@app.route('/api/messages/<room_name>')
def room_messages(room_name):
    """Load message history for specific chat room"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    messages = get_room_messages(room_name)
    return jsonify(messages)

# WEBSOCKET EVENT HANDLERS - REAL-TIME COMMUNICATION
# Based on Socket.IO pattern from: https://blog.chatengine.io/fullstack-chat/python-javascript

@socketio.on('join_room')
def handle_join_room(data):
    """Handle user joining a chat room (similar to CLI room selection)"""
    if 'username' not in session:
        return
    
    room = data['room']
    join_room(room)  # Add user to WebSocket room
    
    # Create RabbitMQ exchange for room (same as CLI chat room creation)
    rabbitmq_manager.create_room_exchange(room)
    
    # Notify other users that someone joined
    emit('user_joined', {
        'username': session['username'],
        'display_name': session['display_name']
    }, room=room, include_self=False)

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle user leaving a chat room"""
    if 'username' not in session:
        return
    
    room = data['room']
    leave_room(room)
    
    emit('user_left', {
        'username': session['username'],
        'display_name': session['display_name']
    }, room=room)

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending message to chat room - core functionality"""
    if 'username' not in session:
        return
    
    room = data['room']
    message = data['message']
    username = session['username']
    display_name = session['display_name']
    timestamp = datetime.now().isoformat()
    
    # Save message to database for persistence (extends CLI functionality)
    save_message(room, username, message)
    
    # Send message via RabbitMQ (same middleware as original CLI chat)
    message_data = {
        'username': username,
        'display_name': display_name,
        'message': message,
        'timestamp': timestamp,
        'room': room
    }
    rabbitmq_manager.send_message(room, message_data)
    
    # Broadcast to all WebSocket clients in room (real-time delivery)
    emit('message', message_data, room=room)

if __name__ == '__main__':
    # Initialize database with tables and test users
    init_db()
    print("=" * 50)
    print("MSN-Style Web Chat Application Started!")
    print("=" * 50)
    print("Database initialized with test users:")
    print("- alice / password123")
    print("- bob / password123") 
    print("- carol / password123")
    print("\nWeb Interface: http://localhost:5000")
    print("RabbitMQ Dashboard: http://localhost:15672")
    print("\nCompatible with original CLI chat from Task 1!")
    print("Reference: https://blog.chatengine.io/fullstack-chat/python-javascript")
    print("\nMake sure RabbitMQ is running:")
    print("docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management")
    print("=" * 50)
    
    # Start Flask application with WebSocket support
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
