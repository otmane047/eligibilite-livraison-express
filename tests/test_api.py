"""
Tests d'intégration des routes de l'API.
Conforme aux spécifications de openapi.yml.
"""

import unittest
from unittest.mock import MagicMock

from app.api.routes.health import get_health, get_readiness
from app.api.routes.model import get_model_card
from app.api.routes.orders import create_order, get_order
from app.api.routes.predictions import create_batch_predictions, create_prediction
from app.core.exceptions import OrderNotFoundError
from app.core.schemas import BatchPredictionRequest, OrderFeatures
from app.infrastructure.in_memory_order_store import InMemoryOrderStore
from app.infrastructure.local_model_store import LocalModelArtifactStore
from app.services.predictor import PredictorService


class TestApiRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = InMemoryOrderStore()
        cls.artifact_store = LocalModelArtifactStore("artifacts")
        pipeline = cls.artifact_store.load_model("1.0.0")
        cls.metadata = cls.artifact_store.load_metadata("1.0.0")
        cls.predictor = PredictorService(model_pipeline=pipeline, model_version="1.0.0")

        cls.sample_order = OrderFeatures(
            hour=14,
            day_of_week=2,
            weekend=0,
            distance_km=3.5,
            order_value_eur=89.9,
            weight_kg=2.4,
            stock_available=1,
            preparation_time_min=18.0,
            carrier_capacity=0.85,
            weather="normal",
            delivery_zone="centre",
            customer_type="premium",
        )

    def setUp(self):
        self.store.clear()
        self.store.set_healthy(True)

    def test_get_health(self):
        """Vérifie la sonde de vivacité (/health)."""
        health = get_health()
        self.assertEqual(health.status, "ok")
        self.assertEqual(health.service, "eligibilite-livraison-express")

    def test_get_readiness_ready(self):
        """Vérifie que la sonde répond 200 quand tout est opérationnel (/health/ready)."""
        response = get_readiness(predictor=self.predictor, order_store=self.store)
        self.assertEqual(response.status_code, 200)

    def test_get_readiness_not_ready_on_unloaded_model(self):
        """Vérifie que la sonde répond 503 si le modèle n'est pas chargé (/health/ready)."""
        unready_predictor = PredictorService(model_pipeline=None)
        response = get_readiness(predictor=unready_predictor, order_store=self.store)
        self.assertEqual(response.status_code, 503)

    def test_create_and_get_order(self):
        """Vérifie le flux de collecte et de restitution (/v1/orders)."""
        accepted = create_order(self.sample_order, order_store=self.store)
        self.assertEqual(accepted.status, "accepted")
        self.assertTrue(accepted.order_id.startswith("CMD-"))

        retrieved = get_order(accepted.order_id, order_store=self.store)
        self.assertEqual(retrieved.hour, 14)
        self.assertEqual(retrieved.distance_km, 3.5)

    def test_get_order_not_found(self):
        """Vérifie qu'un identifiant inexistant lève OrderNotFoundError (404)."""
        with self.assertRaises(OrderNotFoundError):
            get_order("CMD-UNKNOWN", order_store=self.store)

    def test_create_prediction(self):
        """Vérifie la prédiction unitaire (/v1/predictions)."""
        pred = create_prediction(self.sample_order, predictor=self.predictor)
        self.assertIn(pred.decision, {"oui", "non"})
        self.assertGreaterEqual(pred.probability, 0.0)
        self.assertLessEqual(pred.probability, 1.0)

    def test_create_batch_predictions(self):
        """Vérifie la prédiction par lot (/v1/predictions/batch)."""
        req = BatchPredictionRequest(orders=[self.sample_order, self.sample_order])
        resp = create_batch_predictions(req, predictor=self.predictor)
        self.assertEqual(resp.count, 2)
        self.assertEqual(len(resp.predictions), 2)

    def test_get_model_card(self):
        """Vérifie la route d'exposition de la model card (/v1/model)."""
        mock_request = MagicMock()
        mock_request.app.state.model_metadata = self.metadata
        card = get_model_card(mock_request)
        self.assertEqual(card.project, "eligibilite-livraison-express")
        self.assertEqual(card.model_version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
