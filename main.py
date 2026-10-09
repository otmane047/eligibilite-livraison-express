"""
Point d'entrée racine de l'application.

Permet de :
1. Lancer directement le serveur en local :
   python main.py

2. Lancer via Uvicorn en CLI :
   uvicorn main:app --reload
"""

import uvicorn
from app.api.main import app
from app.core.config import API_HOST, API_PORT

__all__ = ["app"]

if __name__ == "__main__":
    print(f"Démarrage de l'API sur http://{API_HOST}:{API_PORT}")
    print(f"Documentation Swagger UI : http://{API_HOST}:{API_PORT}/docs")
    print(f"Spécification OpenAPI : http://{API_HOST}:{API_PORT}/openapi.json")

    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )
