from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import pandas as pd
import requests
import io
import csv
import os
import secrets
import json
from pathlib import Path
from fpdf import FPDF
import calendar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_dance.contrib.google import make_google_blueprint, google
from models import db, User, Device, Reading
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'weather-dashboard-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth configuration
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Initialize Google blueprint
google_bp = make_google_blueprint(
    client_id=app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret=app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
    scope=["profile", "email"],
    redirect_to="google_login_callback"
)
app.register_blueprint(google_bp, url_prefix="/login")

# Folders setup
UPLOAD_FOLDER = "uploads"
DATA_FOLDER = "data"
STATIC_FOLDER = "static"
DATABASE = "climate_data.db"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# ------------------ USER MANAGEMENT ------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/google-login')
def google_login():
    return redirect(url_for('google.login'))

@app.route('/login/google/authorized')
def google_login_callback():
    if not google.authorized:
        flash("Échec de l'authentification Google.", "danger")
        return redirect(url_for('login'))
    
    resp = google.get('/oauth2/v2/userinfo')
    if resp.ok:
        google_info = resp.json()
        google_id = google_info['id']
        email = google_info.get('email', '')
        name = google_info.get('name', '')
        
        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            # Create new user
            user = User(google_id=google_id, email=email, name=name)
            db.session.add(user)
            db.session.commit()
        
        # Login user
        login_user(user)
        flash(f"Bienvenue, {name}!", "success")
        return redirect(url_for('index'))
    
    flash("Impossible de récupérer vos informations Google.", "danger")
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('login'))

@app.route('/generate-api-key')
@login_required
def generate_api_key():
    # Generate a secure API key
    api_key = secrets.token_hex(32)
    current_user.api_key = api_key
    db.session.commit()
    return jsonify({"api_key": api_key})

# ------------------ UTILS ------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db.create_all()
    
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
    conn.commit()
    conn.close()

# ------------------ API COLLECTE ------------------
@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    
    # Check API key if provided
    api_key = request.headers.get('X-API-Key')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            # Save data to device readings if user exists
            device_id = data.get('device_id')
            if device_id:
                device = Device.query.filter_by(id=device_id, user_id=user.id).first()
                if device:
                    reading = Reading(
                        timestamp=now,
                        temperature=data.get('temperature'),
                        humidity=data.get('humidity'),
                        pressure=data.get('pressure'),
                        rainfall=data.get('rainfall'),
                        wind_speed=data.get('wind_speed'),
                        wind_direction=data.get('wind_direction'),
                        device_id=device.id
                    )
                    db.session.add(reading)
                    db.session.commit()
    
    # Also save to climate table for backward compatibility
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO climate (date, time, temperature, humidity, gdd, city)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        date, time, data.get('temperature'), data.get('humidity'), data.get('gdd', 0), data.get('city', 'N/A')
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200

@app.route('/api/today', methods=['GET'])
def get_today_data():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT time, temperature, humidity, city, gdd FROM climate WHERE date = ?", (today,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([
        {"time": row[0], "temperature": row[1], "humidity": row[2], "city": row[3], "gdd": row[4]} for row in rows
    ])

# ------------------ DASHBOARD ------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return render_template("dashboard.html", current_time=current_time)
    else:
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
@login_required
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

# ------------------ IOT DEVICES ------------------
@app.route('/iot')
@login_required
def iot_dashboard():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    # List of supported microcontrollers
    microcontrollers = [
        {"name": "ESP32", "description": "Microcontrôleur dual-core avec WiFi et Bluetooth", "image": "esp32.jpg"},
        {"name": "ESP8266", "description": "Microcontrôleur WiFi à bas coût", "image": "esp8266.jpg"},
        {"name": "Arduino MKR WiFi 1010", "description": "Arduino avec connectivité WiFi", "image": "arduino_mkr.jpg"},
        {"name": "Raspberry Pi Pico W", "description": "Microcontrôleur à bas coût avec WiFi", "image": "pico_w.jpg"},
        {"name": "Arduino Uno + Shield WiFi", "description": "Arduino classique avec shield WiFi", "image": "arduino_uno.jpg"}
    ]
    return render_template('iot.html', devices=devices, microcontrollers=microcontrollers)

@app.route('/iot/add', methods=['POST'])
@login_required
def add_device():
    name = request.form.get('name')
    device_type = request.form.get('device_type')
    location = request.form.get('location')
    
    if not name or not device_type:
        flash("Nom et type de l'appareil requis.", "danger")
        return redirect(url_for('iot_dashboard'))
    
    # Create new device
    device = Device(
        name=name,
        device_type=device_type,
        location=location,
        user_id=current_user.id
    )
    db.session.add(device)
    db.session.commit()
    
    flash("Appareil ajouté avec succès!", "success")
    return redirect(url_for('iot_dashboard'))

@app.route('/iot/device/<int:device_id>')
@login_required
def device_detail(device_id):
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first_or_404()
    readings = Reading.query.filter_by(device_id=device.id).order_by(Reading.timestamp.desc()).limit(100).all()
    return render_template('device.html', device=device, readings=readings)

# ------------------ AI INSIGHTS ------------------
@app.route('/insights')
@login_required
def insights():
    # Check if user has devices with readings
    devices = Device.query.filter_by(user_id=current_user.id).all()
    has_data = False
    for device in devices:
        if Reading.query.filter_by(device_id=device.id).count() > 0:
            has_data = True
            break
    
    return render_template('insights.html', has_data=has_data, devices=devices)

@app.route('/insights/analyze', methods=['POST'])
@login_required
def analyze_data():
    device_id = request.form.get('device_id')
    analysis_type = request.form.get('analysis_type')
    
    if not device_id or not analysis_type:
        return jsonify({"error": "Paramètres manquants"}), 400
    
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()
    if not device:
        return jsonify({"error": "Appareil non trouvé"}), 404
    
    readings = Reading.query.filter_by(device_id=device.id).order_by(Reading.timestamp).all()
    if not readings:
        return jsonify({"error": "Pas de données disponibles"}), 404
    
    # Convert readings to pandas DataFrame
    data = []
    for reading in readings:
        data.append({
            'timestamp': reading.timestamp,
            'temperature': reading.temperature,
            'humidity': reading.humidity,
            'pressure': reading.pressure,
            'rainfall': reading.rainfall,
            'wind_speed': reading.wind_speed,
            'wind_direction': reading.wind_direction
        })
    
    df = pd.DataFrame(data)
    
    # Perform different analyses based on type
    results = {}
    if analysis_type == 'basic':
        # Basic statistics
        results = {
            'temperature': {
                'min': df['temperature'].min(),
                'max': df['temperature'].max(),
                'avg': df['temperature'].mean(),
                'trend': 'up' if df['temperature'].iloc[-1] > df['temperature'].iloc[0] else 'down'
            },
            'humidity': {
                'min': df['humidity'].min(),
                'max': df['humidity'].max(),
                'avg': df['humidity'].mean(),
                'trend': 'up' if df['humidity'].iloc[-1] > df['humidity'].iloc[0] else 'down'
            }
        }
    elif analysis_type == 'weather_patterns':
        # Weather patterns analysis (simplified)
        results = {
            'rainy_days': (df['rainfall'] > 0).sum(),
            'dry_days': (df['rainfall'] == 0).sum(),
            'avg_rainfall': df['rainfall'].mean(),
            'temp_humidity_correlation': df['temperature'].corr(df['humidity']) if 'humidity' in df else None
        }
    elif analysis_type == 'trends':
        # Simple trend analysis
        temp_trend = 'stable'
        if df['temperature'].iloc[-1] > df['temperature'].iloc[0] * 1.1:
            temp_trend = 'increasing'
        elif df['temperature'].iloc[-1] < df['temperature'].iloc[0] * 0.9:
            temp_trend = 'decreasing'
        
        humid_trend = 'stable'
        if df['humidity'].iloc[-1] > df['humidity'].iloc[0] * 1.1:
            humid_trend = 'increasing'
        elif df['humidity'].iloc[-1] < df['humidity'].iloc[0] * 0.9:
            humid_trend = 'decreasing'
        
        results = {
            'temperature_trend': temp_trend,
            'humidity_trend': humid_trend,
            'data_period': f"{df['timestamp'].min()} to {df['timestamp'].max()}"
        }
    elif analysis_type == 'chatgpt':
        # This would normally call OpenAI API but for simplicity, return a mock response
        results = {
            'analysis': "Basé sur les données météo collectées, nous observons une tendance à l'augmentation de la température sur la période étudiée. Les niveaux d'humidité restent relativement stables, ce qui suggère un temps sec et chaud. Il pourrait être judicieux de surveiller les conditions d'arrosage si vous avez des cultures. Les prévisions suggèrent que cette tendance pourrait se poursuivre dans les prochains jours."
        }
    
    return jsonify(results)

# ------------------ UPLOAD ------------------
@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier sélectionné."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Fichier invalide."}), 400
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "json"]:
        return jsonify({"error": "Format non supporté. Veuillez uploader un fichier CSV ou JSON."}), 400
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)
    try:
        if file_ext == "csv":
            df = pd.read_csv(file_path, delimiter=";", encoding="utf-8")
        else:
            df = pd.read_json(file_path)
        # Optionnel : insérer dans la base
        for _, row in df.iterrows():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO climate (date, time, temperature, humidity, gdd, city)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                row.get('Date') or row.get('date'),
                row.get('Heure') or row.get('time'),
                row.get('Température (°C)') or row.get('temperature'),
                row.get('Humidité (%)') or row.get('humidity'),
                row.get('GDD') or row.get('gdd', 0),
                row.get('city', 'N/A')
            ))
            conn.commit()
            conn.close()
        return jsonify({"success": "Fichier chargé avec succès."})
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la lecture du fichier : {str(e)}"}), 500

# ------------------ DAILY ANALYSIS ------------------
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def get_weather_data(station, date):
    base_url = "https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/donnees-synop-essentielles-omm@public/records"
    all_data = []
    offset = 0
    limit = 100
    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "where": f"date >= '{date}T00:00:00Z' AND date <= '{date}T23:59:59Z' AND nom = '{station}'",
            "sort": "date"
        }
        try:
            response = requests.get(base_url, params=params, timeout=25)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                break
            all_data.extend(results)
            offset += limit
        except requests.Timeout:
            break
        except requests.RequestException:
            break
    return [entry for entry in all_data if station.upper() in entry.get("nom", "").upper()]

def process_daily_data(data):
    records = []
    for record in data:
        date_time = record.get("date", "")
        if not date_time:
            continue
        records.append({
            "Date": date_time.split("T")[0],
            "Heure": date_time.split("T")[1][:5],
            "Température (°C)": round(record.get("tc"), 1) if record.get("tc") is not None else None,
            "Humidité (%)": record.get("u"),
            "Précipitations (mm)": record.get("rr1")
        })
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["Heure"] = pd.to_datetime(df["Heure"], format="%H:%M", errors="coerce").dt.strftime("%H:%M")
    df.sort_values(by=["Date", "Heure"], inplace=True)
    df["Température (°C)"] = df["Température (°C)"].interpolate(method="linear")
    df["Humidité (%)"] = df["Humidité (%)"].interpolate(method="linear")
    df.dropna(subset=["Température (°C)", "Humidité (%)"], inplace=True)
    return df

@app.route("/daily", methods=["GET", "POST"])
@login_required
def daily():
    current_datetime = datetime.now()
    context = {
        "current_date": current_datetime.strftime("%Y-%m-%d"),
        "current_time": current_datetime.strftime("%H:%M"),
        "current_month_name": current_datetime.strftime("%B"),
        "current_year": current_datetime.year,
        "station": None
    }
    if request.method == "POST":
        station = request.form["station"].upper()
        date = request.form["date"]
        context["station"] = station
        if not is_valid_date(date):
            return render_template("daily.html", error="Date invalide (YYYY-MM-DD)", **context)
        data = get_weather_data(station, date)
        if not data:
            return render_template("daily.html", error="Aucune donnée trouvée pour cette date.", **context)
        df = process_daily_data(data)
        if df.empty:
            return render_template("daily.html", error="Aucune donnée exploitable.", **context)
        return render_template("daily.html", data=df.to_dict(orient="records"), station=station, date=date, **context)
    return render_template("daily.html", **context)

# ------------------ MONTHLY ANALYSIS ------------------
def get_monthly_weather_data(station, year, month):
    base_url = "https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/donnees-synop-essentielles-omm@public/exports/json"
    last_day = calendar.monthrange(year, month)[1]
    date_prefix = f"{year}-{month:02d}"
    params = {
        "refine.nom": station,
        "where": f"date >= '{date_prefix}-01T00:00:00Z' AND date <= '{date_prefix}-{last_day}T23:59:59Z'",
        "timezone": "UTC"
    }
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data:
            return []
        return data
    except requests.RequestException:
        return []

def process_weather_data(data):
    records = []
    for record in data:
        date_time = record.get("date", "")
        if not date_time:
            continue
        records.append({
            "Date": date_time.split("T")[0],
            "Température min (°C)": record.get("tn12c"),
            "Température max (°C)": record.get("tx12c"),
            "Humidité (%)": record.get("u")
        })
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df = df.groupby("Date").agg({
        "Température min (°C)": "min",
        "Température max (°C)": "max",
        "Humidité (%)": "mean"
    }).reset_index()
    return df

def calculate_gdd(df, tbase=10):
    df["GDD"] = ((df["Température min (°C)"] + df["Température max (°C)"]) / 2) - tbase
    df["GDD"] = df["GDD"].apply(lambda x: max(0, x))
    df["GDD cumulés"] = df["GDD"].cumsum()
    return df

def plot_gdd(df, station, year, month):
    if "GDD cumulés" not in df.columns:
        return
    static_dir = Path(STATIC_FOLDER)
    static_dir.mkdir(exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(df["Date"], df["GDD cumulés"], marker='o', color='green')
    plt.title(f"GDD cumulés - {station} ({month}/{year})")
    plt.xlabel("Date")
    plt.ylabel("GDD cumulés")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid()
    plot_path = static_dir / "gdd_plot.png"
    plt.savefig(plot_path)
    plt.close()

def save_data(df, station, year, month, format="csv"):
    data_dir = Path(DATA_FOLDER)
    data_dir.mkdir(exist_ok=True)
    file_path = data_dir / f"weather_{station}_{year}_{month}.{format}"
    if format == "csv":
        df.to_csv(file_path, index=False, sep=";", encoding="utf-8")
    elif format == "json":
        df.to_json(file_path, orient="records", indent=4, force_ascii=False)
    return file_path

def generate_pdf(df, station, year, month):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Rapport météo - {station} ({month}/{year})", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for index, row in df.iterrows():
        line = f"{row['Date']} - Temp Min: {row['Température min (°C)']}°C, Temp Max: {row['Température max (°C)']}°C, Humidité: {row['Humidité (%)']}%"
        pdf.multi_cell(0, 10, line)
    plot_path = f"{STATIC_FOLDER}/gdd_plot.png"
    if os.path.exists(plot_path):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Graphique des GDD cumulés", ln=True, align="C")
        pdf.ln(5)
        pdf.image(plot_path, x=10, w=190)
    file_path = f"{DATA_FOLDER}/weather_{station}_{year}_{month}.pdf"
    pdf.output(file_path)
    return file_path if os.path.exists(file_path) else None

@app.route("/analysis", methods=["GET", "POST"])
@login_required
def analysis():
    if request.method == "POST":
        station = request.form["station"].upper()
        year = int(request.form["year"])
        month = int(request.form["month"])
        data = get_monthly_weather_data(station, year, month)
        if not data:
            return render_template("analysis.html", error="Aucune donnée trouvée.")
        df = process_weather_data(data)
        if df.empty:
            return render_template("analysis.html", error="Aucune donnée exploitable.")
        df = calculate_gdd(df)
        save_data(df, station, year, month, "csv")
        save_data(df, station, year, month, "json")
        plot_gdd(df, station, year, month)
        return render_template("analysis.html", data=df.to_dict(orient="records"), station=station, year=year, month=month)
    return render_template("analysis.html")

@app.route("/download/<file_type>/<station>/<year>/<month>")
@login_required
def download(file_type, station, year, month):
    if file_type == "pdf":
        file_path_csv = f"{DATA_FOLDER}/weather_{station}_{year}_{month}.csv"
        if not os.path.exists(file_path_csv):
            return "CSV introuvable pour générer le PDF", 404
        df = pd.read_csv(file_path_csv, delimiter=";")
        file_path = generate_pdf(df, station, year, month)
    else:
        file_path = f"{DATA_FOLDER}/weather_{station}_{year}_{month}.{file_type}"
    if not os.path.exists(file_path):
        return "Fichier non trouvé", 404
    return send_file(file_path, as_attachment=True)

@app.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('register.html')

# Remplacer la route forgot_password précédente par celle-ci

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Ici vous pourriez implémenter l'envoi d'email de réinitialisation
            flash('Si cette adresse email existe dans notre base de données, vous recevrez les instructions de réinitialisation.', 'info')
        else:
            # On envoie le même message pour ne pas divulguer si l'email existe ou non
            flash('Si cette adresse email existe dans notre base de données, vous recevrez les instructions de réinitialisation.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')
# ------------------ LANCEMENT ------------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
