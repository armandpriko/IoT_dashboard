import pandas as pd
import numpy as np
from datetime import datetime

def process_weather_data(data):
    """
    Traite les données météorologiques brutes pour les préparer à l'analyse
    """
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Conversion des dates et heures
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df.set_index('datetime', inplace=True)
    
    # Nettoyage des données
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    return df

def calculate_gdd(df, base_temp=10):
    """
    Calcule les degrés-jours de croissance (GDD)
    Base par défaut : 10°C
    """
    if df.empty:
        return df
    
    # Calcul des températures moyennes journalières
    daily_temp = df['temperature'].resample('D').agg(['min', 'max'])
    
    # Calcul du GDD
    daily_temp['gdd'] = ((daily_temp['max'] + daily_temp['min']) / 2) - base_temp
    daily_temp['gdd'] = daily_temp['gdd'].clip(lower=0)  # Les valeurs négatives deviennent 0
    
    # Calcul du GDD cumulé
    daily_temp['gdd_cumul'] = daily_temp['gdd'].cumsum()
    
    return daily_temp

def generate_monthly_stats(df):
    """
    Génère des statistiques mensuelles à partir des données
    """
    if df.empty:
        return {}
    
    stats = {
        'temp_mean': df['temperature'].mean(),
        'temp_min': df['temperature'].min(),
        'temp_max': df['temperature'].max(),
        'humidity_mean': df['humidity'].mean(),
        'total_gdd': df['gdd'].sum() if 'gdd' in df.columns else 0
    }
    
    return stats
