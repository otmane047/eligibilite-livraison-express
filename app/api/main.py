"""
Point d'entrée principal de l'application FastAPI.
Configure le cycle de vie (lifespan), les gestionnaires d'erreurs contractuels et les routes.
"""

from contextlib import asynccontextmanager
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import API_TITLE, API_VERSION, ARTIFACTS_DIR, MODEL_VERSION
from app.core.exceptions import AppBaseException
from app.core.schemas import Error
from app.infrastructure.local_model_store import LocalModelArtifactStore
from app.infrastructure.sqlite_order_store import SqliteOrderStore
from app.services.predictor import PredictorService

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire de cycle de vie de l'application (FastAPI lifespan).
    Conforme à l'ADR-002 :
    - Charge la pipeline Scikit-learn en mémoire au démarrage (Singleton).
    - Initialise l'OrderStore pour la persistance des commandes (ADR-001).
    - Zéro latence disque lors du traitement des requêtes d'inférence.
    """
    # 1. Initialisation du stockage des artefacts
    artifact_store = LocalModelArtifactStore(artifacts_dir=ARTIFACTS_DIR)
    app.state.artifact_store = artifact_store

    try:
        model = artifact_store.load_model(MODEL_VERSION)
        metadata = artifact_store.load_metadata(MODEL_VERSION)
        app.state.predictor = PredictorService(
            model_pipeline=model,
            model_version=MODEL_VERSION,
        )
        app.state.model_metadata = metadata
        app.state.model_ready = True
        logger.info(f"Modèle ML v{MODEL_VERSION} chargé avec succès en mémoire.")
    except Exception as exc:
        logger.warning(f"Impossible de charger le modèle ML v{MODEL_VERSION} : {exc}")
        app.state.predictor = PredictorService(model_pipeline=None)
        app.state.model_metadata = None
        app.state.model_ready = False

    # 2. Initialisation du store de persistance des commandes (SQLite par défaut)
    app.state.order_store = SqliteOrderStore()
    logger.info("OrderStore (SQLite) initialisé.")

    yield

    logger.info("Arrêt de l'application.")


def create_app() -> FastAPI:
    """Factory de création et configuration de l'application FastAPI."""
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description="API de prédiction d'éligibilité à la livraison express.",
        lifespan=lifespan,
    )

    # ── Gestionnaires d'exceptions personnalisés (conformes au schéma Error) ────

    @app.exception_handler(AppBaseException)
    async def app_base_exception_handler(request: Request, exc: AppBaseException):
        payload = Error(
            error=exc.error,
            message=exc.message,
            details=exc.details if exc.details else None,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Formatage des erreurs Pydantic selon le contrat openapi.yml
        details = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()]
        first_msg = details[0] if details else "Erreur de validation de la requête."
        payload = Error(
            error="validation_error",
            message=first_msg,
            details=details,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Erreur interne inattendue : {exc}", exc_info=True)
        payload = Error(
            error="internal_server_error",
            message=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )

    # Inclusion des routers
    app.include_router(api_router)

    return app


app = create_app()
