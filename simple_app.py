from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import sqlite3
from datetime import datetime
import pandas as pd
import io
import csv
import os
import json
from pathlib import Path
import calendar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import random
import hashlib

app = Flask(__name__)
app.secret_key = 'weather-dashboard-secret-key'
UPLOAD_FOLDER = "uploads"
DATA_FOLDER = "data"
STATIC_FOLDER = "static"
DATABASE = "climate_data.db"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# ------------------ LOGIN MANAGER SETUP ------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ------------------ DATABASE SETUP ------------------
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS climate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            temperature REAL,
            humidity REAL,
            gdd REAL,
            city TEXT
        )
    ''')
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create devices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            api_key TEXT NOT NULL,
            device_type TEXT DEFAULT 'ESP8266',
            last_connection TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create readings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            temperature REAL,
            humidity REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Simple User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return User(id=str(user[0]), name=user[1], email=user[2])
    return None

# ------------------ UTILS ------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------ DASHBOARD ------------------
@app.route('/')
def index():
    return render_template("dashboard.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE email = ? AND password = ?", 
                      (email, hashlib.sha256(password.encode()).hexdigest()))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user = User(id=str(user[0]), name=user[1], email=user[2])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        conn.close()
        
        if existing_user:
            flash('Email already exists', 'danger')
        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", 
                          (name, email, hashed_password))
            conn.commit()
            conn.close()
            flash('User created successfully', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/google_login')
def google_login():
    # This would normally use Flask-Dance or similar to handle Google OAuth
    # For now, we'll just simulate a Google login with a placeholder user
    flash('Fonctionnalité Google Login à implémenter avec OAuth réel', 'warning')
    
    # Create a demo Google user for testing
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", ('google_user@example.com',))
    existing_user = cursor.fetchone()
    
    if not existing_user:
        # Create a Google user if it doesn't exist
        hashed_password = hashlib.sha256('google_secure_password'.encode()).hexdigest()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", 
                      ('Google User', 'google_user@example.com', hashed_password))
        conn.commit()
        cursor.execute("SELECT id, name, email FROM users WHERE email = ?", ('google_user@example.com',))
        user_data = cursor.fetchone()
    else:
        # Get existing Google user
        cursor.execute("SELECT id, name, email FROM users WHERE email = ?", ('google_user@example.com',))
        user_data = cursor.fetchone()
    
    conn.close()
    
    # Log in the Google user
    user = User(id=str(user_data[0]), name=user_data[1], email=user_data[2])
    login_user(user)
    
    flash('Connecté via Google (simulation)', 'success')
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # In a real application, you would:
            # 1. Generate a password reset token
            # 2. Store it in the database with an expiration time
            # 3. Send an email with a reset link
            
            # For this demo, we'll just show a success message
            flash('Si ce compte existe, un email de réinitialisation a été envoyé. Vérifiez votre boîte de réception.', 'success')
        else:
            # For security, don't reveal if the email exists or not
            flash('Si ce compte existe, un email de réinitialisation a été envoyé. Vérifiez votre boîte de réception.', 'success')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/data')
def get_data():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time, temperature, humidity, gdd, city FROM climate WHERE date = ?", (today,))
    rows = cursor.fetchall()
    conn.close()
    result = [
        {"time": row[0], "temperature": row[1], "humidity": row[2], "gdd": row[3], "city": row[4]}
        for row in rows
    ]
    return jsonify(result)

@app.route('/export-csv')
def export_csv():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time, temperature, humidity, gdd, city FROM climate WHERE date = ?", (today,))
    rows = cursor.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Time', 'Temperature (°C)', 'Humidity (%)', 'GDD', 'City'])
    writer.writerows(rows)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name=f'data_{today}.csv')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'})
    
    if file:
        # For demonstration, we'll just save the file and return success
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        # In a real app, you would process the file here
        # For example, parse CSV data and insert into database
        
        return jsonify({
            'success': True, 
            'message': f'Fichier {file.filename} importé avec succès!',
            'filename': file.filename
        })
    
    return jsonify({'success': False, 'message': 'Une erreur est survenue lors de l\'importation'})

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    current_year = datetime.now().year
    current_month = datetime.now().month
    station = request.form.get('station') if request.method == 'POST' else None
    year = int(request.form.get('year')) if request.method == 'POST' and request.form.get('year') else current_year
    month = int(request.form.get('month')) if request.method == 'POST' and request.form.get('month') else None
    
    data = []
    error = None
    
    if request.method == 'POST' and station and month:
        # This is a placeholder - actual data processing would go here
        # For now, just return the template with empty data to avoid errors
        pass
        
    return render_template('analysis.html', 
                          station=station, 
                          year=year, 
                          month=month, 
                          current_year=current_year,
                          data=data,
                          error=error)

@app.route('/download')
def download():
    file_type = request.args.get('file_type', 'csv')
    station = request.args.get('station')
    year = request.args.get('year')
    month = request.args.get('month')
    
    # This is a placeholder - actual file download logic would go here
    # For now, just return a message
    return f"Download {file_type} for {station} ({month}/{year}) - Feature coming soon"

@app.route('/iot_dashboard')
def iot_dashboard():
    init_db()
    # Retrieve devices from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, location, api_key, created_at, 
               device_type, last_connection 
        FROM devices 
        WHERE user_id = ?
    """, (current_user.id if current_user.is_authenticated else None,))
    devices = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries for template
    device_list = []
    for device in devices:
        device_list.append({
            'id': device[0],
            'name': device[1],
            'location': device[2],
            'api_key': device[3],
            'created_at': device[4],
            'device_type': device[5] or 'ESP8266',
            'last_connection': device[6]
        })
    
    return render_template('iot.html', devices=device_list)

@app.route('/add_device', methods=['POST'])
@login_required
def add_device():
    name = request.form.get('name')
    location = request.form.get('location')
    device_type = request.form.get('device_type', 'ESP8266')
    
    if not name:
        flash('Le nom de l\'appareil est requis', 'danger')
        return redirect(url_for('iot_dashboard'))
    
    # Generate a unique API key
    api_key = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO devices (name, location, device_type, api_key, user_id) VALUES (?, ?, ?, ?, ?)",
        (name, location, device_type, api_key, current_user.id)
    )
    conn.commit()
    conn.close()
    
    flash('Appareil ajouté avec succès', 'success')
    return redirect(url_for('iot_dashboard'))

@app.route('/device/<int:device_id>')
@login_required
def view_device(device_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, location, api_key, created_at FROM devices WHERE id = ? AND user_id = ?", 
                  (device_id, current_user.id))
    device = cursor.fetchone()
    
    if not device:
        flash('Appareil non trouvé', 'danger')
        return redirect(url_for('iot_dashboard'))
    
    # Get readings for this device
    cursor.execute("SELECT temperature, humidity, timestamp FROM readings WHERE device_id = ? ORDER BY timestamp DESC LIMIT 100", 
                  (device_id,))
    readings = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries for template
    reading_list = []
    for reading in readings:
        reading_list.append({
            'temperature': reading[0],
            'humidity': reading[1],
            'timestamp': reading[2]
        })
    
    device_data = {
        'id': device[0],
        'name': device[1],
        'location': device[2],
        'api_key': device[3],
        'created_at': device[4]
    }
    
    return render_template('device.html', device=device_data, readings=reading_list)

@app.route('/generate_api_key')
@login_required
def generate_api_key():
    # Generate a unique API key
    api_key = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))
    return jsonify({'api_key': api_key})

@app.route('/insight')
def insight():
    return render_template('insights.html')

# ------------------ API ENDPOINTS ------------------
@app.route('/api/auth', methods=['POST'])
def api_auth():
    """Authenticate a device using its API key"""
    data = request.get_json()
    
    if not data or 'api_key' not in data:
        return jsonify({"error": "API key is required"}), 400
        
    api_key = data.get('api_key')
    
    # Check if API key is valid
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM devices WHERE api_key = ?", (api_key,))
    device = cursor.fetchone()
    conn.close()
    
    if not device:
        return jsonify({"error": "Invalid API key"}), 403
        
    return jsonify({
        "success": True, 
        "device_id": device[0],
        "device_name": device[1],
        "message": "Device authenticated successfully"
    }), 200

@app.route('/api/data', methods=['POST'])
def api_data():
    """Receive data from an IoT device"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    required_fields = ['api_key', 'temperature', 'humidity']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
            
    api_key = data.get('api_key')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Check if API key is valid and get device ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM devices WHERE api_key = ?", (api_key,))
    device = cursor.fetchone()
    
    if not device:
        conn.close()
        return jsonify({"error": "Invalid API key"}), 403
        
    device_id = device[0]
    
    # Store the data in the database
    cursor.execute(
        "INSERT INTO readings (device_id, temperature, humidity, timestamp) VALUES (?, ?, ?, ?)",
        (device_id, temperature, humidity, timestamp)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "Data received and stored successfully"
    }), 200

@app.route('/api/device_data/<int:device_id>')
@login_required
def api_device_data(device_id):
    """Get the latest data for a specific device"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify device belongs to the current user
    cursor.execute("SELECT id FROM devices WHERE id = ? AND user_id = ?", 
                  (device_id, current_user.id))
    device = cursor.fetchone()
    
    if not device:
        conn.close()
        return jsonify({"error": "Device not found or unauthorized"}), 404
    
    # Get the latest 100 readings
    cursor.execute("""
        SELECT temperature, humidity, timestamp 
        FROM readings 
        WHERE device_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 100
    """, (device_id,))
    readings = cursor.fetchall()
    conn.close()
    
    reading_list = []
    for reading in readings:
        reading_list.append({
            'temperature': reading[0],
            'humidity': reading[1],
            'timestamp': reading[2]
        })
    
    return jsonify({"success": True, "readings": reading_list}), 200

@app.route('/export_device_data/<int:device_id>')
@login_required
def export_device_data(device_id):
    """Export device readings as CSV or JSON"""
    # Get export parameters
    date_range = request.args.get('range', 'all')
    file_format = request.args.get('format', 'csv')
    
    # Validate the device belongs to current user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM devices WHERE id = ? AND user_id = ?", 
                  (device_id, current_user.id))
    device = cursor.fetchone()
    
    if not device:
        conn.close()
        flash('Appareil non trouvé', 'danger')
        return redirect(url_for('iot_dashboard'))
    
    device_name = device[0]
    
    # Determine date filter based on range
    date_filter = ""
    if date_range != 'all':
        days = int(date_range)
        date_filter = f"AND datetime(timestamp) >= datetime('now', '-{days} days')"
    
    # Get readings
    cursor.execute(f"""
        SELECT temperature, humidity, timestamp 
        FROM readings 
        WHERE device_id = ? {date_filter}
        ORDER BY timestamp DESC
    """, (device_id,))
    readings = cursor.fetchall()
    conn.close()
    
    if not readings:
        flash('Aucune donnée disponible pour l\'exportation', 'warning')
        return redirect(url_for('view_device', device_id=device_id))
    
    # Export as CSV
    if file_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Temperature (°C)', 'Humidity (%)'])
        writer.writerows(readings)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{device_name}_data_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    # Export as JSON
    elif file_format == 'json':
        json_data = []
        for reading in readings:
            json_data.append({
                'timestamp': reading[2],
                'temperature': reading[0],
                'humidity': reading[1]
            })
        
        return send_file(
            io.BytesIO(json.dumps(json_data, indent=2).encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'{device_name}_data_{datetime.now().strftime("%Y%m%d")}.json'
        )
    
    # Invalid format
    flash('Format d\'exportation non valide', 'danger')
    return redirect(url_for('view_device', device_id=device_id))

@app.route('/delete_device/<int:device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    """Delete a device and all its readings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify device belongs to current user
    cursor.execute("SELECT id FROM devices WHERE id = ? AND user_id = ?", 
                  (device_id, current_user.id))
    device = cursor.fetchone()
    
    if not device:
        conn.close()
        flash('Appareil non trouvé', 'danger')
        return redirect(url_for('iot_dashboard'))
    
    # Delete all readings for this device
    cursor.execute("DELETE FROM readings WHERE device_id = ?", (device_id,))
    
    # Delete the device
    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    
    conn.commit()
    conn.close()
    
    flash('Appareil supprimé avec succès', 'success')
    return redirect(url_for('iot_dashboard'))

# ------------------ LANCEMENT ------------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
