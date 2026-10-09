"""
Configuration globale du projet.

Contient les constantes partagées entre les différents modules :
noms de colonnes, chemins, paramètres du modèle, etc.
"""

from pathlib import Path

# ── Projet 
PROJECT_NAME = "eligibilite-livraison-express"
MODEL_VERSION = "1.0.0"

# ── Reproductibilité 
RANDOM_STATE = 42

# ── Répertoire d'artefacts 
ARTIFACTS_DIR = Path("artifacts")

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
DEFAULT_THRESHOLD = 0.5

# ── Stockage & Base de données 
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///orders.db")

# ── Spécifications de l'API 
API_TITLE = "eligibilite-livraison-express API"
API_VERSION = "1.0.0"
