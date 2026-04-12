import sqlite3
import psycopg2
from psycopg2 import extras
import os
import threading
import time
from dotenv import load_dotenv
import decimal

sqlite3.register_adapter(decimal.Decimal, float)

load_dotenv(".env")
# Lógica de Modo Desarrollo (Override si es necesario)
MODO_DESARROLLO = os.getenv("MODO_DESARROLLO") == "True"
if MODO_DESARROLLO:
    load_dotenv(".env.dev", override=True)
    print("🛠️ MODO DESARROLLO (DEV): Usando configuraciones de .env.dev")

# La URL maestra ahora respeta tu modo de trabajo
CLOUD_URL = os.getenv("DATABASE_URL")
DB_LOCAL = "perezboost.db"

# =======================================================
# 🛠️ MOTOR MAESTRO DE SUBIDA (PUSH)
# =======================================================

def _motor_subida_postgres(nombre_target, connection_url):
    if not connection_url:
        print(f"⚠️ Error: URL de {nombre_target} no configurada en .env")
        return False
        
    print(f"🚀 Iniciando SUBIDA PROTEGIDA a {nombre_target}...")
    try:
        conn_local = sqlite3.connect(DB_LOCAL)
        cur_local = conn_local.cursor()
        conn_cloud = psycopg2.connect(connection_url)
        cur_cloud = conn_cloud.cursor()

        # Asegurar Schema
        cur_cloud.execute("""
            CREATE TABLE IF NOT EXISTS boosters (
                id SERIAL PRIMARY KEY, nombre VARCHAR(255) UNIQUE, binance TEXT, 
                en_ranking INTEGER DEFAULT 1, password TEXT DEFAULT '1234', discord_id TEXT DEFAULT ''
            );
        """)
        try: cur_cloud.execute("ALTER TABLE boosters ADD COLUMN IF NOT EXISTS password TEXT DEFAULT '1234';")
        except: pass
        try: cur_cloud.execute("ALTER TABLE boosters ADD COLUMN IF NOT EXISTS discord_id TEXT DEFAULT '';")
        except: pass
        
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS inventario (id SERIAL PRIMARY KEY, user_pass VARCHAR(255), elo_tipo VARCHAR(50), descripcion TEXT);")
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS config_precios (division VARCHAR(50) PRIMARY KEY, precio_cliente DOUBLE PRECISION, margen_perez DOUBLE PRECISION, puntos INTEGER);")
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS sistema_config (clave VARCHAR(255) PRIMARY KEY, valor TEXT);")
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS wallet_perez (id SERIAL PRIMARY KEY, fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, tipo TEXT NOT NULL, categoria TEXT NOT NULL, monto DECIMAL(10,2) NOT NULL, descripcion TEXT);")
        
        cur_cloud.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id SERIAL PRIMARY KEY, booster_id INTEGER, booster_nombre VARCHAR(255),
                user_pass VARCHAR(255), elo_inicial VARCHAR(50), fecha_inicio VARCHAR(50),
                fecha_limite VARCHAR(50), estado VARCHAR(50), elo_final VARCHAR(50),
                wr DOUBLE PRECISION, fecha_fin_real VARCHAR(50),
                pago_cliente DOUBLE PRECISION, pago_booster DOUBLE PRECISION,
                ganancia_empresa DOUBLE PRECISION, ajuste_valor DOUBLE PRECISION DEFAULT 0,
                pago_realizado INTEGER DEFAULT 0,
                opgg TEXT, notas TEXT,
                bote_pedido DOUBLE PRECISION DEFAULT 0, bote_wr DOUBLE PRECISION DEFAULT 0,
                cuenta_ranking INTEGER DEFAULT 1
            );
        """)
        try: cur_cloud.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS bote_pedido DOUBLE PRECISION DEFAULT 0;")
        except: pass
        try: cur_cloud.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS bote_wr DOUBLE PRECISION DEFAULT 0;")
        except: pass
        try: cur_cloud.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cuenta_ranking INTEGER DEFAULT 1;")
        except: pass

        def migrar_tabla(origen, destino):
            if origen == "pedidos":
                cur_local.execute("SELECT id, booster_id, booster_nombre, user_pass, elo_inicial, fecha_inicio, fecha_limite, estado, elo_final, wr, fecha_fin_real, pago_cliente, pago_booster, ganancia_empresa, ajuste_valor, pago_realizado, opgg, notas, bote_pedido, bote_wr, cuenta_ranking FROM pedidos")
            elif origen == "boosters":
                cur_local.execute("SELECT id, nombre, binance, en_ranking, password, discord_id FROM boosters")
            elif origen == "wallet_perez":
                cur_local.execute("SELECT id, fecha, tipo, categoria, monto, descripcion FROM wallet_perez")
            else:
                cur_local.execute(f"SELECT * FROM {origen}")
                
            filas = cur_local.fetchall()
            if not filas: return
            def limpiar(v): return None if v in ["NULL", "NONE", ""] else v
            filas_L = [tuple([limpiar(x) for x in list(f)]) for f in filas]

            if destino == "pedidos":
                query = """
                    INSERT INTO pedidos (
                        id, booster_id, booster_nombre, user_pass, elo_inicial, 
                        fecha_inicio, fecha_limite, estado, elo_final, wr, 
                        fecha_fin_real, pago_cliente, pago_booster, ganancia_empresa, 
                        ajuste_valor, pago_realizado, opgg, notas, bote_pedido, bote_wr, cuenta_ranking
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        booster_nombre = EXCLUDED.booster_nombre,
                        user_pass = EXCLUDED.user_pass,
                        estado = EXCLUDED.estado,
                        elo_final = EXCLUDED.elo_final,
                        wr = EXCLUDED.wr,
                        fecha_fin_real = EXCLUDED.fecha_fin_real,
                        pago_cliente = EXCLUDED.pago_cliente,
                        pago_booster = EXCLUDED.pago_booster,
                        ganancia_empresa = EXCLUDED.ganancia_empresa,
                        pago_realizado = EXCLUDED.pago_realizado,
                        opgg = COALESCE(NULLIF(EXCLUDED.opgg, ''), pedidos.opgg),
                        notas = COALESCE(NULLIF(EXCLUDED.notas, ''), pedidos.notas),
                        bote_pedido = EXCLUDED.bote_pedido,
                        bote_wr = EXCLUDED.bote_wr,
                        cuenta_ranking = EXCLUDED.cuenta_ranking;
                """
                extras.execute_batch(cur_cloud, query, filas_L)
            elif destino == "boosters":
                query = """
                    INSERT INTO boosters (id, nombre, binance, en_ranking, password, discord_id) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        en_ranking = EXCLUDED.en_ranking;
                """
                extras.execute_batch(cur_cloud, query, filas_L)
            elif destino == "wallet_perez":
                cur_cloud.execute("DELETE FROM wallet_perez;")
                query = "INSERT INTO wallet_perez (id, fecha, tipo, categoria, monto, descripcion) VALUES (%s, %s, %s, %s, %s, %s)"
                extras.execute_batch(cur_cloud, query, filas_L)
            else:
                cur_cloud.execute(f"DELETE FROM {destino};")
                cols = len(filas_L[0])
                placeholders = ",".join(["%s"] * cols)
                extras.execute_batch(cur_cloud, f"INSERT INTO {destino} VALUES ({placeholders})", filas_L)

        migrar_tabla("boosters", "boosters")
        migrar_tabla("inventario", "inventario")
        migrar_tabla("config_precios", "config_precios")
        migrar_tabla("pedidos", "pedidos")
        migrar_tabla("sistema_config", "sistema_config")
        migrar_tabla("wallet_perez", "wallet_perez")

        for t in ["pedidos", "boosters", "inventario", "wallet_perez"]:
            try: cur_cloud.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(MAX(id), 1) ) FROM {t};")
            except: pass

        conn_cloud.commit()
        conn_local.close()
        conn_cloud.close()
        print(f"✅ Sincronización exitosa con {nombre_target}.")
        return True
    except Exception as e:
        print(f"❌ Error en subida: {e}")
        return False

# =======================================================
# ⬇️ BAJAR (Pull BRIDGE)
# =======================================================

def _get_cloud_columns(cursor, table_name):
    try:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name.lower()}' AND table_schema = 'public'")
        cols = [row[0] for row in cursor.fetchall()]
        if cols: return cols
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        return [desc[0] for desc in cursor.description]
    except: return []

def _motor_bajar_postgres(nombre_target, connection_url):
    if not connection_url:
        print(f"⚠️ Error: URL de {nombre_target} no configurada.")
        return False

    print(f"⬇️ Conectando a {nombre_target}...")
    try:
        conn_cloud = psycopg2.connect(connection_url)
        cur_cloud = conn_cloud.cursor()
        cur_cloud.execute("SELECT current_database()")
        db_name = cur_cloud.fetchone()[0]
        print(f"✨ Base de Datos: {db_name}")
        
        conn_local = sqlite3.connect(DB_LOCAL)
        cur_local = conn_local.cursor()
        
        cur_local.execute("SELECT clave, valor FROM sistema_config WHERE clave LIKE '%webhook%'")
        respaldos_webhooks = dict(cur_local.fetchall())
        
        tablas = ["pedidos", "inventario", "boosters", "config_precios", "wallet_perez", "sistema_config"]
        for t in tablas:
            cur_local.execute(f"DELETE FROM {t}")

        def bajar(tabla_nube, tabla_local, columnas_deseadas=None, defaults=None):
            if not defaults: defaults = {}
            columnas_reales = _get_cloud_columns(cur_cloud, tabla_nube)
            
            if not columnas_reales:
                cur_cloud.execute(f"SELECT * FROM {tabla_nube}")
                filas = cur_cloud.fetchall()
                if filas:
                    placeholders = ",".join(["?"] * len(filas[0]))
                    cur_local.executemany(f"INSERT INTO {tabla_local} VALUES ({placeholders})", filas)
                return

            if columnas_deseadas:
                cols_para_select = [c for c in columnas_deseadas if c in columnas_reales]
                cur_cloud.execute(f"SELECT {','.join(cols_para_select)} FROM {tabla_nube}")
                filas = cur_cloud.fetchall()
                
                if filas:
                    filas_listas = []
                    for f in filas:
                        idx_cloud = 0
                        fila_final = []
                        for col in columnas_deseadas:
                            if col in columnas_reales:
                                fila_final.append(f[idx_cloud]); idx_cloud += 1
                            else:
                                fila_final.append(defaults.get(col, None))
                        filas_listas.append(tuple(fila_final))
                    
                    placeholders = ",".join(["?"] * len(columnas_deseadas))
                    cur_local.executemany(f"INSERT INTO {tabla_local} ({','.join(columnas_deseadas)}) VALUES ({placeholders})", filas_listas)
            else:
                cur_cloud.execute(f"SELECT * FROM {tabla_nube}")
                filas = cur_cloud.fetchall()
                if filas:
                    placeholders = ",".join(["?"] * len(filas[0]))
                    cur_local.executemany(f"INSERT INTO {tabla_local} VALUES ({placeholders})", filas)
                
        cols_boosters = ["id", "nombre", "binance", "en_ranking", "password", "discord_id"]
        bajar("boosters", "boosters", cols_boosters, defaults={"password": "1234", "discord_id": ""})
        bajar("inventario", "inventario")
        bajar("config_precios", "config_precios")
        
        cols_pedidos = ["id", "booster_id", "booster_nombre", "user_pass", "elo_inicial", "fecha_inicio", "fecha_limite", "estado", "elo_final", "wr", "fecha_fin_real", "pago_cliente", "pago_booster", "ganancia_empresa", "ajuste_valor", "pago_realizado", "opgg", "notas", "bote_pedido", "bote_wr", "cuenta_ranking"]
        bajar("pedidos", "pedidos", cols_pedidos)
        bajar("wallet_perez", "wallet_perez")
        bajar("sistema_config", "sistema_config")
        
        for clave, valor in respaldos_webhooks.items():
            cur_local.execute("INSERT OR REPLACE INTO sistema_config (clave, valor) VALUES (?, ?)", (clave, valor))

        conn_local.commit()
        conn_local.close()
        conn_cloud.close()
        print(f"✅ Sincronización desde nube COMPLETADA.")
        return True
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        return False

# =======================================================
# 🌐 WRAPPERS COMPATIBILIDAD (EL ÚNICO DESTINO)
# =======================================================

def logica_bajar_de_nube(cb_ok, cb_err):
    """Baja datos de DONDE SEA que apunte el .env"""
    if _motor_bajar_postgres("NUBE", CLOUD_URL):
        if cb_ok: cb_ok()
    elif cb_err: cb_err("Fallo en descarga")

def logica_subir_a_nube(cb_ok, cb_err):
    """Sube datos a DONDE SEA que apunte el .env"""
    if _motor_subida_postgres("NUBE", CLOUD_URL):
        if cb_ok: cb_ok()
    elif cb_err: cb_err("Fallo en subida")