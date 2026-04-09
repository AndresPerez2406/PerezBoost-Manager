import streamlit as st
import pandas as pd
import psycopg2
import os
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import warnings
import extra_streamlit_components as stx
import time

# ==============================================================================
# 🔐 UTILIDADES DE SESIÓN HÍBRIDA
# ==============================================================================

def get_session_token(role, name):
    """Genera un token de sesión temporal para la URL"""
    ts = datetime.now().strftime("%Y%m%d%H")
    data = f"{role}|{name}|{ts}"
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_session_token(token):
    """Decodifica el token de sesión de la URL"""
    try:
        data = base64.urlsafe_b64decode(token.encode()).decode()
        role, name, ts = data.split("|")
        return role, name
    except: return None, None

# ==============================================================================
# ⏰ ZONA HORARIA PARA STREAMLIT CLOUD Y VARIABLES
# ==============================================================================

os.environ['TZ'] = 'America/Bogota'
try:
    time.tzset()
except AttributeError:
    pass 

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

MESES_DICT = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

HOY = datetime.now()
MES_ACTUAL_NUM = HOY.month
ANIO_ACTUAL = HOY.year
MES_ACTUAL_ISO = HOY.strftime("%Y-%m")
NOMBRE_MES_ACTUAL = MESES_DICT[MES_ACTUAL_NUM].upper()
st.markdown(f"""
<style>
    .stApp {{ background-color: #0e1117; color: white; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    button[title="View source"] {{display: none;}}
    .viewerBadge_container__1QS1n {{display: none;}}
    div[data-testid="stMetricValue"] {{ font-size: 24px; color: #2ecc71; font-weight: bold; }}
    [data-testid="stTable"] th, [data-testid="stTable"] td {{
        text-align: center !important;
        vertical-align: middle !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #161b22;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 15px;
        color: white;
        font-weight: bold;
    }}
    .stTabs [aria-selected="true"] {{ background-color: #2ecc71 !important; color: black !important; }}
    
    /* 🛡️ Lockdown de UI para no-autenticados */
    {'[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }' if not st.session_state.get("authenticated") else ''}
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

# ==============================================================================
# 🛠️ FUNCIONES FORMATEADORAS (UTILIDADES)
# ==============================================================================

def clean_num(val):
    if val is None or pd.isna(val) or str(val).strip() == "": return 0.0
    if isinstance(val, (int, float, complex)): return float(val)
    if hasattr(val, '__float__'): return float(val)
    s = str(val).replace('$', '').replace(',', '').strip()
    try: return float(s)
    except: return 0.0

def format_fecha_latam(fecha_val):
    if pd.isna(fecha_val) or str(fecha_val).strip() == "": return "N/A"
    try: return pd.to_datetime(fecha_val).strftime("%d/%m/%y")
    except: return str(fecha_val)

def get_connection():
    url = os.getenv("DATABASE_URL")
    try: return psycopg2.connect(url, connect_timeout=10)
    except: return None
# Consultas sin caché para finanzas en tiempo real

def run_query(query):
    conn = get_connection()
    if conn:
        try:
            with conn: return pd.read_sql(query, conn)
        except: return pd.DataFrame()
        finally: conn.close()
    return pd.DataFrame()

# ==============================================================================
# 🚀 RENDERIZADORES Y FUNCIONES DE VISTA
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
    st.markdown(f"""
        <div style='text-align: center; margin-top: 20px; margin-bottom: 10px;'>
            <h1 style='color: white; font-size: 100px !important; font-weight: 950; text-transform: uppercase; letter-spacing: 15px; text-shadow: 0 0 30px rgba(255,255,255,0.2); line-height: 0.9; margin: 0;'>
                🏆 HALL OF FAME 🏆
            </h1>
            <p style='color: #a0a0a0; font-size: 28px; font-weight: 900; text-transform: uppercase; letter-spacing: 5px; margin-top: 20px;'>
                Temporada de {NOMBRE_MES_ACTUAL} <span style='color: #ff0000; text-shadow: 0 0 10px #ff0000;'>🔴</span>
            </p>
        </div>
    """, unsafe_allow_html=True)
    query_publica = f"""
        SELECT p.*,
        (SELECT puntos FROM config_precios WHERE UPPER(TRIM(division)) = UPPER(TRIM(p.elo_final)) LIMIT 1) as puntos_tarifa
        FROM pedidos p
        WHERE p.fecha_fin_real LIKE '{MES_ACTUAL_ISO}%'
        AND COALESCE((SELECT en_ranking FROM boosters WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(p.booster_nombre)) LIMIT 1), 1) = 1
    """
    df_raw = run_query(query_publica)
    if not df_raw.empty:
        if 'dias_pedido' not in df_raw.columns:
            df_raw['f_ini'] = pd.to_datetime(df_raw['fecha_inicio'], errors='coerce')
            df_raw['f_fin'] = pd.to_datetime(df_raw['fecha_fin_real'], errors='coerce')
            df_raw['dias_pedido'] = (df_raw['f_fin'] - df_raw['f_ini']).dt.total_seconds() / 86400
        df_term = df_raw[df_raw['estado'] == 'Terminado'].copy()
        df_stats_global = df_raw[df_raw['estado'].isin(['Terminado', 'Abandonado'])].copy()
        df_stats_global['dias_pedido'] = pd.to_numeric(df_stats_global['dias_pedido'], errors='coerce')
        avg_dias = df_stats_global['dias_pedido'].mean() if not df_stats_global.empty else 0
        if 0 < avg_dias < 1:
            texto_efi = "⚡ < 1 Día"
        else:
            texto_efi = f"{avg_dias:.1f} Días"
        total_pedidos = len(df_term)
        df_term['wr_val'] = pd.to_numeric(df_term['wr'], errors='coerce').fillna(0)
        if 'bote_wr' not in df_term.columns: df_term['bote_wr'] = 0.0
        df_term['bote_wr'] = pd.to_numeric(df_term['bote_wr'], errors='coerce').fillna(0.0)
        total_high = len(df_term[df_term['bote_wr'] > 0])
        wr_global = df_term['wr_val'].mean() if total_pedidos > 0 else 0.0
        df_term['pago_cliente'] = pd.to_numeric(df_term['pago_cliente'], errors='coerce').fillna(0)
        df_term['pago_booster'] = pd.to_numeric(df_term['pago_booster'], errors='coerce').fillna(0)
        df_term['ganancia_empresa'] = pd.to_numeric(df_term['ganancia_empresa'], errors='coerce').fillna(0)
        df_term['bote_calc'] = df_term['pago_cliente'] - df_term['pago_booster'] - df_term['ganancia_empresa']
        if 'bote_pedido' not in df_term.columns: df_term['bote_pedido'] = 0.0
        if 'bote_wr' not in df_term.columns: df_term['bote_wr'] = 0.0
        df_term['bote_pedido'] = pd.to_numeric(df_term['bote_pedido'], errors='coerce').fillna(0.0)
        df_term['bote_wr'] = pd.to_numeric(df_term['bote_wr'], errors='coerce').fillna(0.0)
        bote_pedidos_hist = 0.0
        bote_wr_hist = 0.0
        for _, r in df_term.iterrows():
            bp = float(r['bote_pedido'])
            bw = float(r['bote_wr'])
            bc = float(r['bote_calc'])
            if bp == 0 and bw == 0 and bc > 0:
                bote_pedidos_hist += bc
            else:
                bote_pedidos_hist += bp
                bote_wr_hist += bw
        bote_total = df_term['bote_calc'].sum()
        ajuste_str = ""
        if NOMBRE_MES_ACTUAL == "FEBRERO" and ANIO_ACTUAL == 2026:
            bote_total += 11.0
            ajuste_str = "<span>📈 Enero:</span> +$11.00 &nbsp;&nbsp;|&nbsp;&nbsp; "
        elif NOMBRE_MES_ACTUAL == "ENERO" and ANIO_ACTUAL == 2026:
            bote_total -= 5.0
            ajuste_str = "<span>💰 Ajuste:</span> -$5.00 &nbsp;&nbsp;|&nbsp;&nbsp; "
        if bote_total < 0: bote_total = 0.0
        st.markdown(f"""
<div class="prize-banner">
    <div class="prize-title">💰 GRAN PREMIO {NOMBRE_MES_ACTUAL} 💰</div>
    <div class="prize-amount">${bote_total:.2f} USD</div>
    <div class="prize-breakdown">
        {ajuste_str}<span>📦 Pedidos:</span> +${bote_pedidos_hist:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; <span>🔥 Calidad WR:</span> +${bote_wr_hist:.2f}
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
            if 'bote_wr' not in df_b_term.columns: df_b_term['bote_wr'] = 0.0
            df_b_term['bote_wr'] = pd.to_numeric(df_b_term['bote_wr'], errors='coerce').fillna(0.0)
            high_wr = len(df_b_term[df_b_term['bote_wr'] > 0])
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
        tabla_html = "<table class='esports-table'><thead><tr><th>N°</th><th style='text-align:left'>Staff</th><th>✅ Term.</th><th>🔥 Bonos WR</th><th>❌ Aban.</th><th>⭐ Pts</th></tr></thead><tbody>"
        for index, row in df_rank.iterrows():
            tabla_html += f"<tr><td>{index+1}°</td><td class='col-staff'>{row['booster_nombre']}</td><td>{row['terminados']}</td><td>{row['high_wr']}</td><td style='color:#e74c3c'>{row['abandonos']}</td><td style='color:#2ecc71; font-weight:bold;'>{row['puntaje']} pts</td></tr>"
        tabla_html += "</tbody></table>"
        st.markdown(tabla_html, unsafe_allow_html=True)
    else:
        st.info(f"No hay pedidos terminados registrados para {NOMBRE_MES_ACTUAL} todavía.")
    st.markdown('<div class="dev-footer">⚡ DEVELOPED BY ANDRES PEREZ | © 2026 PEREZBOOST</div>', unsafe_allow_html=True)

def render_booster_dashboard(booster_name):
    # --- 1. CONFIGURACIÓN DE FILTROS ---
    col_f1, col_f2 = st.columns([3, 1])
    with col_f2:
        opciones_mes = ["Todos"] + list(MESES_DICT.values())
        mes_seleccionado = st.selectbox("Selecciona Periodo:", opciones_mes, index=datetime.now().month)
    # --- 2. OBTENCIÓN DE DATOS ---
    # Pedidos Activos
    query_activos = f"SELECT id, user_pass, elo_inicial, fecha_limite, notas, opgg FROM pedidos WHERE booster_nombre = '{booster_name}' AND estado = 'En progreso'"
    df_activos = run_query(query_activos)
    # Datos Históricos
    if mes_seleccionado == "Todos":
        query_mes = f"""
            SELECT id, pago_booster, wr, bote_wr, fecha_fin_real 
            FROM pedidos 
            WHERE booster_nombre = '{booster_name}' 
            AND estado = 'Terminado'
        """
        titulo_grafica = "🔥 Rendimiento Histórico Total"
    else:
        mes_num = [k for k, v in MESES_DICT.items() if v == mes_seleccionado][0]
        mes_iso = f"{datetime.now().year}-{mes_num:02d}"
        query_mes = f"""
            SELECT id, pago_booster, wr, bote_wr, fecha_fin_real 
            FROM pedidos 
            WHERE booster_nombre = '{booster_name}' 
            AND estado = 'Terminado' 
            AND fecha_fin_real LIKE '{mes_iso}%'
        """
        titulo_grafica = f"🔥 Tu Rendimiento en {mes_seleccionado}"
    df_mes = run_query(query_mes)
    # Cálculos
    total_ganado_mes = df_mes['pago_booster'].astype(float).sum() if not df_mes.empty else 0.0
    total_pedidos_mes = len(df_mes)
    avg_wr_mes = df_mes['wr'].astype(float).mean() if not df_mes.empty and not df_mes['wr'].isna().all() else 0.0
    tabs = st.tabs(["📈 Mi Rendimiento", "⚙️ Ajustes de Perfil"])
    with tabs[0]:
        # --- 3. MÉTRICAS (CARDS) ---
        st.write("")
        label_ganancia = "GANANCIA TOTAL" if mes_seleccionado == "Todos" else "GANANCIA MES"
        label_pedidos = "TOTAL TERMINADOS" if mes_seleccionado == "Todos" else "TERMINADOS MES"
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='card-stat' style='background:#161b22; padding:20px; border-radius:10px; border-bottom:3px solid #58a6ff; text-align:center;'><p style='color:#8b949e; font-size:12px; margin:0;'>ACTIVOS</p><p style='font-size:30px; font-weight:bold; margin:0;'>{len(df_activos)}</p></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='card-stat' style='background:#161b22; padding:20px; border-radius:10px; border-bottom:3px solid #2ecc71; text-align:center;'><p style='color:#8b949e; font-size:12px; margin:0;'>{label_ganancia}</p><p style='font-size:30px; font-weight:bold; margin:0;'>${total_ganado_mes:.2f}</p></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='card-stat' style='background:#161b22; padding:20px; border-radius:10px; border-bottom:3px solid #f1c40f; text-align:center;'><p style='color:#8b949e; font-size:12px; margin:0;'>WIN RATE</p><p style='font-size:30px; font-weight:bold; margin:0;'>{avg_wr_mes:.1f}%</p></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='card-stat' style='background:#161b22; padding:20px; border-radius:10px; border-bottom:3px solid #9b59b6; text-align:center;'><p style='color:#8b949e; font-size:12px; margin:0;'>{label_pedidos}</p><p style='font-size:30px; font-weight:bold; margin:0;'>{total_pedidos_mes}</p></div>", unsafe_allow_html=True)
        # --- 4. GRÁFICA GUAPA (Plotly) ---
        st.write("")
        if not df_mes.empty:
            df_mes['fecha_dia'] = pd.to_datetime(df_mes['fecha_fin_real']).dt.date
            df_grafica = df_mes.groupby('fecha_dia')['pago_booster'].sum().reset_index().sort_values('fecha_dia')
            df_grafica['acumulado'] = df_grafica['pago_booster'].cumsum()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_grafica['fecha_dia'], y=df_grafica['pago_booster'], name='Ganancia Diaria', marker_color='#2ecc71', opacity=0.8))
            fig.add_trace(go.Scatter(x=df_grafica['fecha_dia'], y=df_grafica['acumulado'], name='Progreso Total', line=dict(color='#58a6ff', width=3, dash='dot')))
            fig.update_layout(
                title=titulo_grafica, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), xaxis=dict(showgrid=False, title="Día"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info(f"¡Vamos! Termina tu primer pedido de {mes_seleccionado} para ver tus gráficas de crecimiento. 🚀")
        st.write("")
        # --- 5. CUENTAS ACTIVAS / EN CURSO ---
        st.subheader("🛠️ Cuentas en Curso")
        if df_activos.empty:
            st.success("¡Todo al día! No tienes pedidos pendientes.")
        else:
            for _, row in df_activos.iterrows():
                with st.expander(f"🎮 {row['user_pass']}"):
                    ca, cb = st.columns([3, 1])
                    with ca:
                        st.write(f"**Elo / Objetivo:** {row['elo_inicial']}")
                        v_notas = row['notas'] if pd.notna(row['notas']) and str(row['notas']).strip() != "" else "Ninguna"
                        st.info(f"📝 **Notas:** {v_notas}")
                        if row['opgg']: st.markdown(f"🔗 <a href='{row['opgg']}' target='_blank'>Ver OP.GG</a>", unsafe_allow_html=True)
                    with cb:
                        st.write(f"**Límite:** {row['fecha_limite']}")
                        token = base64.urlsafe_b64encode(f"perez-{row['id']}".encode()).decode()
                        st.markdown(f"<a href='/?t={token}' target='_blank' style='text-decoration:none;'><button style='width:100%; cursor:pointer; background:#2ecc71; border:none; color:black; padding:10px; border-radius:5px; font-weight:bold;'>VER DETALLES</button></a>", unsafe_allow_html=True)
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            st.rerun()
    with tabs[1]:
        st.subheader("⚙️ Configuración de Acceso")
        st.write("Gestiona tus credenciales de acceso y tu ID de Discord para recibir notificaciones.")
        # Obtener datos actuales del booster
        df_b = run_query(f"SELECT nombre, password, discord_id, binance FROM boosters WHERE nombre = '{booster_name}'")
        if not df_b.empty:
            curr_name = df_b.iloc[0]['nombre']
            curr_pass = df_b.iloc[0]['password']
            curr_disc = df_b.iloc[0]['discord_id'] or ""
            curr_binance = df_b.iloc[0]['binance'] or ""
            with st.form("perfil_booster_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Nombre de Usuario (Login):", value=curr_name)
                    new_pass = st.text_input("Nueva Contraseña:", value=curr_pass, type="password")
                with col2:
                    new_discord = st.text_input("Discord ID (Ej: 123456789):", value=curr_disc, help="ID para pings automáticos.")
                    new_binance = st.text_input("Binance Pay ID / Wallet:", value=curr_binance)
                if st.form_submit_button("Guardar Cambios 💾", use_container_width=True):
                    conn = get_connection()
                    if conn:
                        try:
                            with conn.cursor() as cur:
                                cur.execute("UPDATE boosters SET nombre = %s, password = %s, discord_id = %s, binance = %s WHERE nombre = %s", 
                                          (new_name, new_pass, new_discord, new_binance, booster_name))
                                conn.commit()
                            st.success("✅ Perfil y Binance actualizados.")
                            st.session_state.user_name = new_name 
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")
                        finally:
                            conn.close()

# ==============================================================================
# 🔐 GESTIÓN DE AUTENTICACIÓN GLOBAL
# ==============================================================================

cookie_manager = stx.CookieManager(key="perez_auth_manager")
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'logout_in_progress' not in st.session_state:
    st.session_state.logout_in_progress = False
if 'login_successful' not in st.session_state:
    st.session_state.login_successful = False

# 🚦 DETECCIÓN DE PORTAL Y PARÁMETROS
v_param = st.query_params.get("v", "")
k_param = st.query_params.get("k", "")
b_param = st.query_params.get("b", "")
p_param = st.query_params.get("p", "")
is_staff_portal = (v_param == "staff")
is_token_view = ("t" in st.query_params)
is_ranking_view = (st.query_params.get("view", "") == "ranking")
# El portal de Admin solo se activa si no es staff y no es una zona neutral (token/ranking)
is_admin_portal = (not is_staff_portal and not is_token_view and not is_ranking_view)
# 1. Recuperar sesión (Memory Latching + URL Token + Cookie fallback)
if not st.session_state.authenticated:
    # A. Recuperación por URL (Instantánea al refrescar F5)
    s_param = st.query_params.get("s", "")
    if s_param:
        r_role, r_name = decode_session_token(s_param)
        if r_role and r_name:
            st.session_state.authenticated = True
            st.session_state.user_role = r_role
            st.session_state.user_name = r_name

    # B. Sincronización Silenciosa de Cookies (Fallback si no hay URL token)
    if not st.session_state.authenticated:
        if 'auth_pulses' not in st.session_state:
            st.session_state.auth_pulses = 0
        
        cookies = cookie_manager.get_all()
        auth_cookie = cookies.get("perez_login_token")
        
        if not auth_cookie and st.session_state.auth_pulses < 3:
            st.session_state.auth_pulses += 1
            st.rerun() 

        if st.session_state.login_successful:
            st.session_state.authenticated = True
            st.session_state.login_successful = False
        
        elif auth_cookie:
            try:
                if "|" in auth_cookie:
                    c_role, c_name = auth_cookie.split("|")
                    if c_role and c_name and c_name != "None":
                        st.session_state.authenticated = True
                        st.session_state.user_role = c_role
                        st.session_state.user_name = c_name
                        st.query_params.s = get_session_token(c_role, c_name)
            except: pass
    
    # 2. Protección de Portal y Auto-Redirección
    if st.session_state.authenticated:
        # Si el rol no coincide con el portal actual, intentamos redirigir en lugar de desloguear
        if is_staff_portal and st.session_state.user_role == "admin":
            # Admin entrando a Staff -> Redirigir a Admin
            st.query_params.clear()
            st.rerun()
        elif is_admin_portal and st.session_state.user_role == "booster":
            # Booster entrando a Admin -> Redirigir a Staff
            st.query_params.v = "staff"
            st.rerun()
    # Prioridad C: Auto-Login via URL
    if not st.session_state.authenticated:
        if k_param:
            try: clave_admin = st.secrets["ADMIN_PASSWORD"]
            except: clave_admin = os.getenv("ADMIN_PASSWORD")
            if k_param == clave_admin:
                st.session_state.authenticated = True
                st.session_state.user_role = "admin"
                st.session_state.user_name = "Administrador"
                st.session_state.login_successful = True
                cookie_manager.set("perez_login_token", "admin|Administrador", expires_at=(datetime.now() + timedelta(days=3)))
                st.query_params.clear()
                st.query_params.s = get_session_token("admin", "Admin") # Token en URL
                st.rerun()
        elif is_staff_portal and b_param and p_param:
            q_b = f"SELECT nombre FROM boosters WHERE nombre ILIKE '{b_param.strip()}' AND password = '{p_param}'"
            df_b = run_query(q_b)
            if not df_b.empty:
                st.session_state.authenticated = True
                st.session_state.user_role = "booster"
                u_name_b = df_b.iloc[0]['nombre']
                st.session_state.user_name = u_name_b
                st.session_state.login_successful = True
                cookie_manager.set("perez_login_token", f"booster|{u_name_b}", expires_at=(datetime.now() + timedelta(days=3)))
                st.query_params.clear(); st.query_params.v = "staff"
                st.query_params.s = get_session_token("booster", u_name_b) # Token en URL
                st.rerun()
# 2. Sincronización de Logout
if st.session_state.logout_in_progress:
    st.session_state.logout_in_progress = False

def perform_logout():
    # Detectar el portal de origen antes de limpiar todo
    is_staff = (st.session_state.get("user_role") == "booster") or ("v" in st.query_params and st.query_params["v"] == "staff")
    
    # 1. Limpieza total y absoluta del estado de sesión
    st.session_state.clear()
    
    # 2. Forzar borrado de cookies
    try:
        exp_p = datetime.now() - timedelta(days=10)
        cookie_manager.set("perez_login_token", "", expires_at=exp_p)
        cookie_manager.delete("perez_login_token")
    except: pass
    
    # 3. Determinar destino (Booster -> ?v=staff, Admin -> /)
    target_url = "/?v=staff" if is_staff else "/"
    
    # 4. Redirección Forzada via Meta-Refresh (Hard Reset del navegador)
    st.markdown(f'<meta http-equiv="refresh" content="0; url={target_url}">', unsafe_allow_html=True)
    st.stop()
login_placeholder = st.empty()

# Enrutamiento se movió abajo de las funciones
if "t" in st.query_params:
    token_recibido = st.query_params["t"]
    try:
        token_decodificado = base64.urlsafe_b64decode(token_recibido.encode('utf-8')).decode('utf-8')
        id_pedido = token_decodificado.split("-")[1]
    except Exception:
        st.error("Error de autenticación: Enlace de asignación inválido o corrupto.")
        st.stop()
    df_info = run_query(f"SELECT booster_nombre, user_pass, elo_inicial, fecha_inicio, fecha_limite, notas FROM pedidos WHERE id = {id_pedido}")
    if df_info.empty:
        st.error("Error: El pedido solicitado no existe en la base de datos.")
        st.stop()
    booster_asignado = df_info.iloc[0]['booster_nombre']
    user_pass_asignado = df_info.iloc[0]['user_pass']
    elo_llevar = df_info.iloc[0]['elo_inicial']
    fecha_inicio_str = df_info.iloc[0]['fecha_inicio']
    fecha_limite_ped = str(df_info.iloc[0]['fecha_limite']).split(" ")[0] if pd.notna(df_info.iloc[0]['fecha_limite']) else ""
    notas_pedido = df_info.iloc[0].get('notas', '')
    if pd.isna(notas_pedido) or str(notas_pedido).strip() == "": notas_pedido = "Ninguna"
    else: notas_pedido = str(notas_pedido).strip()
    dias_restantes_opgg = "N/A"
    try:
        if pd.notna(fecha_inicio_str) and str(fecha_inicio_str).strip() != "":
            fecha_inicio = pd.to_datetime(fecha_inicio_str)
            fecha_limite_opgg = fecha_inicio + timedelta(days=5)
            fecha_limite_str = fecha_limite_opgg.strftime("%d/%m/%y")
            d_res_o = max(0, (fecha_limite_opgg - datetime.now()).days)
            dias_restantes_opgg = "¡Hoy!" if d_res_o == 0 else f"{d_res_o} días"
        else: fecha_limite_str = "No definida"
    except: fecha_limite_str = "No definida"
    
    # --- Contador de cuentas eliminado por solicitud ---
    
    dias_restantes = "N/A"; fecha_limite_ped_ui = "No asignada"
    try:
        if fecha_limite_ped != "":
            f_ped = pd.to_datetime(fecha_limite_ped)
            fecha_limite_ped_ui = f_ped.strftime("%d/%m/%y")
            d_res = max(0, (f_ped - datetime.now()).days)
            dias_restantes = "¡Hoy!" if d_res == 0 else f"{d_res} días restantes"
    except: pass
    st.markdown("""
<style>
.card { background: linear-gradient(145deg, #0d0d12, #121218); border-radius: 15px; padding: 35px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8); border: 1px solid #1f1f2e; text-align: center; margin-bottom: 25px; transition: transform 0.3s, border-color 0.3s; }
.card:hover { border-color: #4a4a6a; transform: translateY(-5px); }
.title_box { color: #e2e8f0; font-size: 32px; font-weight: 900; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 3px; text-shadow: 0 2px 5px rgba(0,0,0,0.5);}
.subtitle { color: #64748b; font-size: 17px; margin-bottom: 25px; letter-spacing: 2px; font-weight: bold; text-transform: uppercase;}
.info-box { background-color: #12121a; border-radius: 12px; padding: 18px 20px; margin: 12px 0; display: flex; flex-direction: column; border: 1px solid #1f1f2e; border-left: 5px solid #475569; text-align: left;}
.info-box .label { color: #64748b; font-size: 13px; text-transform: uppercase; font-weight: 800; letter-spacing: 1px; }
.info-box .value { color: #f8fafc; font-size: 20px; font-weight: 700; margin-top: 5px; }
.alert-box { background-color: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 15px; color: #fbbf24; font-weight: 800; margin: 25px 0 10px 0; }
.earnings-badge { background: #1e293b; color: #94a3b8; padding: 10px 20px; border-radius: 30px; font-size: 16px; font-weight: 900; display: inline-block; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px; border: 1px solid #334155; }
div[data-testid="stForm"] { background: #0d0d12; border: 1px solid #1f1f2e; border-radius: 12px; padding: 25px; }
button[kind="primaryFormSubmit"] { background-color: #1e293b !important; color: #cbd5e1 !important; font-weight: 900 !important; font-size: 18px !important; text-transform: uppercase !important; letter-spacing: 1px !important; border-radius: 8px !important; border: 1px solid #475569 !important; transition: 0.3s !important; }
button[kind="primaryFormSubmit"]:hover { background-color: #334155 !important; transform: scale(1.02); color: #f8fafc !important; border-color: #64748b !important; }
</style>
""", unsafe_allow_html=True)
    # Boton de volver eliminado (Uso de nueva pestaña)
    st.markdown(f"""
<div class="card">
<div class="title_box" style="margin-bottom: 25px; margin-top: 15px;">Área Operativa 🏆</div>
<div class="info-box">
<div class="label">👤 BOOSTER</div>
<div class="value">Cuenta asignada a <b>{booster_asignado}</b></div>
</div>
<div class="info-box">
<div class="label">🔑 CREDENCIALES DE ACCESO:</div>
<div class="value" style="color: #9cdcfe; font-family: monospace; font-size: 20px;">{user_pass_asignado} &nbsp;—&nbsp; <span style="color:#cecece;">{elo_llevar}</span></div>
</div>
<div class="info-box">
<div class="label">📝 NOTAS DEL PEDIDO:</div>
<div class="value" style="color: #e2e8f0; font-size: 16px;">{notas_pedido}</div>
</div>
<div class="info-box" style="border-left-color: #f59e0b;">
  <div class="label">⏳ ENTREGA CUENTA</div>
  <div class="value" style="color: #fbbf24; font-size: 20px;">{dias_restantes} &nbsp;<span style="color:#64748b; font-size: 14px;">(Límite: {fecha_limite_ped_ui})</span></div>
</div>
<div class="alert-box">
⚠️ Recuerda adjuntar el OP.GG antes del {fecha_limite_str} para evitar penalizaciones.<br>
<span style="color:#d97706; font-size: 14px; margin-top: 5px; display: inline-block;">Si tienes algún inconveniente con el boost, escríbeme.</span>
</div>
<div style="margin-top: 25px; color: #475569; font-size: 11px; font-weight: bold; letter-spacing: 2px;">PEREZBOOST - NA ©</div>
</div>
""", unsafe_allow_html=True)
    with st.form("form_booster"):
        st.markdown("<p style='font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 5px;'>🔗 Enlace de Seguimiento de Partidas (OP.GG):</p>", unsafe_allow_html=True)
        opgg_input = st.text_input("Enlace de seguimiento:", placeholder="https://www.op.gg/summoners/lan/...", label_visibility="collapsed")
        if st.form_submit_button("Registrar OP.GG 🚀"):
            if opgg_input.strip() == "" or not opgg_input.startswith("http"):
                st.error("Validación fallida: Registra una URL válida.")
            else:
                conn = get_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE pedidos SET opgg = %s WHERE id = %s", (opgg_input, id_pedido))
                            conn.commit()
                        st.success("¡Registro completado exitosamente! 💪")
                    except Exception as e: st.error(f"Error: {e}")
                    finally: conn.close()
    st.stop()

    st.stop()

# ==============================================================================
# 🚀 ENRUTADOR DE VISTAS PÚBLICAS (TOKEN Y RANKING)
# ==============================================================================
if "view" in st.query_params and st.query_params["view"] == "ranking":
    render_public_ranking()
    st.stop()

# ==============================================================================
# 🎮 MOTOR DE AUDITORÍA Y ALERTAS
# ==============================================================================

def ejecutar_auditoria_alertas():
    # Obtener Webhook de alertas
    url_alertas = run_query("SELECT valor FROM sistema_config WHERE clave = 'discord_webhook_alertas'")
    if url_alertas.empty or not url_alertas.iloc[0,0]:
        st.error("Configuración de Discord no encontrada.")
        return 0
    webhook_url = url_alertas.iloc[0,0]
    query_24h = """
        SELECT id, booster_nombre, user_pass, fecha_limite, 
               (SELECT discord_id FROM boosters WHERE nombre = booster_nombre) as discord_id
        FROM pedidos 
        WHERE estado = 'En progreso' 
        AND fecha_limite IS NOT NULL AND fecha_limite != ''
    """
    df_alert = run_query(query_24h)
    alertas_enviadas = 0
    if not df_alert.empty:
        from core.discord_handler import DiscordNotifier, COLOR_DANGER, COLOR_WARNING
        notifier = DiscordNotifier(webhook_url)
        for _, row in df_alert.iterrows():
            try:
                f_limite = pd.to_datetime(row['fecha_limite'])
                diferencia = f_limite - datetime.now()
                # Alerta Urgente: Menos de 24 horas
                if 0 < diferencia.total_seconds() < 86400:
                    mention = f"<@{row['discord_id']}>" if row['discord_id'] else f"**{row['booster_nombre']}**"
                    notifier.enviar_notificacion(
                        titulo="⚠️ PEDIDO POR VENCER (24H)",
                        descripcion=f"El pedido #{row['id']} para **{row['user_pass']}** está a menos de 24 horas de su límite.",
                        color=COLOR_DANGER,
                        content_text=f"¡Atención {mention}! Revisa tus tiempos de entrega.",
                        campos=[
                            {"name": "Booster", "value": row['booster_nombre'], "inline": True},
                            {"name": "Límite", "value": row['fecha_limite'], "inline": True}
                        ]
                    )
                    alertas_enviadas += 1
            except: continue
    # 2. Buscar pedidos sin OP.GG (> 2 días de iniciado)
    query_opgg = """
        SELECT id, booster_nombre, user_pass, fecha_inicio,
               (SELECT discord_id FROM boosters WHERE nombre = booster_nombre) as discord_id
        FROM pedidos 
        WHERE estado = 'En progreso' 
        AND (opgg IS NULL OR opgg = '')
    """
    df_opgg = run_query(query_opgg)
    if not df_opgg.empty:
        from core.discord_handler import DiscordNotifier, COLOR_WARNING
        notifier = DiscordNotifier(webhook_url)
        for _, row in df_opgg.iterrows():
            try:
                f_inicio = pd.to_datetime(row['fecha_inicio'])
                dias_transcurridos = (datetime.now() - f_inicio).days
                if dias_transcurridos >= 2:
                    mention = f"<@{row['discord_id']}>" if row['discord_id'] else f"**{row['booster_nombre']}**"
                    notifier.enviar_notificacion(
                        titulo="🔗 FALTA LINK OPGG",
                        descripcion=f"El pedido #{row['id']} lleva {dias_transcurridos} días sin link de seguimiento registrado.",
                        color=COLOR_WARNING,
                        content_text=f"Recuerda registrar el OP.GG {mention}.",
                        campos=[
                            {"name": "Booster", "value": row['booster_nombre'], "inline": True},
                            {"name": "Cuenta", "value": row['user_pass'], "inline": True}
                        ]
                    )
                    alertas_enviadas += 1
            except: continue
    return alertas_enviadas


# ==============================================================================
# 🔐 RENDERIZADO DE LOGIN (SI NO ESTÁ AUTENTICADO)
# ==============================================================================

if not st.session_state.authenticated:
    with login_placeholder.container():
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if is_staff_portal:
                st.markdown("""
                    <div style='text-align: center;'>
                        <h2 style='color: #58a6ff; margin-bottom: 5px;'>👨‍💻 Portal de Staff</h2>
                        <p style='color: #8b949e; font-size: 14px;'>Identifícate para ver tus pedidos</p>
                    </div>
                """, unsafe_allow_html=True)
                with st.form("staff_login_form"):
                    u_name = st.text_input("Nombre de Staff:", placeholder="Ej: Perez")
                    u_pass = st.text_input("Contraseña:", type="password")
                    mantener = st.checkbox("Recordarme", value=True)
                    submit = st.form_submit_button("Entrar al Panel 🚀")
                    if submit:
                        u_name_clean = u_name.strip()
                        q_booster = f"SELECT nombre FROM boosters WHERE nombre ILIKE '{u_name_clean}' AND password = '{u_pass}'"
                        df_check = run_query(q_booster)
                        if not df_check.empty:
                            st.session_state.authenticated = True
                            st.session_state.user_role = "booster"
                            u_name_found = df_check.iloc[0]['nombre']
                            st.session_state.user_name = u_name_found
                            st.session_state.login_successful = True
                            if mantener:
                                expira = datetime.now() + timedelta(days=3)
                                cookie_manager.set("perez_login_token", f"booster|{u_name_found}", expires_at=expira)
                            # Inyectar token en URL para persistencia F5
                            st.query_params.s = get_session_token("booster", u_name_found)
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas.")
            else:
                st.markdown("""
                    <div style='text-align: center;'>
                        <h2 style='color: #2ecc71; margin-bottom: 5px;'>🔐 Acceso Administrativo</h2>
                        <p style='color: #8b949e; font-size: 14px;'>Introduce la clave de seguridad</p>
                    </div>
                """, unsafe_allow_html=True)
                with st.form("admin_login_form"):
                    u_pass = st.text_input("Credencial de Acceso:", type="password")
                    mantener = st.checkbox("No cerrar sesión", value=True)
                    submit = st.form_submit_button("Ingresar")
                    if submit:
                        try: clave_admin = st.secrets["ADMIN_PASSWORD"]
                        except: clave_admin = os.getenv("ADMIN_PASSWORD")
                        if u_pass == clave_admin:
                            st.session_state.authenticated = True
                            st.session_state.user_role = "admin"
                            st.session_state.user_name = "Administrador"
                            st.session_state.login_successful = True
                            if mantener:
                                expira = datetime.now() + timedelta(days=3)
                                cookie_manager.set("perez_login_token", "admin|Administrador", expires_at=expira)
                            # Inyectar token en URL
                            st.query_params.s = get_session_token("admin", "Admin")
                            st.rerun()
                        else:
                            st.error("❌ Clave incorrecta.")
    st.stop()

# ==============================================================================
# 3. CONTENIDO AUTENTICADO
# ==============================================================================
if st.session_state.authenticated:
    # Header Uniforme con Botón de Cerrar Sesión
    h1, h2 = st.columns([8, 1.2])
    with h1:
        if st.session_state.user_role == "admin":
            st.title(f"🚀 PerezBoost {APP_VERSION} | Monitor")
        else:
            st.title(f"👨‍💻 Panel Staff: {st.session_state.user_name}")
    with h2:
        st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión", key="global_logout", use_container_width=True):
            perform_logout()
    if st.session_state.user_role == "booster":
        render_booster_dashboard(st.session_state.user_name)
        st.markdown('<br><hr><div style="text-align:center; color:#555; font-size:12px;">PEREZBOOSTNA © 2026</div>', unsafe_allow_html=True)
        st.stop()
else:
    st.stop()
tab_reportes, tab_analytics, tab_inventario, tab_ranking, tab_tracking, tab_gestion, tab_binance = st.tabs(["📊 Reportes", "📈 Analytics", "📦 INVENTARIO", "🏆 TOP STAFF", "🔍 TRACKING", "🛠️ GESTIÓN", "💰 BINANCE"])

# ==============================================================================
# TAB 1: REPORTES
# ==============================================================================

with tab_reportes:
    f1, f2, f3, f4 = st.columns([2.5, 2.5, 1.2, 1.5])
    with f1:
        meses_nombres = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_sel = st.selectbox("📅 Seleccionar Mes", meses_nombres, index=MES_ACTUAL_NUM)
    with f2:
        df_boosters = run_query("SELECT DISTINCT booster_nombre FROM pedidos")
        booster_sel = st.selectbox("👤 Filtrar por Staff", ["Todos"] + sorted(df_boosters['booster_nombre'].dropna().tolist()) if not df_boosters.empty else ["Todos"])
    with f3:
        st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refrescar", use_container_width=True):  
            st.cache_data.clear()
            st.rerun()
    with f4:
        st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚨 Auditoría", use_container_width=True, help="Revisa retrasos y envía pings a Discord"):
            with st.spinner("Auditando..."):
                count = ejecutar_auditoria_alertas()
                if count and count > 0: st.success(f"Auditado: {count} alertas.")
                else: st.info("Sin anomalías.")
    query_base = "SELECT id, booster_nombre, user_pass, elo_inicial, elo_final, wr, fecha_inicio, fecha_fin_real, pago_cliente, pago_booster, ganancia_empresa, bote_pedido, bote_wr FROM pedidos WHERE estado = 'Terminado' AND pago_realizado = 1"
    if mes_sel != "Todos":
        n_mes = str(meses_nombres.index(mes_sel)).zfill(2)
        query_base += f" AND CAST(fecha_fin_real AS TEXT) LIKE '{ANIO_ACTUAL}-{n_mes}%'"
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
            g_empresa = clean_num(row.ganancia_empresa)
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
            mi_neto_real = g_empresa
            try: b_ped = float(row.bote_pedido)
            except: b_ped = 0.0
            try: b_wr = float(row.bote_wr)
            except: b_wr = 0.0
            calc_viejo = p_cli - p_boo - mi_neto_real
            valor_bote = (b_ped + b_wr) if (b_ped + b_wr) > 0 else calc_viejo
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
    else:
        st.info(f"No hay pedidos terminados para el mes de {mes_sel}.")

# ==============================================================================
# TAB 2: GITANALYTICS
# ==============================================================================

with tab_analytics:
    st.subheader("🔮 GitAnalytics")
    f1, f2, f3 = st.columns([2.5, 1.5, 6])
    with f1:
        meses_nombres = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_sel_ana = st.selectbox("📅 Analizar Mes", meses_nombres, index=MES_ACTUAL_NUM, key="mes_ana")
    with f2:
        st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refrescar", key="btn_ref_ana", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    st.divider()
    query_bi = """
        SELECT booster_nombre, wr, pago_cliente, pago_booster, ganancia_empresa, fecha_inicio, fecha_fin_real, bote_pedido, bote_wr
        FROM pedidos
        WHERE estado = 'Terminado' 
        AND pago_realizado = 1 
        AND fecha_fin_real IS NOT NULL
    """
    if mes_sel_ana != "Todos":
        n_mes = str(meses_nombres.index(mes_sel_ana)).zfill(2)
        query_bi += f" AND CAST(fecha_fin_real AS TEXT) LIKE '{ANIO_ACTUAL}-{n_mes}%'"
    df_bi = run_query(query_bi)
    if not df_bi.empty:
        df_bi['wr'] = pd.to_numeric(df_bi['wr'], errors='coerce').fillna(0)
        df_bi['pago_cliente'] = pd.to_numeric(df_bi['pago_cliente'], errors='coerce').fillna(0)
        df_bi['pago_booster'] = pd.to_numeric(df_bi['pago_booster'], errors='coerce').fillna(0)
        df_bi['ganancia_empresa'] = pd.to_numeric(df_bi['ganancia_empresa'], errors='coerce').fillna(0)
        df_bi['calc_bote'] = df_bi['pago_cliente'] - df_bi['pago_booster'] - df_bi['ganancia_empresa']
        if 'bote_pedido' not in df_bi.columns: df_bi['bote_pedido'] = 0.0
        if 'bote_wr' not in df_bi.columns: df_bi['bote_wr'] = 0.0
        df_bi['valor_bote'] = df_bi.apply(
            lambda x: (float(x.get('bote_pedido', 0)) + float(x.get('bote_wr', 0))) 
            if (float(x.get('bote_pedido', 0)) + float(x.get('bote_wr', 0))) > 0 else x['calc_bote'], 
            axis=1
        )
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
        # KPI GLOBALS
        # =======================================================
        global_ganancia = df_bi['ganancia_empresa'].sum()
        if mes_sel_ana in ["Todos", "Enero"]:
            global_ganancia += 5.0
        global_wr = df_bi['wr'].mean()
        total_pedidos = len(df_bi)

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
            st.plotly_chart(fig_scatter, use_container_width=True)
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
            st.plotly_chart(fig_area, use_container_width=True)
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
        st.plotly_chart(fig_bar, use_container_width=True)
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
        if st.button("🔄 Refrescar", key="btn_refresh_inv", use_container_width=True): 
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
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
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
    query_rank = f"""
        SELECT booster_nombre, wr, fecha_inicio, fecha_fin_real, pago_cliente, pago_booster, ganancia_empresa 
        FROM pedidos 
        WHERE estado = 'Terminado'
        AND CAST(fecha_fin_real AS TEXT) LIKE '{MES_ACTUAL_ISO}%'
        AND COALESCE((SELECT en_ranking FROM boosters WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(booster_nombre)) LIMIT 1), 1) = 1
    """
    df_month = run_query(query_rank)
    if not df_month.empty:
        df_month['wr'] = pd.to_numeric(df_month['wr'], errors='coerce').fillna(0)
        df_month['pago_cliente'] = pd.to_numeric(df_month['pago_cliente'], errors='coerce').fillna(0)
        df_month['pago_booster'] = pd.to_numeric(df_month['pago_booster'], errors='coerce').fillna(0)
        df_month['ganancia_empresa'] = pd.to_numeric(df_month['ganancia_empresa'], errors='coerce').fillna(0)
        df_month['bote'] = df_month['pago_cliente'] - df_month['pago_booster'] - df_month['ganancia_empresa']
        df_month['neto'] = df_month['ganancia_empresa']
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
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.write("📋 **Desglose Completo de Staff**")
        df_mostrar = df_grouped[["booster_nombre", "Total_Neto", "USD_por_Dia", "Pedidos", "Promedio_Dias", "WR_Promedio"]].sort_values(by="USD_por_Dia", ascending=False)
        st.dataframe(
            df_mostrar, 
            use_container_width=True, 
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
        if st.button("🔄 Refrescar", key="btn_refresh_track", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    query_activos = """
        SELECT id, booster_nombre, elo_inicial, user_pass, opgg, estado, notas 
        FROM pedidos 
        WHERE estado = 'En progreso'
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
            nota_val = row.notas if pd.notna(row.notas) and str(row.notas).strip() != "" else "FRESH"
            lista_ids_activos.append(row.id)
            tracking_data.append({
                "Nº": i,
                "Staff": row.booster_nombre,
                "Elo": row.elo_inicial,
                "Cuenta (User:Pass)": row.user_pass,
                "Notas": nota_val,
                "Link OP.GG": link_val,
                "Estado": row.estado
            })
            opciones_selector.append(f"{i} | Staff: {row.booster_nombre} | Cuenta: {row.user_pass}")
        df_track = pd.DataFrame(tracking_data)
        st.dataframe(
            df_track, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Notas": st.column_config.TextColumn("Notas", width="medium"),
                "Link OP.GG": st.column_config.LinkColumn(
                    "Link OP.GG", 
                    help="Haz clic para abrir el perfil",
                    display_text="🔗 Abrir Perfil"
                )
            }
        )
        st.divider()
        st.divider()
        st.subheader("🛠️ Gestión de Enlaces (Corrección de Errores)")
        st.write("Selecciona el pedido en la lista para corregir el link. **Para eliminarlo, deja la caja en blanco y guarda.**")
        with st.form("form_editar_opgg"):
            col1, col2 = st.columns([1, 2])
            with col1:
                pedido_visual_sel = st.selectbox("Selecciona el Pedido:", options=opciones_selector)
            with col2:
                nuevo_link = st.text_input("Nuevo Link OP.GG:", placeholder="https://...")
            submit_edit = st.form_submit_button("Actualizar / Eliminar Enlace", use_container_width=True, type="primary")
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
                        st.error(f"âŒ Error al actualizar DB: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("âŒ Error de conexión a la nube.")
    st.divider()
    st.subheader("🚨 Auditoría de Anomalías")
    query_audit = """
        SELECT booster_nombre, elo_inicial, user_pass, opgg, fecha_limite, wr, estado 
        FROM pedidos 
        WHERE estado = 'En progreso'
    """
    df_audit = run_query(query_audit)
    if not df_audit.empty:
        anomalias = []
        for _, row in df_audit.iterrows():
            alerta_texto = ""
            status_icono = ""
            wr = clean_num(row['wr'])
            try: 
                fecha_lim_dt = pd.to_datetime(row['fecha_limite']).date()
                hoy_dt = datetime.now().date()
                dias = (fecha_lim_dt - hoy_dt).days
            except: 
                dias = 99
            has_opgg = pd.notna(row['opgg']) and str(row['opgg']).strip() != ""
            if not has_opgg and dias <= -3:
                if dias <= -5:
                    alerta_texto = f"MULTA 25%: Falta OP.GG ({(dias * -1)}d post-límite)"
                    status_icono = "🔴"
                else:
                    alerta_texto = f"Atención: Falta OP.GG ({(dias * -1)}d post-límite)"
                    status_icono = "🟡"
            elif wr < 50 and wr > 0: 
                alerta_texto = f"WR Bajo ({wr:.1f}%)"
                status_icono = "🔴"
            elif dias <= 1: 
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
                use_container_width=True,
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
# TAB 6: Gestion Financiera
# ==============================================================================

with tab_gestion:
    st.subheader("💰 Liquidaciones Pendientes")
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
                    if st.form_submit_button("🚀 Sincronizar Pago", use_container_width=True, type="primary"):
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
@st.dialog("✍️ Modificar Transacción")

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
# TAB 7: BINANCE
# ==============================================================================

with tab_binance:
    st.subheader("🏦 Binance Wallet")
    # 1. CÁLCULO EN VIVO DE FONDOS (Igual al PC)
    df_pedidos_all = run_query("SELECT pago_cliente, pago_booster, ganancia_empresa FROM pedidos WHERE estado = 'Terminado' AND pago_realizado = 1")
    neto_historico = 0.0
    bote_historico = 0.0
    if not df_pedidos_all.empty:
        # Usamos clean_num en todas las columnas para evitar fallos de tipo (Decimal/String)
        df_pedidos_all['p_cli'] = df_pedidos_all['pago_cliente'].apply(clean_num)
        df_pedidos_all['p_boo'] = df_pedidos_all['pago_booster'].apply(clean_num)
        df_pedidos_all['g_emp'] = df_pedidos_all['ganancia_empresa'].apply(clean_num)
        neto_historico = df_pedidos_all['g_emp'].sum()
        # El bote es la diferencia: Cliente - Booster - Empresa
        bote_historico = (df_pedidos_all['p_cli'] - df_pedidos_all['p_boo'] - df_pedidos_all['g_emp']).sum()
    # Ajuste histórico forzoso (Mismo que en main.py)
    neto_historico += 5.0
    bote_historico -= 5.0
    # 2. MOVIMIENTOS DE BILLETERA
    df_wallet = run_query("SELECT id, fecha, tipo, categoria, monto, descripcion FROM wallet_perez ORDER BY id DESC")
    neto_movimientos = 0.0
    bote_movimientos = 0.0
    if not df_wallet.empty:
        for _, row in df_wallet.iterrows():
            monto = clean_num(row['monto'])
            tipo = str(row['tipo']).strip().upper()
            cat = str(row['categoria']).strip().upper()
            val = monto if tipo == 'INGRESO' else -monto
            if cat == 'NETO': neto_movimientos += val
            elif cat == 'BOTE': bote_movimientos += val
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
            if st.form_submit_button("Registrar Movimiento", use_container_width=True):
                if not desc_tx:
                    st.error("Por favor agrega una descripción.")
                else:
                    conn = get_connection()
                    if conn:
                        try:
                            import time
                            nuevo_id = int(time.time() * 1000) % 2147483647
                            with conn.cursor() as cur:
                                cur.execute("INSERT INTO wallet_perez (id, tipo, categoria, monto, descripcion) VALUES (%s, %s, %s, %s, %s)", 
                                            (nuevo_id, tipo_tx, cat_tx, monto_tx, desc_tx))
                                conn.commit()
                            st.success("✅ Registrado con éxito.")
                            time.sleep(1); st.cache_data.clear(); st.rerun()
                        except Exception as e: 
                            st.error(f"Error: {e}")
                        finally: 
                            conn.close()
    with col_hist:
        st.subheader("📜 Historial de Movimientos")
        if df_wallet.empty:
            st.info("No hay movimientos registrados aún.")
        else:
            df_mostrar = df_wallet.copy()
            df_mostrar['fecha_dt'] = pd.to_datetime(df_mostrar['fecha'])
            df_mostrar['mes_str'] = df_mostrar['fecha_dt'].dt.month.map(MESES_DICT) + " " + df_mostrar['fecha_dt'].dt.year.astype(str)
            opciones_filtro = ["Todos"] + df_mostrar['mes_str'].unique().tolist()
            mes_actual_str = MESES_DICT[ANIO_ACTUAL] + " " + str(ANIO_ACTUAL) if HOY.month == ANIO_ACTUAL else MESES_DICT[MES_ACTUAL_NUM] + " " + str(ANIO_ACTUAL)
            idx_defecto = opciones_filtro.index(mes_actual_str) if mes_actual_str in opciones_filtro else 0
            c_filtro, c_vacio = st.columns([1, 1])
            with c_filtro:
                mes_seleccionado = st.selectbox("📅 Filtrar por mes:", opciones_filtro, index=idx_defecto)
            if mes_seleccionado != "Todos":
                df_filtrado = df_mostrar[df_mostrar['mes_str'] == mes_seleccionado].copy()
            else:
                df_filtrado = df_mostrar.copy()
            df_retiros = df_filtrado[df_filtrado['tipo'] == 'RETIRO']
            retirado_neto = df_retiros[df_retiros['categoria'] == 'NETO']['monto'].astype(float).sum()
            retirado_bote = df_retiros[df_retiros['categoria'] == 'BOTE']['monto'].astype(float).sum()
            total_retirado = retirado_neto + retirado_bote
            st.markdown(f"""
                <div style="background-color: #1a1e23; padding: 15px 20px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px; margin-top: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="text-align: center;">
                            <span style="color: #2ecc71; font-size: 11px; font-weight: bold; display: block; letter-spacing: 1px;">MI NETO</span>
                            <span style="color: white; font-size: 22px; font-weight: bold;">${retirado_neto:.2f}</span>
                        </div>
                        <div style="color: #555; font-size: 20px;">+</div>
                        <div style="text-align: center;">
                            <span style="color: #f1c40f; font-size: 11px; font-weight: bold; display: block; letter-spacing: 1px;">BOTE STAFF</span>
                            <span style="color: white; font-size: 22px; font-weight: bold;">${retirado_bote:.2f}</span>
                        </div>
                        <div style="color: #555; font-size: 20px;">=</div>
                        <div style="text-align: center;">
                            <span style="color: #e74c3c; font-size: 11px; font-weight: bold; display: block; letter-spacing: 1px;">TOTAL RETIRADO</span>
                            <span style="color: #e74c3c; font-size: 24px; font-weight: bold;">${total_retirado:.2f}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
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
                    if st.button("✍️ Editar", use_container_width=True):
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
                        st.cache_data.clear()
                        st.rerun()
