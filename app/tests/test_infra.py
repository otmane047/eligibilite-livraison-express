"""
Tests unitaires des composants d'infrastructure (OrderStores et ModelArtifactStore).
Aligné sur ADR-001 et ADR-002.
"""

import os
import tempfile
import unittest

from app.core.schemas import OrderFeatures
from app.infra.in_memory_order_store import InMemoryOrderStore
from app.infra.local_model_store import LocalModelArtifactStore
from app.infra.sqlite_order_store import SqliteOrderStore


class TestInfraStores(unittest.TestCase):
    def setUp(self):
        self.sample_order = OrderFeatures(
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

    def test_in_memory_order_store(self):
        store = InMemoryOrderStore()
        self.assertTrue(store.ping())

        oid = store.save(self.sample_order)
        self.assertTrue(oid.startswith("CMD-"))

        retrieved = store.get_by_id(oid)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["hour"], 14)

        # Simulation panne
        store.set_healthy(False)
        self.assertFalse(store.ping())
        with self.assertRaises(RuntimeError):
            store.get_by_id(oid)

    def test_sqlite_order_store(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            tmp_db = f.name

        try:
            store = SqliteOrderStore(db_path=tmp_db)
            self.assertTrue(store.ping())

            oid = store.save(self.sample_order)
            self.assertTrue(oid.startswith("CMD-"))

            retrieved = store.get_by_id(oid)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved["order_id"], oid)
            self.assertEqual(retrieved["weather"], "normal")
            self.assertEqual(retrieved["status"], "accepted")

            # Inexistant
            self.assertIsNone(store.get_by_id("CMD-NON-EXISTENT"))
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)

    def test_local_model_artifact_store(self):
        store = LocalModelArtifactStore("artifacts")
        self.assertTrue(store.ping())

        model = store.load_model("1.0.0")
        self.assertIsNotNone(model)

        metadata = store.load_metadata("1.0.0")
        self.assertEqual(metadata["model_version"], "1.0.0")
        self.assertEqual(metadata["project"], "eligibilite-livraison-express")


if __name__ == "__main__":
    unittest.main()
