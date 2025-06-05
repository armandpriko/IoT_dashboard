import requests
from datetime import datetime, timedelta
import sqlite3

def get_weather_data(station, date):
    """
    Récupère les données météorologiques journalières pour une station donnée
    """
    conn = sqlite3.connect('climate_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT time, temperature, humidity, gdd, city
            FROM climate
            WHERE date = ? AND city = ?
            ORDER BY time ASC
        """, (date, station))
        
        data = [{
            'time': row[0],
            'temperature': row[1],
            'humidity': row[2],
            'gdd': row[3],
            'city': row[4]
        } for row in cursor.fetchall()]
        
        return data
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données: {e}")
        return None
    
    finally:
        conn.close()

def get_monthly_weather_data(station, year, month):
    """
    Récupère les données météorologiques mensuelles pour une station donnée
    """
    conn = sqlite3.connect('climate_data.db')
    cursor = conn.cursor()
    
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    try:
        cursor.execute("""
            SELECT date, time, temperature, humidity, gdd, city
            FROM climate
            WHERE city = ? 
            AND date >= ? 
            AND date < ?
            ORDER BY date ASC, time ASC
        """, (station, start_date, end_date))
        
        data = [{
            'date': row[0],
            'time': row[1],
            'temperature': row[2],
            'humidity': row[3],
            'gdd': row[4],
            'city': row[5]
        } for row in cursor.fetchall()]
        
        return data
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données mensuelles: {e}")
        return None
    
    finally:
        conn.close()

def save_weather_data(data, station):
    """
    Sauvegarde les données météorologiques dans la base de données
    """
    conn = sqlite3.connect('climate_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO climate (date, time, temperature, humidity, gdd, city)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data['date'],
            data['time'],
            data['temperature'],
            data['humidity'],
            data.get('gdd', 0),
            station
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()
