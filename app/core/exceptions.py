"""
Exceptions personnalisées pour le projet.
"""

from typing import List, Optional


class AppBaseException(Exception):
    """Exception de base de l'application."""
    def __init__(self, error: str, message: str, details: Optional[List[str]] = None, status_code: int = 400):
        super().__init__(message)
        self.error = error
        self.message = message
        self.details = details or []
        self.status_code = status_code


class OrderNotFoundError(AppBaseException):
    """Levée lorsqu'une commande n'est pas trouvée dans l'OrderStore."""
    def __init__(self, order_id: str):
        super().__init__(
            error="order_not_found",
            message=f"Commande {order_id} inconnue.",
            status_code=404
        )


class ModelNotLoadedError(AppBaseException):
    """Levée lorsque le modèle ML n'a pas pu être chargé."""
    def __init__(self, message: str = "Le modèle de prédiction n'est pas disponible."):
        super().__init__(
            error="model_unavailable",
            message=message,
            status_code=503
        )


class StoreUnavailableError(AppBaseException):
    """Levée lorsque le stockage de persistance est injoignable."""
    def __init__(self, message: str = "Le système de stockage est indisponible."):
        super().__init__(
            error="store_unavailable",
            message=message,
            status_code=503
        )
