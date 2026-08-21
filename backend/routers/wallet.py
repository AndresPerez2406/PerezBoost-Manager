from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import require_admin
from backend.models.wallet import WalletPerez
from backend.models.pedido import Pedido
from backend.schemas.wallet import TransaccionCreate, TransaccionResponse, WalletBalanceResponse

router = APIRouter(prefix="/wallet", tags=["Billetera Binance (Admin)"])

@router.get("/balance", response_model=WalletBalanceResponse)
def get_balance_wallet(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    # 1. Fondos históricos de pedidos terminados y liquidados
    pedidos = db.query(Pedido).filter(Pedido.estado == "Terminado", Pedido.pago_realizado == 1).all()
    neto_historico = sum(float(p.ganancia_empresa or 0.0) for p in pedidos)
    bote_historico = sum(float(p.bote_pedido or 0.0) + float(p.bote_wr or 0.0) for p in pedidos)

    # Ajuste histórico de inicio
    neto_historico += 5.0
    bote_historico -= 5.0

    # 2. Movimientos manuales de Binance
    movimientos = db.query(WalletPerez).all()
    neto_movs = 0.0
    bote_movs = 0.0

    for m in movimientos:
        monto = float(m.monto or 0.0)
        tipo = str(m.tipo).strip().upper()
        cat = str(m.categoria).strip().upper()
        val = monto if tipo == "INGRESO" else -monto

        if cat == "NETO":
            neto_movs += val
        elif cat == "BOTE":
            bote_movs += val

    saldo_neto = neto_historico + neto_movs
    saldo_bote = bote_historico + bote_movs
    total = saldo_neto + saldo_bote

    return WalletBalanceResponse(
        saldo_neto=round(saldo_neto, 2),
        saldo_bote=round(saldo_bote, 2),
        total_binance=round(total, 2)
    )

@router.get("/transacciones", response_model=List[TransaccionResponse])
def listar_transacciones(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    return db.query(WalletPerez).order_by(WalletPerez.id.desc()).all()

@router.post("/transacciones", response_model=TransaccionResponse, status_code=status.HTTP_201_CREATED)
def crear_transaccion(
    datos: TransaccionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    nueva = WalletPerez(
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        tipo=datos.tipo.strip().upper(),
        categoria=datos.categoria.strip().upper(),
        monto=datos.monto,
        descripcion=datos.descripcion or ""
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.delete("/transacciones/{id}", response_model=dict)
def eliminar_transaccion(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    tx = db.query(WalletPerez).filter(WalletPerez.id == id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada.")
    db.delete(tx)
    db.commit()
    return {"ok": True, "eliminada": id}
