"""
Script simplifié de génération de données météorologiques simulées
"""
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Paramètres de simulation
CITIES = ["Paris", "Lyon", "Marseille", "Bordeaux", "Lille", "Strasbourg"]
START_DATE = datetime.now() - timedelta(days=30)  # Données sur 30 jours
END_DATE = datetime.now()
HOURLY_READINGS = True  # Génère des données horaires ou toutes les 3 heures

# Moyennes et écarts-types pour les paramètres météorologiques
TEMP_MEAN = 20  # Température moyenne (°C)
TEMP_STD = 5   # Écart-type
HUMIDITY_MEAN = 65  # Humidité moyenne (%)
HUMIDITY_STD = 15
RAINFALL_PROB = 0.3  # Probabilité de pluie
RAINFALL_MEAN = 2    # Précipitations moyennes en mm

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
                
                # Pluie aléatoire (plus probable quand l'humidité est élevée)
                rain_modifier = (humidity - 50) / 50  # -1 à 1
                rainfall_probability = np.clip(RAINFALL_PROB + (rain_modifier * 0.2), 0, 1)
                rainfall = np.random.exponential(RAINFALL_MEAN) if random.random() < rainfall_probability else 0
                
                # Calcul GDD (Growing Degree Days)
                min_temp = max(0, temp - 2)
                max_temp = temp + 2
                gdd = max(0, ((min_temp + max_temp) / 2) - 10)  # Base 10°C
                
                data.append({
                    'date': timestamp.strftime('%Y-%m-%d'),
                    'time': timestamp.strftime('%H:%M:%S'),
                    'temperature': round(temp, 1),
                    'humidity': round(humidity, 1),
                    'gdd': round(gdd, 2),
                    'city': city
                })
        
        # Passer au jour suivant
        current_date += timedelta(days=1)
    
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
            city TEXT
        )
    ''')
    
    # Insertion des données
    for item in data:
        cursor.execute('''
            INSERT INTO climate (date, time, temperature, humidity, gdd, city)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item['date'], 
            item['time'], 
            item['temperature'], 
            item['humidity'], 
            item['gdd'], 
            item['city']
        ))
    
    conn.commit()
    conn.close()
    print(f"Données sauvegardées dans la table 'climate' ({len(data)} entrées)")

if __name__ == "__main__":
    print("Génération des données météorologiques simulées...")
    data = generate_weather_data()
    print(f"Génération terminée : {len(data)} points de données")
    
    print("Sauvegarde dans la base de données SQLite...")
    save_to_db(data)
    
    print("Terminé! Les données sont prêtes pour être visualisées dans le tableau de bord.")
