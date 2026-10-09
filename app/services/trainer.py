"""
Pipeline d'entraînement et d'évaluation du modèle Scikit-learn avec suivi MLflow.
Extrait des cellules 20, 24, 26, 41 et 55 du notebook.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import mlflow
import mlflow.sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.core.config import (
    ARTIFACTS_DIR,
    CATEGORICAL_FEATURES,
    DEFAULT_THRESHOLD,
    FEATURE_COLUMNS,
    FEATURES_PATH,
    MODEL_VERSION,
    NUMERIC_FEATURES,
    PROJECT_NAME,
    RANDOM_STATE,
    TARGET_COLUMN,
)
from app.infrastructure.local_model_store import LocalModelArtifactStore
from app.services.data_generator import generate_orders_dataset
from app.services.data_quality import clean_orders_data, validate_dataset


def build_model_pipeline() -> Pipeline:
    """
    Construit la pipeline Scikit-learn (préprocesseur + régression logistique).
    (Cellule 24 du notebook)
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, NUMERIC_FEATURES),
            ("categorical", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )

    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def train_and_evaluate(
    df: Optional[Any] = None,
    artifacts_dir: Path = ARTIFACTS_DIR,
    experiment_name: str = "livraison-express",
    track_mlflow: bool = True,
) -> Tuple[Pipeline, Dict[str, float], Dict[str, Any]]:
    """
    Entraîne le modèle, évalue les métriques, trace l'expérience avec MLflow
    et sauvegarde les artefacts physiques.
    """
    if df is None:
        raw_df = generate_orders_dataset(n_rows=6000, random_state=RANDOM_STATE)
    else:
        raw_df = df

    # Nettoyage et validation
    orders_clean = clean_orders_data(raw_df)
    validate_dataset(orders_clean)

    X = orders_clean[FEATURE_COLUMNS]
    y = orders_clean[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    pipeline = build_model_pipeline()

    if track_mlflow:
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(run_name=f"logistic-regression-{MODEL_VERSION}") as run:
            pipeline.fit(X_train, y_train)

            y_pred = pipeline.predict(X_test)
            y_proba = pipeline.predict_proba(X_test)[:, 1]

            metrics = {
                "accuracy": float(round(accuracy_score(y_test, y_pred), 4)),
                "precision": float(round(precision_score(y_test, y_pred, zero_division=0), 4)),
                "recall": float(round(recall_score(y_test, y_pred, zero_division=0), 4)),
                "f1_score": float(round(f1_score(y_test, y_pred, zero_division=0), 4)),
                "roc_auc": float(round(roc_auc_score(y_test, y_proba), 4)),
            }

            mlflow.log_param("model_type", "LogisticRegression")
            mlflow.log_param("random_state", RANDOM_STATE)
            mlflow.log_param("feature_count", len(FEATURE_COLUMNS))
            for k, v in metrics.items():
                mlflow.log_metric(k, v)

            mlflow.sklearn.log_model(pipeline, artifact_path="model")
    else:
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]
        metrics = {
            "accuracy": float(round(accuracy_score(y_test, y_pred), 4)),
            "precision": float(round(precision_score(y_test, y_pred, zero_division=0), 4)),
            "recall": float(round(recall_score(y_test, y_pred, zero_division=0), 4)),
            "f1_score": float(round(f1_score(y_test, y_pred, zero_division=0), 4)),
            "roc_auc": float(round(roc_auc_score(y_test, y_proba), 4)),
        }

    # Création de la Model Card (Cellule 55 & openapi.yml)
    model_card = {
        "project": PROJECT_NAME,
        "model_version": MODEL_VERSION,
        "model_type": "Logistic regression",
        "task": "binary classification",
        "target": TARGET_COLUMN,
        "threshold": DEFAULT_THRESHOLD,
        "trained_at": datetime.utcnow().isoformat(),
        "features": FEATURE_COLUMNS,
        "metrics": metrics,
        "limitations": [
            "Le jeu de données utilisé est synthétique.",
            "La décision ne doit pas être utilisée sans validation des règles métier.",
            "Les performances peuvent varier sur des données réelles.",
            "Le modèle ne remplace pas une analyse des contraintes opérationnelles.",
        ],
    }

    # Sauvegarde via LocalModelArtifactStore (ADR-002)
    store = LocalModelArtifactStore(artifacts_dir=artifacts_dir)
    store.save_artifacts(
        version=MODEL_VERSION,
        model_pipeline=pipeline,
        metrics=metrics,
        model_card=model_card,
    )

    # Sauvegarde features.json
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    with open(artifacts_dir / "features.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "model_version": MODEL_VERSION,
                "target": TARGET_COLUMN,
                "features": FEATURE_COLUMNS,
                "numeric_features": NUMERIC_FEATURES,
                "categorical_features": CATEGORICAL_FEATURES,
            },
            f,
            indent=2,
        )

    return pipeline, metrics, model_card
