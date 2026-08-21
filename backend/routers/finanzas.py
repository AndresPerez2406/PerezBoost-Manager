from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import require_admin
from backend.models.pedido import Pedido
from backend.schemas.dashboard import ResumenFinancieroResponse, StaffAnalyticsItem
from backend.services.finanzas_service import obtener_resumen_financiero_mes

router = APIRouter(prefix="/finanzas", tags=["Finanzas & Reportes (Admin)"])

@router.get("/resumen", response_model=ResumenFinancieroResponse)
def get_resumen_financiero(
    mes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    return obtener_resumen_financiero_mes(db, mes)

@router.get("/saldos-pendientes", response_model=List[dict])
def get_saldos_pendientes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    pedidos_pendientes = db.query(Pedido).filter(
        Pedido.estado == "Terminado",
        (Pedido.pago_realizado == 0) | (Pedido.pago_realizado.is_(None))
    ).all()

    saldos = {}
    for p in pedidos_pendientes:
        nom = p.booster_nombre
        if nom not in saldos:
            saldos[nom] = {
                "booster_nombre": nom,
                "total_pendiente": 0.0,
                "cantidad_pedidos": 0,
                "pedidos": []
            }
        p_boo = float(p.pago_booster or 0.0)
        saldos[nom]["total_pendiente"] += p_boo
        saldos[nom]["cantidad_pedidos"] += 1
        saldos[nom]["pedidos"].append({
            "id": p.id,
            "elo_final": p.elo_final,
            "pago_booster": p_boo,
            "user_pass": p.user_pass
        })

    return sorted(list(saldos.values()), key=lambda x: x["total_pendiente"], reverse=True)

@router.post("/liquidar/{booster_nombre}", response_model=dict)
def liquidar_pagos_booster(
    booster_nombre: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    afectados = db.query(Pedido).filter(
        Pedido.booster_nombre == booster_nombre,
        Pedido.estado == "Terminado",
        (Pedido.pago_realizado == 0) | (Pedido.pago_realizado.is_(None))
    ).update({"pago_realizado": 1}, synchronize_session=False)

    db.commit()
    return {"booster": booster_nombre, "pedidos_liquidados": afectados}
