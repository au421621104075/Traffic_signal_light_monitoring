from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import cv2
import sqlite3
import os
from datetime import datetime
from signal_detector import detect_signal_color
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --- Flask App ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))  # Use Render env variable
login_manager = LoginManager()
login_manager.init_app(app)

# --- Twilio Setup ---
account_sid = os.environ.get("TWILIO_SID")
auth_token = os.environ.get("TWILIO_AUTH")
twilio_client = Client(account_sid, auth_token)
twilio_whatsapp_from = os.environ.get("TWILIO_WHATSAPP_FROM")
twilio_whatsapp_to = os.environ.get("TWILIO_WHATSAPP_TO")

# --- Camera ---
#camera_url = 0  # Default webcam. Change to IP camera URL if needed.

# --- User Model ---
class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {
    "Traffic": {"password": "Traffic123"}
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# --- Database ---
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

def log_status(status):
    conn = sqlite3.connect("traffic_log.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, status) VALUES (?, ?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status))
    conn.commit()
    conn.close()

def get_history(limit=100):
    conn = sqlite3.connect("traffic_log.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, status FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    history = c.fetchall()
    conn.close()
    return history
 # List of images
image_files = [
    "static\darkgreen.webp",
    "static\darkred.png",
    "static\darkyellow.jpg",
    "static\malfunction_20250505_193020.jpg",
    "static\lightgreen.png",
    "static\lightred.jpg",
    "static\lightyellow.jpg",
    "static\malfunction_20250505_193016.jpg",
    ]
    # Index to track current image
image_index = 0

def get_next_image():
    global image_index
    img_path = image_files[image_index]
    image_index = (image_index + 1) % len(image_files)
    return img_path


# --- Routes ---
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

@app.route('/')
@login_required
def dashboard():
    # Read the image
    image_path = get_next_image()
    frame = cv2.imread(image_path)
    """cap = cv2.VideoCapture(camera_url)
    ret, frame = cap.read()
    cap.release() """
    
    if frame is None:
        status = "Camera Error"
        signal = None
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

# --- Run App ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render requires dynamic port
    app.run(host="0.0.0.0", port=port, debug=True)
