"""
Script de génération de données météorologiques simulées pour tester le tableau de bord
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
from models import db, User, Device, Reading
from app import app

# Paramètres de simulation
CITIES = ["Paris", "Lyon", "Marseille", "Bordeaux", "Lille", "Strasbourg"]
START_DATE = datetime.now() - timedelta(days=30)  # Données sur 30 jours
END_DATE = datetime.now()
HOURLY_READINGS = True  # Génère des données horaires ou toutes les 3 heures

# Moyennes et écarts-types saisonniers pour les paramètres météorologiques (basés sur le mois actuel)
MONTH = datetime.now().month
# Configuré pour le mois de mai/juin en France
TEMP_MEAN = 20  # Température moyenne en mai/juin (°C)
TEMP_STD = 5   # Écart-type
HUMIDITY_MEAN = 65  # Humidité moyenne (%)
HUMIDITY_STD = 15
PRESSURE_MEAN = 1013  # Pression atmosphérique moyenne (hPa)
PRESSURE_STD = 5
RAINFALL_PROB = 0.3  # Probabilité de pluie
RAINFALL_MEAN = 2    # Précipitations moyennes en mm
RAINFALL_STD = 4
WIND_SPEED_MEAN = 15  # Vitesse moyenne du vent (km/h)
WIND_SPEED_STD = 8
WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

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
    
    # Pour chaque jour dans la plage
    while current_date <= END_DATE:
        for city in CITIES:
            base_temp = city_base_temps[city]
            # Créer un motif quotidien pour cette ville-jour
            daily_pattern = create_daily_pattern(base_temp, TEMP_STD)
            
            # Générer des données pour chaque heure ou à des intervalles de 3 heures
            hours = range(0, 24, 1 if HOURLY_READINGS else 3)
            
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
                
                # Calcul GDD (Growing Degree Days)
                min_temp = max(0, temp - 2)
                max_temp = temp + 2
                gdd = max(0, ((min_temp + max_temp) / 2) - 10)  # Base 10°C
                
                data.append({
                    'date': timestamp.strftime('%Y-%m-%d'),
                    'time': timestamp.strftime('%H:%M:%S'),
                    'timestamp': timestamp,
                    'temperature': round(temp, 1),
                    'humidity': round(humidity, 1),
                    'pressure': round(pressure, 1),
                    'rainfall': round(rainfall, 1),
                    'wind_speed': round(wind_speed, 1),
                    'wind_direction': wind_direction,
                    'gdd': round(gdd, 2),
                    'city': city
                })
        
        # Passer au jour suivant
        current_date += timedelta(days=1)
    
    return data

def save_to_db(data):
    """Sauvegarde les données dans la base de données SQLite"""
    # Sauvegarde dans la table 'climate' pour la compatibilité
    conn = sqlite3.connect('climate_data.db')
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
            wind_direction TEXT
        )
    ''')
    
    # Insertion des données
    for item in data:
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
            item.get('pressure', None),
            item.get('rainfall', None),
            item.get('wind_speed', None),
            item.get('wind_direction', None)
        ))
    
    conn.commit()
    conn.close()
    print(f"Données sauvegardées dans la table 'climate' ({len(data)} entrées)")

def save_to_flask_db(data):
    """Sauvegarde les données dans la base de données Flask-SQLAlchemy"""
    with app.app_context():
        # Création d'un utilisateur si aucun n'existe
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(
                email='test@example.com',
                name='Utilisateur Test',
                api_key='test_api_key_123456789'
            )
            db.session.add(test_user)
            db.session.commit()
        
        # Création ou récupération des appareils pour chaque ville
        city_devices = {}
        for city in CITIES:
            device = Device.query.filter_by(name=f'Station {city}', user_id=test_user.id).first()
            if not device:
                device = Device(
                    name=f'Station {city}',
                    device_type='WeatherStation',
                    location=city,
                    user_id=test_user.id
                )
                db.session.add(device)
                db.session.commit()
            city_devices[city] = device
        
        # Insertion des données de lecture
        readings_count = 0
        for item in data:
            city = item['city']
            if city in city_devices:
                reading = Reading(
                    timestamp=item['timestamp'],
                    temperature=item['temperature'],
                    humidity=item['humidity'],
                    pressure=item.get('pressure'),
                    rainfall=item.get('rainfall'),
                    wind_speed=item.get('wind_speed'),
                    wind_direction=item.get('wind_direction'),
                    device_id=city_devices[city].id
                )
                db.session.add(reading)
                readings_count += 1
                
                # Commit par lots pour éviter une surcharge mémoire
                if readings_count % 100 == 0:
                    db.session.commit()
        
        # Commit final
        db.session.commit()
        print(f"Données sauvegardées dans la base Flask ({readings_count} lectures)")

if __name__ == "__main__":
    print("Génération des données météorologiques simulées...")
    data = generate_weather_data()
    print(f"Génération terminée : {len(data)} points de données")
    
    print("Sauvegarde dans la base de données SQLite...")
    save_to_db(data)
    
    print("Sauvegarde dans la base de données Flask-SQLAlchemy...")
    try:
        save_to_flask_db(data)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans la base Flask: {e}")
    
    print("Terminé!")
