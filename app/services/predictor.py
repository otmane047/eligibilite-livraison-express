"""
Service d'inférence en mémoire pour les prédictions unitaires et batch.
Extrait des cellules 32, 34 et 46 du notebook.
"""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from sklearn.pipeline import Pipeline

from app.core.config import DEFAULT_THRESHOLD, FEATURE_COLUMNS, MODEL_VERSION
from app.core.exceptions import ModelNotLoadedError
from app.core.schemas import (
    BatchPredictionResponse,
    OrderFeatures,
    Prediction,
)


class PredictorService:
    """
    Service d'inférence encapsulant le modèle Scikit-learn en mémoire vive (Singleton).
    Conforme à l'ADR-002 (zéro latence I/O disque lors des prédictions).
    """

    def __init__(
        self,
        model_pipeline: Optional[Pipeline] = None,
        model_version: str = MODEL_VERSION,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        self.model = model_pipeline
        self.model_version = model_version
        self.threshold = threshold

    def is_ready(self) -> bool:
        """Indique si le modèle est chargé et opérationnel pour l'inférence."""
        return self.model is not None

    def predict_order(
        self,
        order: Union[Dict[str, Any], OrderFeatures],
        order_id: Optional[str] = None,
    ) -> Prediction:
        """
        Effectue une prédiction unitaire synchrone.
        (Cellule 34 du notebook & POST /v1/predictions)
        """
        if not self.is_ready():
            raise ModelNotLoadedError("Le modèle ML n'est pas chargé en mémoire.")

        start_time = time.perf_counter()

        # Conversion en dictionnaire
        if isinstance(order, OrderFeatures):
            data = order.model_dump()
            resolved_order_id = order.order_id or order_id or "CMD-UNKNOWN"
        else:
            data = dict(order)
            resolved_order_id = data.get("order_id") or order_id or "CMD-UNKNOWN"

        # Pour les enums Pydantic éventuels
        for field in ["weather", "delivery_zone", "customer_type"]:
            if hasattr(data.get(field), "value"):
                data[field] = data[field].value

        input_df = pd.DataFrame([{feature: data[feature] for feature in FEATURE_COLUMNS}])

        proba = float(self.model.predict_proba(input_df)[0, 1])
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        eligible = proba >= self.threshold
        decision = "oui" if eligible else "non"

        return Prediction(
            order_id=resolved_order_id,
            express_eligible=eligible,
            decision=decision,
            probability=round(proba, 4),
            model_version=self.model_version,
            predicted_at=datetime.utcnow(),
            latency_ms=round(latency_ms, 2),
        )

    def predict_batch(
        self,
        orders: List[Union[Dict[str, Any], OrderFeatures]],
    ) -> BatchPredictionResponse:
        """
        Effectue une prédiction par lot (vectorisée).
        (Cellule 46 du notebook & POST /v1/predictions/batch)
        """
        if not self.is_ready():
            raise ModelNotLoadedError("Le modèle ML n'est pas chargé en mémoire.")

        start_time = time.perf_counter()
        rows = []
        order_ids = []

        for idx, order in enumerate(orders):
            if isinstance(order, OrderFeatures):
                data = order.model_dump()
                resolved_id = order.order_id or f"CMD-BATCH-{idx:04d}"
            else:
                data = dict(order)
                resolved_id = data.get("order_id") or f"CMD-BATCH-{idx:04d}"

            for field in ["weather", "delivery_zone", "customer_type"]:
                if hasattr(data.get(field), "value"):
                    data[field] = data[field].value

            rows.append({feature: data[feature] for feature in FEATURE_COLUMNS})
            order_ids.append(resolved_id)

        input_df = pd.DataFrame(rows)
        probabilities = self.model.predict_proba(input_df)[:, 1]
        now = datetime.utcnow()
        avg_latency = ((time.perf_counter() - start_time) * 1000.0) / max(len(orders), 1)

        predictions: List[Prediction] = []
        for oid, proba in zip(order_ids, probabilities):
            p = float(proba)
            eligible = p >= self.threshold
            predictions.append(
                Prediction(
                    order_id=oid,
                    express_eligible=eligible,
                    decision="oui" if eligible else "non",
                    probability=round(p, 4),
                    model_version=self.model_version,
                    predicted_at=now,
                    latency_ms=round(avg_latency, 2),
                )
            )

        return BatchPredictionResponse(
            predictions=predictions,
            count=len(predictions),
        )
