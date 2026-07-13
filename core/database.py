import sqlite3
import os
import shutil
from datetime import datetime, timedelta

# ==========================================
# SECCIÓN 0: CONFIGURACIÓN Y BACKUP
# ==========================================

def conectar():

    return sqlite3.connect("perezboost.db")

def realizar_backup_db():
    archivo_db = "perezboost.db"
    carpeta_backups = "backups"

    if not os.path.exists(archivo_db): return
    if not os.path.exists(carpeta_backups): os.makedirs(carpeta_backups)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_destino = os.path.join(carpeta_backups, f"backup_{timestamp}.db")

    try:
        shutil.copy2(archivo_db, ruta_destino)
        gestionar_limite_backups(carpeta_backups)
        print(f"📦 Backup automático creado.")
    except Exception as e:
        print(f"❌ Error en backup: {e}")

def gestionar_limite_backups(ruta_carpeta, limite=10):
    archivos = [os.path.join(ruta_carpeta, f) for f in os.listdir(ruta_carpeta)]
    archivos.sort(key=os.path.getmtime)
    while len(archivos) > limite:
        os.remove(archivos.pop(0))

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS boosters (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE)')
    cursor.execute('CREATE TABLE IF NOT EXISTS inventario (id INTEGER PRIMARY KEY AUTOINCREMENT, user_pass TEXT NOT NULL UNIQUE, elo_tipo TEXT, descripcion TEXT DEFAULT "FRESH")')

    cursor.execute('''CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, booster_id INTEGER, booster_nombre TEXT,
            user_pass TEXT, elo_inicial TEXT, fecha_inicio TEXT, fecha_limite TEXT,
            estado TEXT DEFAULT 'En progreso', elo_final TEXT, wr REAL, fecha_fin_real TEXT,
            pago_cliente REAL, pago_booster REAL, ganancia_empresa REAL,
            ajuste_valor REAL DEFAULT 0, ajuste_motivo TEXT,
            pago_realizado INTEGER DEFAULT 0,
            FOREIGN KEY (booster_id) REFERENCES boosters (id))''')

    try: cursor.execute('ALTER TABLE pedidos ADD COLUMN pago_realizado INTEGER DEFAULT 0')
    except: pass
    try: cursor.execute('ALTER TABLE pedidos ADD COLUMN notas TEXT DEFAULT "FRESH"')
    except: pass
    try: cursor.execute('ALTER TABLE pedidos ADD COLUMN opgg TEXT DEFAULT ""')
    except: pass
    try: cursor.execute('ALTER TABLE boosters ADD COLUMN binance TEXT DEFAULT ""')
    except: pass
    try: cursor.execute('ALTER TABLE pedidos ADD COLUMN bote_pedido REAL DEFAULT 0')
    except: pass
    try: cursor.execute('ALTER TABLE pedidos ADD COLUMN bote_wr REAL DEFAULT 0')
    except: pass
    try: cursor.execute('ALTER TABLE pedidos ADD COLUMN cuenta_ranking INTEGER DEFAULT 1')
    except: pass
    try: cursor.execute('ALTER TABLE boosters ADD COLUMN en_ranking INTEGER DEFAULT 1')
    except: pass
    try: cursor.execute('ALTER TABLE boosters ADD COLUMN password TEXT DEFAULT "1234"')
    except: pass
    try: cursor.execute('ALTER TABLE boosters ADD COLUMN discord_id TEXT DEFAULT ""')
    except: pass

    cursor.execute('CREATE TABLE IF NOT EXISTS logs_auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, evento TEXT, detalles TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS config_precios (division TEXT PRIMARY KEY, precio_cliente REAL, margen_perez REAL, puntos INTEGER DEFAULT 2)')
    cursor.execute('CREATE TABLE IF NOT EXISTS sistema_config (clave TEXT PRIMARY KEY, valor TEXT)')
    
    cursor.execute("SELECT COUNT(*) FROM config_precios")
    if cursor.fetchone()[0] == 0:
        precios = [
            ('D1', 45.0, 10.0, 45), ('D2', 35.0, 10.0, 40), ('D3', 30.0, 10.0, 35), ('D4', 30.0, 10.0, 30),
            ('E1', 18.0, 5.0, 21),  ('E2', 15.0, 5.0, 18),  ('E3', 12.0, 5.0, 15),  ('E4', 12.0, 5.0, 12),
            ('P1', 10.0, 5.0, 8),   ('P2', 10.0, 5.0, 6),   ('P3', 8.0, 5.0, 4),    ('P4', 8.0, 5.0, 2)
        ]
        cursor.executemany("INSERT INTO config_precios VALUES (?, ?, ?, ?)", precios)
    
    conn.commit()
    conn.commit()
    conn.close()


# ==========================================
# SECCIÓN 1: GESTIÓN DE BOOSTERS
# ==========================================

def agregar_booster(nombre, password="1234", discord_id=""):
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO boosters (nombre, password, discord_id) VALUES (?, ?, ?)", (nombre, password, discord_id))
        conn.commit(); return True
    except Exception as e:
        print(f"Error agregando booster: {e}")
        return False
    finally: conn.close()

def obtener_boosters_db():
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, COALESCE(en_ranking, 1), password, discord_id FROM boosters ORDER BY nombre")
    data = cursor.fetchall(); conn.close(); return data

def toggle_ranking_booster(id_booster, nuevo_estado):
    """Activa (1) o desactiva (0) el ranking de un booster."""
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE boosters SET en_ranking = ? WHERE id = ?", (nuevo_estado, id_booster))
        conn.commit(); return True
    except Exception as e:
        print(f"Error toggle ranking: {e}"); return False
    finally: conn.close()

def eliminar_booster(id_booster):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("DELETE FROM boosters WHERE id = ?", (id_booster,))
    exito = cursor.rowcount > 0
    conn.commit(); conn.close(); return exito
    
def obtener_booster_por_id(id_booster):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, en_ranking, password, discord_id FROM boosters WHERE id = ?", (id_booster,))
    data = cursor.fetchone(); conn.close(); return data

def actualizar_booster_db(id_booster, nombre_nuevo, password_nuevo=None, discord_id_nuevo=None):
    conn = conectar()
    cursor = conn.cursor()
    if password_nuevo is not None and discord_id_nuevo is not None:
        cursor.execute("UPDATE boosters SET nombre = ?, password = ?, discord_id = ? WHERE id = ?", 
                       (nombre_nuevo, password_nuevo, discord_id_nuevo, id_booster))
    else:
        cursor.execute("UPDATE boosters SET nombre = ? WHERE id = ?", (nombre_nuevo, id_booster))
    conn.commit()
    conn.close()

# ==========================================
# SECCIÓN 2: GESTIÓN DE INVENTARIO
# ==========================================

def agregar_cuenta(user_pass, elo_tipo, descripcion=None):
    if not descripcion or str(descripcion).strip() == "": descripcion = "FRESH"
    conn = conectar(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO inventario (user_pass, elo_tipo, descripcion) VALUES (?, ?, ?)", (user_pass, elo_tipo, descripcion))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def obtener_inventario():
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT id, user_pass, elo_tipo, descripcion FROM inventario ORDER BY elo_tipo")
    items = cursor.fetchall(); conn.close(); return items

def eliminar_cuenta(id_cuenta):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("DELETE FROM inventario WHERE id = ?", (id_cuenta,))
    exito = cursor.rowcount > 0; conn.commit(); conn.close(); return exito


def actualizar_inventario_db(id_inv, datos):
    conn = conectar()
    cursor = conn.cursor()
    columnas = ", ".join([f"{k} = ?" for k in datos.keys()])
    valores = list(datos.values())
    valores.append(id_inv)
    cursor.execute(f"UPDATE inventario SET {columnas} WHERE id = ?", valores)
    conn.commit()
    conn.close()

# ==========================================
# SECCIÓN 3: GESTIÓN DE PEDIDOS
# ==========================================


def crear_pedido(id_booster, nombre_booster, id_cuenta, user_pass, elo, fecha_fin):
    conn = conectar(); cursor = conn.cursor(); exito = False
    try:
        cursor.execute("SELECT descripcion FROM inventario WHERE id = ?", (id_cuenta,))
        res = cursor.fetchone()
        nota_actual = res[0] if res and res[0] else "FRESH"

        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if "/" in str(fecha_fin):
            f_limite = datetime.strptime(fecha_fin, "%d/%m/%Y").strftime("%Y-%m-%d")
        else:
            f_limite = str(fecha_fin).split(' ')[0]
        cursor.execute('''INSERT INTO pedidos (booster_id, booster_nombre, user_pass, elo_inicial, 
                          fecha_inicio, fecha_limite, estado, notas) VALUES (?, ?, ?, ?, ?, ?, 'En progreso', ?)''', 
                       (id_booster, nombre_booster, user_pass, elo, fecha_hoy, f_limite, nota_actual))
        cursor.execute("DELETE FROM inventario WHERE id = ?", (id_cuenta,))
        conn.commit(); exito = True
    except Exception as e: 
        print(f"Error al crear pedido: {e}")
        conn.rollback()
    finally: conn.close()
    return exito

def obtener_pedidos_activos():
    conn = conectar()
    cursor = conn.cursor()
    # Hacemos JOIN con boosters para traer el ID de discord para notificaciones personalizadas
    cursor.execute("""
        SELECT p.id, p.booster_nombre, p.elo_inicial, p.user_pass, p.fecha_inicio, p.fecha_limite, b.discord_id 
        FROM pedidos p 
        LEFT JOIN boosters b ON p.booster_nombre = b.nombre
        WHERE p.estado = 'En progreso' 
        ORDER BY p.fecha_limite ASC
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def registrar_abandono_db(id_pedido, elo_dejado, wr_dejado):
    conn = conectar(); cursor = conn.cursor(); exito = False
    try:
        cursor.execute("SELECT user_pass, elo_inicial, notas FROM pedidos WHERE id = ?", (id_pedido,))
        datos = cursor.fetchone()
        if not datos: return False
        u_p, elo_orig, nota_antigua = datos
        
        fecha_fin = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("SELECT id FROM inventario WHERE user_pass = ?", (u_p,))
        inv_exists = cursor.fetchone()
        if inv_exists:
            cursor.execute("UPDATE inventario SET elo_tipo=?, descripcion=? WHERE id=?", (elo_orig, nota_antigua, inv_exists[0]))
        else:
            cursor.execute("INSERT INTO inventario (user_pass, elo_tipo, descripcion) VALUES (?, ?, ?)", (u_p, elo_orig, nota_antigua))
        
        cursor.execute("UPDATE pedidos SET estado='Abandonado', elo_final=?, wr=?, fecha_fin_real=? WHERE id=?", (elo_dejado, wr_dejado, fecha_fin, id_pedido))
        conn.commit()
        exito = True
    except Exception as e:
        print(f"Error crítico en abandono: {e}")
    finally: 
        conn.close()
        
    return exito

def actualizar_pedido_db(id_pedido, datos):

    conn = conectar()
    cursor = conn.cursor()

    columnas = ", ".join([f"{k} = ?" for k in datos.keys()])
    valores = list(datos.values())
    valores.append(id_pedido)

    query = f"UPDATE pedidos SET {columnas} WHERE id = ?"
    cursor.execute(query, valores)

    conn.commit()
    conn.close()

def obtener_resumen_alertas():
    conn = conectar()
    cursor = conn.cursor()
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 'En progreso' AND fecha_limite <= ?", (hoy,))
    vencidos = cursor.fetchone()[0]
    
  
    cursor.execute("SELECT COUNT(*) FROM inventario")
    stock = cursor.fetchone()[0]
    
    conn.close()
    return vencidos, stock
    
def finalizar_pedido_db(id_r, wr, fecha_hoy, elo_fin, ganancia, pago_b, pago_c, ajuste_valor, bote_ped=0.0, bote_w=0.0, cuenta_ranking=1):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE pedidos 
            SET estado = 'Terminado', wr = ?, fecha_fin_real = ?, 
                elo_final = ?, ganancia_empresa = ?, pago_booster = ?, 
                pago_cliente = ?, ajuste_valor = ?,
                bote_pedido = ?, bote_wr = ?, cuenta_ranking = ?
            WHERE id = ?
        """, (wr, fecha_hoy, elo_fin, ganancia, pago_b, pago_c, ajuste_valor, bote_ped, bote_w, cuenta_ranking, id_r))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al finalizar pedido en DB: {e}")
        return False
        
# ==========================================
# SECCIÓN 4: HISTORIAL
# ==========================================

def obtener_historial_completo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, booster_nombre, user_pass, elo_final, 
               fecha_inicio, 
               fecha_fin_real, 
               estado,
               wr
        FROM pedidos 
        WHERE estado IN ('Terminado', 'Abandonado', 'Baneada')
        ORDER BY fecha_fin_real DESC, id DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data

# ==========================================
# SECCIÓN 5: CONFIGURACIÓN DE TARIFAS
# ==========================================

def obtener_config_precios():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT division, precio_cliente, margen_perez, puntos FROM config_precios ORDER BY puntos DESC")
    res = cursor.fetchall()
    conn.close()
    return res

def actualizar_precio_db(division, nuevo_precio, nuevo_margen, nuevos_puntos):
    conn = conectar()
    cursor = conn.cursor()
    try:

        cursor.execute("""
            UPDATE config_precios 
            SET precio_cliente = ?, margen_perez = ?, puntos = ? 
            WHERE division = ?
        """, (nuevo_precio, nuevo_margen, nuevos_puntos, division))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar tarifa: {e}")
        return False
    finally:
        conn.close()

def agregar_precio_db(div, p_cli, m_per, pts=2):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO config_precios (division, precio_cliente, margen_perez, puntos) 
            VALUES (?, ?, ?, ?)
        """, (div, p_cli, m_per, pts))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al agregar tarifa: {e}")
        return False
    finally:
        conn.close()

def eliminar_precio_db(div):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM config_precios WHERE division = ?", (div,))
        exito = cursor.rowcount > 0
        conn.commit()
        return exito
    except Exception as e:
        print(f"Error al eliminar tarifa: {e}")
        return False
    finally:
        conn.close()

# ==========================================
# SECCIÓN 6: DASHBOARD Y REPORTES
# ==========================================

def obtener_resumen_financiero_real(filtro_fecha=None):
    conn = conectar()
    cursor = conn.cursor()
    if not filtro_fecha: filtro_fecha = datetime.now().strftime("%Y-%m")

    cursor.execute("""
        SELECT SUM(pago_booster), SUM(ganancia_empresa) - COUNT(*), COUNT(*)
        FROM pedidos 
        WHERE estado = 'Terminado' AND fecha_fin_real LIKE ? 
    """, (f"{filtro_fecha}%",))
    
    res = cursor.fetchone()
    conn.close()
    if res and res[2] > 0: return (res[0] or 0.0, res[1] or 0.0, res[2])
    return (0.0, 0.0, 0)

def obtener_profit_diario_db():
    conn = conectar(); cursor = conn.cursor()
    hoy = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT SUM(ganancia_empresa) 
        FROM pedidos 
        WHERE estado = 'Terminado' 
        AND fecha_fin_real LIKE ?
    """, (f"{hoy}%",))
    
    res = cursor.fetchone()
    conn.close()
    return res[0] if res and res[0] else 0.0

def obtener_kpis_mensuales():
    conn = conectar()
    cursor = conn.cursor()
    mes_actual = datetime.now().strftime("%Y-%m")

    cursor.execute("""
        SELECT SUM(ganancia_empresa) - COUNT(*), COUNT(*) 
        FROM pedidos 
        WHERE estado = 'Terminado' AND fecha_fin_real LIKE ?
    """, (f"{mes_actual}%",))
    
    datos = cursor.fetchone()
    conn.close()
    return datos[0] if datos[0] else 0.0, datos[1] if datos[1] else 0

def obtener_conteo_stock():
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inventario")
        res = cursor.fetchone()
        return res[0] if res else 0
    except Exception as e:
        print(f"Error conteo stock: {e}")
        return 0
    finally:
        conn.close()

def obtener_conteo_pedidos_activos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 'En progreso'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def obtener_ganancia_proyectada():
    conn = conectar()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT elo_inicial FROM pedidos WHERE estado = 'En progreso'")
        pedidos = cursor.fetchall()
        
        cursor.execute("SELECT division, margen_perez FROM config_precios")
        tarifas = {row[0].upper(): row[1] for row in cursor.fetchall()}
        
        total = 0.0
        for (elo,) in pedidos:
            elo_clean = str(elo).upper().strip()
        
            if elo_clean in tarifas:
                total += tarifas[elo_clean]
            else:
                for div, margen in tarifas.items():
                    if div.startswith(elo_clean[0]):
                        total += margen
                        break
        total = total - len(pedidos)
        return float(total)
    except:
        return 0.0
    finally:
        conn.close()

def obtener_datos_reporte_avanzado(mes_nombre, booster_nombre):
    conn = conectar()
    cursor = conn.cursor()

    meses_dict = {
        "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
        "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
        "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
    }

    query = "SELECT * FROM pedidos WHERE estado = 'Terminado'"

    params = []
    
    if mes_nombre != "Todos":
        mes_num = meses_dict.get(mes_nombre)
        anio_actual = datetime.now().year

        query += " AND fecha_fin_real LIKE ?"
        params.append(f"{anio_actual}-{mes_num}%")
        
    if booster_nombre != "Todos":
        query += " AND booster_nombre = ?"
        params.append(booster_nombre)

    query += " ORDER BY fecha_fin_real DESC, id DESC"
    
    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()
    return datos

# ==========================================
# SECCIÓN 7: CONFIGURACIÓN DEL SISTEMA (DISCORD)
# ==========================================

def guardar_config_sistema(clave, valor):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO sistema_config (clave, valor) VALUES (?, ?)", (clave, valor))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def obtener_config_sistema(clave):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT valor FROM sistema_config WHERE clave = ?", (clave,))
        res = cursor.fetchone()
        return res[0] if res else ""
    finally: conn.close()
    
def ya_se_ejecuto_hoy(tarea):
    hoy = datetime.now().strftime("%Y-%m-%d")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM sistema_config WHERE clave = ?", (f"last_run_{tarea}",))
    res = cursor.fetchone()
    conn.close()
    
    if res and res[0] == hoy:
        return True
    return False

def marcar_tarea_completada(tarea):
    hoy = datetime.now().strftime("%Y-%m-%d")
    guardar_config_sistema(f"last_run_{tarea}", hoy)

# ==========================================
# SECCIÓN 8: SISTEMA DE AUDITORÍA (LOGS)
# ==========================================

def registrar_log(evento, detalles):
    """Guarda un evento en la caja negra del sistema."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO logs_auditoria (fecha, evento, detalles) VALUES (?, ?, ?)", (fecha, evento, detalles))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error guardando log: {e}")

def obtener_logs_db(limite=50):
    """Recupera los últimos movimientos."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, evento, detalles FROM logs_auditoria ORDER BY id DESC LIMIT ?", (limite,))
    datos = cursor.fetchall()
    conn.close()
    return datos

# ==========================================
# SECCIÓN 9:SISTEMA LEABOARD
# ==========================================

def obtener_ranking_staff_db(filtro_fecha=None):
    conn = conectar(); cursor = conn.cursor()
    if not filtro_fecha: filtro_fecha = datetime.now().strftime("%Y-%m")
    query = """
    SELECT p.booster_nombre as nombre, 
           COUNT(CASE WHEN p.estado = 'Terminado' AND IFNULL(p.cuenta_ranking, 1) = 1 THEN 1 END) as terminados,
           COUNT(CASE WHEN p.estado = 'Terminado' AND IFNULL(p.cuenta_ranking, 1) = 1 AND p.bote_wr > 0 THEN 1 END) as high_wr,
           COUNT(CASE WHEN p.estado = 'Abandonado' THEN 1 END) as abandonos,
           COALESCE(SUM(CASE 
               WHEN p.estado = 'Terminado' AND IFNULL(p.cuenta_ranking, 1) = 1 THEN COALESCE((SELECT puntos FROM config_precios WHERE UPPER(TRIM(division)) = UPPER(TRIM(p.elo_final))), 2)
               WHEN p.estado = 'Abandonado' THEN -10 
               WHEN p.estado = 'Terminado' AND IFNULL(p.cuenta_ranking, 1) = 0 THEN 0
               ELSE 0 END), 0) as score
    FROM pedidos p
    WHERE p.fecha_fin_real LIKE ? AND COALESCE((SELECT en_ranking FROM boosters WHERE nombre = p.booster_nombre LIMIT 1), 1) = 1
    GROUP BY p.booster_nombre 
    HAVING (terminados > 0 OR abandonos > 0)
    ORDER BY score DESC
    """
    cursor.execute(query, (f"{filtro_fecha}%",))
    ranking = cursor.fetchall(); conn.close(); return ranking

def obtener_total_bote_ranking(mes_filtro=None):
    conn = conectar(); cursor = conn.cursor()
    if not mes_filtro: mes_filtro = datetime.now().strftime("%Y-%m")
    
    # Solo sumar bote de pedidos que cuentan para el ranking
    sql = """
        SELECT SUM(IFNULL(bote_pedido, 0) + IFNULL(bote_wr, 0)) 
        FROM pedidos
        WHERE estado = 'Terminado'
        AND fecha_fin_real LIKE ?
        AND COALESCE((SELECT en_ranking FROM boosters WHERE nombre = booster_nombre LIMIT 1), 1) = 1
    """
    cursor.execute(sql, (f"{mes_filtro}%",))
    resultado = cursor.fetchone()
    conn.close()
    return float(resultado[0] if resultado and resultado[0] else 0.0)

def obtener_pedidos_mes_actual_db():
    conn = conectar(); cursor = conn.cursor()
    mes_actual = datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT COUNT(*) FROM pedidos 
        WHERE estado = 'Terminado' AND fecha_fin_real LIKE ? AND bote_wr > 0
        AND IFNULL(cuenta_ranking, 1) = 1
    """, (f"{mes_actual}%",))
    res = cursor.fetchone(); conn.close(); return res[0] if res else 0

def disolver_ranking_mensual_db(filtro_fecha):
    conn = conectar()
    cursor = conn.cursor()
    hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Obtener todos los pedidos del mes con bote
    cursor.execute("""
        SELECT id, booster_nombre, bote_pedido, bote_wr, pago_realizado
        FROM pedidos
        WHERE estado = 'Terminado' 
        AND fecha_fin_real LIKE ?
        AND (IFNULL(bote_pedido, 0) > 0 OR IFNULL(bote_wr, 0) > 0)
    """, (f"{filtro_fecha}%",))
    
    pedidos_con_bote = cursor.fetchall()
    
    for p in pedidos_con_bote:
        id_pedido = p[0]
        booster = p[1]
        b_ped = float(p[2] or 0)
        b_wr = float(p[3] or 0)
        pago_realizado = int(p[4] or 0)
        
        # 1. El bote_pedido se va a ganancia_empresa del mismo pedido
        # (Esto automáticamente lo añade al neto de la empresa en los reportes)
        cursor.execute("""
            UPDATE pedidos
            SET ganancia_empresa = ganancia_empresa + ?,
                bote_pedido = 0
            WHERE id = ?
        """, (b_ped, id_pedido))
        
        # 2. El bote_wr se va al booster
        if b_wr > 0:
            if pago_realizado == 0:
                # Si el pedido original aún NO se le ha pagado, simplemente se lo sumamos a su pago_booster
                cursor.execute("""
                    UPDATE pedidos
                    SET pago_booster = pago_booster + ?,
                        bote_wr = 0
                    WHERE id = ?
                """, (b_wr, id_pedido))
            else:
                # Si el pedido YA se pagó, necesitamos crearle una liquidación pendiente (un nuevo registro)
                cursor.execute("""
                    INSERT INTO pedidos (booster_nombre, elo_final, estado, pago_booster, 
                                         ganancia_empresa, pago_cliente, fecha_fin_real, 
                                         pago_realizado, bote_pedido, bote_wr, cuenta_ranking)
                    VALUES (?, 'Reembolso Bono WR', 'Terminado', ?, 0, 0, ?, 0, 0, 0, 0)
                """, (booster, b_wr, hoy))
                
                # Y vaciar el bote_wr del pedido original
                cursor.execute("""
                    UPDATE pedidos
                    SET bote_wr = 0
                    WHERE id = ?
                """, (id_pedido,))

    conn.commit()
    conn.close()
    return len(pedidos_con_bote)

def obtener_resumen_mensual_db(filtro_fecha=None):
    conn = conectar()
    cursor = conn.cursor()
    if filtro_fecha:
        where_clause = "WHERE fecha_fin_real LIKE ? AND estado IN ('Terminado', 'Abandonado')"
        params = (f"{filtro_fecha}%",)
    else:
        where_clause = "WHERE estado IN ('Terminado', 'Abandonado')"
        params = ()
        
    query = f"""
        SELECT 
            COUNT(CASE WHEN estado = 'Terminado' AND elo_final != 'Reembolso Bono WR' AND IFNULL(cuenta_ranking, 1) = 1 THEN 1 END),
            COUNT(CASE WHEN estado = 'Abandonado' THEN 1 END),
            COALESCE(AVG(CASE WHEN estado = 'Terminado' AND elo_final != 'Reembolso Bono WR' AND IFNULL(cuenta_ranking, 1) = 1 THEN wr END), 0),
            COUNT(CASE WHEN estado = 'Terminado' AND bote_wr > 0 AND IFNULL(cuenta_ranking, 1) = 1 THEN 1 END),
            COALESCE(AVG(CASE WHEN estado = 'Terminado' AND elo_final != 'Reembolso Bono WR' AND IFNULL(cuenta_ranking, 1) = 1 THEN JULIANDAY(fecha_fin_real) - JULIANDAY(fecha_inicio) END), 0)
        FROM pedidos {where_clause}
    """
    cursor.execute(query, params)
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 0, 0, 0, 0)
    
def obtener_ranking_db():
    conn = conectar(); cursor = conn.cursor()
    mes_actual = datetime.now().strftime("%Y-%m")

    query = """
        SELECT booster_nombre, COUNT(*), AVG(wr)
        FROM pedidos
        WHERE estado = 'Terminado' AND fecha_fin_real LIKE ?
        AND COALESCE((SELECT en_ranking FROM boosters WHERE nombre = booster_nombre LIMIT 1), 1) = 1
        GROUP BY booster_nombre ORDER BY COUNT(*) DESC
    """
    cursor.execute(query, (f"{mes_actual}%",))
    res = cursor.fetchall(); conn.close(); return res
    
# ==========================================
# SECCIÓN 10: SISTEMA PAGOS A BOOSTERS
# ==========================================

def obtener_balance_general_db(filtro_fecha=None):
    conn = conectar(); cursor = conn.cursor()

    query = """
        SELECT SUM(pago_cliente), SUM(pago_booster), SUM(ganancia_empresa), COUNT(*)
        FROM pedidos WHERE estado = 'Terminado'
    """
    params = []
    if filtro_fecha:
        query += " AND fecha_fin_real LIKE ?"
        params.append(f"{filtro_fecha}%")
        
    cursor.execute(query, params)
    res = cursor.fetchone(); conn.close()

    total_cli = res[0] if res[0] is not None else 0.0
    total_boo = res[1] if res[1] is not None else 0.0
    utilidad = res[2] if res[2] is not None else (total_cli - total_boo)
    cantidad = res[3] if res[3] is not None else 0
    return utilidad, total_cli, total_boo, cantidad

def obtener_saldos_pendientes_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            booster_nombre, 
            SUM(pago_booster),
            COUNT(*),
            GROUP_CONCAT(elo_final || ' ($' || pago_booster || ')', ' + ')
        FROM pedidos 
        WHERE estado = 'Terminado' 
        AND (pago_realizado = 0 OR pago_realizado IS NULL)
        GROUP BY booster_nombre
        ORDER BY SUM(pago_booster) DESC
    """)
    res = cursor.fetchall()
    conn.close()
    return res

def liquidar_pagos_booster_db(nombre_booster):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pedidos 
        SET pago_realizado = 1 
        WHERE booster_nombre = ? AND estado = 'Terminado' AND (pago_realizado = 0 OR pago_realizado IS NULL)
    """, (nombre_booster,))
    
    conn.commit()
    cant = cursor.rowcount
    conn.close()
    return cant
    