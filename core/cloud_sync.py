import sqlite3
import psycopg2
from psycopg2 import extras
import os
import threading
import time
from dotenv import load_dotenv
import os
from dotenv import load_dotenv

MODO_DESARROLLO = True

if MODO_DESARROLLO:
    load_dotenv(".env.dev")
    print("🛠️ MODO DEV: Conectado a la base de datos de PRUEBAS")
else:
    load_dotenv(".env")
    print("🚀 MODO PROD: Conectado a la base de datos REAL")

CLOUD_URL = os.getenv("DATABASE_URL")

load_dotenv()
SUPABASE_URL = os.getenv("DATABASE_URL")

AWS_CONF = {
    "host": os.getenv("AWS_HOST"),
    "database": os.getenv("AWS_DB", "postgres"),
    "user": os.getenv("AWS_USER", "postgres"),
    "password": os.getenv("AWS_PASSWORD"),
    "port": os.getenv("AWS_PORT", "5432")
}

DB_LOCAL = "perezboost.db"

# =======================================================
# 🛠️ MOTOR MAESTRO DE SUBIDA
# =======================================================

def _motor_subida_postgres(nombre_nube, connection_params):
    print(f"🚀 Iniciando subida a {nombre_nube}...")
    try:
        conn_local = sqlite3.connect(DB_LOCAL)
        cur_local = conn_local.cursor()

        if isinstance(connection_params, str):
            conn_cloud = psycopg2.connect(connection_params)
        else:
            conn_cloud = psycopg2.connect(**connection_params)
        cur_cloud = conn_cloud.cursor()

        cur_cloud.execute("CREATE TABLE IF NOT EXISTS boosters (id SERIAL PRIMARY KEY, nombre VARCHAR(255) UNIQUE);")
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS inventario (id SERIAL PRIMARY KEY, user_pass VARCHAR(255), elo_tipo VARCHAR(50), descripcion TEXT);")
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS config_precios (division VARCHAR(50) PRIMARY KEY, precio_cliente DOUBLE PRECISION, margen_perez DOUBLE PRECISION, puntos INTEGER);")
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS sistema_config (clave VARCHAR(255) PRIMARY KEY, valor TEXT);")
        cur_cloud.execute("CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, fecha VARCHAR(50), evento VARCHAR(100), detalles TEXT);")
        
        cur_cloud.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id SERIAL PRIMARY KEY, booster_id INTEGER, booster_nombre VARCHAR(255),
                user_pass VARCHAR(255), elo_inicial VARCHAR(50), fecha_inicio VARCHAR(50),
                fecha_limite VARCHAR(50), estado VARCHAR(50), elo_final VARCHAR(50),
                wr DOUBLE PRECISION, fecha_fin_real VARCHAR(50),
                pago_cliente DOUBLE PRECISION, pago_booster DOUBLE PRECISION,
                ganancia_empresa DOUBLE PRECISION, ajuste_valor DOUBLE PRECISION DEFAULT 0,
                ajuste_motivo TEXT, pago_realizado INTEGER DEFAULT 0,
                opgg TEXT
            );
        """)
        conn_cloud.commit()

        def migrar_tabla(origen, destino):
            cur_local.execute(f"SELECT * FROM {origen}")
            filas = cur_local.fetchall()
            if not filas: return

            def limpiar(v): return None if v in ["NULL", "NONE", ""] else v
            filas_L = [tuple([limpiar(x) for x in f]) for f in filas]

            if destino == "pedidos":
                query = """
                    INSERT INTO pedidos (
                        id, booster_id, booster_nombre, user_pass, elo_inicial, 
                        fecha_inicio, fecha_limite, estado, elo_final, wr, 
                        fecha_fin_real, pago_cliente, pago_booster, ganancia_empresa, 
                        ajuste_valor, ajuste_motivo, pago_realizado, opgg
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        booster_id = EXCLUDED.booster_id,
                        booster_nombre = EXCLUDED.booster_nombre,
                        user_pass = EXCLUDED.user_pass,
                        elo_inicial = EXCLUDED.elo_inicial,
                        fecha_inicio = EXCLUDED.fecha_inicio,
                        fecha_limite = EXCLUDED.fecha_limite,
                        estado = EXCLUDED.estado,
                        elo_final = EXCLUDED.elo_final,
                        wr = EXCLUDED.wr,
                        fecha_fin_real = EXCLUDED.fecha_fin_real,
                        pago_cliente = EXCLUDED.pago_cliente,
                        pago_booster = EXCLUDED.pago_booster,
                        ganancia_empresa = EXCLUDED.ganancia_empresa,
                        ajuste_valor = EXCLUDED.ajuste_valor,
                        ajuste_motivo = EXCLUDED.ajuste_motivo,
                        pago_realizado = EXCLUDED.pago_realizado;
                """
                extras.execute_batch(cur_cloud, query, filas_L)
            else:
                cur_cloud.execute(f"DELETE FROM {destino};")
                cols = len(filas_L[0])
                placeholders = ",".join(["%s"] * cols)
                extras.execute_batch(cur_cloud, f"INSERT INTO {destino} VALUES ({placeholders})", filas_L)

        migrar_tabla("boosters", "boosters")
        migrar_tabla("inventario", "inventario")
        migrar_tabla("config_precios", "config_precios")
        migrar_tabla("sistema_config", "sistema_config")
        migrar_tabla("logs_auditoria", "logs") 
        migrar_tabla("pedidos", "pedidos")

        for t in ["pedidos", "boosters", "inventario", "logs"]:
            try: cur_cloud.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(MAX(id), 1) ) FROM {t};")
            except: pass

        conn_cloud.commit()
        conn_local.close()
        conn_cloud.close()
        print(f"✅ Subida a {nombre_nube} COMPLETADA.")
        return True

    except Exception as e:
        print(f"❌ Error subiendo a {nombre_nube}: {e}")
        return False

# =======================================================
# 🌐 SUBIR (Push Dual)
# =======================================================

def logica_subir_a_nube(callback_exito, callback_error):
    errores = []

    def hilo_aws():
        if not _motor_subida_postgres("AWS", AWS_CONF): errores.append("AWS falló")

    def hilo_supabase():
        if SUPABASE_URL:
            if not _motor_subida_postgres("Supabase", SUPABASE_URL): errores.append("Supabase falló")
        else:
            errores.append("Falta URL Supabase")

    t1 = threading.Thread(target=hilo_aws)
    t2 = threading.Thread(target=hilo_supabase)
    t1.start(); t2.start()
    t1.join(); t2.join()

    time.sleep(0.5)

    if not errores:
        if callback_exito: callback_exito()
    else:
        if callback_error: callback_error(f"Errores: {', '.join(errores)}")

# =======================================================
# ⬇️ BAJAR (Pull Supabase)
# =======================================================

def logica_bajar_de_nube(callback_exito, callback_error):
    try:

        if not SUPABASE_URL: raise ValueError("No hay URL de Supabase")

        conn_cloud = psycopg2.connect(SUPABASE_URL)
        cur_cloud = conn_cloud.cursor()
        conn_local = sqlite3.connect(DB_LOCAL)
        cur_local = conn_local.cursor()

        cur_local.execute("PRAGMA foreign_keys = OFF;")
        for t in ["logs_auditoria", "pedidos", "inventario", "boosters", "config_precios", "sistema_config"]:
            cur_local.execute(f"DELETE FROM {t}")

        def bajar(tabla_nube, tabla_local):
            cur_cloud.execute(f"SELECT * FROM {tabla_nube}")
            filas = cur_cloud.fetchall()
            if filas:
                placeholders = ",".join(["?"] * len(filas[0]))
                cur_local.executemany(f"INSERT INTO {tabla_local} VALUES ({placeholders})", filas)

        bajar("boosters", "boosters")
        bajar("inventario", "inventario")
        bajar("config_precios", "config_precios")
        bajar("sistema_config", "sistema_config")
        bajar("logs", "logs_auditoria")
        bajar("pedidos", "pedidos")

        conn_local.commit()
        conn_local.close()
        conn_cloud.close()

        print("⏳ Finalizando hilos y estabilizando GUI...")
        time.sleep(1.0)

        if callback_exito: callback_exito()

    except Exception as e:
        print(f"Error bajando: {e}")
        if callback_error: callback_error(str(e))