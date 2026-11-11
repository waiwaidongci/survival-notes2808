import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from sqlalchemy import text
from .config.database import Base,engine,SessionLocal
from .config.settings import SEED_DEMO,ARTIFACT_DIR
from . import models
from .routes import auth,cohorts,followups,runs,notes,audits
from .middlewares.errors import ErrorMiddleware
from .middlewares.rate_limit import RateLimitMiddleware
from .services.job_queue import queue
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    Path(ARTIFACT_DIR).mkdir(parents=True,exist_ok=True)
    try:
        from .services.recovery_service import backfill_legacy_runs,reconcile_artifacts
        with SessionLocal() as db:
            backfill_legacy_runs(db);reconcile_artifacts(db)
    except Exception:logging.exception("startup recovery failed")
    if SEED_DEMO:
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception:logging.exception("demo seed failed")
    yield
app=FastAPI(title="纸鹤展陈耐久研究簿",lifespan=lifespan)
app.add_middleware(ErrorMiddleware);app.add_middleware(RateLimitMiddleware)
for module in [auth,cohorts,followups,runs,notes,audits]:app.include_router(module.router)
@app.get("/health")
def health():
    with engine.connect() as c:c.execute(text("select 1"))
    queue.ping();return {"status":"healthy","service":"survival-notes"}
