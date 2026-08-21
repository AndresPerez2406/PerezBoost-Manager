from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.core.database import engine, Base
from backend.routers import (
    auth_router,
    pedidos_router,
    inventario_router,
    boosters_router,
    ranking_router,
    finanzas_router,
    tarifas_router,
    wallet_router
)

# Inicializar tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST Centralizada para PerezBoost Pro SaaS",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Registrar Routers bajo /api/v1
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(pedidos_router, prefix=settings.API_V1_STR)
app.include_router(inventario_router, prefix=settings.API_V1_STR)
app.include_router(boosters_router, prefix=settings.API_V1_STR)
app.include_router(ranking_router, prefix=settings.API_V1_STR)
app.include_router(finanzas_router, prefix=settings.API_V1_STR)
app.include_router(tarifas_router, prefix=settings.API_V1_STR)
app.include_router(wallet_router, prefix=settings.API_V1_STR)

@app.get("/api/health", tags=["Root"])
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

# Montar frontend estático si existe la carpeta
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")

    @app.get("/", tags=["Frontend"])
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

