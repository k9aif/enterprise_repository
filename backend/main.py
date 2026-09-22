import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from backend.database import engine, init_schema, SCHEMA
from backend.models import Base
from backend.api.artifacts import router as artifacts_router
from backend.api.standards import router as standards_router, dispensations_router
from backend.api.entities import router as entities_router
from backend.api.search import router as search_router

_ROOT   = Path(__file__).resolve().parent.parent
_WEBUI  = _ROOT / "webui"
_STATIC = _WEBUI / "static"
_INDEX  = _WEBUI / "index.html"


class NoCacheStaticFiles(StaticFiles):
    """StaticFiles that always sends an explicit Cache-Control header.

    Without this, Cloudflare's own default Browser Cache TTL (commonly
    4h for .js/.css) silently takes over, so a rebuilt app.js can sit
    invisible behind the CDN for hours after a real deploy -- confirmed
    live 2026-09-22 on repo.k9x.ai: a real rebuild (verified present via
    a cache-busted request straight to the origin) was still invisible
    to a normal browser load, cf-cache-status: HIT, age: 2597s. Same bug
    class k9x-hil already hit and fixed this same way; ported here rather
    than rediscovered from scratch next time. no-cache (not no-store)
    still lets ETag-based conditional GETs return a cheap 304.
    """

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


app = FastAPI(title="k9x Enterprise Repository", version="0.1.0")

app.include_router(artifacts_router)
app.include_router(standards_router)
app.include_router(dispensations_router)
app.include_router(entities_router)
app.include_router(search_router)

if _STATIC.exists():
    app.mount("/static", NoCacheStaticFiles(directory=str(_STATIC)), name="static")


@app.on_event("startup")
def startup():
    init_schema()
    Base.metadata.create_all(bind=engine, checkfirst=True)


@app.get("/health")
def health():
    return {"status": "ok", "schema": SCHEMA}


@app.get("/api/v1/config")
def config():
    # Frontend link targets — env-driven so local dev points at :8085 while
    # a real deployment points at the live production host, without a
    # hardcoded URL baked into the static JS either way.
    return {"continuum_url": os.getenv("CONTINUUM_URL", "https://continuum.k9x.ai")}


@app.get("/{full_path:path}")
def serve_ui(full_path: str):
    if _INDEX.exists():
        return FileResponse(str(_INDEX))
    return {"error": "webui not found"}
