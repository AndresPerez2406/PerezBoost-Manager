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
APP_VERSION = os.getenv("APP_VERSION", "V.Unknown")
MODO_DESARROLLO = os.getenv("MODO_DESARROLLO") == "True"

st.set_page_config(
    page_title=f"PerezBoost {APP_VERSION} | Portal Operativo",
    page_icon="🎮",
    layout="wide"
)

if MODO_DESARROLLO:
    load_dotenv(".env.dev", override=True)
    print("🛠️ MODO DEV: Conectado a la base de datos de PRUEBAS")
else:
    print("🚀 MODO PROD: Conectado a la base de datos REAL")

def get_connection():
    url = os.getenv("DATABASE_URL")
    try: return psycopg2.connect(url, connect_timeout=10)
    except: return None

@st.cache_data(ttl=60, show_spinner=False)
def run_query(query):
    conn = get_connection()
    if conn:
        try:
            with conn: return pd.read_sql(query, conn)
        except: return pd.DataFrame()
        finally: conn.close()
    return pd.DataFrame()

# ==============================================================================
# 🎮 MODO QUIOSCO (PUBLIC-FACING LEADERBOARD - METALLIC DARK EDITION)
# ==============================================================================

def render_public_ranking():

    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: none !important;}
            [data-testid="stSidebar"] {display: none !important;}
            .stApp { background-color: #0a0a0a; }
            .prize-banner {
                background: linear-gradient(135deg, #111111, #1a251f, #1a4a2e);
                color: white; text-align: center; padding: 50px 20px;
                border-radius: 15px; margin: 10px 0 40px 0;
                box-shadow: 0 10px 50px rgba(46, 204, 113, 0.4); border: 2px solid #2ecc71;
            }
            .prize-title { margin: 0 !important; font-size: 55px !important; color: #ffffff !important; font-weight: 900 !important; letter-spacing: 5px !important; text-transform: uppercase !important; text-shadow: 0 4px 10px rgba(0,0,0,0.9) !important; line-height: 1.1 !important; }
            .prize-amount { font-size: 115px !important; font-weight: 900 !important; color: #2ecc71 !important; text-shadow: 0 0 35px rgba(46, 204, 113, 0.6) !important; margin: 10px 0 25px 0 !important; line-height: 1 !important; }
            .prize-breakdown { font-size: 22px !important; color: #ffffff !important; font-weight: 800 !important; text-shadow: 0 2px 4px rgba(0,0,0,0.8) !important; }
            .prize-breakdown span { color: #888888; font-weight: bold; }
            .global-stats-panel { display: flex; background: linear-gradient(145deg, #151515, #2d2d2d, #1a1a1a); border: 2px solid #444; border-top: 2px solid #777; border-radius: 15px; box-shadow: 0 12px 25px rgba(0,0,0,0.8); margin-bottom: 45px; }
            .stat-segment { flex: 1; padding: 30px 10px; text-align: center; }
            .stat-segment:not(:last-child) { border-right: 2px solid #333; }
            .stat-title { color: #c4c4c4; margin: 0; font-size: 18px; text-transform: uppercase; font-weight: 900; letter-spacing: 3px;}
            .stat-value { font-size: 50px; font-weight: 900; margin: 15px 0 0 0; text-shadow: 0 5px 15px rgba(0,0,0,0.8); line-height: 1; }
            .rank-card { background: linear-gradient(145deg, #141414, #252525); padding: 25px 20px; border-radius: 12px; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.8); border: 1px solid #333; border-top: 1px solid #555; transition: transform 0.3s, border-color 0.3s; }
            .rank-card:hover { transform: translateY(-5px); border-color: #777; }
            .rank-1 { border-top: 6px solid #f1c40f; box-shadow: 0 0 30px rgba(241, 196, 15, 0.2); margin-top: 0px; }
            .rank-2 { border-top: 6px solid #bdc3c7; margin-top: 30px; }
            .rank-3 { border-top: 6px solid #cd7f32; margin-top: 30px; }
            .rank-icon { font-size: 55px; margin-bottom: 15px; filter: drop-shadow(0px 4px 5px rgba(0,0,0,0.5));}
            .rank-name { font-size: 24px; font-weight: 900; color: #ffffff; margin: 0; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 2px 4px rgba(0,0,0,0.8);}
            .rank-pts { font-size: 28px; color: #2ecc71; font-weight: 900; margin: 12px 0 0 0; }
            .rank-label { color: #888; font-size: 15px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;}
            .esports-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 17px; background: #121212; border-radius: 12px; overflow: hidden; border: 1px solid #333; }
            .esports-table thead tr { background: #1a1a1a; color: #e0e0e0; text-transform: uppercase; font-weight: 900; border-bottom: 2px solid #444; }
            .esports-table th, .esports-table td { padding: 18px 15px; border-bottom: 1px solid #252525; text-align: center; }
            .col-staff { font-weight: 900; color: #ffffff; text-align: left !important; padding-left: 20px !important; }
            .dev-footer { text-align: center; color: #444; font-size: 13px; margin-top: 70px; font-family: monospace; letter-spacing: 3px; }
        </style>
    """, unsafe_allow_html=True)

    mes_actual = datetime.now().strftime("%Y-%m")
    nombre_mes = datetime.now().strftime("%B").upper()

    st.markdown(f"""
        <div style='text-align: center; margin-top: 20px; margin-bottom: 10px;'>
            <h1 style='color: white; font-size: 100px !important; font-weight: 950; text-transform: uppercase; letter-spacing: 15px; text-shadow: 0 0 30px rgba(255,255,255,0.2); line-height: 0.9; margin: 0;'>
                🏆 HALL OF FAME 🏆
            </h1>
            <p style='color: #a0a0a0; font-size: 28px; font-weight: 900; text-transform: uppercase; letter-spacing: 5px; margin-top: 20px;'>
                Temporada de {nombre_mes} <span style='color: #ff0000; text-shadow: 0 0 10px #ff0000;'>🔴</span>
            </p>
        </div>
    """, unsafe_allow_html=True)

    query_publica = f"""
        SELECT p.*,
        (SELECT puntos FROM config_precios WHERE UPPER(TRIM(division)) = UPPER(TRIM(p.elo_final)) LIMIT 1) as puntos_tarifa
        FROM pedidos p
        WHERE p.fecha_fin_real LIKE '{mes_actual}%'
    """
    df_raw = run_query(query_publica)

    if df_raw.empty:
        query_backup = "SELECT p.*, (SELECT puntos FROM config_precios WHERE UPPER(TRIM(division)) = UPPER(TRIM(p.elo_final)) LIMIT 1) as puntos_tarifa FROM pedidos p"
        df_all = run_query(query_backup)
        if not df_all.empty:
            df_raw = df_all[df_all['fecha_fin_real'].astype(str).str.contains(mes_actual)]

    if not df_raw.empty:
        df_term = df_raw[df_raw['estado'] == 'Terminado'].copy()
        total_pedidos = len(df_term)

        df_term['wr'] = pd.to_numeric(df_term['wr'], errors='coerce').fillna(0)
        wr_global = df_term['wr'].mean() if not df_term.empty else 0.0
        
        df_term = df_raw[df_raw['estado'] == 'Terminado'].copy()
        df_term['f_ini'] = pd.to_datetime(df_term['fecha_inicio'], errors='coerce')
        df_term['f_fin'] = pd.to_datetime(df_term['fecha_fin_real'], errors='coerce')

        df_term = df_term.dropna(subset=['f_ini', 'f_fin'])

        dias_totales = (df_term['f_fin'] - df_term['f_ini']).dt.total_seconds() / 86400
        dias_limpios = dias_totales.apply(lambda x: max(x, 0.1))
        eficiencia = dias_limpios.mean() if not dias_limpios.empty else 0
        if 0 < eficiencia < 1:
            texto_efi = "⚡ < 1 Día"
        else:
            texto_efi = f"{eficiencia:.1f} Días"

        total_high = len(df_term[df_term['wr'] >= 60])
        bote_pedidos = total_pedidos * 1.0
        bote_wr = total_high * 1.0
        bote_acum_ant = 11.0
        bote_total = bote_pedidos + bote_wr + bote_acum_ant

        st.markdown(f"""
            <div class="prize-banner">
                <div class="prize-title">💰 GRAN PREMIO {nombre_mes} 💰</div>
                <div class="prize-amount">${bote_total:.2f} USD</div>
                <div class="prize-breakdown">
                    <span>📈 Enero:</span> +${bote_acum_ant:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <span>📦 Pedidos:</span> +${bote_pedidos:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <span>🔥 Calidad WR:</span> +${bote_wr:.2f}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="global-stats-panel">
                <div class="stat-segment"><p class="stat-title">📦 Pedidos Totales</p><p class="stat-value">{total_pedidos}</p></div>
                <div class="stat-segment"><p class="stat-title">⚡ Eficiencia</p><p class="stat-value" style="color: #2ecc71;">{texto_efi}</p></div>
                <div class="stat-segment"><p class="stat-title">📊 WR Global</p><p class="stat-value" style="color: #f1c40f;">{wr_global:.1f}%</p></div>
            </div>
        """, unsafe_allow_html=True)

        rank_data = []
        for booster, df_b in df_raw.groupby('booster_nombre'):
            df_b_term = df_b[df_b['estado'] == 'Terminado'].copy()
            abandonos = len(df_b[df_b['estado'] == 'Abandonado'])
            puntos_tarifas = df_b_term['puntos_tarifa'].fillna(2).sum()
            puntaje = puntos_tarifas - (abandonos * 10)
            
            terminados = len(df_b_term)
            df_b_term['wr'] = pd.to_numeric(df_b_term['wr'], errors='coerce').fillna(0)
            high_wr = len(df_b_term[df_b_term['wr'] >= 60])
            
            if terminados > 0 or abandonos > 0:
                rank_data.append([booster, terminados, high_wr, abandonos, puntaje])

        df_rank = pd.DataFrame(rank_data, columns=['booster_nombre', 'terminados', 'high_wr', 'abandonos', 'puntaje'])
        df_rank = df_rank.sort_values(by="puntaje", ascending=False).reset_index(drop=True)

        c1, c2, c3 = st.columns([1, 1.2, 1])
        if not df_rank.empty:
            with c2: st.markdown(f'<div class="rank-card rank-1"><div class="rank-icon">🥇</div><p class="rank-label">MVP ACTUAL</p><p class="rank-name">{df_rank.iloc[0]["booster_nombre"]}</p><p class="rank-pts">{df_rank.iloc[0]["puntaje"]} PTS</p></div>', unsafe_allow_html=True)
            if len(df_rank) > 1:
                with c1: st.markdown(f'<div class="rank-card rank-2"><div class="rank-icon">🥈</div><p class="rank-label">RANGO 2</p><p class="rank-name">{df_rank.iloc[1]["booster_nombre"]}</p><p class="rank-pts">{df_rank.iloc[1]["puntaje"]} PTS</p></div>', unsafe_allow_html=True)
            if len(df_rank) > 2:
                with c3: st.markdown(f'<div class="rank-card rank-3"><div class="rank-icon">🥉</div><p class="rank-label">RANGO 3</p><p class="rank-name">{df_rank.iloc[2]["booster_nombre"]}</p><p class="rank-pts">{df_rank.iloc[2]["puntaje"]} PTS</p></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tabla_html = "<table class='esports-table'><thead><tr><th>N°</th><th style='text-align:left'>Staff</th><th>✅ Term.</th><th>🔥 WR 60%</th><th>❌ Aban.</th><th>⭐ Pts</th></tr></thead><tbody>"
        for index, row in df_rank.iterrows():
            tabla_html += f"<tr><td>{index+1}°</td><td class='col-staff'>{row['booster_nombre']}</td><td>{row['terminados']}</td><td>{row['high_wr']}</td><td style='color:#e74c3c'>{row['abandonos']}</td><td style='color:#2ecc71; font-weight:bold;'>{row['puntaje']} pts</td></tr>"
        tabla_html += "</tbody></table>"
        st.markdown(tabla_html, unsafe_allow_html=True)

    else:
        st.info(f"No hay pedidos terminados registrados para {nombre_mes} todavía.")

    st.markdown('<div class="dev-footer">⚡ DEVELOPED BY ANDRES PEREZ | © 2026 PEREZBOOST</div>', unsafe_allow_html=True)

# ==============================================================================
# 🚦 EL ENRUTADOR (INTERCEPTOR DE URL A PRUEBA DE BALAS)
# ==============================================================================
try:
    if hasattr(st, "query_params"):
        view_mode = st.query_params.get("view", "")
    else:
        params = st.experimental_get_query_params()
        view_mode = params.get("view", [""])[0]
    if view_mode == "ranking":
        render_public_ranking()
        st.stop()
except Exception as e:
    st.error(f"🚨 Error crítico en el Modo Ranking: {e}")
    st.stop()

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
                mantener = st.checkbox("No cerrar sesión.", value=True)
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
                            expira = datetime.now() + timedelta(minutes=300)
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
    st.title(f"🚀 PerezBoost {APP_VERSION} | Monitor")
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

tab_reportes, tab_analytics, tab_inventario, tab_ranking, tab_tracking, tab_gestion, tab_binance = st.tabs(["📊 Reportes", "📈 Analytics", "📦 INVENTARIO", "🏆 TOP STAFF", "🔍 TRACKING", "🛠️ GESTIÓN", "💰 BINANCE"])

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
        if st.button("🔄 Refrescar"):  st.cache_data.clear(); st.rerun()

    query_base = "SELECT * FROM pedidos WHERE estado = 'Terminado' AND pago_realizado = 1"
    if mes_sel != "Todos":
        n_mes = str(meses_nombres.index(mes_sel)).zfill(2)
        query_base += f" AND CAST(fecha_fin_real AS TEXT) LIKE '{datetime.now().year}-{n_mes}%'"
    if booster_sel != "Todos":
        query_base += f" AND booster_nombre = '{booster_sel}'"

    query_base += " ORDER BY fecha_fin_real DESC"
    
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
            st.plotly_chart(fig_pie, width='stretch')
            
        with tc:
            df_mostrar = pd.DataFrame(reporte_data)
            df_mostrar.set_index("#", inplace=True)
            st.dataframe(df_mostrar, height=380, width='stretch')
    else:
        st.info(f"No hay pedidos terminados para el mes de {mes_sel}.")

# ==============================================================================
# TAB 2: GITANALYTICS
# ==============================================================================

with tab_analytics:
    st.subheader("🧠 GitAnalytics: Inteligencia de Negocio y Eficiencia")

    f1, f2 = st.columns([2, 8])
    meses_nombres = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual_idx = datetime.now().month
    with f1:
        mes_sel_ana = st.selectbox("📅 Analizar Mes", meses_nombres, index=mes_actual_idx, key="mes_ana")
    with f2:
        st.write("")
        if st.button("🔄 Refrescar Gráficas", key="btn_ref_ana"):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    query_bi = """
        SELECT booster_nombre, wr, pago_cliente, pago_booster, fecha_inicio, fecha_fin_real 
        FROM pedidos 
        WHERE estado = 'Terminado' 
        AND pago_realizado = 1 
        AND fecha_fin_real IS NOT NULL
    """

    if mes_sel_ana != "Todos":
        n_mes = str(meses_nombres.index(mes_sel_ana)).zfill(2)
        query_bi += f" AND CAST(fecha_fin_real AS TEXT) LIKE '{datetime.now().year}-{n_mes}%'"

    df_bi = run_query(query_bi)

    if not df_bi.empty:

        df_bi['wr'] = pd.to_numeric(df_bi['wr'], errors='coerce').fillna(0)
        df_bi['pago_cliente'] = pd.to_numeric(df_bi['pago_cliente'], errors='coerce').fillna(0)
        df_bi['pago_booster'] = pd.to_numeric(df_bi['pago_booster'], errors='coerce').fillna(0)
        df_bi['valor_bote'] = df_bi['wr'].apply(lambda x: 2.0 if x >= 60 else 1.0)
        df_bi['ganancia_empresa'] = df_bi['pago_cliente'] - df_bi['pago_booster'] - df_bi['valor_bote']
        df_bi['fecha_inicio_dt'] = pd.to_datetime(df_bi['fecha_inicio'], format='mixed', dayfirst=False, errors='coerce')
        df_bi['fecha_fin_dt'] = pd.to_datetime(df_bi['fecha_fin_real'], format='mixed', dayfirst=False, errors='coerce')
        df_bi['dias_entrega'] = (df_bi['fecha_fin_dt'] - df_bi['fecha_inicio_dt']).dt.total_seconds() / (24 * 3600)
        df_bi['dias_entrega'] = df_bi['dias_entrega'].apply(lambda x: max(x, 0.5) if pd.notnull(x) else 1.0)

        df_staff = df_bi.groupby('booster_nombre').agg(
            Total_Ganancia=('ganancia_empresa', 'sum'),
            WR_Promedio=('wr', 'mean'),
            Pedidos_Completados=('booster_nombre', 'count'),
            Tiempo_Promedio=('dias_entrega', 'mean') 
        ).reset_index()

        df_staff['WR_Promedio'] = df_staff['WR_Promedio'].round(1)
        df_staff['Tiempo_Promedio'] = df_staff['Tiempo_Promedio'].round(1)
        df_grafica = df_bi.dropna(subset=['fecha_fin_dt']).copy()
        df_grafica['fecha_corta'] = df_grafica['fecha_fin_dt'].dt.strftime('%Y-%m-%d')
        df_tendencia = df_grafica.groupby('fecha_corta')['ganancia_empresa'].sum().reset_index()
        df_tendencia = df_tendencia.sort_values('fecha_corta')
        df_tendencia['Ganancia_Acumulada'] = df_tendencia['ganancia_empresa'].cumsum()

        if mes_sel_ana in ["Todos", "Enero"]:
            df_tendencia['Ganancia_Acumulada'] = df_tendencia['Ganancia_Acumulada'] + 5.0

        # =======================================================
        # 🏆 KPI GLOBALS
        # =======================================================
        
        global_ganancia = df_bi['ganancia_empresa'].sum()

        if mes_sel_ana in ["Todos", "Enero"]:
            global_ganancia += 5.0
        global_wr = df_bi['wr'].mean()
        total_pedidos = len(df_bi)
        global_tiempo = df_bi['dias_entrega'].mean()
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        kpi1.metric("💰 Ganancia Neta Real", f"${global_ganancia:,.2f} USD")
        kpi2.metric("🎯 Win Rate Global", f"{global_wr:.1f}%")
        kpi3.metric("📦 Pedidos Liquidados", f"{total_pedidos}")
        kpi4.metric("⚡ Velocidad Media", f"{global_tiempo:.1f} Días")
        
        st.write("")

        # =======================================================
        # 📊 DIBUJANDO LAS GRÁFICAS OP
        # =======================================================
        
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown(f"**🎯 Matriz de Calidad y Valor ({mes_sel_ana})**")
            st.caption("Solo se muestran pedidos pagados.")
            
            fig_scatter = px.scatter(
                df_staff, 
                x="WR_Promedio", 
                y="Total_Ganancia", 
                size="Pedidos_Completados", 
                color="booster_nombre",
                hover_name="booster_nombre",
                hover_data={"Tiempo_Promedio": True},
                labels={
                    "WR_Promedio": "Win Rate Promedio (%)", 
                    "Total_Ganancia": "Ganancia Neta ($)",
                    "Pedidos_Completados": "Pedidos",
                    "Tiempo_Promedio": "Días Promedio"
                },
                size_max=45,
                template="plotly_dark"
            )
            fig_scatter.add_vline(x=60, line_dash="dash", line_color="#e74c3c", annotation_text="Meta WR")
            fig_scatter.update_layout(showlegend=False, margin=dict(l=0, r=20, t=30, b=0), height=380)
            st.plotly_chart(fig_scatter, width='stretch')

        with col_chart2:
            st.markdown(f"**📈 Run-Rate: Flujo de Caja Real ({mes_sel_ana})**")
            st.caption("Curva de dinero líquido acumulado.")
            
            fig_area = px.area(
                df_tendencia, 
                x="fecha_corta", 
                y="Ganancia_Acumulada",
                markers=True,
                labels={
                    "fecha_corta": "Fecha", 
                    "Ganancia_Acumulada": "Acumulado ($)"
                },
                template="plotly_dark",
                color_discrete_sequence=['#2ecc71'] 
            )
            fig_area.update_layout(margin=dict(l=0, r=20, t=30, b=0), height=380)
            st.plotly_chart(fig_area, width='stretch')

        st.divider()
        st.markdown(f"**🏎️ Ranking de Velocidad Operativa ({mes_sel_ana})**")
        st.caption("Días promedio por entrega (Solo pedidos pagados).")

        df_staff_sorted = df_staff.sort_values('Tiempo_Promedio', ascending=False)
        
        fig_bar = px.bar(
            df_staff_sorted, 
            x='Tiempo_Promedio', 
            y='booster_nombre', 
            orientation='h',
            text='Tiempo_Promedio',
            color='Tiempo_Promedio',
            color_continuous_scale="RdYlGn_r",
            labels={
                "Tiempo_Promedio": "Días Promedio por Entrega",
                "booster_nombre": "Staff"
            },
            template="plotly_dark"
        )
        fig_bar.update_traces(texttemplate='%{text} Días', textposition='outside')
        fig_bar.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=40, t=10, b=0), height=150 + (len(df_staff) * 30))
        st.plotly_chart(fig_bar, width='stretch')

    else:
        st.info(f"Aún no hay pedidos **PAGADOS** registrados en {mes_sel_ana} para generar métricas financieras.")
        
# ==============================================================================
# TAB 3: INVENTARIO
# ==============================================================================

with tab_inventario:
    c1, c2 = st.columns([8, 1])
    with c1:
        st.subheader("📦 Inventario de Cuentas")
    with c2:
        if st.button("🔄 Refrescar", key="btn_refresh_inv"): 
            st.cache_data.clear()
            st.rerun()
    df_inv = run_query("SELECT id, user_pass, elo_tipo, descripcion FROM inventario ORDER BY elo_tipo")
    if not df_inv.empty:
        elos_disponibles = sorted(df_inv['elo_tipo'].dropna().unique().tolist())
        opciones_filtro = ["Todos"] + elos_disponibles
        col_filtro, col_vacia = st.columns([1, 2])
        with col_filtro:
            filtro_elo = st.selectbox("🎯 Filtrar por Rango/ELO:", opciones_filtro)
        if filtro_elo != "Todos":
            df_mostrar = df_inv[df_inv['elo_tipo'] == filtro_elo].copy()
        else:
            df_mostrar = df_inv.copy()
        if not df_mostrar.empty:
            df_mostrar['id_visual'] = range(1, len(df_mostrar) + 1)
            df_tabla = df_mostrar[['id_visual', 'elo_tipo', 'user_pass', 'descripcion']]
            df_tabla.columns = ["Nº", "Rango", "Cuenta (User:Pass)", "Detalle"]
            st.dataframe(df_tabla, width='stretch', hide_index=True)
            st.caption(f"Mostrando {len(df_tabla)} cuentas de {filtro_elo}")
        else:
            st.warning(f"No se encontraron cuentas para el rango {filtro_elo}.")
    else:
        st.success("✅ El inventario está vacío. No hay cuentas pendientes.")

# ==============================================================================
# TAB 4: TOP STAFF
# ==============================================================================

with tab_ranking:
    st.subheader("🏆 Hall of Fame: Valor y Eficiencia")
    
    mes_actual = datetime.now().strftime("%Y-%m")

    query_rank = f"""
        SELECT booster_nombre, wr, fecha_inicio, fecha_fin_real, pago_cliente, pago_booster 
        FROM pedidos 
        WHERE estado = 'Terminado' AND pago_realizado = 1 
        AND CAST(fecha_fin_real AS TEXT) LIKE '{mes_actual}%'
    """
    df_month = run_query(query_rank)

    if not df_month.empty:
        df_month['wr'] = pd.to_numeric(df_month['wr'], errors='coerce').fillna(0)
        df_month['pago_cliente'] = pd.to_numeric(df_month['pago_cliente'], errors='coerce').fillna(0)
        df_month['pago_booster'] = pd.to_numeric(df_month['pago_booster'], errors='coerce').fillna(0)
        df_month['bote'] = df_month['wr'].apply(lambda x: 2.0 if x >= 60 else 1.0)
        df_month['neto'] = df_month['pago_cliente'] - df_month['pago_booster'] - df_month['bote']
        df_month['f_ini'] = pd.to_datetime(df_month['fecha_inicio'], format='mixed', dayfirst=False, errors='coerce')
        df_month['f_fin'] = pd.to_datetime(df_month['fecha_fin_real'], format='mixed', dayfirst=False, errors='coerce')
        df_month['dias'] = (df_month['f_fin'] - df_month['f_ini']).dt.days.apply(lambda x: max(x, 1) if pd.notnull(x) else 1)
        df_grouped = df_month.groupby('booster_nombre').agg(
            Pedidos=('booster_nombre', 'count'),
            Total_Neto=('neto', 'sum'),
            Total_Dias=('dias', 'sum'),
            Promedio_Dias=('dias', 'mean'),
            WR_Promedio=('wr', 'mean')
        ).reset_index()

        df_grouped['USD_por_Dia'] = df_grouped['Total_Neto'] / df_grouped['Total_Dias']
        df_grouped['WR_Promedio'] = df_grouped['WR_Promedio'].round(1)
        df_grouped['Promedio_Dias'] = df_grouped['Promedio_Dias'].round(1)
        df_grouped['USD_por_Dia'] = df_grouped['USD_por_Dia'].round(2)
        df_grouped['Total_Neto'] = df_grouped['Total_Neto'].round(2)

        c1, c2 = st.columns(2)
        
        with c1:
            st.success("💎 **Most Valuable Players (Más Ganancia Total)**")
            st.caption("Quienes más dinero han traído a la caja este mes.")

            df_mvp = df_grouped.sort_values(by="Total_Neto", ascending=False)[['booster_nombre', 'Total_Neto', 'Pedidos']].head(3).copy()
            df_mvp['Total_Neto'] = df_mvp['Total_Neto'].apply(lambda x: f"${x:.1f}")
            df_mvp.columns = ["Staff", "Mi Neto", "Pedidos"]
            df_mvp.set_index("Staff", inplace=True) 
            st.table(df_mvp)
            
        with c2:
            st.info("⚡ **Top Eficiencia Pura (Mayor $/Día)**")
            st.caption("Ganan más dinero en menos tiempo (Alta rentabilidad).")

            df_efi = df_grouped.sort_values(by="USD_por_Dia", ascending=False)[['booster_nombre', 'USD_por_Dia', 'WR_Promedio']].head(3).copy()
            df_efi['USD_por_Dia'] = df_efi['USD_por_Dia'].apply(lambda x: f"${x:.1f}/Día")
            df_efi['WR_Promedio'] = df_efi['WR_Promedio'].apply(lambda x: f"{x:.1f}%")
            df_efi.columns = ["Staff", "Genera", "WR"]
            df_efi.set_index("Staff", inplace=True) 
            st.table(df_efi)
        
        st.divider()
        
        st.write("📊 **Matriz de Rendimiento: Valor vs Tiempo**")
        fig_scatter = px.scatter(
            df_grouped, 
            x='Promedio_Dias', 
            y='Total_Neto', 
            size='USD_por_Dia', 
            color='booster_nombre',
            hover_name='booster_nombre',
            hover_data={'Pedidos': True, 'WR_Promedio': True},
            labels={
                "Promedio_Dias": "Tiempo Promedio por Pedido (Días)", 
                "Total_Neto": "Ganancia Neta Generada ($)",
                "USD_por_Dia": "Eficiencia ($/Día)",
                "booster_nombre": "Staff"
            },
            template="plotly_dark",
            size_max=40
        )

        fig_scatter.update_xaxes(autorange="reversed")
        st.plotly_chart(fig_scatter, width='stretch')
        
        st.write("📋 **Desglose Completo de Staff**")
        df_mostrar = df_grouped[["booster_nombre", "Total_Neto", "USD_por_Dia", "Pedidos", "Promedio_Dias", "WR_Promedio"]].sort_values(by="USD_por_Dia", ascending=False)
        st.dataframe(
            df_mostrar, 
            width='stretch', 
            hide_index=True,
            column_config={
                "booster_nombre": "Staff",
                "Total_Neto": st.column_config.NumberColumn("Ganancia Total", format="$%.2f"),
                "USD_por_Dia": st.column_config.NumberColumn("Eficiencia ($/Día)", format="$%.2f"),
                "Pedidos": "Nº Pedidos",
                "Promedio_Dias": "Días/Pedido",
                "WR_Promedio": st.column_config.NumberColumn("WR Promedio", format="%.1f%%")
            }
        )

    else:
        st.info("No hay datos de rentabilidad para este mes aún.")
        
# ==============================================================================
# TAB 5: TRACKING
# ==============================================================================

with tab_tracking:
    c1, c2 = st.columns([8, 1])
    with c1:
        st.subheader("🔍 Tracking Operativo")
    with c2:
        if st.button("🔄 Refrescar", key="btn_refresh_track"): 
            st.cache_data.clear()
            st.rerun()

    query_activos = """
        SELECT id, booster_nombre, elo_inicial, user_pass, opgg, estado 
        FROM pedidos 
        WHERE estado NOT IN ('Terminado', 'Cancelado', 'Pagado', 'Abandonado') 
        ORDER BY id DESC
    """
    df_activos = run_query(query_activos)

    if df_activos.empty:
        st.success("✅ No hay pedidos activos en este momento.")
    else:
        tracking_data = []
        lista_ids_activos = []
        opciones_selector = []
        for i, row in enumerate(df_activos.itertuples(), 1):
            link_val = row.opgg if pd.notna(row.opgg) and str(row.opgg).strip() != "" else None
            lista_ids_activos.append(row.id)

            tracking_data.append({
                "Nº": i,
                "Staff": row.booster_nombre,
                "Elo": row.elo_inicial,
                "Cuenta (User:Pass)": row.user_pass,
                "Link OP.GG": link_val,
                "Estado": row.estado
            })
            opciones_selector.append(f"{i} | Staff: {row.booster_nombre} | Cuenta: {row.user_pass}")
            
        df_track = pd.DataFrame(tracking_data)

        st.dataframe(
            df_track, 
            width='stretch',
            hide_index=True,
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
        st.write("Selecciona el pedido en la lista para corregir el link. **Para eliminarlo, deja la caja en blanco y guarda.**")
        
        with st.form("form_editar_opgg"):
            col1, col2 = st.columns([1, 2])
            with col1:
                pedido_visual_sel = st.selectbox("Selecciona el Pedido:", options=opciones_selector)
            with col2:
                nuevo_link = st.text_input("Nuevo Link OP.GG:", placeholder="https://...")
            
            submit_edit = st.form_submit_button("Actualizar / Eliminar Enlace", width='stretch', type="primary")
            
            if submit_edit:
                idx_seleccionado = opciones_selector.index(pedido_visual_sel)
                real_id_a_editar = lista_ids_activos[idx_seleccionado]
                
                conn = get_connection()
                if conn:
                    try:
                        link_final = nuevo_link.strip() if nuevo_link.strip() != "" else None
                        with conn.cursor() as cur:
                            cur.execute("UPDATE pedidos SET opgg = %s WHERE id = %s", (link_final, real_id_a_editar))
                            conn.commit()

                        st.cache_data.clear()
                        st.success(f"✅ ¡Operación exitosa! Refrescando...")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al actualizar DB: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Error de conexión a la nube.")
                    
    st.divider()
    st.subheader("🚨 Auditoría de Anomalías")

    query_audit = """
        SELECT booster_nombre, elo_inicial, user_pass, opgg, fecha_limite, wr, estado 
        FROM pedidos 
        WHERE estado NOT IN ('Terminado', 'Cancelado', 'Pagado', 'Abandonado')
    """
    df_audit = run_query(query_audit)
    
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
                link_audit = row.get('opgg') if pd.notna(row.get('opgg')) and str(row.get('opgg')).strip() != "" else None

                anomalias.append({
                    "Staff": row['booster_nombre'],
                    "Elo": row.get('elo_inicial', 'N/A'),
                    "User:Pass": row.get('user_pass', 'N/A'),
                    "OP.GG": link_audit,
                    "Fecha Final": format_fecha_latam(row['fecha_limite']),
                    "Estado": row['estado'],
                    "Alerta": alerta_texto,
                    "Status": status_icono
                })
                
        if anomalias: 
            df_anom = pd.DataFrame(anomalias)
            df_anom = df_anom[["Staff", "Elo", "User:Pass", "OP.GG", "Fecha Final", "Estado", "Alerta", "Status"]]
            st.dataframe(
                df_anom,
                width='stretch',
                hide_index=True,
                column_config={
                    "Staff": st.column_config.TextColumn("Staff", width="medium"),
                    "Elo": st.column_config.TextColumn("Elo", width="small"),
                    "User:Pass": st.column_config.TextColumn("Cuenta", width="medium"),
                    "OP.GG": st.column_config.LinkColumn("OP.GG", display_text="🔗 Revisar", width="small"),
                    "Fecha Final": st.column_config.TextColumn("Fecha Final", width="small"),
                    "Estado": st.column_config.TextColumn("Estado", width="small"),
                    "Alerta": st.column_config.TextColumn("Alerta", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small")
                }
            )
        else: 
            st.success("✨ Excelente. Sin anomalías operativas en curso.")
        
# ==============================================================================
# TAB 7: Gestion Financiera
# ==============================================================================

with tab_gestion:
    st.subheader("💸 Liquidaciones Pendientes")
    
    query_pendientes = """
        SELECT id, booster_nombre, user_pass, elo_final, wr, pago_cliente, pago_booster, pago_realizado, fecha_fin_real
        FROM pedidos
        WHERE estado = 'Terminado'
        AND (pago_realizado = 0 OR pago_realizado IS NULL)
        ORDER BY fecha_fin_real ASC
    """
    df_pendientes = run_query(query_pendientes)

    if not df_pendientes.empty:
        st.info(f"Tienes **{len(df_pendientes)}** liquidaciones por procesar.")
        
        for index, row in df_pendientes.iterrows():
            titulo_expander = f"🔴 Pendiente: {row['booster_nombre']} ｜ Cuenta: {row['user_pass']}"
            
            with st.expander(titulo_expander):
                with st.form(key=f"form_pay_lock_{row['id']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.text_input("Staff", value=row['booster_nombre'], disabled=True)
                    c2.text_input("Elo Final", value=row['elo_final'], disabled=True)
                    c3.number_input("Win Rate %", value=float(clean_num(row['wr'])), disabled=True)
                    
                    c4, c5, c6 = st.columns(3)
                    c4.number_input("Cobro Cliente $", value=float(clean_num(row['pago_cliente'])), disabled=True)
                    c5.number_input("Pago Staff $", value=float(clean_num(row['pago_booster'])), disabled=True)
                    marcar_pagado = c6.checkbox("CONFIRMAR PAGO", value=False, 
                                                help="Al confirmar, este pedido se sumará a tus métricas financieras.")
                    if st.form_submit_button("🚀 Sincronizar Pago", width='stretch', type="primary"):
                        if marcar_pagado:
                            conn = get_connection()
                            if conn:
                                try:
                                    with conn.cursor() as cur:
                                        sql_pay = "UPDATE pedidos SET pago_realizado = 1 WHERE id = %s"
                                        cur.execute(sql_pay, (int(row['id']),))
                                        conn.commit()
                                    st.success(f"✅ ¡Pago registrado! {row['booster_nombre']} liquidado.")
                                    time.sleep(1)
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error en DB: {e}")
                                finally:
                                    conn.close()
                        else:
                            st.warning("Debes marcar el check de 'Confirmar Pago' antes de sincronizar.")
    else:
        st.success("✨ ¡Todo al día! No tienes pagos pendientes por ahora.")

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

        guardar = st.form_submit_button("💾 Guardar Cambios", type="primary", width='stretch')
        
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
    
    if st.button("🗑️ Sí, Eliminar Definitivamente", type="primary", width='stretch'):
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
# TAB 7: BINANCE
# ==============================================================================

with tab_binance:
    st.subheader("🏦 Binance Wallet")

    df_pedidos_all = run_query("SELECT pago_cliente, pago_booster, wr FROM pedidos WHERE estado = 'Terminado' AND pago_realizado = 1")
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

                st.dataframe(df_final, width='stretch', hide_index=True)
                st.divider()
                st.markdown("### ⚙️ Gestionar Registro")
                opciones_crud = df_filtrado.apply(lambda r: f"Nº {r['id_visual']} | {r['tipo']} | {r['monto_str']} | {r['descripcion']} (ID:{r['id']})", axis=1).tolist()
                seleccion = st.selectbox("Selecciona un movimiento de la tabla:", opciones_crud, label_visibility="collapsed")
                c_btn1, c_btn2, c_btn3 = st.columns(3)
                
                with c_btn1:
                    if st.button("✏️ Editar", width='stretch'):
                        id_real = int(seleccion.split("(ID:")[1].replace(")", "").strip())
                        fila_sel = df_wallet[df_wallet['id'] == id_real].iloc[0]
                        modal_editar_transaccion(fila_sel)
                        
                with c_btn2:
                    if st.button("🗑️ Eliminar", width='stretch'):
                        id_real = int(seleccion.split("(ID:")[1].replace(")", "").strip())
                        detalle_mostrar = seleccion.split("(ID:")[0].strip()
                        modal_eliminar_transaccion(id_real, detalle_mostrar)
                        
                with c_btn3:
                    if st.button("🔄 Refresh", width='stretch'):
                        st.cache_data.clear(), st.rerun()