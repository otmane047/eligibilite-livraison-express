"""
Routes de métadonnées du modèle en service.
Conforme à openapi.yml (Séance 3).
"""

from fastapi import APIRouter, Request, status

from app.core.exceptions import ModelNotLoadedError
from app.core.schemas import Error, ModelCard

router = APIRouter(prefix="/v1/model", tags=["model"])


@router.get(
    "",
    response_model=ModelCard,
    status_code=status.HTTP_200_OK,
    operation_id="getModelCard",
    summary="Métadonnées et métriques du modèle en service",
    description="Implémentation HTTP de la cellule 55 du notebook (model card).",
    responses={
        200: {"model": ModelCard, "description": "Model card du modèle en service"},
        503: {"model": Error, "description": "Modèle ou métadonnées indisponibles"},
    },
)
def get_model_card(request: Request) -> ModelCard:
    """Retourne la Model Card du modèle actuellement servi par l'API."""
    metadata = getattr(request.app.state, "model_metadata", None)
    if not metadata:
        raise ModelNotLoadedError("Les métadonnées du modèle ne sont pas disponibles.")

    return ModelCard(**metadata)
