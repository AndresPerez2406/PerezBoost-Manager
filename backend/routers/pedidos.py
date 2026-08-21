from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user, require_admin, require_booster_or_admin
from backend.models.pedido import Pedido
from backend.schemas.pedido import (
    PedidoCreate, PedidoFinalizar, PedidoEstadoUpdate, PedidoOpggUpdate, PedidoResponse
)
from backend.services.pedidos_service import (
    crear_pedido_service, finalizar_pedido_service, actualizar_estado_pedido_service
)

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

@router.get("", response_model=List[PedidoResponse])
def listar_pedidos(
    estado: Optional[str] = None,
    booster: Optional[str] = None,
    mes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user)
):
    query = db.query(Pedido)
    
    # Aislamiento RBAC: Si es un booster, solo ve sus propios pedidos
    if current_user and current_user.get("role") == "booster":
        query = query.filter(Pedido.booster_nombre == current_user.get("name"))
    elif booster:
        query = query.filter(Pedido.booster_nombre == booster)

    if estado:
        query = query.filter(Pedido.estado == estado)
    if mes:
        query = query.filter(Pedido.fecha_fin_real.like(f"{mes}%"))
    
    query = query.order_by(Pedido.id.desc())
    return query.all()

@router.get("/activos", response_model=List[PedidoResponse])
def listar_pedidos_activos(
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user)
):
    query = db.query(Pedido).filter(Pedido.estado == "En progreso")
    if current_user and current_user.get("role") == "booster":
        query = query.filter(Pedido.booster_nombre == current_user.get("name"))
    return query.order_by(Pedido.fecha_limite.asc()).all()

@router.get("/{id}", response_model=PedidoResponse)
def obtener_pedido(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_booster_or_admin)
):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")
    
    # Si es booster, solo puede ver el pedido si le pertenece
    if current_user.get("role") == "booster" and pedido.booster_nombre != current_user.get("name"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver este pedido.")
    
    return pedido

@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    datos: PedidoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    try:
        nuevo = crear_pedido_service(db, datos)
        return nuevo
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error creando pedido: {str(e)}")

@router.post("/{id}/finalizar", response_model=PedidoResponse)
def finalizar_pedido(
    id: int,
    datos: PedidoFinalizar,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    pedido = finalizar_pedido_service(db, id, datos)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")
    return pedido

@router.patch("/{id}/estado", response_model=PedidoResponse)
def actualizar_estado_pedido(
    id: int,
    datos: PedidoEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    pedido = actualizar_estado_pedido_service(db, id, datos)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")
    return pedido

@router.patch("/{id}/opgg", response_model=PedidoResponse)
def actualizar_opgg_pedido(
    id: int,
    datos: PedidoOpggUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_booster_or_admin)
):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")
    
    # Si es booster, solo puede actualizar el OP.GG si el pedido le pertenece
    if current_user.get("role") == "booster" and pedido.booster_nombre != current_user.get("name"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes modificar un pedido que no te pertenece.")

    pedido.opgg = datos.opgg or ""
    db.commit()
    db.refresh(pedido)
    return pedido
