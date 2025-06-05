"""
Script pour générer des données directement dans la base SQLite pour la fonctionnalité AI Insights
"""
import sqlite3
import os
import random
import numpy as np
from datetime import datetime, timedelta
import uuid

# Constantes pour la génération de données
CITIES = ["Paris", "Lyon", "Marseille", "Bordeaux", "Lille", "Strasbourg"]
START_DATE = datetime.now() - timedelta(days=60)  # 60 jours de données
END_DATE = datetime.now()
HOURLY_READINGS = False  # Générer des lectures toutes les 3 heures pour limiter le volume

# Paramètres météorologiques moyens
TEMP_MEAN = 20
TEMP_STD = 5
HUMIDITY_MEAN = 65
HUMIDITY_STD = 15
PRESSURE_MEAN = 1013
PRESSURE_STD = 5
RAINFALL_PROB = 0.3
RAINFALL_MEAN = 2
RAINFALL_STD = 4
WIND_SPEED_MEAN = 15
WIND_SPEED_STD = 8
WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Chemins des bases de données
CLIMATE_DB = 'climate_data.db'
FLASK_DB = 'weather_dashboard.db'

def create_daily_pattern(base_temp, std_dev):
    """Crée un modèle journalier avec une température plus basse la nuit et plus élevée en journée"""
    hours = range(24)
    daily_pattern = []
    
    for hour in hours:
        # Modification diurne - plus chaud l'après-midi, plus frais la nuit
        if 0 <= hour < 6:
            # Nuit - plus frais
            temp_offset = -2
        elif 6 <= hour < 10:
            # Matin - réchauffement
            temp_offset = -1 + (hour - 6) * 0.5
        elif 10 <= hour < 16:
            # Après-midi - plus chaud
            temp_offset = 2
        elif 16 <= hour < 21:
            # Soir - refroidissement
            temp_offset = 2 - (hour - 16) * 0.5
        else:
            # Nuit - refroidissement continu
            temp_offset = 0 - (hour - 21) * 0.4
        
        # Ajouter un peu de bruit aléatoire
        noise = np.random.normal(0, std_dev * 0.3)
        daily_pattern.append(base_temp + temp_offset + noise)
    
    return daily_pattern

def generate_weather_data():
    """Génère des données météorologiques simulées"""
    data = []
    current_date = START_DATE
    
    # Créer des motifs quotidiens pour chaque ville
    city_base_temps = {city: TEMP_MEAN + random.uniform(-3, 3) for city in CITIES}
    
    print(f"Génération de données depuis {START_DATE.strftime('%Y-%m-%d')} jusqu'à {END_DATE.strftime('%Y-%m-%d')}")
    
    # Pour chaque jour dans la plage
    day_count = 0
    while current_date <= END_DATE:
        for city in CITIES:
            base_temp = city_base_temps[city]
            # Créer un motif quotidien pour cette ville-jour
            daily_pattern = create_daily_pattern(base_temp, TEMP_STD)
            
            # Générer des données pour chaque heure ou à des intervalles de 3 heures
            hours = range(0, 24, 3 if not HOURLY_READINGS else 1)
            
            for hour in hours:
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                
                # Simuler des paramètres météo
                temp = daily_pattern[hour]
                humidity = np.clip(np.random.normal(HUMIDITY_MEAN, HUMIDITY_STD), 0, 100)
                pressure = np.random.normal(PRESSURE_MEAN, PRESSURE_STD)
                
                # Pluie aléatoire (plus probable quand l'humidité est élevée)
                rain_modifier = (humidity - 50) / 50  # -1 à 1
                rainfall_probability = np.clip(RAINFALL_PROB + (rain_modifier * 0.2), 0, 1)
                rainfall = np.random.exponential(RAINFALL_MEAN) if random.random() < rainfall_probability else 0
                
                # Vent
                wind_speed = max(0, np.random.normal(WIND_SPEED_MEAN, WIND_SPEED_STD))
                wind_direction = random.choice(WIND_DIRECTIONS)
                
                data.append({
                    'city': city,
                    'date': timestamp.strftime('%Y-%m-%d'),
                    'time': timestamp.strftime('%H:%M:%S'),
                    'timestamp': timestamp,
                    'temperature': round(temp, 1),
                    'humidity': round(humidity, 1),
                    'pressure': round(pressure, 1),
                    'rainfall': round(rainfall, 1),
                    'wind_speed': round(wind_speed, 1),
                    'wind_direction': wind_direction,
                    'gdd': round(max(0, ((temp - 2 + temp + 2) / 2) - 10), 2)  # GDD avec base 10°C
                })
        
        # Passer au jour suivant
        current_date += timedelta(days=1)
        day_count += 1
        if day_count % 10 == 0:
            print(f"Génération en cours: {day_count} jours générés...")
    
    return data

def setup_flask_db():
    """Crée et configure la base de données Flask-SQLAlchemy"""
    conn = sqlite3.connect(FLASK_DB)
    cursor = conn.cursor()
    
    # Créer les tables si elles n'existent pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        google_id TEXT UNIQUE,
        api_key TEXT UNIQUE,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        device_type TEXT NOT NULL,
        location TEXT,
        last_connection TIMESTAMP,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reading (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP NOT NULL,
        temperature REAL,
        humidity REAL,
        pressure REAL,
        rainfall REAL,
        wind_speed REAL,
        wind_direction TEXT,
        device_id INTEGER NOT NULL,
        FOREIGN KEY (device_id) REFERENCES device (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def save_to_flask_db(data):
    """Sauvegarde les données directement dans la base SQLite pour Flask"""
    conn = sqlite3.connect(FLASK_DB)
    cursor = conn.cursor()
    
    # Nettoyer les données existantes
    print("Suppression des anciennes données...")
    cursor.execute("DELETE FROM reading")
    cursor.execute("DELETE FROM device")
    cursor.execute("DELETE FROM user")
    conn.commit()
    
    # Ajouter un utilisateur test
    api_key = str(uuid.uuid4()).replace('-', '')
    cursor.execute('''
    INSERT INTO user (email, name, api_key, is_active)
    VALUES (?, ?, ?, 1)
    ''', ('test@example.com', 'Utilisateur Test', api_key))
    user_id = cursor.lastrowid
    print(f"Utilisateur test créé avec ID: {user_id}")
    
    # Ajouter des appareils pour chaque ville
    device_ids = {}
    for city in CITIES:
        cursor.execute('''
        INSERT INTO device (name, device_type, location, last_connection, user_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (f'Station {city}', 'WeatherStation', city, datetime.now().isoformat(), user_id))
        device_id = cursor.lastrowid
        device_ids[city] = device_id
        print(f"Appareil créé pour {city} avec ID: {device_id}")
    
    conn.commit()
    
    # Insérer les lectures
    total_readings = len(data)
    print(f"Insertion de {total_readings} lectures...")
    
    batch_size = 100
    for i, item in enumerate(data):
        city = item['city']
        device_id = device_ids[city]
        
        cursor.execute('''
        INSERT INTO reading (timestamp, temperature, humidity, pressure, rainfall, wind_speed, wind_direction, device_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['timestamp'].isoformat(),
            item['temperature'],
            item['humidity'],
            item['pressure'],
            item['rainfall'],
            item['wind_speed'],
            item['wind_direction'],
            device_id
        ))
        
        # Commit par lots
        if (i + 1) % batch_size == 0:
            conn.commit()
            progress = (i + 1) / total_readings * 100
            print(f"  - Progression: {progress:.1f}% ({i + 1}/{total_readings})")
    
    # Commit final
    conn.commit()
    conn.close()
    print(f"Toutes les données ont été sauvegardées ({total_readings} lectures)")

def save_to_climate_db(data):
    """Sauvegarde les données dans la base climate_data.db"""
    conn = sqlite3.connect(CLIMATE_DB)
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS climate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            temperature REAL,
            humidity REAL,
            gdd REAL,
            city TEXT,
            pressure REAL,
            rainfall REAL,
            wind_speed REAL,
            wind_direction TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertion des données
    total_readings = len(data)
    print(f"Insertion de {total_readings} lectures dans climate_data.db...")
    
    batch_size = 100
    for i, item in enumerate(data):
        cursor.execute('''
            INSERT INTO climate (date, time, temperature, humidity, gdd, city, pressure, rainfall, wind_speed, wind_direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['date'], 
            item['time'], 
            item['temperature'], 
            item['humidity'], 
            item['gdd'], 
            item['city'],
            item['pressure'],
            item['rainfall'],
            item['wind_speed'],
            item['wind_direction']
        ))
        
        # Commit par lots
        if (i + 1) % batch_size == 0:
            conn.commit()
            progress = (i + 1) / total_readings * 100
            print(f"  - Progression: {progress:.1f}% ({i + 1}/{total_readings})")
    
    conn.commit()
    conn.close()
    print(f"Données sauvegardées dans la table 'climate' ({total_readings} entrées)")

if __name__ == "__main__":
    print("Démarrage de la génération de données pour AI Insights...")
    
    # Générer les données
    print("Génération des données météorologiques simulées...")
    data = generate_weather_data()
    print(f"Génération terminée : {len(data)} points de données")
    
    # Sauvegarder dans les deux bases de données
    try:
        # Configurer et sauvegarder dans la base Flask
        print("\nPréparation de la base de données Flask...")
        setup_flask_db()
        print("Sauvegarde dans la base de données Flask...")
        save_to_flask_db(data)
        
        # Sauvegarder dans la base climate_data
        print("\nSauvegarde dans la base de données climate_data...")
        save_to_climate_db(data)
        
        print("\nToutes les données ont été sauvegardées avec succès!")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
    
    print("\nRésumé:")
    print(f"- Un utilisateur test a été créé: email=test@example.com")
    print(f"- {len(CITIES)} appareils ont été créés, un pour chaque ville")
    print(f"- {len(data)} lectures météo ont été enregistrées dans les deux bases de données")
    print("\nVous pouvez maintenant lancer l'application et utiliser la fonctionnalité d'AI Insights")
