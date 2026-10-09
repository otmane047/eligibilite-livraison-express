"""
Tests fonctionnels du service d'inférence (PredictorService).
Aligné sur la cellule 39 du notebook.
"""

import unittest
from app.core.schemas import OrderFeatures
from app.infrastructure.local_model_store import LocalModelArtifactStore
from app.services.predictor import PredictorService


class TestPredictor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        store = LocalModelArtifactStore("artifacts")
        pipeline = store.load_model("1.0.0")
        cls.predictor = PredictorService(model_pipeline=pipeline, model_version="1.0.0")
        cls.valid_order = OrderFeatures(
            hour=10,
            day_of_week=1,
            weekend=0,
            distance_km=2.0,
            order_value_eur=50.0,
            weight_kg=1.0,
            stock_available=1,
            preparation_time_min=10.0,
            carrier_capacity=0.9,
            weather="normal",
            delivery_zone="centre",
            customer_type="premium",
        )

    def test_single_prediction_contract(self):
        """Vérifie le format et les bornes de la prédiction (cellule 39 du notebook)."""
        result = self.predictor.predict_order(self.valid_order, order_id="CMD-TEST-001")

        self.assertEqual(result.order_id, "CMD-TEST-001")
        self.assertIn(result.decision, {"oui", "non"})
        self.assertIsInstance(result.express_eligible, bool)
        self.assertGreaterEqual(result.probability, 0.0)
        self.assertLessEqual(result.probability, 1.0)
        self.assertEqual(result.model_version, "1.0.0")
        self.assertIsNotNone(result.latency_ms)
        self.assertGreaterEqual(result.latency_ms, 0.0)

    def test_batch_prediction_count_and_order(self):
        """Vérifie la cohérence de la prédiction par lot."""
        orders = [self.valid_order, self.valid_order, self.valid_order]
        batch_resp = self.predictor.predict_batch(orders)

        self.assertEqual(batch_resp.count, 3)
        self.assertEqual(len(batch_resp.predictions), 3)
        for pred in batch_resp.predictions:
            self.assertIn(pred.decision, {"oui", "non"})
            self.assertGreaterEqual(pred.probability, 0.0)


if __name__ == "__main__":
    unittest.main()
