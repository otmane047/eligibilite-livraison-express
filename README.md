# Éligibilité à la Livraison Express - API & Architecture MLOps

Projet d'industrialisation et de mise en production d'un modèle de Machine Learning pour l'évaluation en temps réel de l'éligibilité des commandes à la livraison express (**M2 IA dans le Cloud - TP1**).

---

## 1. Présentation du Projet

Ce projet transforme le notebook d'expérimentation initial (`project_test_v1_final_final2.ipynb`) en une application modulaire et robuste respectant :
* Le contrat d'API fourni dans [`openapi.yml`](openapi.yml).
* Les **Architecture Decision Records (ADR)** :
  * [**ADR-001**](docs/adr/ADR-001-stockage-des-commandes.md) : Persistance des commandes via le Repository Pattern (`OrderStore` : SQLite et In-Memory).
  * [**ADR-002**](docs/adr/ADR-002-stockage-des-artefacts-de-modele.md) : Découplage du stockage d'artefacts (`ModelArtifactStore`) et mise en cache mémoire au démarrage de l'API (`lifespan` FastAPI) pour une latence d'inférence minimale.

---

## 2. Architecture Logicielle

Le projet est structuré selon les principes de la **Clean Architecture** (Architecture Hexagonale) :

```text
tp1/
├── app/
│   ├── api/                   # Couche Présentation (FastAPI, Routers, Lifespan)
│   │   ├── deps.py            # Injection de dépendances
│   │   ├── main.py            # Application FastAPI & Gestionnaires d'erreurs
│   │   └── routes/            # Endpoints REST (health, orders, predictions, model)
│   ├── core/                  # Domaine & Transverse
│   │   ├── config.py          # Constantes, features, chemins d'artefacts
│   │   ├── exceptions.py      # Hiérarchie d'exceptions typées
│   │   └── schemas.py         # Schémas Pydantic V2 conformes à openapi.yml
│   ├── infrastructure/        # Adaptateurs d'infrastructure concrets
│   │   ├── in_memory_order_store.py  # Store en mémoire (tests isolés)
│   │   ├── local_model_store.py      # Chargement des artefacts Joblib/JSON
│   │   └── sqlite_order_store.py     # Store persistant SQLite local
│   ├── interfaces/            # Ports / Contrats d'abstraction (ABC)
│   │   ├── model_store.py     # Interface abstraite ModelArtifactStore
│   │   └── order_store.py     # Interface abstraite OrderStore
│   └── services/              # Logique métier & Pipeline ML
│       ├── data_generator.py  # Générateur de commandes synthétiques
│       ├── data_quality.py    # Contrôles qualité et nettoyage ETL
│       ├── predictor.py       # Moteur d'inférence unitaire et batch
│       └── trainer.py         # Entraînement Scikit-learn & MLflow
├── tests/                     # Suite complète de tests unitaires et d'intégration
│   ├── test_api.py
│   ├── test_data_quality.py
│   ├── test_infra.py
│   └── test_predictor.py
├── artifacts/                 # Artefacts versionnés générés par l'entraînement
│   ├── express_delivery_model.joblib
│   ├── features.json
│   ├── metrics.json
│   └── model_card.json
├── docs/                      # Registre des décisions d'architecture (ADR)
│   └── adr/
├── scripts/                   # Scripts d'automatisation et CLI
│   ├── run_server.py          # Lancement de l'API Uvicorn
│   └── train.py               # Entraînement du modèle
├── .env.example               # Modèle de variables d'environnement
├── openapi.yml                # Contrat OpenAPI de référence
└── requirements.txt           # Dépendances du projet
```

---

## 3. Guide de Démarrage Rapide

### 3.1. Installation des dépendances

```bash
# Activation de l'environnement virtuel (sous Windows)
.\.venv\Scripts\activate

# Installation des dépendances
pip install -r requirements.txt
```

### 3.2. Configuration de l'environnement (.env)

Copiez le fichier d'exemple pour initialiser votre configuration locale :

```bash
copy .env.example .env
```

Vous pouvez y ajuster `DATABASE_URL`, `DEFAULT_THRESHOLD`, `API_PORT`, etc.

### 3.3. Entraînement du modèle (Génération des artefacts)

Pour exécuter le pipeline d'entraînement complet, calculer les métriques et générer les fichiers dans `artifacts/` :

```bash
python scripts/train.py
```

*Optionnel :* désactiver MLflow si vous ne l'utilisez pas localement :
```bash
python scripts/train.py --no-mlflow
```

### 3.4. Lancement de l'API

Démarrez le serveur FastAPI simplement avec :

```bash
python main.py
```
ou avec Uvicorn en CLI :
```bash
uvicorn main:app --reload
```
ou via le script dédié :
```bash
python scripts/run_server.py
```

L'API est alors disponible sur :
* **Swagger UI (documentation interactive)** : [http://localhost:8000/docs](http://localhost:8000/docs)
* **Spécification OpenAPI générée** : [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 4. Endpoints de l'API

| Méthode | Route | Tag | Séance | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | `health` | 1 | Sonde de vivacité (répond 200 si le processus est vivant) |
| `GET` | `/health/ready` | `health` | 1 | Sonde de disponibilité (200 si le modèle est chargé et le stockage joignable, sinon 503) |
| `POST` | `/v1/orders` | `orders` | 1 | Enregistrement immédiat d'une commande (retourne 202 Accepted) |
| `GET` | `/v1/orders/{order_id}` | `orders` | 1 | Consultation d'une commande persistée (200 ou 404) |
| `POST` | `/v1/predictions` | `predictions` | 1 | Prédiction synchrone d'éligibilité express d'une commande |
| `POST` | `/v1/predictions/batch`| `predictions` | 5 | Prédiction par lot pour une liste de commandes |
| `GET` | `/v1/predictions/{order_id}` | `predictions` | 5 | Relecture / historique d'une prédiction |
| `GET` | `/v1/model` | `model` | 3 | Métadonnées complètes et métriques du modèle en service (Model Card) |

---

## 5. Exécution des Tests Automatisés

Le projet comprend **19 tests automatisés** couvrant la qualité des données, l'inférence, les adaptateurs d'infrastructure et les routes de l'API :

```bash
python -m unittest discover -s tests -v
```

Tous les tests s'exécutent en isolation sans dépendance de réseau externe.
