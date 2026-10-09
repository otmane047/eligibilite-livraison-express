"""
Gestion de l'injection de dépendances pour FastAPI.
"""

from fastapi import Request
from app.interfaces.order_store import OrderStore
from app.services.predictor import PredictorService


def get_order_store(request: Request) -> OrderStore:
    """Récupère l'instance singleton d'OrderStore depuis l'état de l'application."""
    return request.app.state.order_store


def get_predictor(request: Request) -> PredictorService:
    """Récupère l'instance singleton de PredictorService depuis l'état de l'application."""
    return request.app.state.predictor
