# ADR-001 : Stratégie de stockage et persistance des commandes (Order Store)

* **Statut** : Accepté
* **Date** : 2026-10-06
* **Projet** : Éligibilité Livraison Express (`eligibilite-livraison-express`)
* **Cadre** : M2 IA dans le Cloud - TP1 (Industrialisation & Architecture MLOps)
* **Décideurs** : Équipe Architecture & MLOps

---

## 1. Contexte et Problématique

Dans le cadre de l'industrialisation de l'API de prédiction d'éligibilité à la livraison express (décrite dans le contrat d'interface `openapi.yml`), le service doit exposer une route de collecte de données :
* **`POST /v1/orders`** : Réceptionne les caractéristiques d'une commande (`OrderFeatures`), valide la structure (retourne une `422 Unprocessable Entity` en cas de non-respect du schéma), persiste la commande via une brique `OrderStore`, et retourne immédiatement un statut HTTP `202 Accepted` avec un identifiant de commande (`order_id`) et le statut `"accepted"`.
* **`GET /v1/orders/{order_id}`** : Permet de relire une commande précédemment collectée (retourne `200 OK` avec les données ou `404 Not Found`).
* **`GET /health/ready`** : Sonde de disponibilité (*readiness probe*) utilisée par l'orchestrateur (Kubernetes, AWS ECS, Cloud Run) pour vérifier que le service est prêt à recevoir du trafic, nécessitant le contrôle `checks.order_store: "reachable"`.

### Problématique
Comment concevoir le stockage persistant des commandes collectées afin de :
1. Répondre aux contraintes de **faible latence** et de **haute disponibilité** de l'ingestion (`POST /v1/orders`) ?
2. Permettre un requêtage unitaire immédiat par clé (`GET /v1/orders/{order_id}`) ?
3. Respecter les principes **SOLID**, **DRY** et **YAGNI** en évitant une sur-ingénierie prématurée en début de projet tout en garantissant une scalabilité fluide vers le Cloud (séances 2 à 7) ?
4. Alimenter les futurs pipelines de prédiction asynchrone (séance 1 & 5), d'historisation, de détection de dérive de données (*data drift*, séance 7) et de réentraînement continu du modèle ML ?

---

## 2. Facteurs de Décision (Decision Drivers)

* **Conformité au contrat OpenAPI 3.1** : Implémentation stricte des endpoints `/v1/orders`, `/v1/orders/{order_id}` et de la sonde `/health/ready`.
* **Latence et Débit d'ingestion** : L'accusé de réception `202 Accepted` doit être retourné en moins de 50 ms.
* **Intégrité et Typage des données** : Les variables correspondent rigoureusement aux 12 features du modèle (`hour`, `distance_km`, `order_value_eur`, `weather`, etc.).
* **Portabilité Dev/Test/Cloud** : Facilité d'exécution en local sans dépendance lourde, transition sans réécriture de code vers un environnement cloud managé (AWS, GCP, Azure).
* **Testabilité unitaire et d'intégration** : Capacité à simuler ou isoler le stockage dans les tests automatisés (CI/CD).
* **Scalabilité et MLOps** : Capacité à extraire des lots de données pour le calcul de dérive (*drift monitoring*) et le réentraînement régulier.

---

## 3. Options Considérées

| Option | Description | Avantages | Inconvénients / Limites |
| :--- | :--- | :--- | :--- |
| **Option 1 : En mémoire (`InMemoryOrderStore`)** | Stockage dans un dictionnaire ou une liste Python en mémoire vive du processus. | • Zéro dépendance externe<br>• Démarrage instantané en local<br>• Latence sub-milliseconde | • Aucune persistance (perte des données à l'arrêt du conteneur)<br>• Impossible à partager entre plusieurs réplicas de l'API<br>• Incompatible avec la production Cloud |
| **Option 2 : Fichiers plats (JSON Lines / Parquet local ou S3)** | Écriture de chaque commande ou de lots dans des fichiers append-only. | • Format directement exploitable pour le ML (Pandas, DuckDB)<br>• Très simple pour de l'archivage | • Requêtage par `order_id` inefficace (scan complet de fichiers)<br>• Conflits d'écritures concurrentes sans verrou lourd<br>• Latence d'I/O imprévisible |
| **Option 3 : Base Relationnelle SQL (SQLite en dev / PostgreSQL en prod)** | Base relationnelle avec schéma strict aligné sur `OrderFeatures`, interfacée via SQLAlchemy / SQLModel. | • Schéma fortement typé et validation d'intégrité<br>• Indexation optimale sur `order_id` (`O(1)` ou `O(log N)`)<br>• SQLite sans serveur pour le dev et les tests<br>• PostgreSQL managé (AWS RDS, Cloud SQL) hautement scalable pour la prod<br>• Requêtage analytique natif pour le ML | • Nécessite la gestion des migrations (Alembic)<br>• Légère latence de connexion réseau en cloud (résolu par *connection pooling*) |
| **Option 4 : Base NoSQL Document (MongoDB / DynamoDB / Firestore)** | Stockage des commandes sous forme de documents JSON non structurés. | • Stockage JSON natif<br>• Excellente scalabilité horizontale en écriture<br>• Faible latence sur clé primaire | • Schéma moins rigide que les contraintes fortes du ML<br>• Complexité d'infrastructure supplémentaire pour un besoin déjà tabulaire<br>• Coût plus élevé en cloud |
| **Option 5 : Broker de messages (Kafka / RabbitMQ / Redis Streams) seul** | Envoi direct de la commande dans un topic / queue sans base de données transactionnelle. | • Asynchronisme pur<br>• Débit d'ingestion très élevé | • Ne permet pas de relire une commande spécifique à faible latence (`GET /v1/orders/{order_id}`)<br>• Nécessite tout de même un data store en aval |

---

## 4. Décision Retenue

Nous retenons l'**Option 3 : Base de données relationnelle SQL (SQLite en local & PostgreSQL en production Cloud)**, orchestrée via le **patron de conception Repository (Interface `OrderStore`)** selon le principe d'Inversion de Dépendance (DIP - SOLID).

### Justification de la décision :
1. **Adéquation structurelle avec le Machine Learning** : Les données d'une commande correspondent exactement à un tuple tabulaire structuré et typé (`FEATURE_COLUMNS`). Une table relationnelle avec typage strict empêche les corruptions silencieuses en amont du modèle.
2. **Double cible de déploiement (KISS / YAGNI)** :
   * En développement local et en intégration continue (CI) : utilisation de **SQLite** (en mémoire ou fichier local `./data/orders.db`). Démarrage en 0 seconde, zéro conteneur tiers requis.
   * En environnement Cloud (Staging & Production) : bascule transparente sur **PostgreSQL** (AWS Aurora/RDS ou GCP Cloud SQL) par simple changement de la variable d'environnement `DATABASE_URL`.
3. **Découplage architectural (Repository Pattern)** : Le code applicatif FastAPI ne manipule que l'interface abstraite `OrderStore`. L'implémentation concrète est injectée via le système de dépendances de FastAPI (`Depends(get_order_store)`).
4. **Préparation du flux asynchrone (Séances 5 & 6)** :
   * Pour la séance 1 : L'écriture en base via `OrderStore.save()` persiste la commande avec le statut `PENDING`.
   * Pour les séances ultérieures : Une file d'attente (Redis Streams ou Kafka) ou un worker de fond (Celery / BackgroundTasks) viendra consommer les commandes persistées pour exécuter la prédiction et mettre à jour le statut.

---

## 5. Architecture Technique et Implémentation

### 5.1. Schéma Relationnel de la Table `orders`

```sql
CREATE TABLE orders (
    order_id VARCHAR(64) PRIMARY KEY,
    hour SMALLINT NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    weekend SMALLINT NOT NULL CHECK (weekend IN (0, 1)),
    distance_km DOUBLE PRECISION NOT NULL CHECK (distance_km >= 0),
    order_value_eur DOUBLE PRECISION NOT NULL CHECK (order_value_eur >= 0),
    weight_kg DOUBLE PRECISION NOT NULL CHECK (weight_kg >= 0),
    stock_available SMALLINT NOT NULL CHECK (stock_available IN (0, 1)),
    preparation_time_min DOUBLE PRECISION NOT NULL CHECK (preparation_time_min >= 0),
    carrier_capacity DOUBLE PRECISION NOT NULL CHECK (carrier_capacity BETWEEN 0 AND 1),
    weather VARCHAR(16) NOT NULL,
    delivery_zone VARCHAR(32) NOT NULL,
    customer_type VARCHAR(16) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'accepted'
);

CREATE INDEX idx_orders_created_at ON orders (created_at);
```

### 5.2. Contrat d'Interface Abstraite (`OrderStore`)

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class OrderStore(ABC):
    """Interface abstraite définissant les opérations sur les commandes."""

    @abstractmethod
    def save(self, order_data: Dict[str, Any]) -> str:
        """
        Persiste une commande et retourne son order_id (généré ou fourni).
        Lève une exception si l'écriture échoue.
        """
        pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les features d'une commande par son identifiant.
        Retourne None si introuvable.
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Vérifie la disponibilité du support de stockage pour la sonde /health/ready.
        """
        pass
```

### 5.3. Implémentations prévues

1. **`InMemoryOrderStore`** : Dictionnaire thread-safe utilisé pour les tests unitaires isolés.
2. **`SqliteOrderStore`** : Implémentation par défaut pour le développement local (fichier SQLite local).
3. **`SqlAlchemyOrderStore`** : Implémentation générique basée sur SQLAlchemy / SQLModel, supportant indifféremment SQLite et PostgreSQL via la chaîne de connexion.

---

## 6. Conséquences

### Positives
* **Zéro friction de démarrage** : Les étudiants et développeurs lancent l'application immédiatement sans nécessiter Docker ou un serveur SQL externe en séance 1.
* **Respect rigoureux du contrat d'API** : Réponse immédiate 202 Accepted, restitution 200/404 sur `GET /v1/orders/{order_id}`, et intégration directe dans la sonde `/health/ready`.
* **Traçabilité & Auditabilité MLOps** : Chaque commande est horodatée et archivée pour la détection de dérive (*data drift*) et les réentraînements ultérieurs.
* **Facilité de migration** : L'adoption d'un ORM et du pattern Repository permet de passer à PostgreSQL managé en production par simple variable d'environnement sans modifier le code métier.

### Négatives / Compromis
* **Maintenance du schéma** : En production, les modifications de colonnes requièrent des migrations de schéma (Alembic).
* **Gestion des connexions en Cloud** : Nécessite la configuration d'un pool de connexions (`pool_size`, `max_overflow`) pour éviter l'épuisement des connexions lors des pics de requêtes.

---

## 7. Feuille de Route d'Évolution (Par Séance)

* **Séance 1 (Socle API)** : Implémentation de `OrderStore` (interface) + `SqliteOrderStore` pour persister `POST /v1/orders` et servir `GET /v1/orders/{order_id}` et `/health/ready`.
* **Séance 2 (Déploiement)** : Conteneurisation Docker avec volume monté pour SQLite ou connexion à un service PostgreSQL managé.
* **Séance 5 (Batch & Historique)** : Requêtage par lot dans `OrderStore` pour traiter les commandes en attente (`status = 'accepted' -> 'processed'`).
* **Séance 6 (Temps Réel)** : Couplage de `OrderStore.save()` avec la publication d'un événement `OrderEvent` sur message broker.
* **Séance 7 (Observabilité)** : Exposition de métriques Prometheus (`orders_collected_total`, latence d'écriture DB).
