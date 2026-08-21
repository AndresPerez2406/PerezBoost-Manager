from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.pedido import Pedido
from backend.models.inventario import Inventario
from backend.models.log_auditoria import LogAuditoria
from backend.schemas.pedido import PedidoCreate, PedidoFinalizar, PedidoEstadoUpdate

def crear_pedido_service(db: Session, datos: PedidoCreate) -> Pedido:
    # 1. Obtener nota actual de la cuenta en inventario
    cuenta_inv = db.query(Inventario).filter(Inventario.id == datos.id_cuenta).first()
    nota = cuenta_inv.descripcion if cuenta_inv and cuenta_inv.descripcion else "FRESH"

    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Formatear fecha límite
    f_limite = datos.fecha_limite
    if "/" in str(f_limite):
        try:
            f_limite = datetime.strptime(f_limite, "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            f_limite = str(f_limite).split(' ')[0]
    else:
        f_limite = str(f_limite).split(' ')[0]

    # 2. Crear el pedido
    nuevo_pedido = Pedido(
        booster_id=datos.booster_id,
        booster_nombre=datos.booster_nombre,
        user_pass=datos.user_pass,
        elo_inicial=datos.elo_inicial,
        fecha_inicio=fecha_hoy,
        fecha_limite=f_limite,
        estado="En progreso",
        notas=nota
    )
    db.add(nuevo_pedido)

    # 3. Eliminar la cuenta del inventario
    if cuenta_inv:
        db.delete(cuenta_inv)
    else:
        db.query(Inventario).filter(Inventario.user_pass == datos.user_pass).delete()

    # 4. Registrar log
    log = LogAuditoria(
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        evento="PEDIDO_CREADO",
        detalles=f"Pedido creado para {datos.booster_nombre} con cuenta {datos.user_pass} ({datos.elo_inicial})."
    )
    db.add(log)

    db.commit()
    db.refresh(nuevo_pedido)
    return nuevo_pedido

def finalizar_pedido_service(db: Session, id_pedido: int, datos: PedidoFinalizar) -> Optional[Pedido]:
    pedido = db.query(Pedido).filter(Pedido.id == id_pedido).first()
    if not pedido:
        return None

    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
    ganancia = datos.pago_cliente - datos.pago_booster

    pedido.estado = "Terminado"
    pedido.elo_final = datos.elo_final
    pedido.wr = datos.wr
    pedido.fecha_fin_real = fecha_hoy
    pedido.pago_cliente = datos.pago_cliente
    pedido.pago_booster = datos.pago_booster
    pedido.ganancia_empresa = ganancia
    pedido.ajuste_valor = datos.ajuste_valor
    pedido.bote_pedido = datos.bote_pedido
    pedido.bote_wr = datos.bote_wr
    pedido.cuenta_ranking = datos.cuenta_ranking

    # Asegurar que no esté en inventario
    if pedido.user_pass:
        db.query(Inventario).filter(Inventario.user_pass == pedido.user_pass).delete()

    log = LogAuditoria(
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        evento="PEDIDO_FINALIZADO",
        detalles=f"Pedido #{id_pedido} finalizado por {pedido.booster_nombre}. Elo: {datos.elo_final}, WR: {datos.wr}%."
    )
    db.add(log)

    db.commit()
    db.refresh(pedido)
    return pedido

def actualizar_estado_pedido_service(db: Session, id_pedido: int, datos: PedidoEstadoUpdate) -> Optional[Pedido]:
    pedido = db.query(Pedido).filter(Pedido.id == id_pedido).first()
    if not pedido:
        return None

    nuevo_estado = datos.estado
    u_pass = pedido.user_pass

    # Transiciones de estado
    if nuevo_estado == "En progreso":
        # Reactivar pedido -> retirar de inventario si estuviera
        if u_pass:
            db.query(Inventario).filter(Inventario.user_pass == u_pass).delete()
        if datos.pago_realizado is not None:
            pedido.pago_realizado = datos.pago_realizado
        else:
            pedido.pago_realizado = 0
    elif nuevo_estado == "Abandonado":
        # Abandono -> reinsertar cuenta a inventario si no existe
        if u_pass:
            inv_exist = db.query(Inventario).filter(Inventario.user_pass == u_pass).first()
            if not inv_exist:
                nueva_cuenta = Inventario(
                    user_pass=u_pass,
                    elo_tipo=pedido.elo_inicial or "Emerald/Plat",
                    descripcion=pedido.notas or "FRESH"
                )
                db.add(nueva_cuenta)
    else:  # Terminado o Baneada
        if u_pass:
            db.query(Inventario).filter(Inventario.user_pass == u_pass).delete()

    pedido.estado = nuevo_estado

    if datos.booster_nombre is not None:
        pedido.booster_nombre = datos.booster_nombre
    if datos.elo_final is not None:
        pedido.elo_final = datos.elo_final
    if datos.wr is not None:
        pedido.wr = datos.wr
    if datos.pago_cliente is not None:
        pedido.pago_cliente = datos.pago_cliente
    if datos.pago_booster is not None:
        pedido.pago_booster = datos.pago_booster
    if datos.pago_cliente is not None and datos.pago_booster is not None:
        pedido.ganancia_empresa = datos.pago_cliente - datos.pago_booster
    if datos.pago_realizado is not None:
        pedido.pago_realizado = datos.pago_realizado
    if datos.fecha_fin_real is not None:
        pedido.fecha_fin_real = datos.fecha_fin_real
    if datos.bote_pedido is not None:
        pedido.bote_pedido = datos.bote_pedido
    if datos.bote_wr is not None:
        pedido.bote_wr = datos.bote_wr
    if datos.cuenta_ranking is not None:
        pedido.cuenta_ranking = datos.cuenta_ranking

    log = LogAuditoria(
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        evento="ESTADO_MODIFICADO",
        detalles=f"Pedido #{id_pedido} actualizado a estado '{nuevo_estado}'."
    )
    db.add(log)

    db.commit()
    db.refresh(pedido)
    return pedido
