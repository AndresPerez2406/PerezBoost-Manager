from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.pedido import Pedido
from backend.schemas.dashboard import ResumenFinancieroResponse

def obtener_resumen_financiero_mes(db: Session, filtro_mes: Optional[str] = None) -> ResumenFinancieroResponse:
    if not filtro_mes or filtro_mes == "Todos":
        filtro_fecha = ""
    else:
        filtro_fecha = filtro_mes  # Formato YYYY-MM

    query = db.query(Pedido).filter(Pedido.estado == "Terminado", Pedido.pago_realizado == 1)
    if filtro_fecha:
        query = query.filter(Pedido.fecha_fin_real.like(f"{filtro_fecha}%"))
    
    pedidos = query.all()
    
    conteo = len(pedidos)
    t_staff = 0.0
    t_neto = 0.0
    t_bote = 0.0
    t_ventas = 0.0
    dias_totales = 0
    
    for p in pedidos:
        p_cli = float(p.pago_cliente or 0.0)
        p_boo = float(p.pago_booster or 0.0)
        g_emp = float(p.ganancia_empresa or 0.0)
        b_ped = float(p.bote_pedido or 0.0)
        b_wr = float(p.bote_wr or 0.0)
        
        t_staff += p_boo
        t_neto += g_emp
        t_bote += (b_ped + b_wr)
        t_ventas += p_cli
        
        try:
            if p.fecha_inicio and p.fecha_fin_real:
                f_ini = datetime.strptime(str(p.fecha_inicio).split(' ')[0], "%Y-%m-%d")
                f_fin = datetime.strptime(str(p.fecha_fin_real).split(' ')[0], "%Y-%m-%d")
                d = max((f_fin - f_ini).days, 1)
                dias_totales += d
        except Exception:
            dias_totales += 1

    # Ajuste histórico de Enero si aplica
    if filtro_mes in ["Todos", "2026-01"]:
        t_neto += 5.0
        t_bote -= 5.0

    prom_dias = (dias_totales / conteo) if conteo > 0 else 0.0

    return ResumenFinancieroResponse(
        mes=filtro_mes or "Todos",
        pedidos_completados=conteo,
        mi_neto=round(t_neto, 2),
        pago_staff=round(t_staff, 2),
        bote_ranking=round(max(t_bote, 0.0), 2),
        ventas_totales=round(t_ventas, 2),
        velocidad_media_dias=round(prom_dias, 1)
    )
