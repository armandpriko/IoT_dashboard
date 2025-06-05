"""
Script de visualisation des données météorologiques
"""
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

def get_data_from_db():
    """Récupère les données de la base SQLite"""
    conn = sqlite3.connect('climate_data.db')
    query = "SELECT * FROM climate ORDER BY date, time"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def show_data_summary(df):
    """Affiche un résumé des données"""
    print(f"Nombre total d'entrées: {len(df)}")
    print(f"Période couverte: de {df['date'].min()} à {df['date'].max()}")
    print(f"Villes disponibles: {', '.join(df['city'].unique())}")
    print("\nAperçu des données:")
    print(df.head())
    
    # Statistiques de base
    print("\nStatistiques:")
    stats = df.groupby('city').agg({
        'temperature': ['mean', 'min', 'max', 'std'],
        'humidity': ['mean', 'min', 'max', 'std'],
        'gdd': ['mean', 'sum']
    }).round(2)
    print(stats)

def plot_temperature_trends(df):
    """Affiche des graphiques de tendances de température par ville"""
    # Conversion des dates en datetime
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    
    # Création d'un dossier pour sauvegarder les graphiques
    os.makedirs('static/graphs', exist_ok=True)
    
    # Créer un graphique pour chaque ville
    cities = df['city'].unique()
    plt.figure(figsize=(15, 10))
    
    for city in cities:
        city_data = df[df['city'] == city]
        daily_temps = city_data.groupby(city_data['datetime'].dt.date)['temperature'].mean()
        plt.plot(daily_temps.index, daily_temps.values, label=city, linewidth=2)
    
    plt.title("Température moyenne journalière par ville", fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Température (°C)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=12)
    plt.tight_layout()
    
    # Enregistrer le graphique
    plt.savefig('static/graphs/temperature_trends.png')
    print("Graphique de tendances de température enregistré dans static/graphs/temperature_trends.png")
    
    # Fermer la figure pour éviter les problèmes de mémoire
    plt.close()

def plot_humidity_vs_temperature(df):
    """Crée un graphique de dispersion humidité vs température par ville"""
    plt.figure(figsize=(15, 10))
    
    cities = df['city'].unique()
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink']
    
    for i, city in enumerate(cities):
        city_data = df[df['city'] == city]
        color = colors[i % len(colors)]
        plt.scatter(city_data['temperature'], city_data['humidity'], 
                   alpha=0.6, label=city, color=color, s=30)
    
    plt.title("Humidité vs Température par ville", fontsize=16)
    plt.xlabel("Température (°C)", fontsize=12)
    plt.ylabel("Humidité (%)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.legend(fontsize=12)
    plt.tight_layout()
    
    # Enregistrer le graphique
    plt.savefig('static/graphs/humidity_vs_temperature.png')
    print("Graphique de dispersion enregistré dans static/graphs/humidity_vs_temperature.png")
    
    # Fermer la figure pour éviter les problèmes de mémoire
    plt.close()

def plot_gdd_accumulation(df):
    """Trace l'accumulation de GDD pour chaque ville"""
    # Conversion des dates en datetime
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    
    plt.figure(figsize=(15, 10))
    
    cities = df['city'].unique()
    for city in cities:
        city_data = df[df['city'] == city].copy()
        # Grouper par jour et sommer les GDD
        daily_gdd = city_data.groupby(city_data['datetime'].dt.date)['gdd'].sum()
        # Calculer le GDD cumulé
        cumulative_gdd = daily_gdd.cumsum()
        plt.plot(cumulative_gdd.index, cumulative_gdd.values, label=city, linewidth=2)
    
    plt.title("Accumulation de degrés-jours de croissance (GDD) par ville", fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("GDD cumulés (base 10°C)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=12)
    plt.tight_layout()
    
    # Enregistrer le graphique
    plt.savefig('static/graphs/gdd_accumulation.png')
    print("Graphique d'accumulation GDD enregistré dans static/graphs/gdd_accumulation.png")
    
    # Fermer la figure pour éviter les problèmes de mémoire
    plt.close()

if __name__ == "__main__":
    print("Chargement des données météorologiques...")
    df = get_data_from_db()
    
    if df.empty:
        print("Aucune donnée trouvée dans la base de données!")
    else:
        show_data_summary(df)
        
        print("\nCréation des graphiques...")
        plot_temperature_trends(df)
        plot_humidity_vs_temperature(df)
        plot_gdd_accumulation(df)
        
        print("\nTerminé! Les graphiques ont été générés dans le dossier static/graphs/")
