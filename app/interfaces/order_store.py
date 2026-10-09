"""
Contrat d'interface abstraite pour la persistance des commandes.
Conforme aux spécifications de l'ADR-001 (ADR-001-stockage-des-commandes.md).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from app.core.schemas import OrderFeatures


class OrderStore(ABC):
    """
    Interface abstraite définissant les opérations sur les commandes.
    Applique le principe d'Inversion de Dépendance (DIP - SOLID) et le Repository Pattern.
    """

    @abstractmethod
    def save(self, order_data: Union[Dict[str, Any], OrderFeatures]) -> str:
        """
        Persiste une commande et retourne son order_id (généré ou fourni).
        Lève une exception si l'écriture échoue.

        Parameters
        ----------
        order_data : Union[Dict[str, Any], OrderFeatures]
            Données de la commande validées.

        Returns
        -------
        str
            L'identifiant métier unique de la commande (ex: 'CMD-000001').
        """
        pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les features d'une commande par son identifiant.

        Parameters
        ----------
        order_id : str
            Identifiant métier de la commande recherchée.

        Returns
        -------
        Optional[Dict[str, Any]]
            Dictionnaire des caractéristiques de la commande si trouvée, sinon None.
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Vérifie la disponibilité du support de stockage pour la sonde /health/ready.

        Returns
        -------
        bool
            True si le stockage est joignable et opérationnel, False sinon.
        """
        pass
