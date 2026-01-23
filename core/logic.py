from datetime import datetime, timedelta

# ==========================================
# SECCIÓN 1: NORMALIZACIÓN
# ==========================================

def normalizar_elo(entrada):

    if not entrada: return ""
    texto = entrada.strip().upper()
    mapeo = {
        'D': 'Diamante',
        'P': 'Emerald/Plat',
        'E': 'Emerald/Plat',
        'EP': 'Emerald/Plat'
    }
    return mapeo.get(texto, texto)

# ==========================================
# SECCIÓN 2: LÓGICA FINANCIERA DINÁMICA
# ==========================================

def calcular_pago_real(division, wr, ajuste_manual=0):
    
    from core.database import conectar
    
    division = division.upper().strip()
    conn = conectar()
    cursor = conn.cursor()
    
    try:

        cursor.execute("SELECT precio_cliente, margen_perez FROM config_precios WHERE division = ?", (division,))
        resultado = cursor.fetchone()
        
        if not resultado:
            return 0.0, 0.0, 0.0
            
        precio_cliente, margen_perez = resultado
        
        pago_booster = precio_cliente - margen_perez
        
        # --- REGLAS DE RENDIMIENTO (HARDCODED POR POLÍTICA) ---
        
        if wr >= 60:
            pago_booster += 1.0
            precio_cliente += 1.0 

        if wr < 50:
            pago_booster -= (pago_booster * 0.25)
        
        pago_booster += ajuste_manual
        
        if pago_booster < 0: pago_booster = 0

        ganancia_final_empresa = precio_cliente - pago_booster
            
        return round(precio_cliente, 2), round(pago_booster, 2), round(ganancia_final_empresa, 2)

    except Exception as e:
        print(f"Error en cálculo financiero: {e}")
        return 0.0, 0.0, 0.0
    finally:
        conn.close()

# ==========================================
# SECCIÓN 3: GESTIÓN DE TIEMPOS
# ==========================================

def calcular_fecha_limite_sugerida(dias=10): 
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M")

def extender_fecha(fecha_actual_str, dias_a_sumar):
    try:
        fecha_dt = datetime.strptime(fecha_actual_str, "%Y-%m-%d %H:%M")
        nueva = fecha_dt + timedelta(days=dias_a_sumar)
        return nueva.strftime("%Y-%m-%d %H:%M")
    except:
        return None


def calcular_tiempo_transcurrido(inicio_str):
    """Calcula cuánto tiempo lleva activo un pedido (Solo Fecha)."""
    try:

        fecha_limpia = inicio_str.split(' ')[0]
        inicio = datetime.strptime(fecha_limpia, "%Y-%m-%d")
        ahora = datetime.now()
        
        diferencia = ahora - inicio
        dias = diferencia.days
        
        if dias == 0: return "Hoy"
        if dias == 1: return "1 día"
        return f"{dias} días"
    except:
        return "N/A"

def calcular_duracion_servicio(inicio_str, fin_str):
    """Calcula duración total del servicio para el historial."""
    try:
        d1 = datetime.strptime(inicio_str.split(' ')[0], "%Y-%m-%d")
        d2 = datetime.strptime(fin_str.split(' ')[0], "%Y-%m-%d")
        diff = (d2 - d1).days
        return f"{diff} días" if diff > 0 else "Mismo día"
    except:
        return "N/A"
