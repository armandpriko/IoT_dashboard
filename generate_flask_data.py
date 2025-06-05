"""
Script pour générer des données Flask-SQLAlchemy pour la fonctionnalité AI Insights
"""
import os
import sys
import random
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import app, db, User, Device, Reading

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
                    'timestamp': timestamp,
                    'temperature': round(temp, 1),
                    'humidity': round(humidity, 1),
                    'pressure': round(pressure, 1),
                    'rainfall': round(rainfall, 1),
                    'wind_speed': round(wind_speed, 1),
                    'wind_direction': wind_direction
                })
        
        # Passer au jour suivant
        current_date += timedelta(days=1)
        day_count += 1
        if day_count % 10 == 0:
            print(f"Génération en cours: {day_count} jours générés...")
    
    return data

def save_to_flask_db(data):
    """Sauvegarde les données dans la base de données Flask-SQLAlchemy"""
    with app.app_context():
        # Supprimer les données existantes pour éviter les doublons
        print("Suppression des anciennes données...")
        Reading.query.delete()
        Device.query.delete()
        
        # Création d'un utilisateur test s'il n'existe pas
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            print("Création d'un utilisateur test...")
            test_user = User(
                email='test@example.com',
                name='Utilisateur Test',
                api_key='test_api_key_123456'
            )
            db.session.add(test_user)
            db.session.commit()
        else:
            print(f"Utilisateur test trouvé: {test_user.name}")
        
        # Création des appareils pour chaque ville
        city_devices = {}
        for city in CITIES:
            print(f"Création de l'appareil pour {city}...")
            device = Device(
                name=f'Station {city}',
                device_type='WeatherStation',
                location=city,
                user_id=test_user.id,
                last_connection=datetime.now()
            )
            db.session.add(device)
            db.session.commit()
            city_devices[city] = device
            print(f"  - Appareil ID: {device.id}, Nom: {device.name}")
        
        # Insertion des données de lecture
        total_readings = len(data)
        print(f"Insertion de {total_readings} lectures...")
        
        batch_size = 100
        for i, item in enumerate(data):
            city = item['city']
            reading = Reading(
                timestamp=item['timestamp'],
                temperature=item['temperature'],
                humidity=item['humidity'],
                pressure=item['pressure'],
                rainfall=item['rainfall'],
                wind_speed=item['wind_speed'],
                wind_direction=item['wind_direction'],
                device_id=city_devices[city].id
            )
            db.session.add(reading)
            
            # Commit par lots pour éviter une surcharge mémoire
            if (i + 1) % batch_size == 0:
                db.session.commit()
                progress = (i + 1) / total_readings * 100
                print(f"  - Progression: {progress:.1f}% ({i + 1}/{total_readings})")
        
        # Commit final
        db.session.commit()
        print(f"Toutes les données ont été sauvegardées ({total_readings} lectures)")

if __name__ == "__main__":
    print("Démarrage de la génération de données pour AI Insights...")
    
    # Vérifier si l'application Flask est correctement configurée
    if not app:
        print("Erreur: L'application Flask n'est pas initialisée correctement.")
        sys.exit(1)
    
    # Générer les données
    print("Génération des données météorologiques simulées...")
    data = generate_weather_data()
    print(f"Génération terminée : {len(data)} points de données")
    
    # Sauvegarder dans la base de données Flask
    print("Sauvegarde dans la base de données Flask-SQLAlchemy...")
    try:
        save_to_flask_db(data)
        print("Toutes les données ont été sauvegardées avec succès!")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans la base Flask: {e}")
        sys.exit(1)
    
    print("\nRésumé:")
    print(f"- Un utilisateur test a été créé: email=test@example.com")
    print(f"- {len(CITIES)} appareils ont été créés, un pour chaque ville")
    print(f"- {len(data)} lectures météo ont été enregistrées")
    print("\nVous pouvez maintenant vous connecter à l'application et utiliser la fonctionnalité d'AI Insights")
