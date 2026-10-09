"""
Configuration globale du projet.

Contient les constantes et paramètres configurables via variables d'environnement (.env) :
noms de colonnes, chemins, paramètres du modèle, base de données, etc.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# ── Projet 
PROJECT_NAME = os.getenv("PROJECT_NAME", "eligibilite-livraison-express")
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

# ── Reproductibilité 
RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))

# ── Répertoire d'artefacts 
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))

# ── Variable cible 
TARGET_COLUMN = "express_eligible"

# ── Variables d'entrée du modèle 
FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "weekend",
    "distance_km",
    "order_value_eur",
    "weight_kg",
    "stock_available",
    "preparation_time_min",
    "carrier_capacity",
    "weather",
    "delivery_zone",
    "customer_type",
]

NUMERIC_FEATURES = [
    "hour",
    "day_of_week",
    "weekend",
    "distance_km",
    "order_value_eur",
    "weight_kg",
    "stock_available",
    "preparation_time_min",
    "carrier_capacity",
]

CATEGORICAL_FEATURES = [
    "weather",
    "delivery_zone",
    "customer_type",
]

# ── Chemins des fichiers de sortie 
MODEL_PATH = ARTIFACTS_DIR / "express_delivery_model.joblib"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
FEATURES_PATH = ARTIFACTS_DIR / "features.json"
PREDICTIONS_PATH = ARTIFACTS_DIR / "batch_predictions.csv"
MODEL_CARD_PATH = ARTIFACTS_DIR / "model_card.json"

# ── Paramètres d'inférence et métier 
DEFAULT_THRESHOLD = float(os.getenv("DEFAULT_THRESHOLD", "0.5"))

# ── Stockage & Base de données 
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///orders.db")

# ── Spécifications de l'API & Serveur 
API_TITLE = os.getenv("API_TITLE", "eligibilite-livraison-express API")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
