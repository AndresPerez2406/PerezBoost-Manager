import streamlit as st
import pandas as pd
import psycopg2
import os
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import warnings
import extra_streamlit_components as stx
import time

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')
st.set_page_config(page_title="PerezBoost | Portal Operativo", page_icon="🎮", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    button[title="View source"] {display: none;}
    .viewerBadge_container__1QS1n {display: none;}

    div[data-testid="stMetricValue"] { font-size: 24px; color: #2ecc71; font-weight: bold; }
    [data-testid="stTable"] th, [data-testid="stTable"] td {
        text-align: center !important;
        vertical-align: middle !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 15px;
        color: white;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #2ecc71 !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. CONEXIÓN A LA BASE DE DATOS
# ==============================================================================

load_dotenv(".env")
MODO_DESARROLLO = os.getenv("MODO_DESARROLLO") == "True"

if MODO_DESARROLLO:
    load_dotenv(".env.dev", override=True)
    print("🛠️ MODO DEV: Conectado a la base de datos de PRUEBAS")
else:
    print("🚀 MODO PROD: Conectado a la base de datos REAL")

def get_connection():
    url = os.getenv("DATABASE_URL")
    try: return psycopg2.connect(url, connect_timeout=10)
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def run_query(query):
    conn = get_connection()
    if conn:
        try:
            with conn: return pd.read_sql(query, conn)
        except: return pd.DataFrame()
        finally: conn.close()
    return pd.DataFrame()

# ==============================================================================
# 2. ENRUTAMIENTO: MODO BOOSTER
# ==============================================================================

query_params = st.query_params
if "t" in query_params:
    token_recibido = query_params["t"]
    
    try:
        token_decodificado = base64.urlsafe_b64decode(token_recibido.encode('utf-8')).decode('utf-8')
        id_pedido = token_decodificado.split("-")[1]
    except Exception:
        st.error("Error de autenticación: Enlace de asignación inválido o corrupto.")
        st.stop()
    
    df_info = run_query(f"SELECT booster_nombre, user_pass FROM pedidos WHERE id = {id_pedido}")
    
    if df_info.empty:
        st.error("Error: El pedido solicitado no existe en la base de datos.")
        st.stop()
        
    booster_asignado = df_info.iloc[0]['booster_nombre']
    user_pass_asignado = df_info.iloc[0]['user_pass']
    
    st.title("Enlace de Cuenta Operativa")
    st.info(f"Asignación confirmada para: **{booster_asignado}**")
    
    st.write("**Credenciales de acceso asignadas:**")
    st.code(user_pass_asignado, language="text")
    
    with st.form("form_booster"):
        st.write("Ingrese el enlace de telemetría del perfil (OP.GG):")
        opgg_input = st.text_input("Enlace de seguimiento:", placeholder="https://www.op.gg/summoners/...")
        submit = st.form_submit_button("Registrar Enlace")
        
        if submit:
            if opgg_input.strip() == "" or not opgg_input.startswith("http"):
                st.error("Validación fallida: El registro debe ser una URL válida (http/https).")
            else:
                conn = get_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE pedidos SET opgg = %s WHERE id = %s", (opgg_input, id_pedido))
                            conn.commit()
                        st.success("Registro completado exitosamente. Puede cerrar esta ventana.")
                    except Exception as e:
                        st.error(f"Excepción en la base de datos: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("Fallo de conexión con el servidor en la nube.")
    
    st.stop()
    
# ==============================================================================
# 3. AUTENTICACIÓN
# ==============================================================================

cookie_manager = stx.CookieManager(key="perez_auth_manager")

cookie_auth = None
try:
    cookie_auth = cookie_manager.get(cookie="perez_login_token")
except:
    pass

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if cookie_auth == "SESION_VALIDA_PEREZBOOST":
    st.session_state.authenticated = True

login_placeholder = st.empty()

if not st.session_state.authenticated:
    with login_placeholder.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.write("")
            st.write("")
            st.subheader("🔐 Acceso PerezBoost")
            with st.form("login_form"):
                password = st.text_input("Credencial de Acceso:", type="password")
                mantener = st.checkbox("No cerrar sesión (30 min)", value=True)
                submit = st.form_submit_button("Ingresar")
                if submit:
                    try:
                        clave_real = st.secrets["ADMIN_PASSWORD"]
                    except:
                        clave_real = os.getenv("ADMIN_PASSWORD")
                    if not clave_real:
                        st.error("⚠️ Error: Configura ADMIN_PASSWORD en secrets.")
                        st.stop()
                    if password == clave_real:
                        st.session_state.authenticated = True
                        if mantener:
                            expira = datetime.now() + timedelta(minutes=30)
                            cookie_manager.set("perez_login_token", "SESION_VALIDA_PEREZBOOST", expires_at=expira)
                        st.success("✅ Acceso Correcto. Redirigiendo...")
                        time.sleep(2)
                        
                        login_placeholder.empty()
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Credencial Incorrecta")
    st.stop()

# ==============================================================================
# 4. FUNCIONES FORMATEADORAS
# ==============================================================================

def clean_num(val):
    if val is None or pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    try: return float(s)
    except: return 0.0

def format_precio(val):
    return f"{float(val):.1f}"

def format_num(val):
    try:
        return f"{int(val)}" if float(val).is_integer() else f"{round(val, 1)}"
    except:
        return str(val)

def format_fecha_latam(fecha_val):
    if pd.isna(fecha_val) or str(fecha_val).strip() == "": return "N/A"
    try: return pd.to_datetime(fecha_val).strftime("%d/%m/%y")
    except: return str(fecha_val)

h_col1, h_col2 = st.columns([8, 1])
with h_col1:
    st.title("🚀 PerezBoost | Monitor")
with h_col2:
    if st.button("Cerrar Sesión", key="btn_logout"):
        st.session_state["logout_solicitado"] = True
        st.session_state.authenticated = False
        try:
            cookie_manager.delete("perez_login_token")
        except:
            pass
        st.toast("👋 Sesión cerrada", icon="🔒")
        time.sleep(0.5)
        st.rerun()

tab_reportes, tab_inventario, tab_ranking, tab_tracking, tab_binance = st.tabs(["📊 REPORTES", "📦 INVENTARIO", "🏆 TOP STAFF", "🔍 TRACKING", "💰 BINANCE"])

# ==============================================================================
# TAB 1: REPORTES
# ==============================================================================

with tab_reportes:
    f1, f2, f3 = st.columns([2, 2, 1])
    meses_nombres = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual_idx = datetime.now().month
    with f1:
        mes_sel = st.selectbox("📅 Mes", meses_nombres, index=mes_actual_idx)
    with f2:
        df_boosters = run_query("SELECT DISTINCT booster_nombre FROM pedidos")
        booster_sel = st.selectbox("👤 Staff", ["Todos"] + sorted(df_boosters['booster_nombre'].dropna().tolist()) if not df_boosters.empty else ["Todos"])
    with f3:
        st.write("")
        if st.button("🔄 Refrescar"):  st.cache_data.clear(), st.rerun()
    query_base = "SELECT * FROM pedidos WHERE estado = 'Terminado'"
    if mes_sel != "Todos":
        n_mes = str(meses_nombres.index(mes_sel)).zfill(2)
        query_base += f" AND CAST(fecha_inicio AS TEXT) LIKE '{datetime.now().year}-{n_mes}%'"
    if booster_sel != "Todos":
        query_base += f" AND booster_nombre = '{booster_sel}'"

    query_base += " ORDER BY fecha_inicio ASC"
    df_rep = run_query(query_base)
    
    if not df_rep.empty:
        t_staff, t_neto, t_bote, t_ventas = 0.0, 0.0, 0.0, 0.0
        conteo = 0
        reporte_data = []
        
        for i, row in enumerate(df_rep.itertuples(), 1):
            conteo += 1
            p_cli = clean_num(row.pago_cliente)
            p_boo = clean_num(row.pago_booster)

            txt_dias = "⚡ <24h"
            try:
                f_ini_str = str(row.fecha_inicio).split(' ')[0] if row.fecha_inicio else ""
                f_fin_str = str(row.fecha_fin_real).split(' ')[0] if row.fecha_fin_real else ""
                
                if f_ini_str and f_fin_str:
                    d_ini = d_fin = None
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                        try:
                            if not d_ini: d_ini = datetime.strptime(f_ini_str, fmt)
                            if not d_fin: d_fin = datetime.strptime(f_fin_str, fmt)
                        except: continue
                    
                    if d_ini and d_fin:
                        diff = (d_fin - d_ini).days
                        if diff > 0:
                            txt_dias = f"{diff} {'día' if diff == 1 else 'días'}"
            except:
                txt_dias = "N/A"

            try: wr = float(row.wr) if row.wr else 0.0
            except: wr = 0.0
            valor_bote = 2.0 if wr >= 60 else 1.0
            mi_neto_real = p_cli - p_boo - valor_bote
            
            t_staff += p_boo
            t_neto += mi_neto_real
            t_bote += valor_bote
            t_ventas += p_cli

            reporte_data.append({
                "#": i, 
                "Inicio": format_fecha_latam(row.fecha_inicio),
                "Entrega": format_fecha_latam(row.fecha_fin_real),
                "Días": txt_dias,
                "Staff": row.booster_nombre,
                "Elo Final": row.elo_final,
                "Pago Staff": f"${p_boo:.2f}",
                "Mi Neto": f"${mi_neto_real:.2f}", 
                "Bote": f"${valor_bote:.2f}", 
                "Total": f"${p_cli:.2f}"
            })

        if mes_sel in ["Todos", "Enero"]: 
            t_neto += 5.0
            t_bote -= 5.0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("📦 Pedidos", f"{conteo}")
        m2.metric("💰 Mi Neto", f"${t_neto:.2f}")
        m3.metric("👤 Pago Staff", f"${t_staff:.2f}")
        m4.metric("🏦 Bote Ranking", f"${t_bote:.2f}")
        m5.metric("📈 Ventas Totales", f"${t_ventas:.2f}")

        gc, tc = st.columns([1, 4])
        with gc:
            fig_pie = go.Figure(data=[go.Pie(labels=['Staff', 'Neto', 'Bote'], 
                                            values=[t_staff, t_neto, t_bote], 
                                            hole=.4,
                                            marker_colors=['#3498db', '#2ecc71', '#f1c40f'])])
            fig_pie.update_layout(template="plotly_dark", height=380, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with tc:
            df_mostrar = pd.DataFrame(reporte_data)
            df_mostrar.set_index("#", inplace=True)
            st.dataframe(df_mostrar, height=380, use_container_width=True)

    st.divider()
    st.subheader("🚨 Auditoría de Anomalías")
    df_audit = run_query("SELECT booster_nombre, user_pass, fecha_limite, wr, estado FROM pedidos WHERE estado NOT IN ('Terminado', 'Cancelado', 'Pagado', 'Abandonado')")
    if not df_audit.empty:
        anomalias = []
        for _, row in df_audit.iterrows():
            wr = clean_num(row['wr'])
            try: 
                fecha_lim_dt = pd.to_datetime(row['fecha_limite']).date()
                hoy_dt = datetime.now().date()
                dias = (fecha_lim_dt - hoy_dt).days
            except: 
                dias = 99
            
            alerta_texto = ""
            status_icono = ""
            
            if wr < 50 and wr > 0: 
                alerta_texto = f"WR Bajo ({format_num(wr)}%)"
                status_icono = "🔴"
            if dias <= 1: 
                alerta_texto = "RETRASO CRÍTICO" if not alerta_texto else f"{alerta_texto} & RETRASO"
                status_icono = "🔴"
            elif dias <= 3 and not status_icono: 
                alerta_texto = "Vence pronto"
                status_icono = "🟡"
                
            if alerta_texto:
                anomalias.append({
                    "Staff": row['booster_nombre'],
                    "User:Pass": row.get('user_pass', 'N/A'),
                    "Fecha Final": format_fecha_latam(row['fecha_limite']),
                    "Estado": row['estado'],
                    "Alerta": alerta_texto,
                    "Status": status_icono
                })
                
        if anomalias: 
            df_anom = pd.DataFrame(anomalias)
            df_anom.set_index("Staff", inplace=True) 
            st.table(df_anom)
        else: st.success("Sin anomalías operativas.")

# ==============================================================================
# TAB 2: INVENTARIO
# ==============================================================================

with tab_inventario:
    st.subheader("📦 Cuentas Disponibles")
    df_inv = run_query("SELECT id, user_pass, elo_tipo, descripcion FROM inventario WHERE descripcion NOT ILIKE '%VENDIDA%' AND descripcion NOT ILIKE '%USADA%' AND descripcion NOT ILIKE '%OCUPADA%'")
    
    if df_inv.empty:
        st.warning("No hay cuentas.")
    else:
        h1, h2, h3 = st.columns([1, 2, 2])
        h1.markdown("<div style='text-align: center;'><b>Rango</b></div>", unsafe_allow_html=True)
        h2.markdown("<div style='text-align: center;'><b>Usuario:Pass (Toca para copiar)</b></div>", unsafe_allow_html=True)
        h3.markdown("<div style='text-align: center;'><b>Nota</b></div>", unsafe_allow_html=True)
        st.divider()

        for _, acc in df_inv.iterrows():
            c1, c2, c3 = st.columns([1, 2, 2])
            
            with c1:
                st.markdown(f"<div style='text-align: center; margin-top: 10px;'>{acc['elo_tipo']}</div>", unsafe_allow_html=True)
            
            with c2:
                _, sub_centro, _ = st.columns([1, 4, 1])
                with sub_centro:
                    st.code(acc['user_pass'], language="text")
                
            with c3:
                st.markdown(f"<div style='text-align: center; margin-top: 10px;'>{acc['descripcion']}</div>", unsafe_allow_html=True)
                
            st.markdown("<hr style='margin:0; border-color:#333'>", unsafe_allow_html=True)

# ==============================================================================
# TAB 3: TOP STAFF
# ==============================================================================

with tab_ranking:
    st.subheader("🏆 Ranking Mensual de Eficiencia")
    
    mes_actual = datetime.now().strftime("%Y-%m")
    df_month = run_query(f"SELECT booster_nombre, wr, fecha_inicio, fecha_fin_real FROM pedidos WHERE estado = 'Terminado' AND CAST(fecha_fin_real AS TEXT) LIKE '{mes_actual}%'")

    if not df_month.empty:
        stats = []
        for staff in df_month['booster_nombre'].unique():
            df_b = df_month[df_month['booster_nombre'] == staff]
            dias_lista = [max((pd.to_datetime(r.fecha_fin_real) - pd.to_datetime(r.fecha_inicio)).days, 1) for r in df_b.itertuples() if r.fecha_fin_real and r.fecha_inicio]
            
            avg_dias = sum(dias_lista) / len(dias_lista) if dias_lista else 0
            avg_wr = df_b['wr'].astype(float).mean()
            stats.append({
                "Staff": staff, 
                "WR": f"{format_num(avg_wr)}%", 
                "Días_Num": avg_dias, 
                "Días": format_num(avg_dias), 
                "Score_Val": avg_wr / (avg_dias if avg_dias > 0 else 1)
            })
        
        df_ranking = pd.DataFrame(stats)
        
        c1, c2 = st.columns(2)
        with c1:
            st.success("⚡ **Más Rápidos**")
            df_rapidos = df_ranking.sort_values(by="Días_Num", ascending=True)[['Staff', 'Días', 'WR']].head(3)
            df_rapidos.set_index("Staff", inplace=True) 
            st.table(df_rapidos)
            
        with c2:
            st.error("🐢 **Más Lentos**")
            df_lentos = df_ranking.sort_values(by="Días_Num", ascending=False)[['Staff', 'Días', 'WR']].head(3)
            df_lentos.set_index("Staff", inplace=True) 
            st.table(df_lentos)
        
        st.divider()
        st.write("📊 **Score de Eficiencia Global**")
        fig_bar = px.bar(df_ranking.sort_values(by="Score_Val", ascending=False), 
                         x='Staff', y='Score_Val', color='Score_Val', 
                         template="plotly_dark", text_auto='.1f', labels={'Score_Val': 'Score'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Sin datos este mes.")
        
# ==============================================================================
# TAB 4: TRACKING (OP.GG y Cuentas Activas)
# ==============================================================================

with tab_tracking:
    c1, c2 = st.columns([8, 1])
    with c1:
        st.subheader("🔍 Tracking Operativo")
    with c2:
        if st.button("🔄 Refrescar", key="btn_refresh_track"): st.cache_data.clear(),st.rerun()
        
    st.info("💡 Monitorea las cuentas activas y edita los enlaces si el staff cometió un error.")
    
    query_activos = "SELECT id, booster_nombre, user_pass, opgg, estado FROM pedidos WHERE estado NOT IN ('Terminado', 'Cancelado', 'Pagado', 'Abandonado') ORDER BY id DESC"
    df_activos = run_query(query_activos)
    
    if df_activos.empty:
        st.success("✅ No hay pedidos activos en este momento.")
    else:
        tracking_data = []
        lista_ids_activos = []
        
        for i, row in enumerate(df_activos.itertuples(), 1):
            link_val = row.opgg if pd.notna(row.opgg) and str(row.opgg).strip() != "" else None
            lista_ids_activos.append(row.id)
            
            tracking_data.append({
                "#": i,
                "Pedido": f"#{row.id}",
                "Staff": row.booster_nombre,
                "Cuenta (User:Pass)": row.user_pass,
                "Link OP.GG": link_val,
                "Estado": row.estado
            })
            
        df_track = pd.DataFrame(tracking_data)
        df_track.set_index("#", inplace=True)

        st.dataframe(
            df_track, 
            use_container_width=True, 
            column_config={
                "Link OP.GG": st.column_config.LinkColumn(
                    "Link OP.GG", 
                    help="Haz clic para abrir el perfil",
                    display_text="🔗 Abrir Perfil"
                )
            }
        )

        st.divider()

        st.subheader("🛠️ Gestión de Enlaces (Corrección de Errores)")
        st.write("Selecciona el pedido para corregir el link. **Para eliminarlo, simplemente deja la caja en blanco y guarda.**")
        
        with st.form("form_editar_opgg"):
            col1, col2 = st.columns([1, 3])
            with col1:
                pedido_sel = st.selectbox("ID del Pedido:", options=lista_ids_activos)
            with col2:
                nuevo_link = st.text_input("Nuevo Link OP.GG:", placeholder="https://...")
            
            submit_edit = st.form_submit_button("Actualizar / Eliminar Enlace")
            
            if submit_edit:
                conn = get_connection()
                if conn:
                    try:
                        link_final = nuevo_link.strip() if nuevo_link.strip() != "" else None
                        
                        with conn.cursor() as cur:
                            cur.execute("UPDATE pedidos SET opgg = %s WHERE id = %s", (link_final, pedido_sel))
                            conn.commit()
                        st.success(f"✅ ¡Operación exitosa en el Pedido #{pedido_sel}! Haz clic en '🔄 Refrescar' arriba para ver los cambios.")
                    except Exception as e:
                        st.error(f"❌ Error al actualizar la base de datos: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Error de conexión a la nube.") 

# ==============================================================================
# VENTANAS EMERGENTES PARA BINANCE
# ==============================================================================

@st.dialog("✏️ Modificar Transacción")
def modal_editar_transaccion(fila):
    id_real = int(fila['id'])
    st.write(f"Modificando el registro")
    
    with st.form("form_modal_edit"):
        e_tipo = st.selectbox("Tipo:", ["RETIRO", "INGRESO"], index=0 if fila['tipo'] == 'RETIRO' else 1)
        e_cat = st.selectbox("Categoría:", ["NETO", "BOTE"], index=0 if fila['categoria'] == 'NETO' else 1)
        e_monto = st.number_input("Monto ($):", min_value=0.01, step=1.00, value=float(fila['monto']), format="%.2f")
        e_desc = st.text_input("Descripción:", value=fila['descripcion'])

        guardar = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
        
        if guardar:
            conn = get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE wallet_perez SET tipo=%s, categoria=%s, monto=%s, descripcion=%s WHERE id=%s", 
                                    (e_tipo, e_cat, e_monto, e_desc, id_real))
                        conn.commit()
                    st.success("✅ Actualizado correctamente.")
                    time.sleep(1); st.cache_data.clear(),st.rerun()
                except Exception as e: st.error(f"Error: {e}")
                finally: conn.close()

@st.dialog("⚠️ Confirmar Eliminación")
def modal_eliminar_transaccion(id_real, detalle):
    st.error("¿Estás seguro de eliminar este movimiento?")
    st.write(f"**{detalle}**")
    st.write("Esta acción recalculará tu Binance y no se puede deshacer.")
    
    if st.button("🗑️ Sí, Eliminar Definitivamente", type="primary", use_container_width=True):
        conn = get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM wallet_perez WHERE id=%s", (id_real,))
                    conn.commit()
                st.success("🗑️ Registro eliminado.")
                time.sleep(1); st.cache_data.clear(), st.rerun()
            except Exception as e: st.error(f"Error: {e}")
            finally: conn.close()

# ==============================================================================
# TAB 5: BINANCE
# ==============================================================================

with tab_binance:
    st.subheader("🏦 Binance Wallet")

    df_pedidos_all = run_query("SELECT pago_cliente, pago_booster, wr FROM pedidos WHERE estado = 'Terminado'")
    neto_historico = 0.0
    bote_historico = 0.0
    
    if not df_pedidos_all.empty:
        for _, row in df_pedidos_all.iterrows():
            p_cli = clean_num(row['pago_cliente'])
            p_boo = clean_num(row['pago_booster'])
            wr = clean_num(row['wr'])
            valor_bote = 2.0 if wr >= 60 else 1.0
            
            neto_historico += (p_cli - p_boo - valor_bote)
            bote_historico += valor_bote

        neto_historico += 5.0
        bote_historico -= 5.0

    df_wallet = run_query("SELECT id, fecha, tipo, categoria, monto, descripcion FROM wallet_perez ORDER BY id DESC")
    
    neto_movimientos = 0.0
    bote_movimientos = 0.0
    
    if not df_wallet.empty:
        for _, row in df_wallet.iterrows():
            monto = float(row['monto'])
            if row['tipo'] == 'RETIRO':
                if row['categoria'] == 'NETO': neto_movimientos -= monto
                elif row['categoria'] == 'BOTE': bote_movimientos -= monto
            elif row['tipo'] == 'INGRESO':
                if row['categoria'] == 'NETO': neto_movimientos += monto
                elif row['categoria'] == 'BOTE': bote_movimientos += monto

    saldo_neto_actual = neto_historico + neto_movimientos
    saldo_bote_actual = bote_historico + bote_movimientos
    total_binance = saldo_neto_actual + saldo_bote_actual

    st.markdown("""
        <style>
        .metric-box {
            background-color: #1a1e23; border: 1px solid #333; border-radius: 8px;
            padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .metric-title { color: #8892b0; font-size: 16px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
        .metric-value-neto { color: #2ecc71; font-size: 32px; font-weight: bold; }
        .metric-value-bote { color: #f1c40f; font-size: 32px; font-weight: bold; }
        .metric-value-total { color: #ffffff; font-size: 36px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-box"><div class="metric-title">Mi Neto Disponible</div><div class="metric-value-neto">${saldo_neto_actual:.2f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-box"><div class="metric-title">Bote Ranking (Staff)</div><div class="metric-value-bote">${saldo_bote_actual:.2f}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-box"><div class="metric-title">Total en Binance</div><div class="metric-value-total">${total_binance:.2f}</div></div>', unsafe_allow_html=True)

    st.write("")
    st.divider()

    col_form, col_hist = st.columns([1, 2])
    
    with col_form:
        st.subheader("💸 Nueva Transacción")
        with st.form("form_wallet"):
            tipo_tx = st.selectbox("Tipo de Movimiento:", ["RETIRO", "INGRESO"])
            cat_tx = st.selectbox("Categoría afectada:", ["NETO", "BOTE"])
            monto_tx = st.number_input("Monto ($):", min_value=0.01, step=1.00, format="%.2f")
            desc_tx = st.text_input("Descripción (Ej: Retiro a Nequi):")
            
            if st.form_submit_button("Registrar Movimiento"):
                if not desc_tx:
                    st.error("Por favor agrega una descripción.")
                else:
                    conn = get_connection()
                    if conn:
                        try:
                            with conn.cursor() as cur:
                                cur.execute("INSERT INTO wallet_perez (tipo, categoria, monto, descripcion) VALUES (%s, %s, %s, %s)", (tipo_tx, cat_tx, monto_tx, desc_tx))
                                conn.commit()
                            st.success("✅ Registrado con éxito.")
                            time.sleep(1); st.cache_data.clear(),st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                        finally: conn.close()

    with col_hist:
        st.subheader("📜 Historial de Movimientos")
        if df_wallet.empty:
            st.info("No hay movimientos registrados aún.")
        else:
            df_mostrar = df_wallet.copy()
            df_mostrar['fecha_dt'] = pd.to_datetime(df_mostrar['fecha'])
            
            meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
            df_mostrar['mes_str'] = df_mostrar['fecha_dt'].dt.month.map(meses_es) + " " + df_mostrar['fecha_dt'].dt.year.astype(str)
            
            opciones_filtro = ["Todos"] + df_mostrar['mes_str'].unique().tolist()
            mes_actual_str = meses_es[datetime.now().month] + " " + str(datetime.now().year)
            idx_defecto = opciones_filtro.index(mes_actual_str) if mes_actual_str in opciones_filtro else 0
            
            c_filtro, c_vacio = st.columns([1, 1])
            with c_filtro:
                mes_seleccionado = st.selectbox("📅 Filtrar por mes:", opciones_filtro, index=idx_defecto)
                
            if mes_seleccionado != "Todos":
                df_filtrado = df_mostrar[df_mostrar['mes_str'] == mes_seleccionado].copy()
            else:
                df_filtrado = df_mostrar.copy()
                
            total_retirado = df_filtrado[df_filtrado['tipo'] == 'RETIRO']['monto'].astype(float).sum()
            st.markdown(f"**Total Retirado ({mes_seleccionado}):** <span style='color:#2ecc71; font-size:20px;'>**${total_retirado:.2f}**</span>", unsafe_allow_html=True)
            st.write("")
            
            if df_filtrado.empty:
                st.warning(f"No hay movimientos para {mes_seleccionado}.")
            else:
                df_filtrado['fecha_str'] = df_filtrado['fecha_dt'].dt.strftime('%d/%m/%y %H:%M')
                df_filtrado['monto_str'] = df_filtrado.apply(lambda r: f"-${float(r['monto']):.2f}" if r['tipo'] == 'RETIRO' else f"+${float(r['monto']):.2f}", axis=1)
                df_filtrado['id_visual'] = range(1, len(df_filtrado) + 1)
                df_final = df_filtrado[['id_visual', 'fecha_str', 'tipo', 'categoria', 'monto_str', 'descripcion']]
                df_final.columns = ["Nº", "Fecha", "Tipo", "Caja", "Monto", "Detalle"]

                st.dataframe(df_final, use_container_width=True, hide_index=True)
                st.divider()
                st.markdown("### ⚙️ Gestionar Registro")
                opciones_crud = df_filtrado.apply(lambda r: f"Nº {r['id_visual']} | {r['tipo']} | {r['monto_str']} | {r['descripcion']} (ID:{r['id']})", axis=1).tolist()
                seleccion = st.selectbox("Selecciona un movimiento de la tabla:", opciones_crud, label_visibility="collapsed")
                c_btn1, c_btn2, c_btn3 = st.columns(3)
                
                with c_btn1:
                    if st.button("✏️ Editar", use_container_width=True):
                        id_real = int(seleccion.split("(ID:")[1].replace(")", "").strip())
                        fila_sel = df_wallet[df_wallet['id'] == id_real].iloc[0]
                        modal_editar_transaccion(fila_sel)
                        
                with c_btn2:
                    if st.button("🗑️ Eliminar", use_container_width=True):
                        id_real = int(seleccion.split("(ID:")[1].replace(")", "").strip())
                        detalle_mostrar = seleccion.split("(ID:")[0].strip()
                        modal_eliminar_transaccion(id_real, detalle_mostrar)
                        
                with c_btn3:
                    if st.button("🔄 Refresh", use_container_width=True):
                        st.cache_data.clear(), st.rerun()