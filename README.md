# Weather Dashboard

Application de tableau de bord météorologique développée avec Flask pour afficher et analyser les données météorologiques en temps réel.

## Fonctionnalités

- Affichage en temps réel des données météorologiques (température, humidité, GDD)
- Analyse des données journalières et mensuelles
- Export des données au format CSV
- Génération de rapports PDF
- Visualisation graphique avec Chart.js

## Installation

1. Créer un environnement virtuel :
```bash
python -m venv venv
```

2. Activer l'environnement virtuel :
```bash
# Windows
venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Initialiser la base de données :
```bash
python init_db.py
```

5. Lancer l'application :
```bash
python app.py
```

## Structure du Projet

```
Weather_Dashboard/
├── app.py               # Application Flask principale
├── weather_analysis.py  # Fonctions d'analyse météo
├── weather_daily.py     # Fonctions d'analyse journalière
├── init_db.py          # Script d'initialisation de la BDD
├── templates/          # Templates HTML
├── static/            # Fichiers statiques (CSS, JS)
├── climate_data.db    # Base de données SQLite
└── requirements.txt   # Dépendances du projet
```
