try:
    from flask import Flask
    print("Flask importé avec succès")
    
    from flask_login import LoginManager
    print("Flask-Login importé avec succès")
    
    from flask_dance.contrib.google import make_google_blueprint
    print("Flask-Dance importé avec succès")

    from models import db, User, Device, Reading
    print("Modèles importés avec succès")
    
except Exception as e:
    print(f"Erreur : {e}")
    import traceback
    traceback.print_exc()

print("Fin du debug")
