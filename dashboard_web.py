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
    
    /* Centrar tablas nativas (Anomalías y Ranking) */
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
# 1. CONEXIÓN A LA BASE DE DATOS (Movido arriba para el Booster)
# ==============================================================================

load_dotenv(override=True)

def get_connection():
    url = os.getenv("DATABASE_URL")
    try: return psycopg2.connect(url, connect_timeout=10)
    except: return None

def run_query(query):
    conn = get_connection()
    if conn:
        try:
            with conn: return pd.read_sql(query, conn)
        except: return pd.DataFrame()
        finally: conn.close()
    return pd.DataFrame()

# ==============================================================================
# 2. ENRUTAMIENTO: MODO BOOSTER (Detectado por URL)
# ==============================================================================
query_params = st.query_params
if "pedido" in query_params:
    id_pedido = query_params["pedido"]
    df_info = run_query(f"SELECT booster_nombre, user_pass FROM pedidos WHERE id = {id_pedido}")
    
    if df_info.empty:
        st.error("❌ Pedido no encontrado o ID inválido.")
        st.stop()
        
    booster_asignado = df_info.iloc[0]['booster_nombre']
    user_pass_asignado = df_info.iloc[0]['user_pass']
    
    st.title("🎮 Enlace de Cuenta")
    st.info(f"**Asignado a:** {booster_asignado}")
    st.write("**Credenciales asignadas:**")
    st.code(user_pass_asignado, language="text")
    
    with st.form("form_booster"):
        st.write("Por favor, ingresa el enlace directo del perfil OP.GG:")
        opgg_input = st.text_input("🔗 Link OP.GG:", placeholder="https://www.op.gg/summoners/...")
        submit = st.form_submit_button("Guardar Link")
        
        if submit:
            if opgg_input.strip() == "" or not opgg_input.startswith("http"):
                st.error("❌ Por favor ingresa un enlace válido (debe empezar con http:// o https://).")
            else:
                conn = get_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE pedidos SET opgg = %s WHERE id = %s", (opgg_input, id_pedido))
                            conn.commit()
                        st.success("✅ ¡Guardado exitosamente! Ya puedes cerrar esta ventana y empezar a jugar.")
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Error de conexión a la base de datos.")
    
    st.stop()
# ==============================================================================
# 3. AUTENTICACIÓN ADMIN (Tu login normal)
# ==============================================================================

if 'authenticated' not in st.session_state: st.session_state.authenticated = False

def verificar_login():
    if st.session_state.pass_input == st.secrets["ADMIN_PASSWORD"]:
        st.session_state.authenticated = True
    else:
        st.error("❌ Clave incorrecta.")

if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 PerezBoost Cloud")
        with st.form("login"):
            st.text_input("Contraseña:", type="password", key="pass_input")
            st.form_submit_button("Entrar", on_click=verificar_login)
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
    if st.button("Salir"):
        st.session_state.authenticated = False
        st.rerun()

tab_reportes, tab_inventario, tab_ranking, tab_tracking = st.tabs(["📊 REPORTES", "📦 INVENTARIO", "🏆 TOP STAFF", "🔍 TRACKING"])

# ==============================================================================
# TAB 1: REPORTES
# ==============================================================================

with tab_reportes:
    f1, f2, f3 = st.columns([2, 2, 1])
    meses_nombres = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    with f1: mes_sel = st.selectbox("📅 Mes", meses_nombres)
    with f2: 
        df_boosters = run_query("SELECT DISTINCT booster_nombre FROM pedidos")
        booster_sel = st.selectbox("👤 Staff", ["Todos"] + sorted(df_boosters['booster_nombre'].dropna().tolist()) if not df_boosters.empty else ["Todos"])
    with f3:
        st.write("")
        if st.button("🔄 Refrescar"): st.rerun()

    query_base = "SELECT * FROM pedidos WHERE estado = 'Terminado'"
    if mes_sel != "Todos":
        query_base += f" AND CAST(fecha_inicio AS TEXT) LIKE '{datetime.now().year}-{str(meses_nombres.index(mes_sel)).zfill(2)}%'"
    if booster_sel != "Todos":
        query_base += f" AND booster_nombre = '{booster_sel}'"

    query_base += " ORDER BY fecha_inicio ASC"
    
    df_rep = run_query(query_base)
    
    if not df_rep.empty:
        t_staff, t_neto, t_bote, conteo = 0.0, 0.0, 0.0, 0
        reporte_data = []
        for i, row in enumerate(df_rep.itertuples(), 1):
            conteo += 1
            p_cli, p_boo, wr = clean_num(row.pago_cliente), clean_num(row.pago_booster), clean_num(row.wr)
            bote = 2.0 if wr >= 60 else 1.0
            neto = p_cli - p_boo - bote
            t_staff += p_boo; t_neto += neto; t_bote += bote
            
            reporte_data.append({
                "#": i, 
                "Fecha": format_fecha_latam(row.fecha_inicio), 
                "Staff": row.booster_nombre, 
                "Neto": f"${format_precio(neto)}", 
                "WR": f"{format_num(wr)}%"
            })
        
        if mes_sel in ["Todos", "Enero"]: 
            t_neto += 5.0
            t_bote -= 5.0

        m1, m2, m3 = st.columns(3)
        m1.metric("📦 Pedidos", f"{conteo}")
        m2.metric("💰 Mi Neto Total", f"${format_precio(t_neto)}")
        m3.metric("🏦 Bote Total", f"${format_precio(t_bote)}")

        gc, tc = st.columns([1, 2])
        with gc:
            fig_pie = go.Figure(data=[go.Pie(labels=['Staff', 'Neto', 'Bote'], values=[t_staff, t_neto, t_bote], hole=.4)])
            fig_pie.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        with tc:
            df_mostrar = pd.DataFrame(reporte_data)
            df_mostrar.set_index("#", inplace=True)

            df_styled = df_mostrar.style.set_properties(**{'text-align': 'center'})
            df_styled = df_styled.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
            st.dataframe(df_styled, height=280, use_container_width=True)
    
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
        if st.button("🔄 Refrescar", key="btn_refresh_track"): st.rerun()
        
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