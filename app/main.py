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
from sqlalchemy import inspect
from urllib.parse import urlparse, urlunparse
from .models import user
from .models import crop
from .models import community_post
from .models import community_post_image
from .models import community_comment

# MiniRAG heavy loading will be imported during startup to avoid
# loading heavy models at module import time.
import logging


def _safe_db_url_for_logs(url: str) -> str:
    """Return a redacted DB URL safe to write to logs."""
    try:
        parsed = urlparse(url)
    except Exception:
        return "<unparseable DATABASE_URL>"

    if not parsed.scheme:
        return "<missing scheme>"

    if parsed.scheme.startswith("sqlite"):
        return url

    # Redact password if present.
    if parsed.password is None:
        return url

    netloc = parsed.netloc
    # netloc is like user:pass@host:port
    if "@" in netloc and ":" in netloc.split("@", 1)[0]:
        userinfo, hostinfo = netloc.split("@", 1)
        user = userinfo.split(":", 1)[0]
        netloc = f"{user}:***@{hostinfo}"

    return urlunparse(parsed._replace(netloc=netloc))


def _dataset_paths():
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    files = [
        root / "app" / "dataset" / "pest.json",
        root / "app" / "dataset" / "weed.json",
        root / "app" / "dataset" / "village_plant_disease_dataset.json",
    ]
    return [str(path) for path in files if path.exists()]


def _minirag_storage_has_index() -> bool:
    """Check if a prebuilt MiniRAG index already exists.

    If the vector DB files are present, we can skip the expensive
    dataset ingestion step during app startup. This is important
    for Azure App Service, which has a strict startup time limit.
    """
    # Local path (repo root)
    root = Path(__file__).resolve().parents[1]
    local_storage_dir = root / "minirag_storage"

    # Azure App Service Linux note: only /home is persisted.
    azure_storage_dir = Path("/home/site/wwwroot/minirag_storage")

    candidate_dirs = [local_storage_dir]
    if str(azure_storage_dir).startswith("/home"):
        candidate_dirs.append(azure_storage_dir)

    for storage_dir in candidate_dirs:
        vdb_path = storage_dir / "vdb_chunks.json"
        text_path = storage_dir / "kv_store_text_chunks.json"
        if vdb_path.exists() and text_path.exists():
            return True

    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB tables exist
    try:
        db_url = getattr(engine, "url", None)
        logging.info(f"[STARTUP] Database URL: {_safe_db_url_for_logs(str(db_url) if db_url else 'unknown')}")

        # Fail fast if DB is unreachable.
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        logging.info("[STARTUP] Database connection: OK")

        Base.metadata.create_all(bind=engine)
        logging.info("[STARTUP] Base.metadata.create_all(): complete")

        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        expected_tables = {
            "users",
            "crops",
            "community_posts",
            "community_post_images",
            "community_comments",
        }
        missing_tables = sorted(expected_tables - existing_tables)
        logging.info(f"[STARTUP] Tables found: {sorted(existing_tables)}")
        if missing_tables:
            logging.warning(f"[STARTUP] Expected tables missing AFTER create_all(): {missing_tables}")
        else:
            logging.info("[STARTUP] Expected tables exist: OK")

        # Column-level sanity checks (helps confirm correct schema in Azure Log Stream)
        expected_columns = {
            "users": {
                "id",
                "full_name",
                "phone",
                "weather_alert",
                "pest_alert",
                "market_update",
                "notification_alert",
                "created_at",
                "updated_at",
                "image_url",
                "location_name",
                "location_state",
                "location_district",
            },
            "crops": {"id", "user_id", "name", "created_at", "updated_at"},
            "community_posts": {
                "id",
                "user_id",
                "title",
                "content",
                "image_url",
                "likes_count",
                "comments_count",
                "created_at",
                "updated_at",
            },
            "community_comments": {
                "id",
                "post_id",
                "user_id",
                "content",
                "created_at",
                "updated_at",
            },
            "community_post_images": {"id", "post_id", "image_url", "created_at"},
        }

        for table_name, cols_expected in expected_columns.items():
            if table_name not in existing_tables:
                continue
            cols_actual = {col.get("name") for col in inspector.get_columns(table_name) if isinstance(col, dict)}
            missing_cols = sorted(set(cols_expected) - set(cols_actual))
            if missing_cols:
                logging.warning(
                    f"[STARTUP] Missing columns in {table_name}: {missing_cols} (create_all does not alter existing tables)"
                )
            else:
                logging.info(f"[STARTUP] Columns OK for {table_name}")

    except Exception as exc:
        logging.exception(f"[STARTUP] Database initialization failed: {exc}")
        raise

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