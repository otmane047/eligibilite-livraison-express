"""
Script de lancement du serveur API en local.
Usage:
    python scripts/run_server.py [--host 0.0.0.0] [--port 8000] [--reload]
"""

import argparse
import sys
from pathlib import Path
import uvicorn

# Ajoute la racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import API_HOST, API_PORT


def main():
    parser = argparse.ArgumentParser(description="Lance le serveur API FastAPI.")
    parser.add_argument("--host", type=str, default=API_HOST, help=f"Hôte d'écoute (défaut: {API_HOST})")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Port d'écoute (défaut: {API_PORT})")
    parser.add_argument("--reload", action="store_true", default=True, help="Rechargement à chaud")
    args = parser.parse_args()

    print(f"Démarrage de l'API sur http://{args.host}:{args.port}")
    print(f"Documentation Swagger UI : http://{args.host}:{args.port}/docs")
    print(f"Spécification OpenAPI : http://{args.host}:{args.port}/openapi.json")

    uvicorn.run(
        "app.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
