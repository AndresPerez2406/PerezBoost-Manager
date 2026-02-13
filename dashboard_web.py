import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="PerezBoost | Owner's Eye", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #2ecc71; font-weight: bold; }
    .stDataFrame { border: 1px solid #333; border-radius: 5px; }
    hr { margin-top: 10px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state: st.session_state.authenticated = False

def verificar_login():
    if st.session_state.pass_input == st.secrets["ADMIN_PASSWORD"]:
        st.session_state.authenticated = True
    else:
        st.error("❌ Clave incorrecta. Acceso denegado.")

if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 PerezBoost Cloud")
        with st.form("login"):
            st.text_input("Contraseña:", type="password", key="pass_input")
            st.form_submit_button("Entrar", on_click=verificar_login)
    st.stop()

env_prod = Path('.') / '.env'
load_dotenv(dotenv_path=env_prod, override=True)

def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url: return None
    try:
        # Uso de puerto 6543 recomendado para Cloud
        return psycopg2.connect(url, connect_timeout=10)
    except Exception as e:
        st.error(f"⚠️ Error de red: {e}")
        return None

def run_query(query):
    conn = get_connection()
    if conn:
        try:
            with conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            st.error(f"❌ Error en datos: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def clean_num(val):
    if val is None or pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    try: return float(s)
    except: return 0.0

# --- HEADER ---
col_t, col_b = st.columns([8,1])
with col_t:
    st.title("🚀 PerezBoost | Monitor & Analítica")
    st.caption(f"Filtrado por FECHA DE INICIO • {datetime.now().strftime('%d/%m/%Y')}")
with col_b:
    if st.button("Salir"):
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# ==============================================================================
# SECCIÓN 1: KPIs GLOBALES (VISTA RÁPIDA)
# ==============================================================================

mes_actual = datetime.now().strftime("%Y-%m")

df_activos = run_query("SELECT count(*) as total FROM pedidos WHERE estado NOT IN ('Terminado', 'Cancelado', 'Pagado', 'Abandonado')")
df_stock = run_query("SELECT count(*) as total FROM inventario")
df_caja_mes = run_query(f"SELECT * FROM pedidos WHERE estado='Terminado' AND CAST(fecha_inicio AS TEXT) LIKE '{mes_actual}%'")

neto_caja = 0.0
for _, r in df_caja_mes.iterrows():
    p_cli = clean_num(r.get('pago_cliente'))
    p_boo = clean_num(r.get('pago_booster'))
    wr = clean_num(r.get('wr'))
    bote = 2.0 if wr >= 60 else 1.0
    neto_caja += (p_cli - p_boo - bote)

if datetime.now().month == 1: neto_caja += 5.0

activos_val = df_activos['total'].iloc[0] if not df_activos.empty else 0
stock_val = df_stock['total'].iloc[0] if not df_stock.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("📦 Activos", activos_val, delta="En curso")
k2.metric("🧊 Stock", stock_val, delta="Cuentas")
k3.metric("💰 Neto Mes", f"${neto_caja:,.2f}", delta="Caja actual")
k4.metric("🕒 Actualizado", datetime.now().strftime("%H:%M"))

st.divider()

# ==============================================================================
# SECCIÓN 2: REPORTES DETALLADOS (FILTRADOS)
# ==============================================================================

st.subheader("📊 Analítica de Pedidos (Filtrado Dinámico)")

f_col1, f_col2, f_col3 = st.columns([2, 2, 1])
meses_nombres = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with f_col1:
    mes_sel = st.selectbox("📅 Mes de Inicio", meses_nombres, index=0)

df_boosters = run_query("SELECT DISTINCT booster_nombre FROM pedidos")
lista_boosters = ["Todos"] + sorted(df_boosters['booster_nombre'].dropna().tolist()) if not df_boosters.empty else ["Todos"]

with f_col2:
    booster_sel = st.selectbox("👤 Filtrar Staff", lista_boosters)

with f_col3:
    st.write("") 
    btn_calc = st.button("🔄 Refrescar", type="primary", use_container_width=True)

query_base = "SELECT * FROM pedidos WHERE estado = 'Terminado'"
if mes_sel != "Todos":
    idx = meses_nombres.index(mes_sel)
    anio = datetime.now().year
    query_base += f" AND CAST(fecha_inicio AS TEXT) LIKE '{anio}-{str(idx).zfill(2)}%'"
if booster_sel != "Todos":
    query_base += f" AND booster_nombre = '{booster_sel}'"

df_rep = run_query(query_base)

if df_rep.empty:
    st.info("No hay registros terminados para este filtro.")
else:
    reporte_data = []
    t_staff, t_neto, t_bote, t_ventas, dias_acum, conteo = 0.0, 0.0, 0.0, 0.0, 0, 0

    for _, row in df_rep.iterrows():
        conteo += 1
        p_cli = clean_num(row.get('pago_cliente'))
        p_boo = clean_num(row.get('pago_booster')) 
        wr = clean_num(row.get('wr'))

        try:
            fi = datetime.strptime(str(row.get('fecha_inicio')).split(' ')[0], "%Y-%m-%d")
            ff = datetime.strptime(str(row.get('fecha_fin_real')).split(' ')[0], "%Y-%m-%d")
            d = (ff - fi).days
            dias = d if d > 0 else 1 
        except: dias = 1
        dias_acum += dias

        bote = 2.0 if wr >= 60 else 1.0
        neto_real = p_cli - p_boo - bote
        
        t_staff += p_boo
        t_neto += neto_real
        t_bote += bote
        t_ventas += p_cli
        
        reporte_data.append({
            "#": conteo,
            "Inicio": str(row.get('fecha_inicio')).split(' ')[0], 
            "Staff": row.get('booster_nombre'),
            "Elo Final": row.get('elo_final'),
            "Días": dias,
            "Pago Staff": p_boo,
            "Mi Neto": neto_real,
            "Bote": bote,
            "Total Cli": p_cli,
            "WR": wr
        })
        
    if mes_sel == "Todos" or mes_sel == "Enero":
        t_bote -= 5.0
        t_neto += 5.0
        
    prom_dias = dias_acum / conteo if conteo > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📦 Entregas", f"{conteo} Und", delta="Volumen")
    c2.metric("Pago Staff", f"${t_staff:,.2f}")
    c3.metric("MI NETO", f"${t_neto:,.2f}", delta="Limpio", delta_color="normal")
    c4.metric("Bote", f"${t_bote:,.2f}", delta="Fondo")
    c5.metric("Prom. Días", f"{prom_dias:.1f} d")
    
    st.markdown("---")

    gc, tc = st.columns([1, 2])
    with gc:
        fig = go.Figure(data=[go.Pie(labels=['Staff', 'Neto', 'Bote'], values=[t_staff, t_neto, t_bote], hole=.4)])
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        
    with tc:
        df_visual = pd.DataFrame(reporte_data).sort_values(by="#", ascending=True)
        st.dataframe(
            df_visual,
            column_config={
                "#": st.column_config.NumberColumn(width="small"),
                "Pago Staff": st.column_config.NumberColumn(format="$%.2f"),
                "Mi Neto": st.column_config.NumberColumn(format="$%.2f"),
                "Bote": st.column_config.NumberColumn(format="$%.2f"),
                "Total Cli": st.column_config.NumberColumn(format="$%.2f"),
                "WR": st.column_config.NumberColumn(format="%.1f%%"),
            },
            use_container_width=True,
            hide_index=True,
            height=350
        )
        csv = df_visual.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte", data=csv, file_name=f"Reporte_{mes_sel}.csv", mime='text/csv')