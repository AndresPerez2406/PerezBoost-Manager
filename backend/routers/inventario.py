from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.inventario import Inventario
from backend.schemas.inventario import CuentaCreate, CuentaUpdate, CuentaResponse, LoteCuentasCreate

router = APIRouter(prefix="/inventario", tags=["Inventario"])

@router.get("", response_model=List[CuentaResponse])
def listar_inventario(elo: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Inventario)
    if elo:
        query = query.filter(Inventario.elo_tipo == elo)
    return query.order_by(Inventario.elo_tipo.asc()).all()

@router.get("/elos", response_model=List[str])
def listar_elos_en_stock(db: Session = Depends(get_db)):
    resultados = db.query(Inventario.elo_tipo).distinct().all()
    return [r[0] for r in resultados if r[0]]

@router.post("", response_model=CuentaResponse, status_code=status.HTTP_201_CREATED)
def agregar_cuenta(datos: CuentaCreate, db: Session = Depends(get_db)):
    existente = db.query(Inventario).filter(Inventario.user_pass == datos.user_pass).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta ya existe en el inventario.")
    
    cuenta = Inventario(
        user_pass=datos.user_pass.strip(),
        elo_tipo=datos.elo_tipo.strip(),
        descripcion=datos.descripcion or "FRESH"
    )
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta

@router.post("/lote", response_model=dict, status_code=status.HTTP_201_CREATED)
def agregar_lote_cuentas(datos: LoteCuentasCreate, db: Session = Depends(get_db)):
    agregadas = 0
    duplicadas = 0
    for u_p in datos.cuentas:
        u_p = u_p.strip()
        if not u_p: continue
        existente = db.query(Inventario).filter(Inventario.user_pass == u_p).first()
        if not existente:
            cuenta = Inventario(user_pass=u_p, elo_tipo=datos.elo_tipo, descripcion=datos.descripcion)
            db.add(cuenta)
            agregadas += 1
        else:
            duplicadas += 1
    db.commit()
    return {"agregadas": agregadas, "duplicadas": duplicadas}

@router.put("/{id}", response_model=CuentaResponse)
def actualizar_cuenta(id: int, datos: CuentaUpdate, db: Session = Depends(get_db)):
    cuenta = db.query(Inventario).filter(Inventario.id == id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada.")
    if datos.user_pass is not None:
        cuenta.user_pass = datos.user_pass
    if datos.elo_tipo is not None:
        cuenta.elo_tipo = datos.elo_tipo
    if datos.descripcion is not None:
        cuenta.descripcion = datos.descripcion
    db.commit()
    db.refresh(cuenta)
    return cuenta

@router.delete("/{id}", response_model=dict)
def eliminar_cuenta(id: int, db: Session = Depends(get_db)):
    cuenta = db.query(Inventario).filter(Inventario.id == id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada.")
    db.delete(cuenta)
    db.commit()
    return {"ok": True, "eliminada": id}
