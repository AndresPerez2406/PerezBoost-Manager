from core.database import agregar_booster, obtener_boosters_db, eliminar_booster

def registrar_booster_logica(nombre_entrada):

    nombre_limpio = nombre_entrada.strip().title()

    if not nombre_limpio:
        return False, "⚠️ El nombre no puede estar vacío."

    if len(nombre_limpio) < 3:
        return False, "⚠️ El nombre es demasiado corto (mínimo 3 letras)."

    if agregar_booster(nombre_limpio):
        return True, f"✅ '{nombre_limpio}' registrado exitosamente."
    else:
        return False, f"❌ El booster '{nombre_limpio}' ya existe."

def obtener_boosters_procesados():

    try:
        datos_raw = obtener_boosters_db()
       
        return [(i, b[0], b[1]) for i, b in enumerate(datos_raw, start=1)]
    except Exception as e:
        print(f"Error en lectura de boosters: {e}")
        return []

def eliminar_booster_logica(id_real):

    if eliminar_booster(id_real):
        return True, "✅ Booster eliminado correctamente."
    else:
        return False, "❌ Error: No se encontró el registro."