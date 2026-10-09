"""
Interfaces abstraites (ports) de l'application.
"""

from app.interfaces.order_store import OrderStore
from app.interfaces.model_store import ModelArtifactStore

__all__ = ["OrderStore", "ModelArtifactStore"]
