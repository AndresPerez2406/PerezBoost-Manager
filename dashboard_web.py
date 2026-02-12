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
    if st.session_state.pass_input == "Andres2406.":
        st.session_state.authenticated = True
    else:
        st.error("Clave incorrecta")

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
    if not url:
        st.error("❌ ERROR: No se encontró la variable DATABASE_URL en los Secrets.")
        return None
    try:
        return psycopg2.connect(url)
    except Exception as e:
        st.error(f"❌ ERROR DE CONEXIÓN: {e}")
        return None

def run_query(query):
    conn = get_connection()
    if conn:
        try: 
            df = pd.read_sql(query, conn)
            conn.close() 
            return df
        except Exception as e: 
            st.error(f"❌ ERROR EN CONSULTA: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def clean_num(val):
    if val is None or pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    try: return float(s)
    except: return 0.0

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
# SECCIÓN 1: KPIs EN VIVO
# ==============================================================================
hoy = datetime.now().strftime("%Y-%m-%d")
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

if datetime.now().month == 1:
    neto_caja += 5.0

activos_val = df_activos['total'].iloc[0] if not df_activos.empty else 0
stock_val = df_stock['total'].iloc[0] if not df_stock.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("📦 Activos", activos_val, delta="En curso")
k2.metric("🧊 Stock", stock_val, delta="Cuentas")
k3.metric("💰 Proyección Mes", f"${neto_caja:,.2f}", delta="Iniciados este mes")
k4.metric("📅 Fecha", hoy)

st.divider()

# ==============================================================================
# SECCIÓN 2: REPORTES PRO (Por Fecha Inicio)
# ==============================================================================

st.subheader("📊 Analítica de Pedidos (Según Fecha Inicio)")

f_col1, f_col2, f_col3 = st.columns([2, 2, 1])

meses_nombres = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with f_col1:
    mes_sel = st.selectbox("📅 Filtrar por Mes de INICIO", meses_nombres, index=0)

df_boosters = run_query("SELECT DISTINCT booster_nombre FROM pedidos")
lista_boosters = ["Todos"] + sorted(df_boosters['booster_nombre'].dropna().tolist()) if not df_boosters.empty else ["Todos"]

with f_col2:
    booster_sel = st.selectbox("👤 Filtrar Staff", lista_boosters)
    
with f_col3:
    st.write("") 
    btn_calc = st.button("🔄 Actualizar Datos", type="primary", use_container_width=True)

query_base = "SELECT * FROM pedidos WHERE estado = 'Terminado'"

if mes_sel != "Todos":
    try:
        idx = meses_nombres.index(mes_sel) 
        anio = datetime.now().year
        query_base += f" AND CAST(fecha_inicio AS TEXT) LIKE '{anio}-{str(idx).zfill(2)}%'"
    except: pass
    
if booster_sel != "Todos":
    query_base += f" AND booster_nombre = '{booster_sel}'"

df_rep = run_query(query_base)

if df_rep.empty:
    st.info("No hay pedidos iniciados en este periodo que ya estén terminados.")
else:

    reporte_data = []
    
    t_staff = 0.0
    t_neto = 0.0
    t_bote = 0.0
    t_ventas = 0.0
    dias_acum = 0
    conteo = 0
    
    for _, row in df_rep.iterrows():
        conteo += 1
        p_cli = clean_num(row.get('pago_cliente'))
        p_boo = clean_num(row.get('pago_booster')) 
        wr = clean_num(row.get('wr'))
        
        # Días
        try:
            fi = str(row.get('fecha_inicio')).split(' ')[0]
            ff = str(row.get('fecha_fin_real')).split(' ')[0]
            d1 = datetime.strptime(fi, "%Y-%m-%d")
            d2 = datetime.strptime(ff, "%Y-%m-%d")
            dias = (d2 - d1).days
            dias = dias if dias > 0 else 1 
        except:
            dias = 1
        dias_acum += dias

        bote = 2.0 if wr >= 60 else 1.0
        neto_real = p_cli - p_boo - bote
        
        t_staff += p_boo
        t_neto += neto_real
        t_bote += bote
        t_ventas += p_cli
        
        reporte_data.append({
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pago Staff", f"${t_staff:,.2f}")
    c2.metric("MI NETO (Real)", f"${t_neto:,.2f}", delta="Ganancia Limpia")
    c3.metric("Bote Ranking", f"${t_bote:,.2f}", delta="Fondo", delta_color="off")
    c4.metric("Promedio Días", f"{prom_dias:.1f} d")
    
    st.markdown("---")

    gc, tc = st.columns([1, 2])
    
    with gc:
        st.caption("Distribución de Ingresos")
        fig = go.Figure(data=[go.Pie(labels=['Pago Staff', 'Mi Neto', 'Bote'], values=[t_staff, t_neto, t_bote], hole=.4)])
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
    with tc:
        st.caption("Detalle de Pedidos")
        df_visual = pd.DataFrame(reporte_data)

        df_visual = df_visual.sort_values(by="Inicio", ascending=False)
        
        st.dataframe(
            df_visual,
            column_config={
                "Pago Staff": st.column_config.NumberColumn(format="$%.2f"),
                "Mi Neto": st.column_config.NumberColumn(format="$%.2f"),
                "Bote": st.column_config.NumberColumn(format="$%.2f"),
                "Total Cli": st.column_config.NumberColumn(format="$%.2f"),
                "WR": st.column_config.NumberColumn(format="%.1f%%"),
            },
            use_container_width=True,
            hide_index=True,
            height=300
        )
        
        csv = df_visual.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", data=csv, file_name="Reporte_PerezBoost.csv", mime='text/csv')