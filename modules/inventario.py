from core.database import agregar_cuenta, obtener_inventario, eliminar_cuenta

def obtener_inventario_visual():
    
    try:
        datos_reales = obtener_inventario()
        datos_procesados = []
        
        for indice, fila in enumerate(datos_reales, start=1):

            id_real = fila[0]
            user    = fila[1]
            elo     = fila[2] if fila[2] else "Unranked"
            desc    = fila[3] if fila[3] else "FRESH"
            
      
            datos_procesados.append((indice, id_real, user, elo, desc))
            
        return datos_procesados
    except Exception as e:
        print(f"Error en procesamiento visual de inventario: {e}")
        return []

def registrar_cuenta_gui(u_pass, elo, notas):

    u_pass = u_pass.strip()
    if not u_pass or ":" not in u_pass:
        return False, "❌ Formato inválido. Usa 'Usuario:Password'"
        
    exito = agregar_cuenta(u_pass, elo, notas if notas.strip() else None)
    return exito, "✅ Cuenta guardada" if exito else "❌ Error: Registro fallido (Duplicado?)"

def registrar_lote_gui(texto_masivo, elo):
    
    lineas = texto_masivo.strip().split("\n")
    exitos, errores = 0, 0

    for linea in lineas:
        clean_line = linea.replace("---", ":").replace("    ", ":").strip()
        
        if ":" in clean_line:
            parts = clean_line.split(":")
            if len(parts) >= 2:
                user_pass = f"{parts[0].strip()}:{parts[1].strip()}"
                if agregar_cuenta(user_pass, elo, None):
                    exitos += 1
                    continue
        errores += 1
            
    return exitos, errores

def eliminar_cuenta_gui(id_real):

    return eliminar_cuenta(id_real)