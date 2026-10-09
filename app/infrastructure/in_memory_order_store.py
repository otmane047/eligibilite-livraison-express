"""
Implémentation en mémoire d'OrderStore pour les tests unitaires isolés.
Conforme à l'ADR-001 (Section 5.3).
"""

import threading
import uuid
from typing import Any, Dict, Optional, Union
from app.core.schemas import OrderFeatures
from app.interfaces.order_store import OrderStore


class InMemoryOrderStore(OrderStore):
    """
    Store de commandes en mémoire, thread-safe.
    Idéal pour les tests unitaires rapides et découplés de toute base de données.
    """

    def __init__(self, healthy: bool = True):
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._counter = 0
        self._healthy = healthy

    def save(self, order_data: Union[Dict[str, Any], OrderFeatures]) -> str:
        """Persiste une commande en mémoire et retourne son identifiant unique."""
        if not self._healthy:
            raise RuntimeError("Stockage en mémoire indisponible.")

        if isinstance(order_data, OrderFeatures):
            data = order_data.model_dump()
        else:
            data = dict(order_data)

        with self._lock:
            order_id = data.get("order_id")
            if not order_id:
                self._counter += 1
                order_id = f"CMD-{self._counter:06d}"
                data["order_id"] = order_id

            if "status" not in data:
                data["status"] = "accepted"

            self._orders[order_id] = data
            return order_id

    def get_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une commande par son identifiant."""
        if not self._healthy:
            raise RuntimeError("Stockage en mémoire indisponible.")

        with self._lock:
            order = self._orders.get(order_id)
            return dict(order) if order else None

    def ping(self) -> bool:
        """Vérifie la santé du store."""
        return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        """Permet de simuler une panne pour tester les sondes /health/ready."""
        self._healthy = healthy

    def clear(self) -> None:
        """Vide le contenu du store."""
        with self._lock:
            self._orders.clear()
            self._counter = 0
