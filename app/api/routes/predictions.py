"""
Routes de calcul des prédictions (unitaires, batch et relecture).
Conforme à openapi.yml (Séances 1 et 5).
"""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_order_store, get_predictor
from app.core.exceptions import OrderNotFoundError
from app.core.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    Error,
    OrderFeatures,
    Prediction,
)
from app.interfaces.order_store import OrderStore
from app.services.predictor import PredictorService

router = APIRouter(prefix="/v1/predictions", tags=["predictions"])


@router.post(
    "",
    response_model=Prediction,
    status_code=status.HTTP_200_OK,
    operation_id="createPrediction",
    summary="Prédire l'éligibilité express d'une commande",
    description="Prédiction synchrone en mémoire. Implémentation HTTP de la cellule 34 du notebook.",
    responses={
        200: {"model": Prediction, "description": "Prédiction calculée"},
        422: {"model": Error, "description": "Commande invalide"},
        503: {"model": Error, "description": "Modèle indisponible"},
    },
)
def create_prediction(
    order: OrderFeatures,
    predictor: PredictorService = Depends(get_predictor),
) -> Prediction:
    """Calcule la prédiction d'éligibilité express pour une commande."""
    return predictor.predict_order(order)


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    operation_id="createBatchPredictions",
    summary="Prédire un lot de commandes",
    description="Prédiction vectorisée par lot (Séance 5). Implémentation HTTP de la cellule 46 du notebook.",
    responses={
        200: {"model": BatchPredictionResponse, "description": "Prédictions du lot"},
        422: {"model": Error, "description": "Lot invalide"},
    },
)
def create_batch_predictions(
    request: BatchPredictionRequest,
    predictor: PredictorService = Depends(get_predictor),
) -> BatchPredictionResponse:
    """Calcule les prédictions d'éligibilité express pour un lot de commandes."""
    return predictor.predict_batch(request.orders)


@router.get(
    "/{order_id}",
    response_model=Prediction,
    operation_id="getPrediction",
    summary="Relire une prédiction déjà calculée",
    description="Récupère la commande collectée et recalcule ou restitue sa prédiction.",
    responses={
        200: {"model": Prediction, "description": "Prédiction trouvée"},
        404: {"model": Error, "description": "Prédiction inconnue"},
    },
)
def get_prediction(
    order_id: str,
    predictor: PredictorService = Depends(get_predictor),
    order_store: OrderStore = Depends(get_order_store),
) -> Prediction:
    """Relit la prédiction d'une commande persistée."""
    order_dict = order_store.get_by_id(order_id)
    if not order_dict:
        raise OrderNotFoundError(order_id)

    order_dict.pop("created_at", None)
    order_dict.pop("status", None)
    features = OrderFeatures(**order_dict)
    return predictor.predict_order(features, order_id=order_id)
