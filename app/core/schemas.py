"""
Schémas de validation Pydantic conformes au contrat d'API OpenAPI (openapi.yml).
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Énumérations ───────────────────────────────────────────────────────────────

class Weather(str, Enum):
    NORMAL = "normal"
    PLUIE = "pluie"
    NEIGE = "neige"
    ORAGE = "orage"


class DeliveryZone(str, Enum):
    CENTRE = "centre"
    PROCHE_BANLIEUE = "proche_banlieue"
    BANLIEUE = "banlieue"
    RURALE = "rurale"


class CustomerType(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"


class Decision(str, Enum):
    OUI = "oui"
    NON = "non"


# ── Schémas de données ─────────────────────────────────────────────────────────

class OrderFeatures(BaseModel):
    """
    Caractéristiques d'une commande.
    Correspond exactement aux FEATURE_COLUMNS du notebook.
    Toute variable en trop ou absente lève une erreur de validation 422 (extra='forbid').
    """
    model_config = ConfigDict(extra="forbid")

    order_id: Optional[str] = Field(
        default=None,
        description="Identifiant métier de la commande. Généré par le serveur si absent.",
        json_schema_extra={"example": "CMD-000001"}
    )
    hour: int = Field(
        ...,
        ge=0,
        le=23,
        description="Heure de passage de la commande (0-23)",
        json_schema_extra={"example": 14}
    )
    day_of_week: int = Field(
        ...,
        ge=0,
        le=6,
        description="0 = lundi ... 6 = dimanche",
        json_schema_extra={"example": 2}
    )
    weekend: Literal[0, 1] = Field(
        ...,
        description="1 si week-end (samedi/dimanche), 0 sinon",
        json_schema_extra={"example": 0}
    )
    distance_km: float = Field(
        ...,
        ge=0.0,
        description="Distance de livraison en kilomètres",
        json_schema_extra={"example": 3.5}
    )
    order_value_eur: float = Field(
        ...,
        ge=0.0,
        description="Montant de la commande en euros",
        json_schema_extra={"example": 89.9}
    )
    weight_kg: float = Field(
        ...,
        ge=0.0,
        description="Poids du colis en kilogrammes",
        json_schema_extra={"example": 2.4}
    )
    stock_available: Literal[0, 1] = Field(
        ...,
        description="Disponibilité immédiate du stock (1=oui, 0=non)",
        json_schema_extra={"example": 1}
    )
    preparation_time_min: float = Field(
        ...,
        ge=0.0,
        description="Temps estimé de préparation en minutes",
        json_schema_extra={"example": 18.0}
    )
    carrier_capacity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Capacité résiduelle du transporteur (0.0 à 1.0)",
        json_schema_extra={"example": 0.85}
    )
    weather: Weather = Field(
        ...,
        description="Conditions météorologiques prévues",
        json_schema_extra={"example": Weather.NORMAL.value}
    )
    delivery_zone: DeliveryZone = Field(
        ...,
        description="Zone géographique de livraison",
        json_schema_extra={"example": DeliveryZone.CENTRE.value}
    )
    customer_type: CustomerType = Field(
        ...,
        description="Catégorie du client (standard ou premium)",
        json_schema_extra={"example": CustomerType.PREMIUM.value}
    )


class OrderAccepted(BaseModel):
    """Réponse d'enregistrement immédiat d'une commande (202 Accepted)."""
    order_id: str = Field(..., json_schema_extra={"example": "CMD-000001"})
    status: Literal["accepted"] = Field(default="accepted", json_schema_extra={"example": "accepted"})


class Prediction(BaseModel):
    """Résultat de la prédiction d'éligibilité pour une commande."""
    order_id: str = Field(..., json_schema_extra={"example": "CMD-000001"})
    express_eligible: bool = Field(..., json_schema_extra={"example": True})
    decision: Literal["oui", "non"] = Field(..., json_schema_extra={"example": "oui"})
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probabilité estimée de livraison express réussie",
        json_schema_extra={"example": 0.8734}
    )
    model_version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    predicted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Horodatage ISO-8601 du calcul de la prédiction"
    )
    latency_ms: Optional[float] = Field(
        default=None,
        description="Temps de calcul en millisecondes"
    )


class BatchPredictionRequest(BaseModel):
    """Requête de prédiction par lot (Séance 5)."""
    orders: List[OrderFeatures] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Liste de commandes à prédire (1 à 1000)"
    )


class BatchPredictionResponse(BaseModel):
    """Réponse de prédiction par lot."""
    predictions: List[Prediction]
    count: int = Field(..., json_schema_extra={"example": 3})


class ModelCard(BaseModel):
    """Fiche descriptive du modèle en service (Séance 3)."""
    project: str = Field(..., json_schema_extra={"example": "eligibilite-livraison-express"})
    model_version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    model_type: str = Field(..., json_schema_extra={"example": "Logistic regression"})
    task: str = Field(..., json_schema_extra={"example": "binary classification"})
    target: str = Field(..., json_schema_extra={"example": "express_eligible"})
    threshold: float = Field(..., json_schema_extra={"example": 0.5})
    trained_at: Optional[datetime] = None
    features: List[str]
    metrics: Dict[str, float] = Field(
        ...,
        json_schema_extra={
            "example": {
                "accuracy": 0.86,
                "precision": 0.88,
                "recall": 0.84,
                "f1_score": 0.86,
                "roc_auc": 0.93,
            }
        }
    )
    limitations: Optional[List[str]] = None


class HealthStatus(BaseModel):
    """Sonde de vivacité (liveness)."""
    status: Literal["ok"] = Field(default="ok", json_schema_extra={"example": "ok"})
    service: str = Field(..., json_schema_extra={"example": "eligibilite-livraison-express"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})


class ReadinessStatus(BaseModel):
    """Sonde de disponibilité (readiness)."""
    status: Literal["ready", "not_ready"] = Field(..., json_schema_extra={"example": "ready"})
    checks: Dict[str, str] = Field(
        ...,
        json_schema_extra={
            "example": {
                "model": "loaded",
                "order_store": "reachable"
            }
        }
    )
    version: Optional[str] = None


class Error(BaseModel):
    """Format d'erreur d'API standardisé."""
    error: str = Field(
        ...,
        description="Code d'erreur stable branchable côté client",
        json_schema_extra={"example": "validation_error"}
    )
    message: str = Field(
        ...,
        description="Message lisible pour l'humain",
        json_schema_extra={"example": "Feature manquante : distance_km"}
    )
    details: Optional[List[str]] = Field(default=None)
