"""Configuration de la base de données SQLite"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Chemin vers la base de données
DATABASE_URL = "sqlite:///./data/water_points.db"

# Créer les dossiers nécessaires
os.makedirs("data", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# Configuration SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Obligatoire pour SQLite en mode multi-threads
    echo=False  # Passe à True pour voir les requêtes SQL dans la console
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Fonction pour obtenir une session DB
def get_db_session():
    """Retourne une session de base de données"""
    return SessionLocal()

# Fonction pour créer toutes les tables
def create_tables():
    """Créer toutes les tables dans la base de données"""
    # ⚠️ Importer les modèles ici pour que SQLAlchemy les enregistre
    from app import models  
    Base.metadata.create_all(bind=engine)
