from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.pedido import Pedido
from backend.models.booster import Booster
from backend.models.config_precio import ConfigPrecio
from backend.schemas.dashboard import RankingLeaderboardResponse, RankingItemResponse

def obtener_leaderboard_mes(db: Session, filtro_mes: Optional[str] = None) -> RankingLeaderboardResponse:
    if not filtro_mes:
        filtro_mes = datetime.now().strftime("%Y-%m")

    # Obtener tarifas de puntos
    precios = db.query(ConfigPrecio).all()
    puntos_dict = {p.division.strip().upper(): p.puntos for p in precios}

    # Obtener boosters activos en ranking
    boosters_rank = db.query(Booster).filter(Booster.en_ranking == 1).all()
    nombres_rank = {b.nombre for b in boosters_rank}

    # Obtener pedidos del mes que participan
    pedidos_mes = db.query(Pedido).filter(
        Pedido.fecha_fin_real.like(f"{filtro_mes}%"),
        Pedido.estado.in_(["Terminado", "Abandonado"])
    ).all()

    # Calcular estadísticas por booster
    stats = {}
    bote_total = 0.0
    pedidos_completados_mes = 0

    for p in pedidos_mes:
        if p.booster_nombre not in nombres_rank:
            continue

        nombre = p.booster_nombre
        if nombre not in stats:
            stats[nombre] = {
                "terminados": 0,
                "high_wr": 0,
                "abandonos": 0,
                "score": 0.0
            }

        if p.estado == "Terminado":
            cuenta_rank = int(p.cuenta_ranking if p.cuenta_ranking is not None else 1)
            if cuenta_rank == 1 and p.elo_final != "Reembolso Bono WR":
                pedidos_completados_mes += 1
                stats[nombre]["terminados"] += 1
                
                # Bote
                b_ped = float(p.bote_pedido or 0.0)
                b_wr = float(p.bote_wr or 0.0)
                bote_total += (b_ped + b_wr)

                # High WR
                if b_wr > 0 or (p.wr and float(p.wr) >= 60.0):
                    stats[nombre]["high_wr"] += 1

                # Puntos
                elo_fin_clean = str(p.elo_final or "").strip().upper()
                pts = puntos_dict.get(elo_fin_clean, 2)
                stats[nombre]["score"] += pts
        elif p.estado == "Abandonado":
            stats[nombre]["abandonos"] += 1
            stats[nombre]["score"] -= 10.0

    # Ordenar ranking por score descendente
    ranking_lista: List[RankingItemResponse] = []
    items_ordenados = sorted(stats.items(), key=lambda x: x[1]["score"], reverse=True)

    for rango, (booster_nom, datos) in enumerate(items_ordenados, 1):
        if datos["terminados"] > 0 or datos["abandonos"] > 0:
            ranking_lista.append(RankingItemResponse(
                rango=rango,
                booster_nombre=booster_nom,
                terminados=datos["terminados"],
                high_wr=datos["high_wr"],
                abandonos=datos["abandonos"],
                score=round(datos["score"], 1)
            ))

    return RankingLeaderboardResponse(
        mes=filtro_mes,
        bote_total=round(max(bote_total, 0.0), 2),
        meta_cumplida=bool(pedidos_completados_mes >= 15),
        pedidos_actuales=pedidos_completados_mes,
        ranking=ranking_lista
    )
