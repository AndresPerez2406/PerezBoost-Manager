"""
MÓDULO: GESTIÓN DE PEDIDOS (DURANTE EL SERVICIO)
-----------------------------------------------
Maneja la lógica de visualización y cierre de trabajos activos.
"""
from core.database import (
    obtener_historial_completo, 
    conectar, 
    obtener_boosters_db as db_get_boosters
)
from core.logic import calcular_tiempo_transcurrido, calcular_duracion_servicio

# ======================================================
#  PUENTE PARA GUI Y LÓGICA VISUAL
# ======================================================

def obtener_pedidos_visual():
    from core.database import obtener_pedidos_activos
    from core.logic import calcular_tiempo_transcurrido
    datos = obtener_pedidos_activos()
    procesados = []
    for i, p in enumerate(datos, start=1):
        
        f_ini = p[4].split(' ')[0]
        f_lim = p[5].split(' ')[0]
        tiempo = calcular_tiempo_transcurrido(f_ini)
        
        procesados.append((i, p[0], p[1], p[3], f_ini, f_lim, tiempo))
    return procesados

def obtener_historial_visual():
    from core.database import obtener_historial_completo
    from datetime import datetime
    datos = obtener_historial_completo()
    procesados = []
    
    for i, h in enumerate(datos, start=1):
        # h: [7]inicio, [8]fin_real, [10]estado
        estado = str(h[10]).upper() if h[10] else "TERMINADO"
        icon = "✅" if estado == "TERMINADO" else "❌"
        usuario = h[9].split(':')[0] if h[9] else "N/A"
        
        # --- CÁLCULO DE DÍAS ---
        try:
            d_ini = datetime.strptime(str(h[7]).split(' ')[0], "%Y-%m-%d")
            d_fin = datetime.strptime(str(h[8]).split(' ')[0], "%Y-%m-%d")
            diferencia = (d_fin - d_ini).days
            txt_duracion = f"{diferencia} días" if diferencia > 0 else "Mismo día"
        except:
            txt_duracion = "N/A"

        # [8] será la duración y añadimos [9] como el estado oculto para la suma
        fila = (
            i,                          # [0]
            h[1],                       # [1]
            f"{icon} {usuario} ({h[2]})",# [2]
            f"${(h[4] or 0.0):.2f}",    # [3]
            f"${(h[5] or 0.0):.2f}",    # [4]
            f"${(h[6] or 0.0):.2f}",    # [5]
            str(h[7]).split(' ')[0],    # [6]
            str(h[8]).split(' ')[0],    # [7]
            txt_duracion,               # [8] LO QUE SE VE
            estado                      # [9] OCULTO (para la lógica)
        )
        procesados.append(fila)
        
    return procesados, None

# ======================================================
#  INTERFAZ CMD
# ======================================================

def menu_pedidos_cli():
    print("\n" + "--- ⚔️ PEDIDOS EN CURSO ---".center(40))
    pedidos = obtener_pedidos_visual()
    if not pedidos:
        print("No hay pedidos activos.")
    else:
        print(f"{'#':<3} | {'BOOSTER':<12} | {'CUENTA':<18} | {'TIEMPO'}")
        print("-" * 50)
        for v, r, b, c, ini, lim, t in pedidos:
            print(f"{v:<3} | {b:<12} | {c[:18]:<18} | {t}")
    input("\nPresiona Enter para volver...")

# ======================================================
#  FUNCIONES AUXILIARES PARA FORMULARIOS GUI
# ======================================================

def obtener_elos_en_stock():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT elo_tipo FROM inventario ORDER BY elo_tipo")
    resultados = cursor.fetchall()
    conn.close()
    return [r[0] for r in resultados] if resultados else []

def obtener_cuentas_filtradas_datos(elo_seleccionado):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_pass, descripcion FROM inventario WHERE elo_tipo = ?", (elo_seleccionado,))
    data = cursor.fetchall()
    conn.close()
    return data

def obtener_boosters_db():
    return db_get_boosters()