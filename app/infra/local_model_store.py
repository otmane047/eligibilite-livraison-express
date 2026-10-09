"""
Implémentation locale de ModelArtifactStore basée sur le système de fichiers.
Conforme à l'ADR-002 (Sections 4.4, 5.1 et 5.2).
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
import joblib

from app.core.config import ARTIFACTS_DIR
from app.core.exceptions import ModelNotLoadedError
from app.interfaces.model_store import ModelArtifactStore


class LocalModelArtifactStore(ModelArtifactStore):
    """
    Gestionnaire local des artefacts ML (sérialisation Joblib et métadonnées JSON).
    Idéal pour le développement local et les tests de validation.
    """

    def __init__(self, artifacts_dir: Union[str, Path] = ARTIFACTS_DIR):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _get_model_file(self, version: str) -> Path:
        # Supporte la structure directe artifacts/ ou sous-dossier de version artifacts/v1.0.0/
        versioned_path = self.artifacts_dir / f"v{version}" / "express_delivery_model.joblib"
        if versioned_path.exists():
            return versioned_path
        return self.artifacts_dir / "express_delivery_model.joblib"

    def _get_card_file(self, version: str) -> Path:
        versioned_path = self.artifacts_dir / f"v{version}" / "model_card.json"
        if versioned_path.exists():
            return versioned_path
        return self.artifacts_dir / "model_card.json"

    def load_model(self, version: str) -> Any:
        """Charge le pipeline de modèle sérialisé depuis le disque."""
        model_file = self._get_model_file(version)
        if not model_file.exists():
            raise ModelNotLoadedError(
                f"Artefact de modèle introuvable à l'emplacement : {model_file}"
            )
        try:
            return joblib.load(model_file)
        except Exception as exc:
            raise ModelNotLoadedError(
                f"Échec du chargement du modèle depuis {model_file} : {exc}"
            ) from exc

    def load_metadata(self, version: str) -> Dict[str, Any]:
        """Charge le fichier model_card.json associé."""
        card_file = self._get_card_file(version)
        if not card_file.exists():
            raise FileNotFoundError(
                f"Métadonnées introuvables à l'emplacement : {card_file}"
            )
        with open(card_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_artifacts(
        self,
        version: str,
        model_pipeline: Any,
        metrics: Dict[str, float],
        model_card: Dict[str, Any],
    ) -> None:
        """Sauvegarde l'ensemble des artefacts sur le disque."""
        target_dir = self.artifacts_dir / f"v{version}"
        target_dir.mkdir(parents=True, exist_ok=True)

        # Sauvegarde versionnée
        joblib.dump(model_pipeline, target_dir / "express_delivery_model.joblib")
        with open(target_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        with open(target_dir / "model_card.json", "w", encoding="utf-8") as f:
            json.dump(model_card, f, indent=2)

        # Sauvegarde racine pour accès direct par défaut
        joblib.dump(model_pipeline, self.artifacts_dir / "express_delivery_model.joblib")
        with open(self.artifacts_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        with open(self.artifacts_dir / "model_card.json", "w", encoding="utf-8") as f:
            json.dump(model_card, f, indent=2)

    def ping(self) -> bool:
        """Vérifie que le répertoire d'artefacts est accessible."""
        return self.artifacts_dir.exists()
