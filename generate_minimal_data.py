"""
Script simplifié pour générer des données météorologiques uniquement dans climate_data.db
"""
import sqlite3
import random
import numpy as np
from datetime import datetime, timedelta

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
WIND_SPEED_MEAN = 15
WIND_STD = 8
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
                wind_speed = max(0, np.random.normal(WIND_SPEED_MEAN, WIND_STD))
                wind_direction = random.choice(WIND_DIRECTIONS)
                
                # Calcul GDD (Growing Degree Days)
                min_temp = max(0, temp - 2)
                max_temp = temp + 2
                gdd = max(0, ((min_temp + max_temp) / 2) - 10)  # Base 10°C
                
                data.append({
                    'date': timestamp.strftime('%Y-%m-%d'),
                    'time': timestamp.strftime('%H:%M:%S'),
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
        day_count += 1
        if day_count % 10 == 0:
            print(f"Génération en cours: {day_count} jours générés...")
    
    return data

def save_to_db(data):
    """Sauvegarde les données dans la base de données SQLite"""
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
    
    # Nettoyage des données existantes (optionnel)
    # cursor.execute("DELETE FROM climate")
    # conn.commit()
    
    # Insertion des données
    batch_size = 100
    total_readings = len(data)
    
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
            item.get('pressure', None),
            item.get('rainfall', None),
            item.get('wind_speed', None),
            item.get('wind_direction', None)
        ))
        
        # Commit par lots
        if (i + 1) % batch_size == 0:
            conn.commit()
            progress = (i + 1) / total_readings * 100
            print(f"  - Progression: {progress:.1f}% ({i + 1}/{total_readings})")
    
    conn.commit()
    conn.close()
    print(f"Données sauvegardées dans la table 'climate' ({len(data)} entrées)")

if __name__ == "__main__":
    print("Démarrage de la génération de données météorologiques...")
    
    # Générer les données
    data = generate_weather_data()
    print(f"Génération terminée : {len(data)} points de données")
    
    # Sauvegarder dans la base de données
    print("Sauvegarde dans la base de données SQLite...")
    save_to_db(data)
    
    print("Terminé! Les données sont prêtes pour être utilisées dans le tableau de bord.")
