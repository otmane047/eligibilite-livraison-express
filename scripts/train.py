"""
Script CLI pour lancer l'entraînement du modèle et la génération des artefacts.
Usage:
    python scripts/train.py [--no-mlflow]
"""

import argparse
import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.trainer import train_and_evaluate
from app.core.config import ARTIFACTS_DIR


def main():
    parser = argparse.ArgumentParser(description="Entraîne le modèle d'éligibilité livraison express.")
    parser.add_argument("--no-mlflow", action="store_true", help="Désactive le tracking MLflow")
    parser.add_argument("--artifacts-dir", type=str, default=str(ARTIFACTS_DIR), help="Répertoire de sortie des artefacts")
    args = parser.parse_args()

    print("==================================================")
    print(" Lancement de l'entraînement du modèle ML")
    print("==================================================")

    pipeline, metrics, model_card = train_and_evaluate(
        artifacts_dir=Path(args.artifacts_dir),
        track_mlflow=not args.no_mlflow,
    )

    print("\nEntraînement terminé avec succès !")
    print("Métriques obtenues :")
    for k, v in metrics.items():
        print(f"  - {k:>12} : {v:.4f}")
    print(f"\nArtefacts enregistrés dans : {args.artifacts_dir}")


if __name__ == "__main__":
    main()
