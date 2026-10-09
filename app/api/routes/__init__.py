"""
Ensemble des routeurs de l'API.
"""

from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.orders import router as orders_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.model import router as model_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(orders_router)
api_router.include_router(predictions_router)
api_router.include_router(model_router)
