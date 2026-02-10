import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

# ==========================================
# SECCIÓN 0: CONFIGURACIÓN Y CONEXIÓN
# ==========================================

load_dotenv()
CLOUD_URL = os.getenv("DATABASE_URL")

def conectar():
    """Conexión a Supabase (PostgreSQL)"""
    try:
        if not CLOUD_URL:
            print("❌ ERROR: Falta DATABASE_URL en .env")
            return None
        return psycopg2.connect(CLOUD_URL)
    except Exception as e:
        print(f"❌ Error conexión Cloud: {e}")
        return None

def realizar_backup_db():
    """
    En la nube (Supabase), los backups son automáticos.
    Esta función se mantiene para compatibilidad con el botón de la interfaz.
    """
    print("☁️ [NUBE] Backup gestionado automáticamente por Supabase.")

def inicializar_db():
    """Verifica la conexión al iniciar."""
    conn = conectar()
    if conn:
        print("✅ [SYSTEM] Conectado a la Nube (PostgreSQL)")
        conn.close()
    else:
        print("❌ [SYSTEM] Error conectando a la Nube.")

# ==========================================
# SECCIÓN 1: GESTIÓN DE BOOSTERS
# ==========================================

def agregar_booster(nombre):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO boosters (nombre) VALUES (%s)", (nombre,))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def obtener_boosters_db():
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nombre FROM boosters ORDER BY nombre") 
        return cursor.fetchall()
    finally: conn.close()

def eliminar_booster(id_booster):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM boosters WHERE id = %s", (id_booster,))
        conn.commit()
        return True # En postgres cursor.rowcount funciona igual
    except: return False
    finally: conn.close()

def actualizar_booster_db(id_booster, nombre_nuevo):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE boosters SET nombre = %s WHERE id = %s", (nombre_nuevo, id_booster))
        conn.commit()
    finally: conn.close()

# ==========================================
# SECCIÓN 2: GESTIÓN DE INVENTARIO
# ==========================================

def agregar_cuenta(user_pass, elo_tipo, descripcion=None):
    if not descripcion or str(descripcion).strip() == "": descripcion = "FRESH"
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO inventario (user_pass, elo_tipo, descripcion) VALUES (%s, %s, %s)", (user_pass, elo_tipo, descripcion))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def obtener_inventario():
    conn = conectar(); cursor = conn.cursor()
    try:
        # Devolvemos ID duplicado para mantener índices compatibles con tu tabla antigua
        cursor.execute("SELECT id, id, user_pass, elo_tipo, descripcion FROM inventario ORDER BY elo_tipo")
        return cursor.fetchall()
    finally: conn.close()

# Alias para compatibilidad con main.py nuevo
def obtener_inventario_visual():
    return obtener_inventario()

def eliminar_cuenta(id_cuenta):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM inventario WHERE id = %s", (id_cuenta,))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

# Alias para compatibilidad si alguna parte llama a _gui
def eliminar_cuenta_gui(id_cuenta):
    return eliminar_cuenta(id_cuenta)

def actualizar_inventario_db(id_inv, datos):
    conn = conectar(); cursor = conn.cursor()
    try:
        sets = [f"{k} = %s" for k in datos.keys()]
        vals = list(datos.values())
        vals.append(id_inv)
        sql = f"UPDATE inventario SET {', '.join(sets)} WHERE id = %s"
        cursor.execute(sql, tuple(vals))
        conn.commit()
    except Exception as e: print(f"Error inv: {e}")
    finally: conn.close()

# ==========================================
# SECCIÓN 3: GESTIÓN DE PEDIDOS
# ==========================================

def crear_pedido(id_booster, nombre_booster, id_cuenta, user_pass, elo, fecha_fin):
    conn = conectar(); cursor = conn.cursor()
    try:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
        f_limite = str(fecha_fin).split(' ')[0]
        if "/" in str(fecha_fin):
            try: f_limite = datetime.strptime(fecha_fin, "%d/%m/%Y").strftime("%Y-%m-%d")
            except: pass

        cursor.execute('''INSERT INTO pedidos (booster_id, booster_nombre, user_pass, elo_inicial, 
                          fecha_inicio, fecha_limite, estado) VALUES (%s, %s, %s, %s, %s, %s, 'En progreso')''', 
                       (id_booster, nombre_booster, user_pass, elo, fecha_hoy, f_limite))
        
        cursor.execute("DELETE FROM inventario WHERE id = %s", (id_cuenta,))
        conn.commit(); return True
    except Exception as e: 
        print(f"Error al crear pedido: {e}")
        conn.rollback()
        return False
    finally: conn.close()

def obtener_pedidos_activos():
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, booster_nombre, elo_inicial, user_pass, fecha_inicio, fecha_limite FROM pedidos WHERE estado = 'En progreso'")
        return cursor.fetchall()
    finally: conn.close()

def registrar_abandono_db(id_pedido, elo_dejado, wr_dejado):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_pass, elo_inicial FROM pedidos WHERE id = %s", (id_pedido,))
        datos = cursor.fetchone()
        if not datos: return False
        u_p, elo_orig = datos
        fecha_fin = datetime.now().strftime("%Y-%m-%d %H:%M")
        nota = f"⚠️ ABANDONO. Dejada en: {elo_dejado} ({wr_dejado}% WR)"
        
        # Sintaxis UPSERT de PostgreSQL
        cursor.execute("""
            INSERT INTO inventario (user_pass, elo_tipo, descripcion) VALUES (%s, %s, %s) 
            ON CONFLICT(user_pass) DO UPDATE SET elo_tipo = EXCLUDED.elo_tipo, descripcion = EXCLUDED.descripcion
        """, (u_p, elo_orig, nota))
        
        cursor.execute("UPDATE pedidos SET estado='Abandonado', elo_final=%s, wr=%s, fecha_fin_real=%s WHERE id=%s", 
                       (elo_dejado, wr_dejado, fecha_fin, id_pedido))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def actualizar_pedido_db(id_pedido, datos):
    conn = conectar(); cursor = conn.cursor()
    try:
        sets = [f"{k} = %s" for k in datos.keys()]
        vals = list(datos.values())
        vals.append(id_pedido)
        sql = f"UPDATE pedidos SET {', '.join(sets)} WHERE id = %s"
        cursor.execute(sql, tuple(vals))
        conn.commit()
    finally: conn.close()

def obtener_resumen_alertas():
    conn = conectar(); cursor = conn.cursor()
    try:
        hoy = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 'En progreso' AND fecha_limite <= %s", (hoy,))
        vencidos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM inventario")
        stock = cursor.fetchone()[0]
        return vencidos, stock
    except: return 0, 0
    finally: conn.close()

def finalizar_pedido_db(id_pedido, wr_final, fecha_fin, elo_final, ganancia_empresa, pago_booster, pago_cliente):
    conn = conectar(); cursor = conn.cursor()
    try:
        fecha_db = str(fecha_fin).split(' ')[0]
        if "/" in str(fecha_fin):
            try: fecha_db = datetime.strptime(fecha_fin, "%d/%m/%Y").strftime("%Y-%m-%d")
            except: pass

        cursor.execute("""
            UPDATE pedidos 
            SET estado = 'Terminado', wr = %s, fecha_fin_real = %s, elo_final = %s,
                ganancia_empresa = %s, pago_booster = %s, pago_cliente = %s
            WHERE id = %s
        """, (wr_final, fecha_db, elo_final, float(ganancia_empresa), float(pago_booster), float(pago_cliente), id_pedido))
        conn.commit(); return True
    except Exception as e:
        print(f"Error Crítico BD: {e}")
        return False
    finally: conn.close()

# ==========================================
# SECCIÓN 4: HISTORIAL
# ==========================================

def obtener_historial_completo():
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, booster_nombre, user_pass, elo_final, fecha_inicio, fecha_fin_real, estado, wr
            FROM pedidos WHERE estado IN ('Terminado', 'Abandonado') 
            ORDER BY fecha_fin_real DESC, id DESC
        """)
        return cursor.fetchall()
    finally: conn.close()

# ==========================================
# SECCIÓN 5: CONFIGURACIÓN DE TARIFAS
# ==========================================

def obtener_config_precios():
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT division, precio_cliente, margen_perez, puntos FROM config_precios ORDER BY puntos DESC")
        return cursor.fetchall()
    finally: conn.close()

def actualizar_precio_db(division, nuevo_precio, nuevo_margen, nuevos_puntos):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE config_precios SET precio_cliente=%s, margen_perez=%s, puntos=%s WHERE division=%s", 
                       (nuevo_precio, nuevo_margen, nuevos_puntos, division))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def agregar_precio_db(div, p_cli, m_per, pts=2):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO config_precios (division, precio_cliente, margen_perez, puntos) VALUES (%s, %s, %s, %s)", 
                       (div, p_cli, m_per, pts))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def eliminar_precio_db(div):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM config_precios WHERE division = %s", (div,))
        conn.commit(); return True
    except: return False
    finally: conn.close()

# ==========================================
# SECCIÓN 6: DASHBOARD Y REPORTES
# ==========================================

def obtener_resumen_financiero_real(filtro_fecha=None):
    conn = conectar(); cursor = conn.cursor()
    try:
        if not filtro_fecha: filtro_fecha = datetime.now().strftime("%Y-%m")
        cursor.execute("""
            SELECT SUM(pago_booster), SUM(ganancia_empresa) - COUNT(*), COUNT(*)
            FROM pedidos WHERE estado = 'Terminado' AND fecha_inicio LIKE %s 
        """, (f"{filtro_fecha}%",))
        res = cursor.fetchone()
        if res and res[2] > 0:
            return (float(res[0] or 0), float(res[1] or 0), int(res[2]))
        return (0.0, 0.0, 0)
    finally: conn.close()

def obtener_profit_diario_db():
    conn = conectar(); cursor = conn.cursor()
    try:
        hoy = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT SUM(ganancia_empresa) FROM pedidos WHERE estado = 'Terminado' AND fecha_fin_real LIKE %s", (f"{hoy}%",))
        res = cursor.fetchone()
        return res[0] if res and res[0] else 0.0
    finally: conn.close()

def obtener_kpis_mensuales():
    conn = conectar(); cursor = conn.cursor()
    try:
        mes_actual = datetime.now().strftime("%Y-%m")
        cursor.execute("SELECT SUM(ganancia_empresa) - COUNT(*), COUNT(*) FROM pedidos WHERE estado = 'Terminado' AND fecha_inicio LIKE %s", (f"{mes_actual}%",))
        datos = cursor.fetchone()
        return (datos[0] if datos and datos[0] else 0.0, datos[1] if datos and datos[1] else 0)
    finally: conn.close()

def obtener_conteo_stock():
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM inventario")
        res = cursor.fetchone()
        return res[0] if res else 0
    except: return 0
    finally: conn.close()

def obtener_conteo_pedidos_activos():
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 'En progreso'")
        res = cursor.fetchone()
        return res[0] if res else 0
    finally: conn.close()

def obtener_ganancia_proyectada():
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT elo_inicial FROM pedidos WHERE estado = 'En progreso'")
        pedidos = cursor.fetchall()
        cursor.execute("SELECT division, margen_perez FROM config_precios")
        tarifas = {row[0].upper(): row[1] for row in cursor.fetchall()}
        
        total = 0.0
        for (elo,) in pedidos:
            elo_clean = str(elo).upper().strip()
            if elo_clean in tarifas: total += tarifas[elo_clean]
            else:
                for div, margen in tarifas.items():
                    if div.startswith(elo_clean[0]):
                        total += margen
                        break
        total = total - len(pedidos)
        return float(total)
    except: return 0.0
    finally: conn.close()

def obtener_datos_reporte_avanzado(mes_nombre, booster_nombre):
    conn = conectar(); cursor = conn.cursor()
    try:
        meses_dict = {"Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04", "Mayo": "05", "Junio": "06", 
                      "Julio": "07", "Agosto": "08", "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"}
        query = "SELECT * FROM pedidos WHERE estado = 'Terminado'"
        params = []
        if mes_nombre != "Todos":
            mes_num = meses_dict.get(mes_nombre)
            anio_actual = datetime.now().year
            query += " AND fecha_inicio LIKE %s"
            params.append(f"{anio_actual}-{mes_num}%")
        if booster_nombre != "Todos":
            query += " AND booster_nombre = %s"
            params.append(booster_nombre)
        query += " ORDER BY fecha_fin_real DESC, id DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally: conn.close()

# ==========================================
# SECCIÓN 7: CONFIGURACIÓN Y LOGS
# ==========================================

def guardar_config_sistema(clave, valor):
    conn = conectar(); cursor = conn.cursor()
    try:
        # PostgreSQL Upsert
        cursor.execute("INSERT INTO config_sistema (clave, valor) VALUES (%s, %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor", (clave, valor))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def obtener_config_sistema(clave):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT valor FROM config_sistema WHERE clave = %s", (clave,))
        res = cursor.fetchone()
        return res[0] if res else ""
    finally: conn.close()

def registrar_log(evento, detalles):
    try:
        conn = conectar(); cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO logs (fecha, evento, detalles) VALUES (%s, %s, %s)", (fecha, evento, detalles))
        conn.commit(); conn.close()
    except: pass

def obtener_logs_db(limite=50):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT fecha, evento, detalles FROM logs ORDER BY id DESC LIMIT %s", (limite,))
        return cursor.fetchall()
    finally: conn.close()

# ==========================================
# SECCIÓN 8: RANKING Y FINANZAS
# ==========================================

def obtener_ranking_staff_db(filtro_fecha=None):
    conn = conectar(); cursor = conn.cursor()
    try:
        if not filtro_fecha: filtro_fecha = datetime.now().strftime("%Y-%m")
        query = """
        SELECT b.nombre, 
               COUNT(CASE WHEN p.estado = 'Terminado' THEN 1 END) as terminados,
               COUNT(CASE WHEN p.estado = 'Terminado' AND p.wr >= 60 THEN 1 END) as high_wr,
               COUNT(CASE WHEN p.estado = 'Abandonado' THEN 1 END) as abandonos,
               COALESCE(SUM(CASE 
                  WHEN p.estado = 'Terminado' THEN 
                      COALESCE((SELECT puntos FROM config_precios WHERE UPPER(TRIM(division)) = UPPER(TRIM(p.elo_final))), 2)
                  WHEN p.estado = 'Abandonado' THEN -10 
                  ELSE 0 END), 0) as score
        FROM boosters b 
        LEFT JOIN pedidos p ON b.nombre = p.booster_nombre 
        WHERE p.fecha_inicio LIKE %s 
        GROUP BY b.id, b.nombre 
        HAVING (COUNT(CASE WHEN p.estado = 'Terminado' THEN 1 END) > 0 OR COUNT(CASE WHEN p.estado = 'Abandonado' THEN 1 END) > 0)
        ORDER BY score DESC LIMIT 10
        """
        cursor.execute(query, (f"{filtro_fecha}%",))
        return cursor.fetchall()
    finally: conn.close()

def obtener_total_bote_ranking():
    conn = conectar(); cursor = conn.cursor()
    try:
        mes_actual = datetime.now().strftime("%Y-%m")
        cursor.execute("""
            SELECT COUNT(*) + COALESCE(SUM(CASE WHEN wr >= 60 THEN 1 ELSE 0 END), 0) 
            FROM pedidos WHERE estado = 'Terminado' AND fecha_inicio LIKE %s
        """, (f"{mes_actual}%",))
        res = cursor.fetchone()
        return float(res[0]) if res and res[0] else 0.0
    finally: conn.close()

def obtener_pedidos_mes_actual_db():
    conn = conectar(); cursor = conn.cursor()
    try:
        mes_actual = datetime.now().strftime("%Y-%m")
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 'Terminado' AND fecha_inicio LIKE %s AND wr > 60", (f"{mes_actual}%",))
        res = cursor.fetchone()
        return res[0] if res else 0
    finally: conn.close()

def obtener_resumen_mensual_db(filtro_fecha=None):
    conn = conectar(); cursor = conn.cursor()
    try:
        params = []
        where = "WHERE estado IN ('Terminado', 'Abandonado')"
        if filtro_fecha:
            where += " AND fecha_inicio LIKE %s"
            params.append(f"{filtro_fecha}%")

        # CÁLCULO DE DÍAS (Sintaxis PostgreSQL)
        query = f"""
            SELECT 
                COUNT(CASE WHEN estado = 'Terminado' THEN 1 END),
                COUNT(CASE WHEN estado = 'Abandonado' THEN 1 END),
                COALESCE(AVG(CASE WHEN estado = 'Terminado' THEN wr END), 0),
                COUNT(CASE WHEN estado = 'Terminado' AND wr >= 60 THEN 1 END),
                COALESCE(AVG(CASE WHEN estado = 'Terminado' AND fecha_fin_real != '' THEN 
                    DATE(SPLIT_PART(fecha_fin_real, ' ', 1)) - DATE(SPLIT_PART(fecha_inicio, ' ', 1))
                END), 0)
            FROM pedidos {where}
        """
        cursor.execute(query, tuple(params))
        res = cursor.fetchone()
        return res if res else (0,0,0,0,0)
    except: return (0,0,0,0,0)
    finally: conn.close()

def obtener_balance_general_db(filtro_fecha=None):
    conn = conectar(); cursor = conn.cursor()
    try:
        query = "SELECT SUM(pago_cliente), SUM(pago_booster), SUM(ganancia_empresa), COUNT(*) FROM pedidos WHERE estado = 'Terminado'"
        params = []
        if filtro_fecha:
            query += " AND fecha_inicio LIKE %s"
            params.append(f"{filtro_fecha}%")
        cursor.execute(query, tuple(params))
        res = cursor.fetchone()
        t_cli = res[0] if res[0] else 0.0
        t_boo = res[1] if res[1] else 0.0
        util = res[2] if res[2] else (t_cli - t_boo)
        cant = res[3] if res[3] else 0
        return util, t_cli, t_boo, cant
    finally: conn.close()

def obtener_saldos_pendientes_db():
    conn = conectar(); cursor = conn.cursor()
    try:
        # STRING_AGG es el equivalente de GROUP_CONCAT en Postgres
        cursor.execute("""
            SELECT booster_nombre, SUM(pago_booster), COUNT(*),
                   STRING_AGG(elo_final || ' ($' || pago_booster || ')', ' + ')
            FROM pedidos 
            WHERE estado = 'Terminado' AND (pago_realizado = 0 OR pago_realizado IS NULL)
            GROUP BY booster_nombre
            ORDER BY SUM(pago_booster) DESC
        """)
        return cursor.fetchall()
    finally: conn.close()

def liquidar_pagos_booster_db(nombre_booster):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE pedidos SET pago_realizado = 1 WHERE booster_nombre = %s AND estado = 'Terminado' AND (pago_realizado = 0 OR pago_realizado IS NULL)", (nombre_booster,))
        conn.commit()
        return cursor.rowcount
    finally: conn.close()