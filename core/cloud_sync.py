import sqlite3
import psycopg2
from psycopg2 import extras
import shutil
from datetime import datetime


AWS_HOST = "perezboost-db.cfyakym2046h.us-east-2.rds.amazonaws.com"
AWS_DB = "postgres"
AWS_USER = "postgres"
AWS_PASS = "Andres2406."
AWS_PORT = "5432"

def logica_subir_a_nube(callback_exito, callback_error):
    try:
        conn_local = sqlite3.connect("perezboost.db")
        cur_local = conn_local.cursor()
        conn_cloud = psycopg2.connect(host=AWS_HOST, database=AWS_DB, user=AWS_USER, password=AWS_PASS, port=AWS_PORT)
        cur_cloud = conn_cloud.cursor()

        tablas = ["logs_auditoria", "pedidos", "inventario", "boosters", "config_precios", "sistema_config"]
        for t in tablas: cur_cloud.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

        cur_cloud.execute("CREATE TABLE boosters (id SERIAL PRIMARY KEY, nombre VARCHAR(255) UNIQUE);")
        cur_cloud.execute("CREATE TABLE inventario (id SERIAL PRIMARY KEY, user_pass VARCHAR(255), elo_tipo VARCHAR(50), descripcion TEXT);")
        cur_cloud.execute("CREATE TABLE config_precios (division VARCHAR(50) PRIMARY KEY, precio_cliente DOUBLE PRECISION, margen_perez DOUBLE PRECISION, puntos INTEGER);")
        cur_cloud.execute("CREATE TABLE sistema_config (clave VARCHAR(255) PRIMARY KEY, valor TEXT);")
        cur_cloud.execute("CREATE TABLE logs_auditoria (id SERIAL PRIMARY KEY, fecha VARCHAR(50), evento VARCHAR(100), detalles TEXT);")
        cur_cloud.execute("""
            CREATE TABLE pedidos (
                id SERIAL PRIMARY KEY, booster_id INTEGER, booster_nombre VARCHAR(255),
                user_pass VARCHAR(255), elo_inicial VARCHAR(50), fecha_inicio VARCHAR(50),
                fecha_limite VARCHAR(50), estado VARCHAR(50), elo_final VARCHAR(50),
                wr DOUBLE PRECISION, fecha_fin_real VARCHAR(50), 
                pago_cliente DOUBLE PRECISION, pago_booster DOUBLE PRECISION, 
                ganancia_empresa DOUBLE PRECISION, ajuste_valor DOUBLE PRECISION, 
                ajuste_motivo TEXT, pago_realizado INTEGER
            );
        """)
        conn_cloud.commit()

        def migrar(tabla):
            cur_local.execute(f"SELECT * FROM {tabla}")
            filas = cur_local.fetchall()
            if not filas: return
            def limpiar(v): return None if v in [None, "NULL", "NONE", ""] else v
            filas_L = [tuple([limpiar(x) for x in f]) for f in filas]
            placeholders = ",".join(["%s"] * len(filas_L[0]))
            extras.execute_batch(cur_cloud, f"INSERT INTO {tabla} VALUES ({placeholders})", filas_L)

        migrar("boosters"); migrar("inventario"); migrar("config_precios")
        migrar("sistema_config"); migrar("logs_auditoria"); migrar("pedidos")

        for t in ["pedidos", "boosters", "inventario", "logs_auditoria"]:
            try: cur_cloud.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(MAX(id), 1) ) FROM {t};")
            except: pass

        conn_cloud.commit(); conn_local.close(); conn_cloud.close()
        callback_exito()
    except Exception as e: callback_error(str(e))

def logica_bajar_de_nube(callback_exito, callback_error):
    try:

        shutil.copy2("perezboost.db", f"backup_pre_sync_{datetime.now().strftime('%H%M%S')}.db")

        conn_cloud = psycopg2.connect(host=AWS_HOST, database=AWS_DB, user=AWS_USER, password=AWS_PASS, port=AWS_PORT)
        cur_cloud = conn_cloud.cursor()
        conn_local = sqlite3.connect("perezboost.db"); cur_local = conn_local.cursor()

        cur_local.execute("PRAGMA foreign_keys = OFF;")
        for t in ["logs_auditoria", "pedidos", "inventario", "boosters", "config_precios", "sistema_config"]:
            cur_local.execute(f"DELETE FROM {t}")

        def bajar(tabla):
            cur_cloud.execute(f"SELECT * FROM {tabla}")
            filas = cur_cloud.fetchall()
            if filas: cur_local.executemany(f"INSERT INTO {tabla} VALUES ({','.join(['?']*len(filas[0]))})", filas)

        bajar("boosters"); bajar("inventario"); bajar("config_precios")
        bajar("sistema_config"); bajar("logs_auditoria"); bajar("pedidos")

        conn_local.commit(); conn_local.close(); conn_cloud.close()
        callback_exito()
    except Exception as e: callback_error(str(e))