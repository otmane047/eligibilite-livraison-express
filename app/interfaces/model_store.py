"""
Contrat d'interface abstraite pour la gestion des artefacts de modèle ML.
Conforme aux spécifications de l'ADR-002 (ADR-002-stockage-des-artefacts-de-modele.md).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ModelArtifactStore(ABC):
    """
    Interface abstraite d'accès et de stockage des artefacts de modèle Machine Learning.
    Applique le principe d'Inversion de Dépendance (DIP - SOLID) pour découpler
    le code applicatif de l'emplacement physique des artefacts (Local, MinIO, S3, MLflow Registry).
    """

    @abstractmethod
    def load_model(self, version: str) -> Any:
        """
        Charge la pipeline de modèle sérialisée en mémoire.

        Parameters
        ----------
        version : str
            Version sémantique du modèle (ex: '1.0.0').

        Returns
        -------
        Any
            Pipeline Scikit-learn instanciée en mémoire.
        """
        pass

    @abstractmethod
    def load_metadata(self, version: str) -> Dict[str, Any]:
        """
        Charge les métadonnées associées au modèle (model_card.json ou metrics.json).

        Parameters
        ----------
        version : str
            Version sémantique du modèle (ex: '1.0.0').

        Returns
        -------
        Dict[str, Any]
            Dictionnaire complet des métadonnées du modèle.
        """
        pass

    @abstractmethod
    def save_artifacts(
        self,
        version: str,
        model_pipeline: Any,
        metrics: Dict[str, float],
        model_card: Dict[str, Any],
    ) -> None:
        """
        Sauvegarde l'ensemble des artefacts pour une version donnée.

        Parameters
        ----------
        version : str
            Version sémantique du modèle.
        model_pipeline : Any
            Pipeline Scikit-learn entraînée.
        metrics : Dict[str, float]
            Métriques d'évaluation calculées sur le jeu de test.
        model_card : Dict[str, Any]
            Dictionnaire de la fiche modèle (Model Card).
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Vérifie la disponibilité et l'accessibilité du support d'artefacts pour la sonde /health/ready.

        Returns
        -------
        bool
            True si le store d'artefacts est accessible, False sinon.
        """
        pass
