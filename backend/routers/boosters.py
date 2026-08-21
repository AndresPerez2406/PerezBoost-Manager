from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import require_admin, get_current_user, hash_password
from backend.models.booster import Booster
from backend.models.pedido import Pedido
from backend.schemas.booster import BoosterCreate, BoosterUpdate, BoosterResponse
from backend.schemas.pedido import PedidoResponse

router = APIRouter(prefix="/boosters", tags=["Boosters & Staff"])

# =============================================================================
# ENDPOINTS DE AUTOSERVICIO DEL BOOSTER (ROL: BOOSTER O ADMIN)
# =============================================================================

@router.get("/me/pedidos", response_model=List[PedidoResponse])
def get_mis_pedidos(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    nombre = current_user.get("name")
    return db.query(Pedido).filter(Pedido.booster_nombre == nombre).order_by(Pedido.id.desc()).all()

@router.get("/me/saldo", response_model=dict)
def get_mi_saldo(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    nombre = current_user.get("name")
    pedidos_pendientes = db.query(Pedido).filter(
        Pedido.booster_nombre == nombre,
        Pedido.estado == "Terminado",
        (Pedido.pago_realizado == 0) | (Pedido.pago_realizado.is_(None))
    ).all()
    
    total = sum(float(p.pago_booster or 0.0) for p in pedidos_pendientes)
    return {
        "booster": nombre,
        "saldo_pendiente": round(total, 2),
        "pedidos_pendientes": len(pedidos_pendientes)
    }

@router.patch("/me/perfil", response_model=BoosterResponse)
def actualizar_mi_perfil(
    binance: Optional[str] = None,
    discord_id: Optional[str] = None,
    password_actual: Optional[str] = None,
    password_nueva: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    nombre = current_user.get("name")
    booster = db.query(Booster).filter(Booster.nombre == nombre).first()
    if not booster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booster no encontrado.")

    if binance is not None:
        booster.binance = binance.strip()
    if discord_id is not None:
        booster.discord_id = discord_id.strip()

    if password_nueva:
        from backend.core.security import verify_password
        if not password_actual or not verify_password(password_actual, booster.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta.")
        booster.password = hash_password(password_nueva)

    db.commit()
    db.refresh(booster)
    return booster

# =============================================================================
# ENDPOINTS ADMINISTRATIVOS (ROL: ADMIN)
# =============================================================================

@router.get("", response_model=List[BoosterResponse])
def listar_boosters(db: Session = Depends(get_db)):
    return db.query(Booster).order_by(Booster.nombre.asc()).all()

@router.get("/{id}", response_model=BoosterResponse)
def obtener_booster(id: int, db: Session = Depends(get_db)):
    booster = db.query(Booster).filter(Booster.id == id).first()
    if not booster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booster no encontrado.")
    return booster

@router.post("", response_model=BoosterResponse, status_code=status.HTTP_201_CREATED)
def crear_booster(datos: BoosterCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    existente = db.query(Booster).filter(Booster.nombre == datos.nombre).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre del booster ya está registrado.")
    
    nuevo = Booster(
        nombre=datos.nombre.strip(),
        binance=datos.binance or "",
        discord_id=datos.discord_id or "",
        password=hash_password(datos.password or "1234"),
        en_ranking=datos.en_ranking if datos.en_ranking is not None else 1
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.put("/{id}", response_model=BoosterResponse)
def actualizar_booster(id: int, datos: BoosterUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    booster = db.query(Booster).filter(Booster.id == id).first()
    if not booster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booster no encontrado.")
    
    if datos.nombre is not None:
        booster.nombre = datos.nombre
    if datos.binance is not None:
        booster.binance = datos.binance
    if datos.discord_id is not None:
        booster.discord_id = datos.discord_id
    if datos.password is not None:
        booster.password = hash_password(datos.password)
    if datos.en_ranking is not None:
        booster.en_ranking = datos.en_ranking

    db.commit()
    db.refresh(booster)
    return booster

@router.patch("/{id}/toggle-ranking", response_model=BoosterResponse)
def toggle_ranking_booster(id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    booster = db.query(Booster).filter(Booster.id == id).first()
    if not booster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booster no encontrado.")
    
    booster.en_ranking = 0 if booster.en_ranking == 1 else 1
    db.commit()
    db.refresh(booster)
    return booster

@router.delete("/{id}", response_model=dict)
def eliminar_booster(id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    booster = db.query(Booster).filter(Booster.id == id).first()
    if not booster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booster no encontrado.")
    db.delete(booster)
    db.commit()
    return {"ok": True, "eliminado": id}
