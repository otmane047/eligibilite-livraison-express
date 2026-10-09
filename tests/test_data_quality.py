"""
Tests unitaires pour les fonctions de validation et nettoyage des données (data_quality.py).
Aligné sur les cellules 14 et 18 du notebook.
"""

import unittest
import pandas as pd
import numpy as np

from app.services.data_generator import generate_orders_dataset
from app.services.data_quality import clean_orders_data, validate_dataset


class TestDataQuality(unittest.TestCase):
    def setUp(self):
        self.df = generate_orders_dataset(n_rows=100, random_state=42)

    def test_valid_dataset_passes(self):
        """Vérifie qu'un dataset propre passe tous les contrôles sans exception."""
        self.assertTrue(validate_dataset(self.df))

    def test_missing_column_raises_error(self):
        """Vérifie qu'une colonne obligatoire absente déclenche un ValueError."""
        bad_df = self.df.drop(columns=["distance_km"])
        with self.assertRaises(ValueError):
            validate_dataset(bad_df)

    def test_duplicate_order_id_raises_error(self):
        """Vérifie que la présence de doublons sur order_id déclenche un ValueError."""
        bad_df = pd.concat([self.df, self.df.iloc[[0]]], ignore_index=True)
        with self.assertRaises(ValueError):
            validate_dataset(bad_df)

    def test_invalid_carrier_capacity_raises_error(self):
        """Vérifie qu'une capacité transporteur hors [0, 1] lève une erreur."""
        bad_df = self.df.copy()
        bad_df.loc[0, "carrier_capacity"] = 1.5
        with self.assertRaises(ValueError):
            validate_dataset(bad_df)

    def test_negative_distance_raises_error(self):
        """Vérifie qu'une distance négative lève une erreur."""
        bad_df = self.df.copy()
        bad_df.loc[0, "distance_km"] = -5.0
        with self.assertRaises(ValueError):
            validate_dataset(bad_df)

    def test_clean_orders_data_removes_duplicates_and_invalid(self):
        """Vérifie que clean_orders_data nettoie efficacement les doublons et valeurs négatives."""
        dirty_df = self.df.copy()
        # 1. Ajout d'un doublon (ligne 0 dupliquée)
        duplicate_row = dirty_df.iloc[[0]].copy()
        dirty_df = pd.concat([dirty_df, duplicate_row], ignore_index=True)

        # 2. Ajout d'une ligne avec une valeur aberrante (distance négative)
        invalid_row = dirty_df.iloc[[1]].copy()
        invalid_row["order_id"] = "CMD-INVALID-999"
        invalid_row["distance_km"] = -10.0
        dirty_df = pd.concat([dirty_df, invalid_row], ignore_index=True)

        self.assertEqual(len(dirty_df), len(self.df) + 2)

        cleaned = clean_orders_data(dirty_df)
        self.assertEqual(len(cleaned), len(self.df))
        self.assertTrue(validate_dataset(cleaned))


if __name__ == "__main__":
    unittest.main()
