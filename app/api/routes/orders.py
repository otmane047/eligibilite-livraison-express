"""
Routes de collecte et consultation des commandes.
Conforme à openapi.yml (Séance 1).
"""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_order_store
from app.core.exceptions import OrderNotFoundError
from app.core.schemas import Error, OrderAccepted, OrderFeatures
from app.interfaces.order_store import OrderStore

router = APIRouter(prefix="/v1/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="createOrder",
    summary="Enregistrer une commande à prédire",
    description="Collecte de données : la commande est persistée via OrderStore.",
    responses={
        202: {"model": OrderAccepted, "description": "Commande acceptée"},
        422: {"model": Error, "description": "Commande invalide"},
    },
)
def create_order(
    order: OrderFeatures,
    order_store: OrderStore = Depends(get_order_store),
) -> OrderAccepted:
    """Enregistre une commande et retourne immédiatement 202 Accepted avec son order_id."""
    order_id = order_store.save(order)
    return OrderAccepted(order_id=order_id, status="accepted")


@router.get(
    "/{order_id}",
    response_model=OrderFeatures,
    operation_id="getOrder",
    summary="Relire une commande collectée",
    responses={
        200: {"model": OrderFeatures, "description": "Commande trouvée"},
        404: {"model": Error, "description": "Commande inconnue"},
    },
)
def get_order(
    order_id: str,
    order_store: OrderStore = Depends(get_order_store),
) -> OrderFeatures:
    """Récupère une commande persistée par son identifiant."""
    order_dict = order_store.get_by_id(order_id)
    if not order_dict:
        raise OrderNotFoundError(order_id)

    # Retire les colonnes internes non attendues dans OrderFeatures
    order_dict.pop("created_at", None)
    order_dict.pop("status", None)
    return OrderFeatures(**order_dict)
