from backend.routers.auth import router as auth_router
from backend.routers.pedidos import router as pedidos_router
from backend.routers.inventario import router as inventario_router
from backend.routers.boosters import router as boosters_router
from backend.routers.ranking import router as ranking_router
from backend.routers.finanzas import router as finanzas_router
from backend.routers.tarifas import router as tarifas_router
from backend.routers.wallet import router as wallet_router

__all__ = [
    "auth_router",
    "pedidos_router",
    "inventario_router",
    "boosters_router",
    "ranking_router",
    "finanzas_router",
    "tarifas_router",
    "wallet_router"
]
