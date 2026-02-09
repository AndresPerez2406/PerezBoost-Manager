from core.database import (
    conectar, 
    obtener_boosters_db as db_get_boosters,
    obtener_pedidos_activos
)
from core.logic import calcular_tiempo_transcurrido

def obtener_pedidos_visual():

    datos = obtener_pedidos_activos()
    procesados = []
    for i, p in enumerate(datos, start=1):
        
        f_ini = p[4].split(' ')[0]
        f_lim = p[5].split(' ')[0]
        tiempo = calcular_tiempo_transcurrido(f_ini)
        
        procesados.append((i, p[0], p[1], p[3], f_ini, f_lim, tiempo))
    return procesados

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