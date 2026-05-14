# from fastapi import FastAPI
# from contextlib import asynccontextmanager
# from fastapi.staticfiles import StaticFiles
# import os
# from pathlib import Path
# from fastapi.middleware.cors import CORSMiddleware
# from app.routes import weather_routes, market_routes
# from app.routes import community_routes
# from app.routes import crops_routes
# from app.routes import fertilizer_routes
# from app.routes import soil_routes
# from app.routes import pest_routes
# from app.routes import weed_routes
# from app.routes import soil_ph_routes
# from app.routes import user_routes
# from app.routes import chatbot_routes
# from .database import Base, engine
# from .models import user  
# from .models import crop
# from .models import community_post
# from .models import community_post_image
# from .models import community_comment

# # --- MiniRAG imports for startup initialization ---
# from app.services.Embedding_and_Retrivel import init_minirag, add_json_files
# import logging

# def _dataset_paths():
#     import pathlib
#     root = pathlib.Path(__file__).resolve().parents[1]
#     files = [
#         root / "dataset" / "pest.json",
#         root / "dataset" / "weed.json",
#         root / "dataset" / "village_plant_disease_dataset.json",
#     ]
#     return [str(path) for path in files if path.exists()]


# def _minirag_storage_has_index() -> bool:
#     """Check if a prebuilt MiniRAG index already exists.

#     If the vector DB files are present, we can skip the expensive
#     dataset ingestion step during app startup. This is important
#     for Azure App Service, which has a strict startup time limit.
#     """
#     root = Path(__file__).resolve().parents[1]
#     storage_dir = root / "minirag_storage"
#     vdb_path = storage_dir / "vdb_chunks.json"
#     text_path = storage_dir / "kv_store_text_chunks.json"
#     return vdb_path.exists() and text_path.exists()

# # @asynccontextmanager
# # async def lifespan(app: FastAPI):
# #     Base.metadata.create_all(bind=engine)
# #     # --- MiniRAG and dataset initialization ---
# #     try:
# #         logging.info("[STARTUP] Initializing MiniRAG...")
# #         rag = init_minirag()

# #         if _minirag_storage_has_index():
# #             # We already have a prebuilt index (minirag_storage/*). Avoid
# #             # re-ingesting JSON on every container start to keep Azure
# #             # startup times well within limits.
# #             logging.info("[STARTUP] Existing MiniRAG index detected; skipping dataset ingestion.")
# #         else:
# #             logging.info("[STARTUP] No existing MiniRAG index detected; loading datasets once...")
# #             dataset_files = _dataset_paths()
# #             if dataset_files:
# #                 add_json_files(rag, dataset_files)
# #             else:
# #                 logging.warning("[STARTUP] No dataset files found for MiniRAG initialization.")

# #         app.state.rag = rag
# #         logging.info("[STARTUP] MiniRAG initialization complete.")
# #     except Exception as exc:
# #         logging.exception(f"[STARTUP] MiniRAG initialization failed: {exc}")
# #         app.state.rag = None
# #     yield

# # app = FastAPI(lifespan=lifespan)

# app = FastAPI()

# os.makedirs("media", exist_ok=True)
# app.mount("/media", StaticFiles(directory="media"), name="media")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(weather_routes.router, prefix="/weather", tags=["weather"])
# app.include_router(market_routes.router, prefix="/market", tags=["market"])
# app.include_router(community_routes.router)
# app.include_router(crops_routes.router)
# app.include_router(fertilizer_routes.router)
# app.include_router(soil_routes.router)
# app.include_router(pest_routes.router)
# app.include_router(weed_routes.router)
# app.include_router(soil_ph_routes.router)
# app.include_router(user_routes.router)
# app.include_router(chatbot_routes.router)

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the Farming Advisory API"}

# @app.get("/health")
# def health_check():
#     """Simple health check endpoint for uptime probes."""
#     return {"status": "ok", "service": "farming-advisory-api", "version": "1.0.0"}


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware

# routers
from app.routes import weather_routes, market_routes
from app.routes import community_routes
from app.routes import crops_routes
from app.routes import fertilizer_routes
from app.routes import soil_routes
from app.routes import pest_routes
from app.routes import weed_routes
from app.routes import soil_ph_routes
from app.routes import user_routes
from app.routes import chatbot_routes


# ==============================
# HEAVY IMPORTS (STARTUP)
# ==============================

from contextlib import asynccontextmanager
from pathlib import Path
from .database import Base, engine
from .models import user
from .models import crop
from .models import community_post
from .models import community_post_image
from .models import community_comment

# MiniRAG heavy loading will be imported during startup to avoid
# loading heavy models at module import time.
import logging


def _dataset_paths():
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    files = [
        root / "dataset" / "pest.json",
        root / "dataset" / "weed.json",
        root / "dataset" / "village_plant_disease_dataset.json",
    ]
    return [str(path) for path in files if path.exists()]


def _minirag_storage_has_index() -> bool:
    """Check if a prebuilt MiniRAG index already exists.

    If the vector DB files are present, we can skip the expensive
    dataset ingestion step during app startup. This is important
    for Azure App Service, which has a strict startup time limit.
    """
    root = Path(__file__).resolve().parents[1]
    storage_dir = root / "minirag_storage"
    vdb_path = storage_dir / "vdb_chunks.json"
    text_path = storage_dir / "kv_store_text_chunks.json"
    return vdb_path.exists() and text_path.exists()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB tables exist
    Base.metadata.create_all(bind=engine)

    # --- MiniRAG and dataset initialization ---
    try:
        logging.info("[STARTUP] Initializing MiniRAG...")
        # Import here to avoid heavy model loads during normal module import
        from app.services.Embedding_and_Retrivel import init_minirag, add_json_files

        rag = init_minirag()

        if _minirag_storage_has_index():
            logging.info("[STARTUP] Existing MiniRAG index detected; skipping dataset ingestion.")
        else:
            logging.info("[STARTUP] No existing MiniRAG index detected; loading datasets once...")
            dataset_files = _dataset_paths()
            if dataset_files:
                add_json_files(rag, dataset_files)
            else:
                logging.warning("[STARTUP] No dataset files found for MiniRAG initialization.")

        app.state.rag = rag
        logging.info("[STARTUP] MiniRAG initialization complete.")
    except Exception as exc:
        logging.exception(f"[STARTUP] MiniRAG initialization failed: {exc}")
        app.state.rag = None
    yield


app = FastAPI(lifespan=lifespan)


# ==============================
# FAST START APP
# ==============================

# static files
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================
# ROUTERS
# ==============================

app.include_router(weather_routes.router, prefix="/weather", tags=["weather"])
app.include_router(market_routes.router, prefix="/market", tags=["market"])
app.include_router(community_routes.router)
app.include_router(crops_routes.router)
app.include_router(fertilizer_routes.router)
app.include_router(soil_routes.router)
app.include_router(pest_routes.router)
app.include_router(weed_routes.router)
app.include_router(soil_ph_routes.router)
app.include_router(user_routes.router)
app.include_router(chatbot_routes.router)


# ==============================
# HEALTH ROUTES (IMPORTANT)
# ==============================

@app.get("/")
def read_root():
    return {"message": "Welcome to the Farming Advisory API"}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "farming-advisory-api",
        "version": "1.0.0"
    }