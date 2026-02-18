import os
import base64
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import customtkinter as ctk
import pandas as pd
import threading
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from core.discord_handler import DiscordNotifier, COLOR_SUCCESS, COLOR_INFO, COLOR_WARNING
from core.cloud_sync import logica_subir_a_nube, logica_bajar_de_nube
from core.database import (
    actualizar_pedido_db, actualizar_booster_db, actualizar_inventario_db,
    agregar_booster, eliminar_booster, obtener_boosters_db,
    realizar_backup_db, obtener_config_precios, actualizar_precio_db,
    agregar_precio_db, eliminar_precio_db, inicializar_db, conectar,
    obtener_conteo_pedidos_activos, obtener_conteo_stock, obtener_ganancia_proyectada,
    finalizar_pedido_db, registrar_abandono_db, obtener_datos_reporte_avanzado,
    obtener_pedidos_activos, crear_pedido, guardar_config_sistema, obtener_config_sistema,
    obtener_kpis_mensuales, registrar_log, obtener_logs_db, obtener_ranking_staff_db,
    obtener_pedidos_mes_actual_db, liquidar_pagos_booster_db, obtener_saldos_pendientes_db,
    obtener_balance_general_db, obtener_historial_completo, obtener_profit_diario_db,
    obtener_total_bote_ranking, obtener_ranking_staff_db, obtener_resumen_mensual_db,
    obtener_resumen_financiero_real
)

from core.logic import (
    calcular_tiempo_transcurrido, calcular_pago_real, calcular_fecha_limite_sugerida
)
from modules.inventario import (
    obtener_inventario_visual, registrar_cuenta_gui, registrar_lote_gui, eliminar_cuenta_gui
)
from modules.pedidos import (
    obtener_elos_en_stock, obtener_cuentas_filtradas_datos
)

# =============================================================================
# CLASE PRINCIPAL: PEREZBOOST APP
# =============================================================================

class PerezBoostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_db()
        version = "V12.0"

        try:
            from core.cloud_sync import MODO_DESARROLLO
        except ImportError:
            MODO_DESARROLLO = True

        if MODO_DESARROLLO:
            env_tag = " [TEST]"
            self.color_status = "#e67e22"
        else:
            env_tag = " [PRODUCCIÓN]"
            self.color_status = "#2ecc71"

        self.title(f"PerezBoost Manager {version}{env_tag}")

        self.geometry("1240x750")
        ctk.set_appearance_mode("dark")
        self.centrar_ventana(self, 1240, 750)

        self.menu_contextual = None
        self.tabla_inv = None
        self.tabla_pedidos = None
        self.tabla_boosters = None
        self.tabla_precios = None
        self.tabla_historial = None
        self.tabla_rep = None

        self.datos_inventario = []
        self.map_c_id = {}
        self.map_c_note = {}

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🚀 PEREZBOOST", 
                                     font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=30)

        self.crear_boton_menu("🏠 Dashboard", self.mostrar_dashboard, 1)
        self.crear_boton_menu("⚙️ Tarifas", self.mostrar_precios, 2)
        self.crear_boton_menu("👥 Boosters", self.mostrar_boosters, 3)
        self.crear_boton_menu("🏆 Ranking Staff", self.mostrar_leaderboard, 4)
        self.crear_boton_menu("📦 Inventario", self.mostrar_inventario, 5)
        self.crear_boton_menu("📜 Pedidos Activos", self.mostrar_pedidos, 6)
        self.crear_boton_menu("💰 Finanzas", self.mostrar_finanzas, 7)
        self.crear_boton_menu("📊 Historial", self.mostrar_historial, 8)
        self.crear_boton_menu("📈 Reportes Pro", self.mostrar_reportes, 9)

        self.content_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212")
        self.content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.configurar_menus()
        self.mostrar_dashboard()

    # =========================================================================
    # 1. UTILIDADES Y CONFIGURACIÓN UI
    # =========================================================================

    def limpiar_pantalla(self):
        """Elimina widgets y resetea referencias para evitar errores de 'command name'"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.tabla_pedidos = None
        self.tabla_historial = None
        self.tabla_inv = None
        self.tabla_boosters = None
        self.tabla_precios = None
        self.tabla_rep = None

    def centrar_ventana(self, ventana, ancho, alto):
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana.winfo_screenheight() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    def crear_boton_menu(self, texto, comando, fila):
        boton = ctk.CTkButton(self.sidebar_frame, text=texto, command=comando, corner_radius=10, height=40, fg_color="#2b2b2b", hover_color="#3d3d3d")
        boton.grid(row=fila, column=0, padx=20, pady=10, sticky="ew")

    def configurar_menus(self):
        self.menu_contextual = tk.Menu(self, tearoff=0, bg="#1a1a1a", fg="white", activebackground="#1f538d", font=("Segoe UI", 10))
        self.menu_contextual.add_command(label="📋 Copiar Info (Booster)", command=self.copiar_info_booster)
        self.menu_contextual.add_command(label="✅ Finalizar Pedido", command=self.abrir_ventana_finalizar)
        self.menu_contextual.add_command(label="📝 Editar Información", command=self.abrir_ventana_editar_pedido)
        self.menu_contextual.add_command(label="⏳ Extender Tiempo", command=self.abrir_ventana_extender_tiempo)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="🚫 Reportar Abandono", command=self.abrir_ventana_reportar_abandono)

    def lanzar_menu_contextual(self, event):
       
        if self.tabla_pedidos:
            item_id = self.tabla_pedidos.identify_row(event.y)
            if item_id:
                self.tabla_pedidos.selection_set(item_id)
                self.menu_contextual.post(event.x_root, event.y_root)

    def configurar_estilo_tabla(self):
        """Configura SOLAMENTE el estilo general, sin tocar instancias específicas."""
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview", background="#1e1e1e", foreground="white", fieldbackground="#1e1e1e", borderwidth=0, font=("Segoe UI", 10), rowheight=35)
        
        style.configure("Treeview.Heading", background="#333333", foreground="white", relief="flat", font=("Segoe UI", 11, "bold"))
        
        style.map("Treeview", background=[('selected', '#1f538d')])

    def copiar_info_booster(self):

        if not self.tabla_pedidos: return
        sel = self.tabla_pedidos.selection()
        if not sel: return

        item_id = sel[0]
        val = self.tabla_pedidos.item(item_id)['values']

        id_pedido = str(val[1]) 
        cuenta = val[4] 
        fecha_raw = str(val[6])

        token_raw = f"PB-{id_pedido}".encode('utf-8')
        token_seguro = base64.urlsafe_b64encode(token_raw).decode('utf-8')

        fecha_bonita = fecha_raw
        try:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

            fecha_limpia = fecha_raw.split(' ')[0]

            dt = None
            if "-" in fecha_limpia:
                dt = datetime.strptime(fecha_limpia, "%Y-%m-%d")
            elif "/" in fecha_limpia:
                dt = datetime.strptime(fecha_limpia, "%d/%m/%Y")
            
            if dt:
                fecha_bonita = f"{dt.day} {meses[dt.month - 1]}"
                
        except Exception as e:
            print(f"Error formateando fecha: {e}")

        URL_DASHBOARD = "https://perezboost-manager.streamlit.app"
        texto_final = f"{cuenta} - Límite: {fecha_bonita} - {URL_DASHBOARD}/?t={token_seguro}"

        self.clipboard_clear()
        self.clipboard_append(texto_final)
        self.update() 

        print(f"✅ Copiado exitoso: {texto_final}")
        
    # =========================================================================
    # 2. SECCIÓN: DASHBOARD
    # =========================================================================

    def mostrar_dashboard(self):
        self.limpiar_pantalla()

        n_pedidos = obtener_conteo_pedidos_activos()
        n_stock = obtener_conteo_stock()
        proyeccion = obtener_ganancia_proyectada()

        profit_neto_hoy = obtener_profit_diario_db()

        ganancia_mes, terminados_mes = obtener_kpis_mensuales()
        criticos, proximos = self.calcular_resumen_emergencias()
        stats_completa = obtener_resumen_mensual_db()
        eficiencia_real = stats_completa[4]

        main_wrapper = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_wrapper.pack(expand=True, fill="both")
        container = ctk.CTkFrame(main_wrapper, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center") 

        ctk.CTkLabel(container, text=f"PANEL DE CONTROL - {datetime.now().strftime('%B').upper()}", 
                     font=("Arial", 26, "bold")).pack(pady=(0, 25))

        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(pady=10)

        col_stock = "#e74c3c" if n_stock == 0 else ("#f1c40f" if n_stock < 5 else "#2ecc71")
        
        self.crear_card(cards_frame, "📦 STOCK", f"{n_stock}", col_stock, 0, 0)
        self.crear_card(cards_frame, "⚔️ EN PROGRESO", f"{n_pedidos}", "#3498db", 0, 1)
        self.crear_card(cards_frame, "✅ TERMINADOS", f"{terminados_mes}", "#9b59b6", 0, 2)

        self.crear_card(cards_frame, "💵 PROFIT HOY", f"${profit_neto_hoy:,.2f}", "#27ae60", 1, 0)
        self.crear_card(cards_frame, "💰 PROYECCIÓN", f"${proyeccion:,.2f}", "#00b894", 1, 1) 
        self.crear_card(cards_frame, "⚡ EFICIENCIA", f"{eficiencia_real:.1f} d", "#e67e22", 1, 2)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=40)
        ctk.CTkButton(btn_frame, text="📊 Ver Reporte Detallado", command=self.abrir_reporte_diario,
                      fg_color="#2c3e50", height=45, width=200).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔄 Actualizar", command=self.mostrar_dashboard,
                      fg_color="#1f538d", height=45, width=200).pack(side="left", padx=10)

    def abrir_reporte_diario(self):
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        conn = conectar()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, booster_nombre, user_pass, elo_inicial, elo_final, wr,
                       fecha_inicio, fecha_fin_real,
                       pago_cliente, pago_booster, ganancia_empresa 
                FROM pedidos 
                WHERE estado = 'Terminado' AND DATE(fecha_fin_real) = DATE(?)
                ORDER BY fecha_fin_real ASC
            """, (hoy_str,))
            
            pedidos_hoy = cursor.fetchall()
            sum_ventas = 0.0; sum_staff = 0.0; sum_profit_db = 0.0
            total_bote_ranking = 0.0    
            
            reporte = f"📊 REPORTE DE CIERRE DIARIO\n📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            if not pedidos_hoy:
                reporte += "       (No se registraron cierres hoy)\n"
            
            def clean_f(val):
                try: return float(str(val).replace('$', '').replace(',', '').strip())
                except: return 0.0

            for i, p in enumerate(pedidos_hoy, start=1):
                p_id, staff, cuenta, e_ini, e_fin, wr, f_ini, f_fin, cobro, pago, ganancia = p
                
                v_cobro = clean_f(cobro)
                v_pago = clean_f(pago)
                v_ganancia = clean_f(ganancia)

                try: wr_val = float(wr) 
                except: wr_val = 0.0

                bote_visual = 2.0 if wr_val >= 60 else 1.0
                
                sum_ventas += v_cobro
                sum_staff += v_pago
                sum_profit_db += v_ganancia
                total_bote_ranking += bote_visual

                reporte += f"📦 ORDEN #{i} | {str(staff).upper()}\n"
                reporte += f"   ├─ 🎮 {e_ini} ➔ {e_fin} ({wr_val}% WR)\n"
                reporte += f"   └─ 💰 Margen: +${v_ganancia:.2f} (Bote: ${bote_visual:.2f})\n" 
                reporte += f"────────────────────────────────────\n"

            reporte += (
                f"\n💵 BALANCE FINAL:\n"
                f"   VENTAS BRUTAS:    ${sum_ventas:,.2f}\n"
                f"   PAGO STAFF:      -${sum_staff:,.2f}\n"
                f"   BOTE RANKING:    -${total_bote_ranking:,.2f}\n"
                f"   --------------------------------\n"
                f"   ✅ PROFIT NETO:   ${sum_profit_db:,.2f}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

            v = ctk.CTkToplevel(self)
            v.title("Reporte Ejecutivo")

            self.centrar_ventana(v, 500, 650)

            v.attributes("-topmost", True)  
            v.focus_force()                 
            v.grab_set()                    

            txt_area = ctk.CTkTextbox(v, width=460, height=500, font=("Consolas", 12))
            txt_area.insert("0.0", reporte)
            txt_area.pack(pady=20)
            txt_area.configure(state="disabled")

            ctk.CTkButton(v, text="📋 Copiar", fg_color="#2ecc71", 
                          command=lambda: [self.clipboard_clear(), self.clipboard_append(reporte), 
                                           messagebox.showinfo("Listo", "Copiado")]).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
        finally: 
            conn.close()
            
    def crear_card(self, master, titulo, valor, color, fila, columna):
        
        card = ctk.CTkFrame(master, corner_radius=15, fg_color="#1a1a1a", 
                            border_width=2, border_color=color, width=260, height=140)
        card.grid(row=fila, column=columna, padx=15, pady=15)
        

        card.grid_propagate(False)

        inner_frame = ctk.CTkFrame(card, fg_color="transparent")
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner_frame, text=titulo, font=("Arial", 12, "bold"), text_color=color).pack(pady=(0, 5))
        ctk.CTkLabel(inner_frame, text=valor, font=("Arial", 28, "bold")).pack()
        
    def calcular_resumen_emergencias(self):
        
        criticos = 0
        proximos = 0
        hoy = datetime.now().date()
        
        try:
            pedidos = obtener_pedidos_activos()
            for p in pedidos:
                try:
                    fecha_str = str(p[5]).split(' ')[0].strip()
                    fecha_entrega = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    dias_diferencia = (fecha_entrega - hoy).days
                    
                    if dias_diferencia <= 1:
                        criticos += 1
                    elif dias_diferencia <= 3:
                        proximos += 1
                except:
                    continue
        except Exception as e:
            print(f"Error calculando resumen: {e}")
            
        return criticos, proximos

    # =========================================================================
    # 3. SECCIÓN: TARIFAS Y CONFIGURACIÓN NUBE
    # =========================================================================

    def mostrar_precios(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()

        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=15, padx=30, fill="x")
        ctk.CTkLabel(header, text="⚙️ CONFIGURACIÓN DE SISTEMA", font=("Arial", 20, "bold")).pack(side="left")

        cols = ("div", "p_cli", "m_per", "p_boo", "pts")
        self.tabla_precios = ttk.Treeview(self.content_frame, columns=cols, show="headings", height=6)

        headers = ["DIVISIÓN", "PRECIO CLIENTE", "MARGEN PEREZ", "PAGO BOOSTER", "PUNTOS RANK"]
        for col, h in zip(cols, headers):
            self.tabla_precios.heading(col, text=h)
            ancho = 100 if col == "pts" else 150
            self.tabla_precios.column(col, anchor="center", width=ancho)

        self.tabla_precios.pack(padx=30, pady=10, fill="x") 
        self.actualizar_tabla_precios()

        footer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        footer.pack(pady=(5, 10), padx=30, fill="x")
        
        ctk.CTkButton(footer, text="+ Nueva Tarifa", fg_color="#2ecc71", width=110,
                      command=self.abrir_ventana_nuevo_precio).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="📝 Editar", fg_color="#f39c12", width=100,
                      command=self.abrir_ventana_editar_precio).pack(side="left", padx=5)
        
        ctk.CTkFrame(footer, width=20, height=1, fg_color="transparent").pack(side="left") 
        
        ctk.CTkButton(footer, text="💾 Backup Local", fg_color="#1f538d", width=110,
                      command=self.ejecutar_backup_manual).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="🕵️ Auditoría", fg_color="#34495e", hover_color="#2c3e50", width=110,
                      command=self.abrir_visor_logs).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="🗑️ Eliminar", fg_color="#e74c3c", width=100,
                      command=self.eliminar_precio_seleccionado).pack(side="right")

        ctk.CTkFrame(self.content_frame, height=2, fg_color="#333333").pack(fill="x", padx=30, pady=10)

        frame_discord = ctk.CTkFrame(self.content_frame, fg_color="#1a1a1a", corner_radius=10)
        frame_discord.pack(fill="x", padx=30, pady=5)
        
        ctk.CTkLabel(frame_discord, text="🤖 CONECTIVIDAD DISCORD", font=("Arial", 14, "bold"), text_color="#5865F2").pack(anchor="w", padx=15, pady=(10,5))

        row1 = ctk.CTkFrame(frame_discord, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row1, text="🔔 Canal Pedidos/Log:", width=150, anchor="w").pack(side="left")
        self.entry_webhook = ctk.CTkEntry(row1, width=400, placeholder_text="Webhook General...")
        self.entry_webhook.pack(side="left", fill="x", expand=True, padx=5)

        row2 = ctk.CTkFrame(frame_discord, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row2, text="🏆 Canal Ranking:", width=150, anchor="w").pack(side="left")
        self.entry_webhook_rank = ctk.CTkEntry(row2, width=400, placeholder_text="Webhook Ranking...")
        self.entry_webhook_rank.pack(side="left", fill="x", expand=True, padx=5)

        url_pedidos = obtener_config_sistema("discord_webhook")
        url_ranking = obtener_config_sistema("discord_webhook_ranking")
        if url_pedidos: self.entry_webhook.insert(0, url_pedidos)
        if url_ranking: self.entry_webhook_rank.insert(0, url_ranking)
        
        ctk.CTkButton(frame_discord, text="Guardar Webhooks", width=150, height=30, fg_color="#404eed", 
                      command=self.guardar_webhooks_discord).pack(pady=10)

        frame_cloud = ctk.CTkFrame(self.content_frame, fg_color="#2d2042", corner_radius=10) 
        frame_cloud.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(frame_cloud, text="☁️ SINCRONIZACIÓN NUBE", font=("Arial", 14, "bold"), text_color="#a29bfe").pack(anchor="w", padx=15, pady=(10,5))

        btns_cloud = ctk.CTkFrame(frame_cloud, fg_color="transparent")
        btns_cloud.pack(pady=10)

        btn_subir = ctk.CTkButton(
            btns_cloud, 
            text="⬆️ SUBIR a Nube\n(Backup)", 
            fg_color="#8e44ad", hover_color="#9b59b6", 
            width=160, height=50,
            font=("Arial", 12, "bold"),
            command=self.accion_subir_nube 
        )
        btn_subir.pack(side="left", padx=20)

        btn_bajar = ctk.CTkButton(
            btns_cloud, 
            text="⬇️ BAJAR de Nube\n(Restore)", 
            fg_color="#e67e22", hover_color="#d35400", 
            width=160, height=50,
            font=("Arial", 12, "bold"),
            command=self.accion_bajar_nube 
        )
        btn_bajar.pack(side="left", padx=20)

        ctk.CTkLabel(frame_cloud, text="Nota: 'Subir' guarda tu PC en la nube. 'Bajar' trae la nube a tu PC (sobrescribe local).", font=("Arial", 10, "italic"), text_color="gray").pack(pady=(0,10))
    def guardar_webhooks_discord(self):
        url_pedidos = self.entry_webhook.get().strip()
        url_ranking = self.entry_webhook_rank.get().strip()

        g1 = guardar_config_sistema("discord_webhook", url_pedidos)
        g2 = guardar_config_sistema("discord_webhook_ranking", url_ranking)
        
        if g1 and g2:
            messagebox.showinfo("Discord", "✅ Ambas conexiones guardadas exitosamente.")
        else:
            messagebox.showerror("Error", "Hubo un problema guardando la configuración.")

    def actualizar_tabla_precios(self):
        for item in self.tabla_precios.get_children():
            self.tabla_precios.delete(item)

        tarifas = obtener_config_precios()
        
        for t in tarifas:
            div, p_cli, m_per, pts = t
            p_boo = p_cli - m_per
            self.tabla_precios.insert("", "end", values=(
                div,
                f"${p_cli:,.2f}",
                f"${m_per:,.2f}",
                f"${p_boo:,.2f}",
                pts
            ))
            
    def accion_subir_nube(self):
        self.win = ctk.CTkToplevel(self); self.centrar_ventana(self.win, 300, 150); self.win.attributes("-topmost", True)
        ctk.CTkLabel(self.win, text="🚀 Subiendo a la Nube...", font=("Arial", 14)).pack(pady=20)
        bar = ctk.CTkProgressBar(self.win, mode="indeterminate"); bar.pack(pady=10); bar.start()
        
        def fin(): self.win.destroy(); messagebox.showinfo("Nube", "✅ Datos subidos correctamente.")
        def err(e): self.win.destroy(); messagebox.showerror("Error", f"Fallo: {e}")
        threading.Thread(target=logica_subir_a_nube, args=(fin, err)).start()

    def accion_bajar_nube(self):
        if not messagebox.askyesno("Confirmar", "⚠️ ¿Borrar datos locales y traer los de la Nube?"): return
        self.win = ctk.CTkToplevel(self); self.centrar_ventana(self.win, 300, 150); self.win.attributes("-topmost", True)
        ctk.CTkLabel(self.win, text="⬇️ Sincronizando con la Nube...", font=("Arial", 14)).pack(pady=20)
        bar = ctk.CTkProgressBar(self.win, mode="indeterminate"); bar.pack(pady=10); bar.start()

        def fin(): self.win.destroy(); messagebox.showinfo("Nube", "✅ Datos descargados."); self.mostrar_dashboard()
        def err(e): self.win.destroy(); messagebox.showerror("Error", f"Fallo: {e}")
        threading.Thread(target=logica_bajar_de_nube, args=(fin, err)).start()
        
    # =========================================================================
    # 4. SECCIÓN: BOOSTERS (STAFF)
    # =========================================================================

    def mostrar_boosters(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=(15, 5), padx=30, fill="x")
        ctk.CTkLabel(header, text="👥 GESTIÓN DE STAFF", font=("Arial", 20, "bold")).pack(side="left")
        
        self.entry_busqueda_b = ctk.CTkEntry(header, placeholder_text="Nombre del Booster...", width=200)
        self.entry_busqueda_b.pack(side="right")
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_boosters).pack(side="right", padx=5)

        cols = ("id_v", "id_r", "nombre")
        self.tabla_boosters = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        self.tabla_boosters.heading("id_v", text="#")
        self.tabla_boosters.heading("nombre", text="NOMBRE DEL STAFF")
        self.tabla_boosters.column("id_v", width=60, anchor="center", stretch=False)
        self.tabla_boosters.column("id_r", width=0, stretch=tk.NO) 
        self.tabla_boosters.column("nombre", width=600, anchor="center") 

        self.tabla_boosters.pack(padx=30, pady=10, fill="both", expand=True)
        self.filtrar_boosters()

        footer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        footer.pack(pady=(5, 20), padx=30, fill="x")
        ctk.CTkButton(footer, text="+ Nuevo Booster", fg_color="#2ecc71", command=self.abrir_ventana_booster).pack(side="left")
        ctk.CTkButton(footer, text="📝 Editar", fg_color="#f39c12", command=self.abrir_ventana_editar_booster).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="🗑️ Despedir", fg_color="#e74c3c", command=self.eliminar_booster_seleccionado).pack(side="right")

    def filtrar_boosters(self):
        query = self.entry_busqueda_b.get().lower()
        for i in self.tabla_boosters.get_children(): self.tabla_boosters.delete(i)
        for i, b in enumerate(obtener_boosters_db(), start=1):
            if query == "" or query in b[1].lower():
                self.tabla_boosters.insert("", tk.END, values=(i, b[0], b[1]))

    # =========================================================================
    # 5. SECCIÓN: INVENTARIO (STOCK)
    # =========================================================================

    def mostrar_inventario(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=15, padx=30, fill="x")
        ctk.CTkLabel(header, text="📦 STOCK DISPONIBLE", font=("Arial", 20, "bold")).pack(side="left")
        
        self.entry_busqueda_i = ctk.CTkEntry(header, placeholder_text="Buscar Elo...", width=200)
        self.entry_busqueda_i.pack(side="right")

        self.entry_busqueda_i.bind("<KeyRelease>", lambda event: self.filtrar_inventario())
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_inventario).pack(side="right", padx=5)

        cols = ("id_v", "elo", "user_pass", "desc")
        self.tabla_inv = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        
        headers = ["#", "ELO", "USUARIO / CONTRASEÑA", "NOTAS"]
        anchos = [50, 120, 300, 200]

        for col, txt, ancho in zip(cols, headers, anchos):
            self.tabla_inv.heading(col, text=txt)
            self.tabla_inv.column(col, width=ancho, anchor="center")

        self.tabla_inv.pack(padx=30, pady=10, fill="both", expand=True)
        self.filtrar_inventario()

        footer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        footer.pack(pady=(5, 20), padx=30, fill="x")
        ctk.CTkButton(footer, text="+ Añadir", fg_color="#2ecc71", command=self.abrir_ventana_registro).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="📝 Editar", fg_color="#f39c12", command=self.abrir_ventana_editar_inventario).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="📥 Masivo", fg_color="#3498db", command=self.abrir_ventana_masivo).pack(side="left")
        ctk.CTkButton(footer, text="🗑️ Borrar", fg_color="#e74c3c", command=self.eliminar_seleccionado).pack(side="right")

    def filtrar_inventario(self):
        query = self.entry_busqueda_i.get().lower()
        for i in self.tabla_inv.get_children(): self.tabla_inv.delete(i)
        
        self.datos_inventario = obtener_inventario_visual()
        
        for d in self.datos_inventario:
            if query == "" or query in str(d[3]).lower() or query in str(d[2]).lower():
                self.tabla_inv.insert("", tk.END, values=(d[0], d[3], d[2], d[4]))

    # =========================================================================
    # 6. SECCIÓN: PEDIDOS ACTIVOS
    # =========================================================================

    def mostrar_pedidos(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=(15, 5), padx=30, fill="x")
        ctk.CTkLabel(header, text="⚔️ PEDIDOS ACTIVOS", font=("Arial", 20, "bold")).pack(side="left")
        
        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="Buscar Booster...", width=200)
        self.entry_busqueda.bind("<KeyRelease>", self.filtrar_pedidos)
        self.entry_busqueda.pack(side="right")
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_pedidos).pack(side="right", padx=5)

        cols = ("id_v", "id_r", "booster", "elo", "cuenta", "inicio", "fin", "tiempo") 
        self.tabla_pedidos = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        self.tabla_pedidos.bind("<Button-3>", self.lanzar_menu_contextual)
        
        self.tabla_pedidos.tag_configure('urgente', foreground='#8b0000')
        self.tabla_pedidos.tag_configure('alerta', foreground='#ffa500')
        self.tabla_pedidos.tag_configure('normal', foreground='#2ecc71')
        
        headers = ["#", "ID_R", "STAFF", "ELO", "CUENTA / USER", "INICIO", "FIN", "TIEMPO"]
        anchos = [40, 0, 130, 100, 200, 100, 100, 130]

        for c, h, w in zip(cols, headers, anchos):
            self.tabla_pedidos.heading(c, text=h)
            if c == "id_r":
                self.tabla_pedidos.column(c, width=0, stretch=tk.NO)
            else:
                self.tabla_pedidos.column(c, width=w, anchor="center", stretch=(c == "cuenta"))

        self.tabla_pedidos.pack(padx=30, pady=10, fill="both", expand=True)
        self.filtrar_pedidos()

        footer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        footer.pack(pady=(5, 20), padx=30, fill="x")
        ctk.CTkButton(footer, text="⚡ Nuevo", fg_color="#3498db", command=self.abrir_ventana_nuevo_pedido).pack(side="left")
        ctk.CTkButton(footer, text="⏳ Extender", command=self.abrir_ventana_extender_tiempo).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="📝 Editar", fg_color="#f39c12", command=self.abrir_ventana_editar_pedido).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="✅ Finalizar", fg_color="#2ecc71", command=self.abrir_ventana_finalizar).pack(side="right")
        ctk.CTkButton(footer, text="🚫 Abandono", fg_color="#e74c3c", command=self.abrir_ventana_reportar_abandono).pack(side="right", padx=10)

    def filtrar_pedidos(self, event=None):
        query = self.entry_busqueda.get().lower().strip()
        hoy = datetime.now().date()
        
        if not self.tabla_pedidos: return
        for i in self.tabla_pedidos.get_children(): self.tabla_pedidos.delete(i)
        
        try:
            datos_raw = obtener_pedidos_activos()
            if not datos_raw: return

            for i, p in enumerate(datos_raw, start=1):
                try:
                    def procesar_fecha(txt):
                        txt = str(txt).split(' ')[0].strip()
                        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                            try:
                                return datetime.strptime(txt, fmt).date()
                            except:
                                continue
                        return None

                    dt_inicio = procesar_fecha(p[4])
                    dt_limite = procesar_fecha(p[5])

                    if dt_inicio and dt_limite:
                        dias_activa = (hoy - dt_inicio).days
                        dias_restantes = (dt_limite - hoy).days

                        if dias_restantes < 0: 
                            tag, ico = 'urgente', f"💀 {dias_activa}d"
                        elif dias_restantes <= 1: 
                            tag, ico = 'urgente', f"🔴 {dias_activa}d"
                        elif dias_restantes <= 3: 
                            tag, ico = 'alerta', f"🟡 {dias_activa}d"
                        else: 
                            tag, ico = 'normal', f"🟢 {dias_activa}d"

                        f_ini_v = dt_inicio.strftime("%d/%m/%Y")
                        f_lim_v = dt_limite.strftime("%d/%m/%Y")
                    else:
                        raise ValueError("Formato no reconocido")

                except Exception as e:
                    f_ini_v, f_lim_v, ico, tag = str(p[4]), str(p[5]), "⚪ Error", "normal"

                if query == "" or query in str(p[0]) or query in str(p[1]).lower() or query in str(p[3]).lower():
                    fila = (i, p[0], p[1], p[2], p[3], f_ini_v, f_lim_v, ico)
                    self.tabla_pedidos.insert("", tk.END, values=fila, tags=(tag,))
                    
        except Exception as e:
            print(f"Error en tabla: {e}")

    # =========================================================================
    # 7. SECCIÓN: HISTORIAL
    # =========================================================================

    def mostrar_historial(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()

        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=15, padx=20, fill="x")
        ctk.CTkLabel(header, text="📊 HISTORIAL OPERATIVO", font=("Arial", 20, "bold")).pack(side="left")

        ctk.CTkButton(header, text="⚠️ Ver Abandonos", fg_color="#e74c3c", hover_color="#c0392b",
                      width=120, command=lambda: self.filtrar_historial(solo_abandonos=True)).pack(side="right", padx=10)

        self.entry_busqueda_h = ctk.CTkEntry(header, placeholder_text="Filtrar Staff/Estado...", width=200)
        self.entry_busqueda_h.pack(side="right")
        self.entry_busqueda_h.bind("<KeyRelease>", lambda e: self.filtrar_historial())
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_historial).pack(side="right", padx=5)

        cols = ("id_visual", "booster", "cuenta", "wr", "inicio", "fin", "duracion", "estado_oculto")
        self.tabla_historial = ttk.Treeview(self.content_frame, columns=cols, show="headings")

        anchos = [50, 150, 280, 70, 110, 110, 100, 0] 
        headers = ["#", "STAFF", "CUENTA / ELO FINAL", "WR", "INICIO", "FIN", "DURACIÓN", ""]
        
        for col, head, ancho in zip(cols, headers, anchos):
            self.tabla_historial.heading(col, text=head, command=lambda c=col: self.ordenar_columna(c, False))
            
            if col == "estado_oculto": 
                self.tabla_historial.column(col, width=0, stretch=tk.NO)
            elif col == "id_visual":
                self.tabla_historial.column(col, width=ancho, anchor="center", stretch=tk.NO)
            else: 
                self.tabla_historial.column(col, width=ancho, anchor="center", stretch=(col=="cuenta"))

        self.tabla_historial.tag_configure('terminado', foreground='#2ecc71')
        self.tabla_historial.tag_configure('abandonado', foreground='#e74c3c')
        
        self.tabla_historial.pack(padx=20, pady=10, fill="both", expand=True)

        self.panel_total_h = ctk.CTkFrame(self.content_frame, fg_color="#1a1a1a", corner_radius=10, height=40)
        self.panel_total_h.pack(pady=10, fill="x", padx=20)
        self.panel_total_h.pack_propagate(False)
        self.lbl_totales_h = ctk.CTkLabel(self.panel_total_h, text="", font=("Arial", 14, "bold"), text_color="#7f8c8d")
        self.lbl_totales_h.pack(expand=True)
        
        self.filtrar_historial()
        
    def ordenar_columna(self, col, reverse):
        """Ordena las filas del Treeview al hacer clic en el encabezado"""
        l = [(self.tabla_historial.set(k, col), k) for k in self.tabla_historial.get_children('')]

        try:

            if col in ("inicio", "fin"):
                def convertir_fecha(txt):
                    try:

                        txt = str(txt).split(' ')[0].strip()
                        return datetime.strptime(txt, "%d/%m/%Y")
                    except:
                        return datetime.min
                
                l.sort(key=lambda t: convertir_fecha(t[0]), reverse=reverse)

            elif col == "id_visual":
                 l.sort(key=lambda t: int(t[0]), reverse=reverse)

            else:
                l.sort(reverse=reverse)
        except Exception as e:
            print(f"Error ordenando: {e}")
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tabla_historial.move(k, '', index)
        self.tabla_historial.heading(col, command=lambda: self.ordenar_columna(col, not reverse))
        
    def filtrar_historial(self, solo_abandonos=False):
        query = self.entry_busqueda_h.get().lower()
        if not self.tabla_historial: return

        for item in self.tabla_historial.get_children():
            self.tabla_historial.delete(item)
        
        try:
            datos = obtener_historial_completo()
            contador_visual = 1
            
            for row in datos:

                id_ped_real, booster, user, elo_fin, ini_raw, fin_raw, estado, wr = row
                est_str = str(estado).upper()

                mostrar = False
                if solo_abandonos:
                    if "ABANDONADO" in est_str: mostrar = True
                else:
                    if query == "" or query in str(booster).lower() or query in est_str.lower(): 
                        mostrar = True
                
                if mostrar:

                    def f_v(t):
                        if not t: return "---"
                        t = str(t).split(' ')[0]
                        try: return datetime.strptime(t, "%Y-%m-%d").strftime("%d/%m/%Y")
                        except: return t

                    duracion = "---"

                    try:
                        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                            try:
                                f1 = datetime.strptime(str(ini_raw).split(' ')[0], fmt)
                                f2 = datetime.strptime(str(fin_raw).split(' ')[0], fmt)
                                d = (f2 - f1).days
                                duracion = f"{d} días" if d > 0 else "⚡ Hoy"
                                break
                            except: continue
                    except: pass

                    tag = 'terminado' if "TERMINADO" in est_str else 'abandonado'

                    self.tabla_historial.insert("", "end", values=(
                        contador_visual, 
                        booster, 
                        f"{user} -> {elo_fin}",     
                        f"{wr}%" if wr else "-", 
                        f_v(ini_raw), 
                        f_v(fin_raw), 
                        duracion, 
                        est_str    
                    ), tags=(tag,))
                    
                    contador_visual += 1
            
            self.lbl_totales_h.configure(text=f"MOSTRANDO {len(self.tabla_historial.get_children())} REGISTROS")
            
        except Exception as e:
            print(f"Error en historial: {e}")

    # =========================================================================
    # 8. SECCIÓN: REPORTES AVANZADOS Y GRÁFICOS
    # =========================================================================

    def mostrar_reportes(self):
        self.limpiar_pantalla()
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background="#1a1a1a", foreground="white", relief="flat", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#1f538d")], foreground=[("selected", "white")])

        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(expand=True, fill="both", padx=30, pady=20)

        filtros_frame = ctk.CTkFrame(main_container, fg_color="#1a1a1a", corner_radius=15)
        filtros_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(filtros_frame, text="📊 ANALÍTICA FINANCIERA", font=("Arial", 16, "bold")).pack(side="left", padx=20)
        
        self.combo_mes = ctk.CTkOptionMenu(filtros_frame, width=120,
            values=["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        self.combo_mes.pack(side="left", padx=10)
        
        try:
            boosters = ["Todos"] + [b[1] for b in obtener_boosters_db()]
        except: boosters = ["Todos"]
        self.combo_booster_rep = ctk.CTkOptionMenu(filtros_frame, width=140, values=boosters)
        self.combo_booster_rep.pack(side="left", padx=10)

        ctk.CTkButton(filtros_frame, text="Calcular", width=100, command=self.actualizar_analitica).pack(side="left", padx=10)
        ctk.CTkButton(filtros_frame, text="📥 Exportar Excel", fg_color="#1d6f42", hover_color="#145231",
                      command=self.exportar_excel_avanzado).pack(side="right", padx=20)

        self.graficos_frame = ctk.CTkFrame(main_container, fg_color="#1a1a1a", height=280)
        self.graficos_frame.pack(fill="x", pady=10)
        self.graficos_frame.pack_propagate(False) 

        self.kpi_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=10)

        table_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=10)

        cols = ("#", "booster", "elo", "demora", "pago_b", "ganancia_p", "bote", "total")
        self.tabla_rep = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)

        headers = {
            "#": "N°", 
            "booster": "STAFF", 
            "elo": "ELO FINAL", 
            "demora": "DÍAS", 
            "pago_b": "PAGO STAFF", 
            "ganancia_p": "MI NETO", 
            "bote": "BOTE",           
            "total": "TOTAL CLI"
        }

        anchos = [40, 120, 100, 60, 100, 100, 80, 100]
        
        for c, w in zip(cols, anchos):
            self.tabla_rep.heading(c, text=headers[c])
            self.tabla_rep.column(c, width=w, anchor="center")

        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tabla_rep.yview)
        self.tabla_rep.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tabla_rep.pack(side="left", fill="both", expand=True)

        self.actualizar_analitica()

    def actualizar_analitica(self):

        for widget in self.kpi_frame.winfo_children(): widget.destroy()
        for i in self.tabla_rep.get_children(): self.tabla_rep.delete(i)
        for widget in self.graficos_frame.winfo_children(): widget.destroy()
        
        mes_sel = self.combo_mes.get()
        booster_sel = self.combo_booster_rep.get()
        datos = obtener_datos_reporte_avanzado(self.combo_mes.get(), booster_sel)

        t_staff, t_neto, t_bote, t_ventas = 0.0, 0.0, 0.0, 0.0
        conteo, dias_totales = 0, 0

        def limpiar(v):
            try: return float(str(v).replace('$','').replace(',','').strip()) if v else 0.0
            except: return 0.0

        if not datos:
            ctk.CTkLabel(self.graficos_frame, text="Sin registros").pack(expand=True)
            return

        contador_visual = 1

        for r in datos:
            v_total_cli = limpiar(r[11])
            v_pago_staff = limpiar(r[12])

            txt_dias = "⚡ <24h"
            try:
                f_ini_str = str(r[5]).split(' ')[0] if r[5] else ""
                f_fin_str = str(r[10]).split(' ')[0] if r[10] else ""
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
                            txt_dias = f"{diff} días"
                            dias_totales += diff
            except: txt_dias = "N/A"

            try: wr = float(r[9]) if r[9] else 0.0
            except: wr = 0.0
            valor_bote = 2.0 if wr >= 60 else 1.0
            mi_neto_real = v_total_cli - v_pago_staff - valor_bote

            t_staff += v_pago_staff
            t_neto += mi_neto_real
            t_bote += valor_bote
            t_ventas += v_total_cli
            conteo += 1

            self.tabla_rep.insert("", "end", values=(
                contador_visual, 
                r[2],            
                r[8],            
                txt_dias,        
                f"${v_pago_staff:.2f}", 
                f"${mi_neto_real:.2f}", 
                f"${valor_bote:.2f}", 
                f"${v_total_cli:.2f}"
            ))
            contador_visual += 1

        if mes_sel == "Todos" or mes_sel == "Enero":
            t_bote -= 5.0
            t_neto += 5.0

        prom_dias = dias_totales / conteo if conteo > 0 else 0
        
        self.crear_card_mini(self.kpi_frame, "PAGO STAFF", f"${t_staff:.2f}", "#3498db", 0)
        self.crear_card_mini(self.kpi_frame, "MI NETO", f"${t_neto:.2f}", "#2ecc71", 1)
        self.crear_card_mini(self.kpi_frame, "BOTE RANKING", f"${t_bote:.2f}", "#f1c40f", 2)
        self.crear_card_mini(self.kpi_frame, "VENTAS TOTALES", f"${t_ventas:.2f}", "#9b59b6", 3)
        self.crear_card_mini(self.kpi_frame, "PROM. DÍAS", f"{prom_dias:.1f} d", "#e67e22", 4)

        self.dibujar_grafico_financiero(t_neto, t_staff, t_bote, booster_sel)

    def dibujar_grafico_financiero(self, total_perez, total_staff, total_bote, nombre_filtro):
        plt.close('all')
        plt.rcParams.update({
            'figure.facecolor': '#1a1a1a', 'axes.facecolor': '#1a1a1a',
            'axes.edgecolor': '#444444', 'axes.labelcolor': 'white',
            'xtick.color': 'white', 'ytick.color': 'white', 'text.color': 'white'
        })

        fig, ax = plt.subplots(figsize=(6, 2.8), dpi=100)
        
        label_izquierda = "Staff Total" if nombre_filtro == "Todos" else nombre_filtro

        categorias = [label_izquierda, 'Perez (Neto)', 'Bote Ranking']
        valores = [total_staff, total_perez, total_bote]
        colores = ['#3498db', '#2ecc71', '#f1c40f']

        barras = ax.bar(categorias, valores, color=colores, width=0.5, zorder=3)

        ax.set_title(f'DISTRIBUCIÓN FINANCIERA: {label_izquierda.upper()}', fontsize=11, fontweight='bold', pad=15)
        ax.set_ylabel('USD ($)', fontsize=9, fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)

        for b in barras:
            height = b.get_height()
            if height > 0: 
                ax.annotate(f'${height:,.2f}', 
                            xy=(b.get_x() + b.get_width()/2, height),
                            xytext=(0, 5), textcoords="offset points", 
                            ha='center', va='bottom', weight='bold', fontsize=9, color="white")

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.graficos_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.configure(bg='#1a1a1a', highlightthickness=0)
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()

    def crear_card_mini(self, master, titulo, valor, color, col):
        card = ctk.CTkFrame(master, fg_color="#1a1a1a", border_width=1, border_color=color)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="nsew") 
        master.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(card, text=titulo, font=("Arial", 10, "bold"), text_color=color).pack(pady=(8,0))
        ctk.CTkLabel(card, text=valor, font=("Arial", 16, "bold"), text_color="white").pack(pady=(2,8))

    def exportar_excel_avanzado(self):
        import pandas as pd
        from datetime import datetime
        
        mes = self.combo_mes.get()
        booster = self.combo_booster_rep.get()
        nombre_sugerido = f"Reporte_V10_{mes}_{booster.replace(' ', '_')}.xlsx"
        
        datos = obtener_datos_reporte_avanzado(mes, booster)
        if not datos: 
            messagebox.showwarning("Sin Datos", "No hay datos para exportar.")
            return

        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=nombre_sugerido)
        if not ruta: return

        lista_procesada = []
        for r in datos:
            if str(r[7]).upper() == 'TERMINADO':

                try:
                    if r[5] and r[10]:
                        str_ini = str(r[5])[:10] 
                        str_fin = str(r[10])[:10]
                        try: ini = datetime.strptime(str_ini, "%Y-%m-%d")
                        except: ini = datetime.strptime(str_ini, "%d/%m/%Y")
                        try: fin = datetime.strptime(str_fin, "%Y-%m-%d")
                        except: fin = datetime.strptime(str_fin, "%d/%m/%Y")
                        
                        dias = (fin - ini).days
                        dias = dias if dias > 0 else 1
                    else: dias = 1
                except: dias = 1

                val_staff = float(r[12] or 0)
                val_perez_bruto = float(r[13] or 0)

                val_perez_neto = val_perez_bruto - 1.0
                val_bote = 1.0
                val_total_cliente = val_staff + val_perez_bruto

                lista_procesada.append({
                    "Booster": r[2],
                    "Elo Final": r[8],
                    "WR": f"{r[9]}%",
                    "Días": dias,
                    "PAGO STAFF": val_staff,
                    "GANANCIA NETA": val_perez_neto, 
                    "APORTE BOTE": val_bote,         
                    "TOTAL CLIENTE": val_total_cliente
                })

        if not lista_procesada: 
            messagebox.showinfo("Info", "No hay pedidos terminados para exportar.")
            return
        
        df = pd.DataFrame(lista_procesada)

        totales = df.sum(numeric_only=True)
        row_total = pd.DataFrame([{
            "Booster": "TOTALES >>", "Elo Final": "", "WR": "", "Días": "",
            "PAGO STAFF": totales["PAGO STAFF"],
            "GANANCIA NETA": totales["GANANCIA NETA"],
            "APORTE BOTE": totales["APORTE BOTE"],
            "TOTAL CLIENTE": totales["TOTAL CLIENTE"]
        }])
        df = pd.concat([df, row_total], ignore_index=True) 

        try:
            with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Cierre_Mes', index=False)

                ws = writer.sheets['Cierre_Mes']
                for col in ['E', 'F', 'G', 'H']: 
                    for cell in ws[col]:
                        cell.number_format = '$ #,##0.00'
                
                ws.column_dimensions['A'].width = 20
                ws.column_dimensions['H'].width = 18
            
            messagebox.showinfo("Éxito", "Reporte Excel V10 generado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    # =========================================================================
    # 9. SECCIÓN: LEABOARD
    # =========================================================================
    
    def mostrar_leaderboard(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()

        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_hoy = datetime.now()
        mes_actual_idx = fecha_hoy.month - 1
        anio_actual = fecha_hoy.year

        main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header_frame, text="🏆 HALL OF FAME", font=("Arial", 28, "bold"), text_color="#ecf0f1").pack(side="left")

        self.combo_mes_rank = ctk.CTkOptionMenu(header_frame, values=meses_nombres, width=140, fg_color="#34495e")
        self.combo_mes_rank.set(meses_nombres[mes_actual_idx]) 
        self.combo_mes_rank.pack(side="right")
        ctk.CTkLabel(header_frame, text="📅 Filtrar Mes:", font=("Arial", 14)).pack(side="right", padx=10)

        prize_frame = ctk.CTkFrame(main_frame, fg_color="#2c3e50")
        prize_frame.pack(fill="x", pady=(0, 20), padx=5)
        self.lbl_bote = ctk.CTkLabel(prize_frame, text="...", font=("Arial", 18, "bold"), text_color="#ecf0f1")
        self.lbl_bote.pack(pady=15)

        stats_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", border_width=1, border_color="#5865F2")
        stats_frame.pack(fill="x", pady=(0, 20))
        stats_frame.columnconfigure((0,1,2), weight=1)

        ctk.CTkLabel(stats_frame, text="📦 Pedidos Totales", font=("Arial", 11), text_color="gray").grid(row=0, column=0, pady=(10,0))
        self.lbl_totales = ctk.CTkLabel(stats_frame, text="0", font=("Arial", 16, "bold"), text_color="white")
        self.lbl_totales.grid(row=1, column=0, pady=(0,10))

        ctk.CTkLabel(stats_frame, text="⚡ Eficiencia (Días/Pedido)", font=("Arial", 11), text_color="gray").grid(row=0, column=1, pady=(10,0))
        self.lbl_eficiencia = ctk.CTkLabel(stats_frame, text="0 Días", font=("Arial", 16, "bold"), text_color="#2ecc71")
        self.lbl_eficiencia.grid(row=1, column=1, pady=(0,10))

        ctk.CTkLabel(stats_frame, text="📊 WR Global", font=("Arial", 11), text_color="gray").grid(row=0, column=2, pady=(10,0))
        self.lbl_wr = ctk.CTkLabel(stats_frame, text="0%", font=("Arial", 16, "bold"), text_color="#f1c40f")
        self.lbl_wr.grid(row=1, column=2, pady=(0,10))

        tabla_frame = ctk.CTkFrame(main_frame, fg_color="#1e1e1e", corner_radius=10)
        tabla_frame.pack(expand=True, fill="both", pady=(0, 20))

        cols = ("Rango", "Staff", "Completados", "High_WR", "Abandonos", "Puntaje")
        self.tabla_rank = ttk.Treeview(tabla_frame, columns=cols, show="headings", height=8)

        headers = ["Rango", "Staff", "Terminados", "WR => 60%", "Abandonos", "Puntaje"]
        anchos = [80, 150, 100, 100, 80, 100]

        for col, title, ancho in zip(cols, headers, anchos):
            self.tabla_rank.heading(col, text=title)
            self.tabla_rank.column(col, width=ancho, anchor="center")
        
        self.tabla_rank.pack(side="left", expand=True, fill="both", padx=5, pady=5)
        self.tabla_rank.tag_configure("top1", background="#2d2d2d") 

        def actualizar_datos_ranking(event=None):
            nombre_mes = self.combo_mes_rank.get()
            num_mes = str(meses_nombres.index(nombre_mes) + 1).zfill(2)
            filtro = f"{anio_actual}-{num_mes}"

            for item in self.tabla_rank.get_children(): self.tabla_rank.delete(item)

            try:

                cant_term, cant_aban, wr_prom, cant_high_wr, avg_dias = obtener_resumen_mensual_db(filtro)

                total_pedidos = cant_term

                bote_total = (float(cant_term) * 1.0) + (float(cant_high_wr) * 1.0) 

            except Exception as e:
                print(f"Error calculo stats: {e}")
                cant_term, total_pedidos, avg_dias, wr_prom, cant_high_wr = 0, 0, 0, 0, 0
                bote_total = 0.0

            self.lbl_totales.configure(text=f"{total_pedidos}") 

            if avg_dias > 0 and avg_dias < 1:
                texto_eficiencia = "⚡ < 1 Día"
            else:
                texto_eficiencia = f"{avg_dias:.1f} Días"
            self.lbl_eficiencia.configure(text=texto_eficiencia)

            self.lbl_wr.configure(text=f"{wr_prom:.1f}%")
            
            self.lbl_bote.configure(text=f"💰 BOTE {nombre_mes.upper()}: ${bote_total:.2f} USD 💰\n($1 Pedido + $1 Bono WR)")

            ranking_data = obtener_ranking_staff_db(filtro) 
            
            if not ranking_data:
                self.tabla_rank.insert("", "end", values=("...", "Sin datos...", "-", "-", "-", "0 pts"))
            else:
                for i, b in enumerate(ranking_data, start=1):

                    nombre = b[0]
                    terminados = b[1]
                    aportes_wr = b[2]
                    abandonos = b[3]
                    puntaje = int(b[4])

                    if i == 1: rango = "🥇 MVP"
                    elif i == 2: rango = "🥈"
                    elif i == 3: rango = "🥉"
                    else: rango = f"#{i}"

                    item = self.tabla_rank.insert("", "end", values=(
                        rango, 
                        nombre, 
                        terminados, 
                        f"{aportes_wr}",
                        abandonos, 
                        f"{puntaje} pts"
                    ))
                    
                    if i == 1: self.tabla_rank.item(item, tags=("top1",))

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="🔄 Recargar", command=actualizar_datos_ranking, 
                      fg_color="#1f538d", height=40).pack(side="left", expand=True, padx=10)

        ctk.CTkButton(btn_frame, text="📢 Publicar Ranking", command=self.compartir_ranking_discord, 
                      fg_color="#5865F2", hover_color="#4752C4", height=40).pack(side="left", expand=True, padx=10)

        self.combo_mes_rank.configure(command=actualizar_datos_ranking)

        actualizar_datos_ranking()
    
    def compartir_ranking_discord(self):
        url = obtener_config_sistema("discord_webhook_ranking") 
        if not url: url = obtener_config_sistema("discord_webhook")
        
        if not url:
            messagebox.showerror("Error", "No hay Webhook configurado.")
            return

        mes_nombre = self.combo_mes_rank.get()
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        try:
            num_mes = str(meses_nombres.index(mes_nombre) + 1).zfill(2)
            anio = datetime.now().year
            filtro = f"{anio}-{num_mes}"
        except:
            filtro = datetime.now().strftime("%Y-%m")

        try:
            cant_term, cant_aban, wr_prom, cant_high_wr, avg_dias = obtener_resumen_mensual_db(filtro)

            total_bote = (cant_term * 1.0) + (cant_high_wr * 1.0)
        except:
            cant_term, cant_high_wr, total_bote = 0, 0, 0.0

        ranking = obtener_ranking_staff_db(filtro)
        if not ranking:
            messagebox.showinfo("Vacío", f"No hay datos en {mes_nombre} para publicar.")
            return

        descripcion = f"# 🏆 HALL OF FAME - {mes_nombre.upper()} {anio}\n"
        descripcion += f"## 💰 BOTE ACUMULADO: `${total_bote:.2f} USD` 💰\n"
        descripcion += f"\n\n* ✅ Pedidos Terminados: `{cant_term}` ($1.00 c/u)\n"
        descripcion += f"* 🔥 Bonos High WR (>60%): `{cant_high_wr}` ($1.00 c/u)\n"
        descripcion += "\n**DETALLE POR STAFF:**\n\n"
        
        for i, b in enumerate(ranking[:10], start=1):
            nombre, terminados, high_wr_count, abandonos, puntaje = b[0], b[1], b[2], b[3], b[4]

            if i == 1: icon = "🥇"
            elif i == 2: icon = "🥈"
            elif i == 3: icon = "🥉"
            else: icon = f"#{i}"

            descripcion += f"{icon} **{nombre}** — 🏆 `{int(puntaje)} Pts`\n"
            descripcion += f"   ✅ `{terminados}` Terminados  |  🔥 `{high_wr_count}` High WR  |  ❌ `{abandonos}` Drops\n\n"

        descripcion += "\nEl bote lo gana el primer lugar al final del mes."

        try:
            noti = DiscordNotifier(url)
            noti.enviar_notificacion(
                titulo="",
                descripcion=descripcion,
                color=0xFFD700, 
                campos=[] 
            )
            messagebox.showinfo("Éxito", f"Ranking y Bote de {mes_nombre} publicados.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al enviar: {e}")
            
    # ==========================================
    # 10. GESTIÓN FINANCIERA
    # ==========================================

    def mostrar_finanzas(self):
        self.limpiar_pantalla()

        self.main_scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        header.pack(pady=20, padx=30, fill="x")
        
        ctk.CTkLabel(header, text="📊 DASHBOARD FINANCIERO", font=("Arial", 24, "bold")).pack(side="left")

        meses = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        self.combo_filtro_finanzas = ctk.CTkOptionMenu(
            header, 
            values=meses, 
            width=150,
            command=self.actualizar_tarjetas_finanzas 
        )
        self.combo_filtro_finanzas.set("Todos")
        self.combo_filtro_finanzas.pack(side="right")
        ctk.CTkLabel(header, text="📅 Periodo:", font=("Arial", 12, "bold")).pack(side="right", padx=10)

        self.stats_container = ctk.CTkFrame(self.main_scroll, fg_color="#161616", corner_radius=15)
        self.stats_container.pack(fill="x", padx=30, pady=10)

        self.actualizar_tarjetas_finanzas("Todos")

        ctk.CTkLabel(self.main_scroll, text="👤 PAGOS PENDIENTES POR STAFF (Deuda Actual)", 
                     font=("Arial", 16, "bold")).pack(anchor="w", padx=35, pady=(30, 10))

        self.container_pagos = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.container_pagos.pack(fill="x", padx=30)
        
        self.actualizar_lista_liquidaciones()

    def actualizar_tarjetas_finanzas(self, seleccion):
        """Recalcula el Dashboard Financiero con el ajuste manual de Enero (V10.5)"""
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        filtro_db = None
        if seleccion != "Todos":
            meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            try:
                mes_idx = meses_nombres.index(seleccion) + 1
                anio_actual = datetime.now().year
                filtro_db = f"{anio_actual}-{str(mes_idx).zfill(2)}"
            except:
                filtro_db = None

        resumen = obtener_resumen_mensual_db(filtro_db)
        cant_term = float(resumen[0] or 0)
        cant_high_wr = float(resumen[3] or 0)
        _, total_cli, total_staff, _ = obtener_balance_general_db(filtro_db)

        bote_real = cant_term + cant_high_wr
        utilidad_neta_real = total_cli - total_staff - bote_real

        ## --- 🛠️ AJUSTE MANUAL ENERO Pagos WR (Filtro Todos y Enero) ---
        if seleccion == "Todos" or seleccion == "Enero":
            bote_real -= 5.0
            utilidad_neta_real += 5.0
        # --------------------------------------------------------

        def crear_card(parent, titulo, valor, color):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(side="left", expand=True, pady=25)
            ctk.CTkLabel(f, text=titulo, font=("Arial", 11, "bold"), text_color="gray").pack()
            ctk.CTkLabel(f, text=f"${valor:,.2f}", font=("Arial", 24, "bold"), text_color=color).pack()

        crear_card(self.stats_container, "INGRESOS TOTALES", total_cli, "#9b59b6") 
        crear_card(self.stats_container, "COSTO STAFF", total_staff, "#e74c3c")      
        
        lbl_bote = "BOTE ACUMULADO" if seleccion == "Todos" else f"BOTE {seleccion.upper()}"
        crear_card(self.stats_container, lbl_bote, bote_real, "#f1c40f") 
        
        crear_card(self.stats_container, "MI NETO (Bolsillo)", utilidad_neta_real, "#2ecc71")

    def actualizar_lista_liquidaciones(self):
        for widget in self.container_pagos.winfo_children():
            widget.destroy()
            
        saldos = obtener_saldos_pendientes_db()
        
        if not saldos:
            ctk.CTkLabel(self.container_pagos, text="✨ No hay deudas pendientes. ¡Buen trabajo!", 
                         font=("Arial", 14), text_color="gray").pack(pady=40)
            return

        for booster, total, cant, detalle in saldos:
            card = ctk.CTkFrame(self.container_pagos, fg_color="#1e1e1e", height=85)
            card.pack(fill="x", pady=5)
            card.pack_propagate(False) 

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", padx=20, fill="x", expand=True)
            
            ctk.CTkLabel(info, text=f"{booster}  •  {cant} pedidos", font=("Arial", 14, "bold"), anchor="w").pack(anchor="w")
            
            if detalle and len(detalle) > 60: 
                detalle = detalle[:60] + "..." 
            
            ctk.CTkLabel(info, text=f"📄 {detalle}", font=("Arial", 11), text_color="#aaaaaa", anchor="w").pack(anchor="w")

            ctk.CTkButton(card, text=f"Pagar ${total:,.2f}", width=130, height=35,
                          fg_color="#2ecc71", hover_color="#27ae60", font=("Arial", 12, "bold"),
                          command=lambda b=booster, t=total: self.ejecutar_pago(b, t)).pack(side="right", padx=20)

    def ejecutar_pago(self, booster, total):
        if messagebox.askyesno("Confirmar Liquidación", f"¿Confirmas el pago de ${total:,.2f} a {booster}?\n\nEsta acción marcará {booster} como PAGADO."):
            cant = liquidar_pagos_booster_db(booster)
            registrar_log("PAGO_STAFF", f"Liquidación de ${total:,.2f} a {booster} ({cant} pedidos)")
            messagebox.showinfo("Pago Exitoso", f"Se han liquidado {cant} pedidos de {booster} correctamente.")

            self.mostrar_finanzas()

    # =========================================================================
    # 11. SECCIÓN: POP-UPS (VENTANAS EMERGENTES)
    # =========================================================================

    def abrir_ventana_booster(self):
        v = ctk.CTkToplevel(self); v.title("Nuevo Staff"); self.centrar_ventana(v, 400, 300); v.attributes("-topmost", True)
        entry = ctk.CTkEntry(v, width=250); entry.pack(pady=30)
        def save():
            if entry.get() and agregar_booster(entry.get().strip().title()):
                v.destroy(); self.mostrar_boosters()
        ctk.CTkButton(v, text="Guardar", command=save, fg_color="#2ecc71").pack()

    def abrir_ventana_editar_booster(self):
        sel = self.tabla_boosters.selection()
        if not sel: return
        id_r = self.tabla_boosters.item(sel)['values'][1]
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 350, 250); v.attributes("-topmost", True)
        entry = ctk.CTkEntry(v, width=200); entry.pack(pady=20)
        def save():
            actualizar_booster_db(id_r, entry.get().strip().title()); v.destroy(); self.mostrar_boosters()
        ctk.CTkButton(v, text="Actualizar", fg_color="#27ae60", command=save).pack()

    def eliminar_booster_seleccionado(self):
        sel = self.tabla_boosters.selection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar staff?", parent=self):
            id_r = self.tabla_boosters.item(sel)['values'][1]
            if eliminar_booster(id_r): self.mostrar_boosters()

    def abrir_ventana_editar_pedido(self):
        sel = self.tabla_pedidos.selection()
        if not sel: return

        val = self.tabla_pedidos.item(sel)['values']
        id_r = val[1]
        
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 400, 580); v.attributes("-topmost", True)
        v.title(f"Editar Pedido #{id_r}")
        
        entradas = {}
        campos = [
            ("Staff:", "booster_nombre", val[2]),
            ("Elo Inicial:", "elo_inicial", val[3]),
            ("Cuenta / User:", "user_pass", val[4]), 
            ("Fecha Inicio (D/M/Y):", "fecha_inicio", val[5]),
            ("Fecha Entrega (D/M/Y):", "fecha_limite", val[6])
        ]
        
        for lab, col, act in campos:
            ctk.CTkLabel(v, text=lab, font=("Arial", 12, "bold")).pack(pady=(10, 0))
            e = ctk.CTkEntry(v, width=280)
            e.insert(0, act)
            e.pack(pady=5)
            entradas[col] = e

        def save():
            try:
                datos_nuevos = {}
                for k, e in entradas.items():
                    valor = e.get().strip()

                    if k in ["fecha_inicio", "fecha_limite"]:
                        if "/" in valor:
                            valor = datetime.strptime(valor, "%d/%m/%Y").strftime("%Y-%m-%d")
                        elif "-" in valor and len(valor) >= 10:
                            valor = valor.split(' ')[0]
                    
                    datos_nuevos[k] = valor

                actualizar_pedido_db(id_r, datos_nuevos)
                
                registrar_log("EDICION_PEDIDO", f"Pedido #{id_r} editado manualmente.")
                v.destroy()
                self.mostrar_pedidos()
                
            except Exception as ex:
                messagebox.showerror("Error de Formato", f"Revisa las fechas (D/M/Y).\nError: {ex}", parent=v)

        ctk.CTkButton(v, text="💾 Guardar Cambios", fg_color="#27ae60", hover_color="#1e8449",
                       height=40, font=("Arial", 12, "bold"), command=save).pack(pady=25)

    def abrir_ventana_finalizar(self):
        sel = self.tabla_pedidos.selection()
        if not sel: return

        val_fila = self.tabla_pedidos.item(sel)['values']
        id_r = val_fila[1]
        nom_booster = val_fila[2]

        try:
            conn = conectar()
            cursor = conn.cursor()
            mes_actual_iso = datetime.now().strftime("%Y-%m")
            cursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 'Terminado' AND fecha_fin_real LIKE ?", (f"{mes_actual_iso}%",))
            num_orden_mes = cursor.fetchone()[0] + 1
            conn.close()
        except:
            num_orden_mes = "?"

        tarifas_raw = obtener_config_precios()
        tarifas = [t[0] for t in tarifas_raw]

        v = ctk.CTkToplevel(self)
        self.centrar_ventana(v, 400, 520)
        v.attributes("-topmost", True)

        v.title(f"Finalizar Orden #{num_orden_mes}")

        ctk.CTkLabel(v, text="¿En qué Elo quedó la cuenta?").pack()
        cb_div = ctk.CTkOptionMenu(v, values=tarifas, width=250)
        cb_div.pack(pady=5)
        
        ctk.CTkLabel(v, text="WinRate Final (%):").pack()
        e_wr = ctk.CTkEntry(v, placeholder_text="Ej: 85")
        e_wr.pack(pady=5)

        var_publicar = ctk.BooleanVar(value=True) 
        chk_discord = ctk.CTkCheckBox(
            v, text="📢 Publicar resultado en Discord", 
            variable=var_publicar, fg_color="#5865F2",
            checkbox_height=20, checkbox_width=20
        )
        chk_discord.pack(pady=(15, 10))

        def finish():
            try:
                val_wr = e_wr.get()
                if not val_wr:
                    messagebox.showerror("Error", "El WinRate está vacío.", parent=v)
                    return

                wr = float(val_wr)
                elo_fin = cb_div.get()
                fecha_hoy_iso = datetime.now().strftime("%Y-%m-%d")

                conn = conectar(); cursor = conn.cursor()

                cursor.execute("SELECT precio_cliente, margen_perez FROM config_precios WHERE division = ?", (elo_fin,))
                tarifa = cursor.fetchone()

                if tarifa:
                    p_cli_base = float(tarifa[0])
                    g_per_base = float(tarifa[1])

                    p_booster = p_cli_base - g_per_base
                    g_perez = g_per_base - 1.0

                    if wr >= 60:
                        p_cliente = p_cli_base + 1.0
                    else:
                        p_cliente = p_cli_base
                else:
                    p_cliente, g_perez, p_booster = 0.0, 0.0, 0.0

                cursor.execute("SELECT fecha_inicio FROM pedidos WHERE id = ?", (id_r,))
                res_fecha = cursor.fetchone()
                fecha_inicio_str = res_fecha[0] if res_fecha else fecha_hoy_iso

                try:

                    if "/" in str(fecha_inicio_str):
                        f_obj = datetime.strptime(str(fecha_inicio_str).split(' ')[0], "%d/%m/%Y")
                    else:
                        f_obj = datetime.strptime(str(fecha_inicio_str).split(' ')[0], "%Y-%m-%d")
                    
                    mes_inicio_iso = f_obj.strftime("%Y-%m")
                    meses_es = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
                                7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
                    nombre_mes_es = meses_es[f_obj.month]
                except:
                    mes_inicio_iso = datetime.now().strftime("%Y-%m")
                    nombre_mes_es = "ACTUAL"

                if finalizar_pedido_db(id_r, wr, fecha_hoy_iso, elo_fin, g_perez, p_booster, p_cliente):

                    if var_publicar.get():
                        try:

                            cursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 'Terminado' AND fecha_inicio LIKE ?", (f"{mes_inicio_iso}%",))
                            num_orden_discord = cursor.fetchone()[0]
                            
                            titulo_discord = f"✅ PEDIDO #{num_orden_discord} DE {nombre_mes_es}"
                            url = obtener_config_sistema("discord_webhook")
                            
                            if url:
                                cursor.execute("SELECT COUNT(*) FROM pedidos WHERE booster_nombre = ? AND estado = 'Terminado' AND fecha_inicio LIKE ?", (nom_booster, f"{mes_inicio_iso}%"))
                                total_mes_booster = cursor.fetchone()[0]

                                noti = DiscordNotifier(url)
                                campos_embed = [
                                    {
                                        "name": "👤 Staff", 
                                        "value": f"**{nom_booster}**\n\n**📌 Quedó en**\n`{elo_fin}`", 
                                        "inline": True
                                    },
                                    {
                                        "name": "🔥 Racha", 
                                        "value": f"{total_mes_booster}º de {nombre_mes_es}\n\n**🎯 WinRate**\n`{wr}%`", 
                                        "inline": True
                                    },
                                    {
                                        "name": "💸 Pago Staff", 
                                        "value": f"__**${p_booster:.2f}**__", 
                                        "inline": False
                                    }
                                ]
                                noti.enviar_notificacion(
                                    titulo=titulo_discord, 
                                    descripcion="", 
                                    color=5763719, 
                                    campos=campos_embed
                                )
                        except Exception as e:
                            print(f"Error notificando Discord: {e}")

                    conn.close() 
                    registrar_log("PEDIDO_FINALIZADO", f"Orden #{id_r} cerrada por {nom_booster}.")
                    messagebox.showinfo("Éxito", "¡Pedido finalizado!", parent=v)
                    v.destroy()
                    self.mostrar_pedidos()

                    if hasattr(self, 'actualizar_dashboard'):
                        self.actualizar_dashboard()
                else:
                    conn.close()
                    messagebox.showerror("Error", "No se pudo actualizar la base de datos.", parent=v)

            except ValueError:
                messagebox.showerror("Error", "El WinRate debe ser un número.", parent=v)
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}", parent=v)

        ctk.CTkButton(v, text="Confirmar Finalización", fg_color="#2ecc71",
                      height=40, font=("Arial", 12, "bold"), command=finish).pack(pady=20)
        
    def abrir_ventana_extender_tiempo(self):
        sel = self.tabla_pedidos.selection()
        if not sel: return
        id_r = self.tabla_pedidos.item(sel)['values'][1]
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 300, 200); v.attributes("-topmost", True)
        e_dias = ctk.CTkEntry(v, width=100); e_dias.insert(0, "1"); e_dias.pack(pady=20)
        def confirm():
            f_act = str(self.tabla_pedidos.item(sel)['values'][6])
            nueva = (datetime.strptime(f_act, "%Y-%m-%d") + timedelta(days=int(e_dias.get()))).strftime("%Y-%m-%d")
            actualizar_pedido_db(id_r, {"fecha_limite": nueva}); v.destroy(); self.mostrar_pedidos()
        ctk.CTkButton(v, text="Extender", command=confirm).pack()

    def abrir_ventana_nuevo_pedido(self):
        
        b_raw = obtener_boosters_db(); elos = obtener_elos_en_stock()
        
        if not b_raw:
            messagebox.showwarning("Falta Staff", "No tienes Boosters registrados.")
            return

        if not elos:
            messagebox.showwarning("Sin Stock", "⚠️ No hay cuentas disponibles en el Inventario.")
            return
        
        map_b = {b[1]: b[0] for b in b_raw}
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 450, 650); v.attributes("-topmost", True)
        
        ctk.CTkLabel(v, text="NUEVO PEDIDO", font=("Arial", 16, "bold")).pack(pady=15)

        cb_b = ctk.CTkOptionMenu(v, values=list(map_b.keys()), width=300); cb_b.pack(pady=10)
        self.map_c_id = {}; self.map_c_note = {}
        
        def update_note(choice):
            n = self.map_c_note.get(choice, "FRESH")
            e_n.configure(state="normal"); e_n.delete(0, "end"); e_n.insert(0, n); e_n.configure(state="readonly")
        
        def change_elo(choice):
            data = obtener_cuentas_filtradas_datos(choice)
            if data:
                self.map_c_id = {c[1]: c[0] for c in data}; self.map_c_note = {c[1]: (c[2] if c[2] else "FRESH") for c in data}
                names = list(self.map_c_id.keys()); cb_c.configure(values=names); cb_c.set(names[0]); update_note(names[0])
        
        ctk.CTkLabel(v, text="Elo Inicial:").pack()
        cb_e = ctk.CTkOptionMenu(v, values=elos, width=300, command=change_elo); cb_e.pack(pady=5)
        
        ctk.CTkLabel(v, text="Cuenta a Asignar:").pack()
        cb_c = ctk.CTkOptionMenu(v, values=[], width=300, command=update_note); cb_c.pack(pady=5)
        
        ctk.CTkLabel(v, text="Nota de la Cuenta:").pack()
        e_n = ctk.CTkEntry(v, width=300, state="readonly"); e_n.pack(pady=5)
        
        ctk.CTkLabel(v, text="Días para entregar:").pack()
        e_d = ctk.CTkEntry(v, width=300); e_d.insert(0, "10"); e_d.pack(pady=5)
        
        if elos: change_elo(elos[0])
        
        def go():
            try:
                dias = int(e_d.get())
                f_fin = calcular_fecha_limite_sugerida(dias).split(' ')[0]
                b_name = cb_b.get()
                c_name = cb_c.get()
                if crear_pedido(map_b[cb_b.get()], cb_b.get(), self.map_c_id[cb_c.get()], cb_c.get(), cb_e.get(), f_fin):
                    registrar_log("NUEVO_PEDIDO", f"Asignado a {b_name}. Cuenta: {c_name}")
                    v.destroy(); self.mostrar_pedidos()
            except ValueError:
                messagebox.showerror("Error", "Los días deben ser un número entero.", parent=v)

        ctk.CTkButton(v, text="Iniciar Orden", fg_color="#2ecc71", command=go).pack(pady=20)

    def abrir_ventana_reportar_abandono(self):
        sel = self.tabla_pedidos.selection()
        if not sel: return
        id_r = self.tabla_pedidos.item(sel)['values'][1]
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 350, 400); v.attributes("-topmost", True)
        e_elo = ctk.CTkEntry(v, placeholder_text="Elo dejado..."); e_elo.pack(pady=10)
        e_wr = ctk.CTkEntry(v, placeholder_text="WR dejado..."); e_wr.pack(pady=10)
        def confirm():
            if registrar_abandono_db(id_r, e_elo.get().upper(), e_wr.get()):
                registrar_log("ABANDONO_PEDIDO", f"Pedido #{id_r} marcado como abandonado. Elo dejado: {e_elo.get()}")
                v.destroy(); self.mostrar_pedidos()
        ctk.CTkButton(v, text="Confirmar DROP", fg_color="#e74c3c", command=confirm).pack()

    def abrir_ventana_registro(self):
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 400, 450); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="AÑADIR CUENTA", font=("Arial", 16, "bold")).pack(pady=20)
        up = ctk.CTkEntry(v, placeholder_text="User:Pass", width=250); up.pack(pady=10)
        elo = ctk.CTkOptionMenu(v, values=["Emerald/Plat", "DIAMANTE"], width=250); elo.pack(pady=10)
        not_ent = ctk.CTkEntry(v, placeholder_text="Notas", width=250); not_ent.pack(pady=10)
        def save():
            if registrar_cuenta_gui(up.get(), elo.get(), not_ent.get())[0]:
                v.destroy(); self.mostrar_inventario()
        ctk.CTkButton(v, text="Guardar", command=save, fg_color="#2ecc71").pack(pady=20)

    def abrir_ventana_editar_inventario(self):
        sel = self.tabla_inv.selection()
        if not sel: return
        v_id = self.tabla_inv.item(sel)['values'][0]
        datos_r = next(d for d in self.datos_inventario if d[0] == v_id)
        id_real = datos_r[1]
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 400, 450); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="EDITAR CUENTA", font=("Arial", 16, "bold")).pack(pady=20)
        e_up = ctk.CTkEntry(v, width=250); e_up.insert(0, datos_r[2]); e_up.pack(pady=10)
        e_elo = ctk.CTkOptionMenu(v, values=["Emerald/Plat", "DIAMANTE"], width=250); e_elo.set(datos_r[3]); e_elo.pack(pady=10)
        e_not = ctk.CTkEntry(v, width=250); e_not.insert(0, datos_r[4]); e_not.pack(pady=10)
        def save():
            actualizar_inventario_db(id_real, {"user_pass": e_up.get(), "elo_tipo": e_elo.get(), "descripcion": e_not.get()})
            v.destroy(); self.mostrar_inventario()
        ctk.CTkButton(v, text="Actualizar", fg_color="#27ae60", command=save).pack(pady=20)

    def abrir_ventana_masivo(self):
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 500, 550); v.attributes("-topmost", True)
        txt = ctk.CTkTextbox(v, width=450, height=250); txt.pack(pady=10)
        elo = ctk.CTkOptionMenu(v, values=["Emerald/Plat", "DIAMANTE"], width=200); elo.pack(pady=10)
        def proc():
            registrar_lote_gui(txt.get("1.0", "end"), elo.get())
            v.destroy(); self.mostrar_inventario()
        ctk.CTkButton(v, text="🚀 Importar", command=proc, fg_color="#3498db").pack(pady=20)

    def eliminar_seleccionado(self):
        sel = self.tabla_inv.selection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar cuenta permanentemente?", parent=self):
            v_id = self.tabla_inv.item(sel)['values'][0]
            cuenta_afectada = self.tabla_inv.item(sel)['values'][1]
            id_r = next(d[1] for d in self.datos_inventario if d[0] == v_id)
            if eliminar_cuenta_gui(id_r):
                registrar_log("STOCK_ELIMINADO", f"Cuenta eliminada: {cuenta_afectada}")
                self.mostrar_inventario()

    def abrir_ventana_nuevo_precio(self):
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 350, 480); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="NUEVA TARIFA", font=("Arial", 16, "bold")).pack(pady=20)
        ctk.CTkLabel(v, text="Puntos de Ranking:", font=("Arial", 11)).pack(pady=(5,0))
        
        e_div = ctk.CTkEntry(v, placeholder_text="Ej: D1", width=200); e_div.pack(pady=5)
        e_cli = ctk.CTkEntry(v, placeholder_text="Precio Cliente $", width=200); e_cli.pack(pady=5)
        e_per = ctk.CTkEntry(v, placeholder_text="Margen Perez $", width=200); e_per.pack(pady=5)
        e_pts = ctk.CTkEntry(v, placeholder_text="Ej: 45", width=200); e_pts.insert(0, "2"); e_pts.pack(pady=5)
        
        def save():
            try:
                div = e_div.get().upper()
                cli = float(e_cli.get())
                per = float(e_per.get())
                pts = int(e_pts.get())
                
                if agregar_precio_db(div, cli, per, pts):
                    v.destroy(); self.actualizar_tabla_precios()
            except ValueError:
                messagebox.showerror("Error", "Asegúrate de ingresar números válidos en Precio y Puntos.")

        ctk.CTkButton(v, text="Guardar", command=save, fg_color="#2ecc71").pack(pady=20)
    
    def abrir_ventana_editar_precio(self):
        sel = self.tabla_precios.selection()
        if not sel: return
        datos = self.tabla_precios.item(sel)['values']
        
        div = datos[0]
        p_cli = str(datos[1]).replace('$','').replace(',','')
        m_per = str(datos[2]).replace('$','').replace(',','')
        p_pts = str(datos[4])
        
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 350, 480); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text=f"EDITAR {div}", font=("Arial", 16, "bold")).pack(pady=20)
        
        ctk.CTkLabel(v, text="Precio Cliente:").pack()
        e_cli = ctk.CTkEntry(v, width=200); e_cli.insert(0, p_cli); e_cli.pack(pady=5)
        
        ctk.CTkLabel(v, text="Margen Perez:").pack()
        e_per = ctk.CTkEntry(v, width=200); e_per.insert(0, m_per); e_per.pack(pady=5)
        
        ctk.CTkLabel(v, text="Puntos Ranking:").pack()
        e_pts = ctk.CTkEntry(v, width=200); e_pts.insert(0, p_pts); e_pts.pack(pady=5)
        
        def save():
            try:
                old_price = p_cli
                new_price = e_cli.get()
                new_margen = e_per.get()
                new_pts = e_pts.get()
                
                if actualizar_precio_db(div, float(new_price), float(new_margen), int(new_pts)):
                    registrar_log("CAMBIO_TARIFA", f"División {div}: ${old_price} -> ${new_price} | Pts: {new_pts}")
                    v.destroy(); self.actualizar_tabla_precios()
            except ValueError:
                messagebox.showerror("Error", "Valores numéricos inválidos.")

        ctk.CTkButton(v, text="Actualizar", command=save, fg_color="#3498db").pack(pady=20)
    
    def eliminar_precio_seleccionado(self):
        sel = self.tabla_precios.selection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar tarifa?", parent=self):
            if eliminar_precio_db(self.tabla_precios.item(sel)['values'][0]): self.actualizar_tabla_precios()

    def ejecutar_backup_manual(self):
        try:
            realizar_backup_db()
            messagebox.showinfo("Seguridad", "✅ Base de datos respaldada con éxito.\nRevisa la carpeta /backups")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el respaldo: {e}")

    def abrir_visor_logs(self):

        v = ctk.CTkToplevel(self)
        v.title("Registro de Seguridad y Auditoría")
        self.centrar_ventana(v, 700, 500)
        v.attributes("-topmost", True)
        v.grab_set()

        header = ctk.CTkFrame(v, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="🛡️ LOGS DE SISTEMA (CAJA NEGRA)", font=("Consolas", 16, "bold")).pack(side="left")
        ctk.CTkButton(header, text="Cerrar", width=80, fg_color="#e74c3c", command=v.destroy).pack(side="right")

        txt_frame = ctk.CTkFrame(v, fg_color="#1a1a1a", corner_radius=10)
        txt_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        txt = ctk.CTkTextbox(txt_frame, width=600, height=400, font=("Consolas", 11), fg_color="#0f0f0f", text_color="#00ff00", activate_scrollbars=True)
        txt.pack(fill="both", expand=True, padx=5, pady=5)

        logs = obtener_logs_db(limite=100)

        if not logs:
            txt.insert("0.0", "\n   [ SYSTEM ] No hay registros de actividad reciente.")
        else:
            header_txt = f"{'FECHA/HORA':<20} | {'EVENTO':<18} | DETALLES\n"
            sep = "-"*85 + "\n"
            txt.insert("0.0", header_txt + sep)

            for log in logs:
                fecha_corta = log[0][5:-3]
                linea = f"{fecha_corta:<20} | {log[1]:<18} | {log[2]}\n"
                txt.insert("end", linea)
        txt.configure(state="disabled")

    def on_closing(self):
        print("💾 Realizando backup automático antes de cerrar...")
        try:
            realizar_backup_db()
        except Exception as e:
            print(f"⚠️ Error en backup al cerrar: {e}")
        try:
            plt.close('all')
        except:
            pass
        self.destroy()
        print("🔴 Apagado forzoso del sistema.")
        os._exit(0)

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    app = PerezBoostApp()
    app.mainloop()