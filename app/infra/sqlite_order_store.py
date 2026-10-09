"""
Implémentation SQLite d'OrderStore pour la persistance locale.
Conforme à l'ADR-001 (Sections 5.1 et 5.3).
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from app.core.schemas import OrderFeatures
from app.interfaces.order_store import OrderStore


class SqliteOrderStore(OrderStore):
    """
    Store persistant de commandes basé sur SQLite.
    Garantit zéro friction de démarrage sans nécessiter un serveur externe en local.
    """

    def __init__(self, db_path: Union[str, Path] = "orders.db"):
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialise le schéma de la table orders si elle n'existe pas."""
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
                    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                    weekend INTEGER NOT NULL CHECK (weekend IN (0, 1)),
                    distance_km REAL NOT NULL CHECK (distance_km >= 0),
                    order_value_eur REAL NOT NULL CHECK (order_value_eur >= 0),
                    weight_kg REAL NOT NULL CHECK (weight_kg >= 0),
                    stock_available INTEGER NOT NULL CHECK (stock_available IN (0, 1)),
                    preparation_time_min REAL NOT NULL CHECK (preparation_time_min >= 0),
                    carrier_capacity REAL NOT NULL CHECK (carrier_capacity BETWEEN 0 AND 1),
                    weather TEXT NOT NULL,
                    delivery_zone TEXT NOT NULL,
                    customer_type TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    status TEXT DEFAULT 'accepted'
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at);")
            conn.commit()

    def save(self, order_data: Union[Dict[str, Any], OrderFeatures]) -> str:
        """Persiste une commande dans SQLite et retourne son order_id."""
        if isinstance(order_data, OrderFeatures):
            data = order_data.model_dump()
        else:
            data = dict(order_data)

        order_id = data.get("order_id")
        if not order_id:
            # Génère un identifiant séquentiel ou horodaté CMD-YYYYMMDD-XXXX
            now_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            import random
            rand_suffix = random.randint(100, 999)
            order_id = f"CMD-{now_str}-{rand_suffix}"
            data["order_id"] = order_id

        # Convert enums en strings si nécessaire
        for field in ["weather", "delivery_zone", "customer_type"]:
            if hasattr(data.get(field), "value"):
                data[field] = data[field].value

        query = """
            INSERT INTO orders (
                order_id, hour, day_of_week, weekend, distance_km,
                order_value_eur, weight_kg, stock_available,
                preparation_time_min, carrier_capacity, weather,
                delivery_zone, customer_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            order_id,
            int(data["hour"]),
            int(data["day_of_week"]),
            int(data["weekend"]),
            float(data["distance_km"]),
            float(data["order_value_eur"]),
            float(data["weight_kg"]),
            int(data["stock_available"]),
            float(data["preparation_time_min"]),
            float(data["carrier_capacity"]),
            str(data["weather"]),
            str(data["delivery_zone"]),
            str(data["customer_type"]),
            data.get("status", "accepted"),
        )

        with self._lock, self._get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

        return order_id

    def get_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une commande par son identifiant unique."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(row)

    def ping(self) -> bool:
        """Vérifie la disponibilité de SQLite pour la sonde /health/ready."""
        try:
            with self._get_connection() as conn:
                conn.execute("SELECT 1;").fetchone()
            return True
        except Exception:
            return False
