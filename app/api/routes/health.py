"""
Routes des sondes de vivacité et de disponibilité (liveness & readiness).
Conforme aux spécifications de openapi.yml (Séance 1).
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.deps import get_order_store, get_predictor
from app.core.config import API_VERSION, PROJECT_NAME
from app.core.schemas import HealthStatus, ReadinessStatus
from app.interfaces.order_store import OrderStore
from app.services.predictor import PredictorService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    operation_id="getHealth",
    summary="Sonde de vivacité",
    description="Répond 200 si le processus est vivant. Ne doit jamais dépendre d'une brique externe.",
)
def get_health() -> HealthStatus:
    """Sonde de vivacité simple."""
    return HealthStatus(
        status="ok",
        service=PROJECT_NAME,
        version=API_VERSION,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessStatus,
    responses={
        200: {"model": ReadinessStatus, "description": "Le service est prêt à recevoir du trafic"},
        503: {"model": ReadinessStatus, "description": "Le service n'est pas prêt"},
    },
    operation_id="getReadiness",
    summary="Sonde de disponibilité",
    description="Répond 200 uniquement si le modèle est chargé et le stockage joignable.",
)
def get_readiness(
    predictor: PredictorService = Depends(get_predictor),
    order_store: OrderStore = Depends(get_order_store),
):
    """Sonde de disponibilité pour l'orchestrateur."""
    model_loaded = predictor.is_ready()
    store_reachable = order_store.ping()

    checks = {
        "model": "loaded" if model_loaded else "not_loaded",
        "order_store": "reachable" if store_reachable else "unreachable",
    }

    is_ready = model_loaded and store_reachable
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    payload = ReadinessStatus(
        status="ready" if is_ready else "not_ready",
        checks=checks,
        version=API_VERSION,
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
    )
