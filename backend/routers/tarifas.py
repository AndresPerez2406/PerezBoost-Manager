from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import require_admin
from backend.models.config_precio import ConfigPrecio
from backend.schemas.config_precio import TarifaCreate, TarifaUpdate, TarifaResponse

router = APIRouter(prefix="/tarifas", tags=["Tarifas de Precios"])

@router.get("", response_model=List[TarifaResponse])
def listar_tarifas(db: Session = Depends(get_db)):
    return db.query(ConfigPrecio).order_by(ConfigPrecio.puntos.desc()).all()

@router.post("", response_model=TarifaResponse, status_code=status.HTTP_201_CREATED)
def crear_tarifa(
    datos: TarifaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    div = datos.division.strip().upper()
    existente = db.query(ConfigPrecio).filter(ConfigPrecio.division == div).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La división ya existe.")
    
    tarifa = ConfigPrecio(
        division=div,
        precio_cliente=datos.precio_cliente,
        margen_perez=datos.margen_perez,
        puntos=datos.puntos or 2
    )
    db.add(tarifa)
    db.commit()
    db.refresh(tarifa)
    return tarifa

@router.put("/{division}", response_model=TarifaResponse)
def actualizar_tarifa(
    division: str,
    datos: TarifaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    div = division.strip().upper()
    tarifa = db.query(ConfigPrecio).filter(ConfigPrecio.division == div).first()
    if not tarifa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarifa no encontrada.")
    
    if datos.precio_cliente is not None:
        tarifa.precio_cliente = datos.precio_cliente
    if datos.margen_perez is not None:
        tarifa.margen_perez = datos.margen_perez
    if datos.puntos is not None:
        tarifa.puntos = datos.puntos

    db.commit()
    db.refresh(tarifa)
    return tarifa

@router.delete("/{division}", response_model=dict)
def eliminar_tarifa(
    division: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    div = division.strip().upper()
    tarifa = db.query(ConfigPrecio).filter(ConfigPrecio.division == div).first()
    if not tarifa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarifa no encontrada.")
    db.delete(tarifa)
    db.commit()
    return {"ok": True, "eliminada": div}
