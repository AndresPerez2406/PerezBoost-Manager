import sqlite3
import psycopg2
from psycopg2 import extras
import threading
from tkinter import messagebox

AWS_HOST = "perezboost-db.cfyakym2046h.us-east-2.rds.amazonaws.com"
AWS_DB = "postgres"
AWS_USER = "postgres"
AWS_PASS = "Andres2406."
AWS_PORT = "5432"

def limpiar_valor(valor):
    """Convierte 'NULL', 'None' o vacíos en None real o 0.0 para Postgres"""
    if valor is None: return None
    s_val = str(valor).strip().upper()
    if s_val in ["NULL", "NONE", ""]: return None
    return valor

def ejecutar_sincronizacion(callback_exito, callback_error):
    """Función que hace el trabajo pesado en segundo plano"""
    try:

        conn_local = sqlite3.connect("perezboost.db")
        cur_local = conn_local.cursor()


        conn_cloud = psycopg2.connect(
            host=AWS_HOST, database=AWS_DB, user=AWS_USER, password=AWS_PASS, port=AWS_PORT
        )
        cur_cloud = conn_cloud.cursor()


        tablas = ["logs_auditoria", "pedidos", "inventario", "boosters", "config_precios", "sistema_config"]
        for t in tablas:
            cur_cloud.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

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

        def migrar(tabla, cols_sql):
            cur_local.execute(f"SELECT * FROM {tabla}")
            filas = cur_local.fetchall()
            if not filas: return

            filas_limpias = []
            for f in filas:
                nuevo_f = [limpiar_valor(x) for x in f]
                filas_limpias.append(tuple(nuevo_f))
            
            placeholders = ",".join(["%s"] * len(filas_limpias[0]))
            query = f"INSERT INTO {tabla} VALUES ({placeholders})"
            extras.execute_batch(cur_cloud, query, filas_limpias)

        migrar("boosters", "id, nombre")
        migrar("inventario", "id, user_pass, elo_tipo, descripcion")
        migrar("config_precios", "division, precio_cliente, margen_perez, puntos")
        migrar("sistema_config", "clave, valor")
        migrar("logs_auditoria", "id, fecha, evento, detalles")
        migrar("pedidos", "id, ...")

        tablas_id = ["pedidos", "boosters", "inventario", "logs_auditoria"]
        for t in tablas_id:
            try: cur_cloud.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE(MAX(id), 1) ) FROM {t};")
            except: pass

        conn_cloud.commit()
        conn_local.close()
        conn_cloud.close()
        
        callback_exito()

    except Exception as e:
        print(f"Error Sync: {e}")
        callback_error(str(e))

def iniciar_sync_thread(on_success, on_error):
    """Lanza la sincronización en un hilo aparte para no congelar la app"""
    hilo = threading.Thread(target=ejecutar_sincronizacion, args=(on_success, on_error))
    hilo.start()