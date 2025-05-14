from flask import Flask, render_template, redirect, url_for, request, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import cv2
import sqlite3         # To store logs in a local database
import os           # To access environment variables
from datetime import datetime
from signal_detector import detect_signal_color     # Your custom color detection logic
from twilio.rest import Client
from dotenv import load_dotenv      # Load .env variables
from twilio.base.exceptions import TwilioRestException       # Handle Twilio errors

load_dotenv()  #load_dotenv() loads environment variables from a .env file into your Python script, allowing secure access to sensitive data like API keys, passwords, and tokens.
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions
login_manager = LoginManager()
login_manager.init_app(app)

account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH")
twilio_client = Client(account_sid, auth_token)
twilio_whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")
twilio_whatsapp_to = os.getenv("TWILIO_WHATSAPP_TO")

camera_url = 0  # Default webcam. Replace with IP camera URL if needed.

# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# In-memory users for demonstration, replace with actual DB
users = {
    "admin": {"password": "admin123"}
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def init_db():
    conn = sqlite3.connect("traffic_log.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        status TEXT
    )''')
    conn.commit()  
    conn.close()

init_db()

# inserting a new log entry into the logs table in the traffic_log.db
def log_status(status):
    conn = sqlite3.connect("traffic_log.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, status) VALUES (?, ?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status))
    conn.commit()
    conn.close()

# retrieve (not directly display) the most recent log entries from the database.
def get_history(limit=100):
    conn = sqlite3.connect("traffic_log.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, status FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    history = c.fetchall()  #Fehttp://127.0.0.1:5000/tches all the results from the executed query and stores them in the history list.
    conn.close()
    return history

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password", 401
    return render_template("login.html")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

#
@app.route('/')
def dashboard():
    cap = cv2.VideoCapture(camera_url)
    ret, frame = cap.read()  #Captures a single frame from the camera.ret is True if successful.frame contains the image data.
    cap.release()

    if not ret:
        status = "Camera Error"
    else:
        signal = detect_signal_color(frame)
        status = f"Signal: {signal}"
        log_status(signal)

    if signal == "Malfunction":
        filename = f"malfunction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(f"static/{filename}", frame)
        try:
           twilio_client.messages.create(
              body="🚨 Traffic Signal Malfunction Detected!",
              from_=twilio_whatsapp_from,
              to=twilio_whatsapp_to
            )
        except TwilioRestException as e:
           print(f"Twilio error: {e}")


    history = get_history()
    return render_template("dashboard.html", status=status, history=history)

if __name__ == '__main__':
    app.run(debug=True)

