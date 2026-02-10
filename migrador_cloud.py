import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# --- CONFIGURACIÓN ---
load_dotenv()
CLOUD_URL = os.getenv("DATABASE_URL")
DB_LOCAL = "perezboost.db"

def migrar_a_la_nube():
    print("🚀 INICIANDO MIGRACIÓN A SUPABASE (V11 FINAL - CORREGIDA)...")
    
    if not CLOUD_URL:
        print("❌ ERROR: No encontré la variable DATABASE_URL en el archivo .env")
        return

    # 1. Conexión LOCAL
    try:
        conn_local = sqlite3.connect(DB_LOCAL)
        cur_local = conn_local.cursor()
        print("✅ Conexión Local: OK")
    except Exception as e:
        print(f"❌ Error conectando local: {e}")
        return

    # 2. Conexión NUBE
    try:
        conn_cloud = psycopg2.connect(CLOUD_URL)
        cur_cloud = conn_cloud.cursor()
        print("✅ Conexión Nube: OK")
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return

    # --- 3. LIMPIEZA Y RECREACIÓN (SCHEMA) ---
    print("\n🧹 Limpiando tablas antiguas en la nube para evitar conflictos...")
    cur_cloud.execute("DROP TABLE IF EXISTS pedidos CASCADE;")
    cur_cloud.execute("DROP TABLE IF EXISTS inventario CASCADE;")
    cur_cloud.execute("DROP TABLE IF EXISTS boosters CASCADE;")
    cur_cloud.execute("DROP TABLE IF EXISTS config_precios CASCADE;")
    cur_cloud.execute("DROP TABLE IF EXISTS config_sistema CASCADE;")
    cur_cloud.execute("DROP TABLE IF EXISTS logs CASCADE;")
    conn_cloud.commit()

    print("🏗️  Creando estructura EXACTA a tu SQLite...")
    
    tablas_sql = [
        # 1. Configuración
        """CREATE TABLE config_sistema (
            clave TEXT PRIMARY KEY,
            valor TEXT
        );""",
        # 2. Precios
        """CREATE TABLE config_precios (
            division TEXT PRIMARY KEY,
            precio_cliente REAL,
            margen_perez REAL,
            puntos INTEGER DEFAULT 2
        );""",
        # 3. Boosters
        """CREATE TABLE boosters (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE
        );""",
        # 4. Inventario
        """CREATE TABLE inventario (
            id SERIAL PRIMARY KEY,
            user_pass TEXT UNIQUE,
            elo_tipo TEXT,
            descripcion TEXT DEFAULT 'FRESH'
        );""",
        # 5. Pedidos (ESTRUCTURA CORREGIDA COMPLETA)
        """CREATE TABLE pedidos (
            id SERIAL PRIMARY KEY,
            booster_id INTEGER,           -- Estaba faltando
            booster_nombre TEXT,
            user_pass TEXT,
            elo_inicial TEXT,
            fecha_inicio TEXT,
            fecha_limite TEXT,
            estado TEXT DEFAULT 'En progreso',
            elo_final TEXT,
            wr REAL,
            fecha_fin_real TEXT,
            pago_cliente REAL,
            pago_booster REAL,
            ganancia_empresa REAL,
            ajuste_valor REAL DEFAULT 0,  -- Estaba faltando
            ajuste_motivo TEXT,           -- Estaba faltando
            pago_realizado INTEGER DEFAULT 0 -- Estaba faltando
        );""",
        # 6. Logs
        """CREATE TABLE logs (
            id SERIAL PRIMARY KEY,
            fecha TEXT,
            evento TEXT,
            detalles TEXT
        );"""
    ]

    for sql in tablas_sql:
        cur_cloud.execute(sql)
    conn_cloud.commit()
    print("✅ Tablas creadas correctamente.")

    # --- 4. COPIA DE DATOS ---
    print("\n📦 Copiando datos...")

    def migrar_tabla(tabla_local, tabla_nube):
        try:
            # Leemos de local
            cur_local.execute(f"SELECT * FROM {tabla_local}")
            datos = cur_local.fetchall()
            
            if not datos:
                print(f"   🔹 {tabla_local}: Vacía localmente.")
                return

            # Construimos el INSERT dinámico
            columnas = len(datos[0])
            placeholders = ",".join(["%s"] * columnas)
            sql_insert = f"INSERT INTO {tabla_nube} VALUES ({placeholders})"
            
            cur_cloud.executemany(sql_insert, datos)
            conn_cloud.commit()
            print(f"   ✅ {tabla_local}: {len(datos)} registros migrados.")

        except Exception as e:
            conn_cloud.rollback() # IMPORTANTE: Si falla, desbloquea la base de datos
            print(f"   ❌ Error migrando {tabla_local}: {e}")

    # Ejecutamos la migración
    migrar_tabla("sistema_config", "config_sistema")
    migrar_tabla("config_precios", "config_precios")
    migrar_tabla("boosters", "boosters")
    migrar_tabla("inventario", "inventario")
    migrar_tabla("pedidos", "pedidos") # Ahora sí debe funcionar
    migrar_tabla("logs_auditoria", "logs")

    # --- 5. AJUSTAR IDs ---
    print("\n🔧 Sincronizando contadores...")
    seqs = [("pedidos", "id"), ("inventario", "id"), ("logs", "id"), ("boosters", "id")]
    for t, col in seqs:
        try:
            cur_cloud.execute(f"SELECT setval(pg_get_serial_sequence('{t}', '{col}'), coalesce(max({col}),0) + 1, false) FROM {t};")
        except: pass
    conn_cloud.commit()

    conn_local.close()
    conn_cloud.close()
    print("\n✨✨ ¡MIGRACIÓN COMPLETADA! AHORA SÍ ✨✨")

if __name__ == "__main__":
    migrar_a_la_nube()