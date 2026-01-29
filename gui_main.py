import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import customtkinter as ctk
import pandas as pd
import matplotlib
matplotlib.use("TkAgg") 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from discord_handler import DiscordNotifier, COLOR_SUCCESS, COLOR_INFO, COLOR_WARNING
from core.database import (
    actualizar_pedido_db, actualizar_booster_db, actualizar_inventario_db,
    agregar_booster, eliminar_booster, obtener_boosters_db,
    realizar_backup_db, obtener_config_precios, actualizar_precio_db,
    agregar_precio_db, eliminar_precio_db, inicializar_db, conectar,
    obtener_conteo_pedidos_activos, obtener_conteo_stock, obtener_ganancia_proyectada,
    finalizar_pedido_db, registrar_abandono_db, obtener_datos_reporte_avanzado,
    obtener_pedidos_activos, crear_pedido, guardar_config_sistema, obtener_config_sistema,
    obtener_kpis_mensuales, registrar_log, obtener_logs_db, obtener_ranking_staff_db,
    obtener_resumen_mensual_db
    
)
from core.logic import (
    calcular_tiempo_transcurrido, calcular_pago_real, calcular_fecha_limite_sugerida
)
from modules.inventario import (
    obtener_inventario_visual, registrar_cuenta_gui, registrar_lote_gui, eliminar_cuenta_gui
)
from modules.pedidos import (
    obtener_elos_en_stock, obtener_cuentas_filtradas_datos, obtener_historial_visual
)

# =============================================================================
# CLASE PRINCIPAL: PEREZBOOST APP
# =============================================================================

class PerezBoostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        inicializar_db()
        
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
        
        # Configuración de Ventana
        self.title("PerezBoost Manager V9.0 - Platinum Edition") # ¡Actualizamos nombre!
        self.geometry("1240x750")
        ctk.set_appearance_mode("dark")
        self.centrar_ventana(self, 1240, 750)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Configuración del Grid Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. CREAR EL FRAME DEL SIDEBAR
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # 2. LOGO
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🚀 PEREZBOOST", 
                                     font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=30)
        
        # 3. BOTONES DEL MENÚ
        self.crear_boton_menu("🏠 Dashboard", self.mostrar_dashboard, 1)
        self.crear_boton_menu("⚙️ Tarifas", self.mostrar_precios, 2)      
        self.crear_boton_menu("👥 Boosters", self.mostrar_boosters, 3)    
        self.crear_boton_menu("🏆 Ranking Staff", self.mostrar_leaderboard, 4)
        self.crear_boton_menu("📦 Inventario", self.mostrar_inventario, 5) 
        self.crear_boton_menu("📜 Pedidos Activos", self.mostrar_pedidos, 6)
        self.crear_boton_menu("📊 Historial", self.mostrar_historial, 7)
        self.crear_boton_menu("📈 Reportes Pro", self.mostrar_reportes, 8)
        
        # 4. FRAME DE CONTENIDO
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
        val = self.tabla_pedidos.item(sel)['values']
        cuenta = val[4]
        fecha_raw = str(val[6])
        try:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            partes = fecha_raw.split("-")
            dia = int(partes[2])
            mes_nombre = meses[int(partes[1]) - 1]
            fecha_natural = f"{dia} {mes_nombre}"
        except:
            fecha_natural = fecha_raw

        texto_final = f"{cuenta} - {fecha_natural}"
        self.clipboard_clear()
        self.clipboard_append(texto_final)
        print(f"Copiado: {texto_final}")
        
    # =========================================================================
    # 2. SECCIÓN: DASHBOARD
    # =========================================================================

    def mostrar_dashboard(self):
        self.limpiar_pantalla()

        n_pedidos = obtener_conteo_pedidos_activos()
        n_stock = obtener_conteo_stock()
        proyeccion = obtener_ganancia_proyectada()
        ganancia_real_mes, terminados_mes = obtener_kpis_mensuales()
        criticos, proximos = self.calcular_resumen_emergencias()

        main_wrapper = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_wrapper.pack(expand=True, fill="both")

        container = ctk.CTkFrame(main_wrapper, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center") 

        if criticos > 0:
            banner_rojo = ctk.CTkFrame(container, fg_color="#3a1212", border_width=1, border_color="#ff4d4d", corner_radius=8)
            banner_rojo.pack(fill="x", pady=(0, 10)) 
            ctk.CTkLabel(banner_rojo, text=f"🚨 URGENTE: {criticos} pedidos vencen hoy (< 24h)", 
                         font=("Arial", 14, "bold"), text_color="#ff4d4d").pack(pady=8)

        if proximos > 0:
            banner_amarillo = ctk.CTkFrame(container, fg_color="#332512", border_width=1, border_color="#ffa500", corner_radius=8)
            banner_amarillo.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(banner_amarillo, text=f"⚠️ ATENCIÓN: {proximos} entregas próximas (1-3 días)", 
                         font=("Arial", 14, "bold"), text_color="#ffa500").pack(pady=8)

        if criticos == 0 and proximos == 0:

             pass
        ctk.CTkLabel(container, text=f"PANEL DE CONTROL - {datetime.now().strftime('%B').upper()}", font=("Arial", 26, "bold")).pack(pady=(0, 25))

        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(pady=10)

        col_stock = "#e74c3c" if n_stock == 0 else ("#f1c40f" if n_stock < 5 else "#2ecc71")
        
        self.crear_card(cards_frame, "📦 STOCK", f"{n_stock}", col_stock, 0, 0)
        self.crear_card(cards_frame, "⚔️ EN PROGRESO", f"{n_pedidos}", "#3498db", 0, 1)
        self.crear_card(cards_frame, "✅ TERMINADOS", f"{terminados_mes}", "#9b59b6", 0, 2)
        self.crear_card(cards_frame, "💵 CAJA (MES)", f"${ganancia_real_mes:,.2f}", "#27ae60", 1, 0)
        self.crear_card(cards_frame, "💰 PROYECCIÓN", f"${proyeccion:,.2f}", "#00b894", 1, 1) 
        self.crear_card(cards_frame, "⚡ EFICIENCIA", "1.2 d", "#e67e22", 1, 2)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=40)
        
        ctk.CTkButton(btn_frame, text="📊 Ver Reporte Detallado", command=self.abrir_reporte_diario,
                      fg_color="#2c3e50", height=45, width=200).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="🔄 Actualizar", command=self.mostrar_dashboard,
                      fg_color="#1f538d", height=45, width=200).pack(side="left", padx=10)

    def abrir_reporte_diario(self):
        """Genera el reporte Full Audit con detalles de eficiencia y finanzas."""
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
            """, (hoy_str,))
            
            pedidos_hoy = cursor.fetchall()

            sum_ganancia = 0.0
            sum_staff = 0.0
            sum_ventas = 0.0

            reporte = (
                f"📊 REPORTE DE CIERRE DIARIO\n"
                f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            
            if not pedidos_hoy:
                reporte += "       (No hubo cierres el día de hoy)\n"
            
            for i, p in enumerate(pedidos_hoy, start=1):

                p_id_interno, staff, cuenta, e_ini, e_fin, wr, f_ini, f_fin, cobro, pago, ganancia = p

                cobro = cobro or 0.0
                pago = pago or 0.0
                ganancia = ganancia or 0.0
                
                sum_ventas += cobro
                sum_staff += pago
                sum_ganancia += ganancia

                try:

                    d1 = datetime.strptime(str(f_ini).split(' ')[0], "%Y-%m-%d")
                    d2 = datetime.strptime(str(f_fin).split(' ')[0], "%Y-%m-%d")
                    dias = (d2 - d1).days
                    duracion_txt = f"{dias} días" if dias > 0 else "⚡ <24h"
                except:
                    duracion_txt = "N/A"

                reporte += f"📦 ORDEN #{i} | {staff.upper()}\n"
                reporte += f"   ├─ 🎮 Cuenta: {cuenta}\n"
                reporte += f"   ├─ 📈 Rendimiento: {e_ini} ➔ {e_fin} ({wr}% WR)\n"
                reporte += f"   ├─ ⏳ Eficiencia: {duracion_txt}\n"
                reporte += f"   └─ 💰 Finanzas: Venta ${cobro:.0f} | Staff -${pago:.0f} | Net +${ganancia:.0f}\n"
                reporte += f"────────────────────────────────────\n"

            reporte += (
                f"\n💵 RESUMEN FINANCIERO:\n"
                f"   TOTAL VENTAS:    ${sum_ventas:,.2f}\n"
                f"   PAGO NÓMINA:    -${sum_staff:,.2f}\n"
                f"   PROFIT NETO:    +${sum_ganancia:,.2f}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

            # Mostrar en Ventana
            v = ctk.CTkToplevel(self)
            v.title("Reporte Ejecutivo Full Audit")
            self.centrar_ventana(v, 500, 600) # Un poco más alto para ver detalles
            v.attributes("-topmost", True)
            
            txt_area = ctk.CTkTextbox(v, width=460, height=450, font=("Consolas", 12), fg_color="#1a1a1a")
            txt_area.insert("0.0", reporte)
            txt_area.pack(pady=20)
            
            # Botón Copiar
            ctk.CTkButton(v, text="📋 Copiar Todo", fg_color="#2ecc71", width=200,
                          command=lambda: [self.clipboard_clear(), self.clipboard_append(reporte), 
                                           messagebox.showinfo("Reporte", "¡Copiado!")]).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Fallo generando reporte: {e}")
            print(e)
        finally: 
            conn.close()
            
    def crear_card(self, master, titulo, valor, color, fila, columna):
        
        # 1. Crear el marco de tamaño fijo (260x140)
        card = ctk.CTkFrame(master, corner_radius=15, fg_color="#1a1a1a", 
                            border_width=2, border_color=color, width=260, height=140)
        card.grid(row=fila, column=columna, padx=15, pady=15)
        
        # 2. Congelar el tamaño para que no se achique
        card.grid_propagate(False)
        
        # 3. Contenedor interno para centrar perfectamente el texto
        inner_frame = ctk.CTkFrame(card, fg_color="transparent")
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # 4. Textos (SOLO UNA VEZ)
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
    # 3. SECCIÓN: TARIFAS
    # =========================================================================

    def mostrar_precios(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        # Header
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=15, padx=30, fill="x")
        ctk.CTkLabel(header, text="⚙️ CONFIGURACIÓN DE TARIFAS Y PUNTOS", font=("Arial", 20, "bold")).pack(side="left")

        # --- TABLA ACTUALIZADA (Agregada col 'pts') ---
        cols = ("div", "p_cli", "m_per", "p_boo", "pts")
        self.tabla_precios = ttk.Treeview(self.content_frame, columns=cols, show="headings", height=8)
        
        # Headers actualizados
        headers = ["DIVISIÓN", "PRECIO CLIENTE", "MARGEN PEREZ", "PAGO BOOSTER", "PUNTOS RANK"]
        for col, h in zip(cols, headers):
            self.tabla_precios.heading(col, text=h)
            # Ajustamos anchos para que quepa la nueva columna
            ancho = 100 if col == "pts" else 150
            self.tabla_precios.column(col, anchor="center", width=ancho)

        self.tabla_precios.pack(padx=30, pady=10, fill="both", expand=True)
        self.actualizar_tabla_precios() # Esta función debe llamar a obtener_config_precios()

        # Botones de Acción Tarifas
        footer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        footer.pack(pady=(5, 20), padx=30, fill="x")
        
        ctk.CTkButton(footer, text="+ Nueva Tarifa", fg_color="#2ecc71", width=120,
                      command=self.abrir_ventana_nuevo_precio).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="📝 Editar", fg_color="#f39c12", width=100,
                      command=self.abrir_ventana_editar_precio).pack(side="left", padx=5)
        
        ctk.CTkFrame(footer, width=20, height=1, fg_color="transparent").pack(side="left")
        
        ctk.CTkButton(footer, text="💾 Backup DB", fg_color="#1f538d", width=110,
                      command=self.ejecutar_backup_manual).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="🕵️ Auditoría", fg_color="#34495e", hover_color="#2c3e50", width=110,
                      command=self.abrir_visor_logs).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="🗑️ Eliminar", fg_color="#e74c3c", width=100,
                      command=self.eliminar_precio_seleccionado).pack(side="right")
        
        # --- SECCIÓN DISCORD (DOBLE WEBHOOK) ---
        frame_discord = ctk.CTkFrame(self.content_frame, fg_color="#1a1a1a", corner_radius=10)
        frame_discord.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(frame_discord, text="🤖 CONECTIVIDAD DISCORD", font=("Arial", 14, "bold")).pack(anchor="w", padx=15, pady=(10,5))
        
        # Canal 1: Pedidos
        row1 = ctk.CTkFrame(frame_discord, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row1, text="🔔 Canal Pedidos/Log:", width=150, anchor="w").pack(side="left")
        self.entry_webhook = ctk.CTkEntry(row1, width=400, placeholder_text="Webhook para Notificaciones...")
        self.entry_webhook.pack(side="left", fill="x", expand=True, padx=5)
        
        # Canal 2: Ranking
        row2 = ctk.CTkFrame(frame_discord, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row2, text="🏆 Canal Ranking:", width=150, anchor="w").pack(side="left")
        self.entry_webhook_rank = ctk.CTkEntry(row2, width=400, placeholder_text="Webhook para el Ranking Semanal...")
        self.entry_webhook_rank.pack(side="left", fill="x", expand=True, padx=5)

        # Cargar datos guardados
        url_pedidos = obtener_config_sistema("discord_webhook")
        url_ranking = obtener_config_sistema("discord_webhook_ranking")
        
        if url_pedidos: self.entry_webhook.insert(0, url_pedidos)
        if url_ranking: self.entry_webhook_rank.insert(0, url_ranking)
        
        ctk.CTkButton(frame_discord, text="💾 Guardar Conexiones", width=200, fg_color="#5865F2", 
                      command=self.guardar_webhooks_discord).pack(pady=15)
        
    def guardar_webhooks_discord(self):
        url_pedidos = self.entry_webhook.get().strip()
        url_ranking = self.entry_webhook_rank.get().strip()
        
        # Guardamos ambas URLs con claves diferentes
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
            # t[0]=div, t[1]=p_cli, t[2]=m_per, t[3]=pts
            div, p_cli, m_per, pts = t
            p_boo = p_cli - m_per
            # IMPORTANTE: Insertamos 'div' tal cual viene de la DB
            self.tabla_precios.insert("", "end", values=(div, f"${p_cli}", f"${m_per}", f"${p_boo}", pts))

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
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_inventario).pack(side="right", padx=5)

        cols = ("id_v", "user_pass", "elo", "desc")
        self.tabla_inv = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        for col, txt in zip(cols, ["#", "CUENTA", "ELO", "NOTAS"]):
            self.tabla_inv.heading(col, text=txt); self.tabla_inv.column(col, anchor="center")

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
            if query == "" or query in d[3].lower():
                self.tabla_inv.insert("", tk.END, values=(d[0], d[2], d[3], d[4]))

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
        
        headers = ["#", "ID_R", "STAFF", "ELO", "CUENTA / USER", "INICIO", "ENTREGA", "TIEMPO"]
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

        for i in self.tabla_pedidos.get_children(): 
            self.tabla_pedidos.delete(i)
        
        try:
            datos_raw = obtener_pedidos_activos()
            if not datos_raw: return

            for i, p in enumerate(datos_raw, start=1):

                id_pedido = str(p[0])
                booster_nom = str(p[1]).lower()
                cuenta_user = str(p[3]).lower()
                elo_actual = str(p[2]).lower()

                if (query == "" or 
                    query in id_pedido or 
                    query in booster_nom or 
                    query in cuenta_user or
                    query in elo_actual):

                    try:
                        fecha_str = str(p[5]).split(' ')[0].strip()
                        fecha_entrega = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        dias_dif = (fecha_entrega - hoy).days
                        
                        if dias_dif <= 1: tag, ico = 'urgente', "🔴"
                        elif dias_dif <= 3: tag, ico = 'alerta', "🟡"
                        else: tag, ico = 'normal', "🟢"
                    except: tag, ico = 'normal', "⚪"

                    tiempo_trans = calcular_tiempo_transcurrido(str(p[4]))

                    fila = (i, p[0], p[1], p[2], p[3], str(p[4]).split(' ')[0], 
                            str(p[5]).split(' ')[0], f"{ico} {tiempo_trans}")
                    self.tabla_pedidos.insert("", tk.END, values=fila, tags=(tag,))
                    
        except Exception as e:
            print(f"Error en Búsqueda Global: {e}")

    # =========================================================================
    # 7. SECCIÓN: HISTORIAL
    # =========================================================================

    def mostrar_historial(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=15, padx=20, fill="x")
        ctk.CTkLabel(header, text="📊 HISTORIAL", font=("Arial", 20, "bold")).pack(side="left")

        ctk.CTkButton(header, text="⚠️ Ver Abandonos", fg_color="#e74c3c", hover_color="#c0392b",
                      width=120, command=lambda: self.filtrar_historial(solo_abandonos=True)).pack(side="right", padx=10)

        self.entry_busqueda_h = ctk.CTkEntry(header, placeholder_text="Filtrar Staff/Estado...", width=200)
        self.entry_busqueda_h.pack(side="right")
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_historial).pack(side="right", padx=5)

        cols = ("#", "booster", "cuenta", "pago_b", "perez", "total", "inicio", "fin", "duracion", "estado_oculto")
        self.tabla_historial = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        anchos = [35, 110, 240, 80, 80, 80, 90, 90, 90, 0] 
        for col, head, ancho in zip(cols, ["#", "STAFF", "CUENTA", "BOOSTER", "PEREZ", "CLIENTE", "INI", "FIN", "DURACIÓN", ""], anchos):
            self.tabla_historial.heading(col, text=head)
            if col == "estado_oculto": self.tabla_historial.column(col, width=0, stretch=tk.NO)
            else: self.tabla_historial.column(col, width=ancho, anchor="center", stretch=(col=="cuenta"))

        self.tabla_historial.tag_configure('terminado', foreground='#2ecc71')
        self.tabla_historial.tag_configure('abandonado', foreground='#e74c3c')
        
        self.tabla_historial.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.panel_total_h = ctk.CTkFrame(self.content_frame, fg_color="#1a1a1a", corner_radius=10, height=50)
        self.panel_total_h.pack(pady=15, fill="x", padx=20)
        self.panel_total_h.pack_propagate(False)
        self.lbl_totales_h = ctk.CTkLabel(self.panel_total_h, text="", font=("Arial", 16, "bold"), text_color="#3498db")
        self.lbl_totales_h.pack(expand=True)
        self.filtrar_historial()

    def filtrar_historial(self, solo_abandonos=False):
        query = self.entry_busqueda_h.get().lower()
        if not self.tabla_historial: return

        for i in self.tabla_historial.get_children(): self.tabla_historial.delete(i)
        try:
            datos, _ = obtener_historial_visual()
            s_b, s_p, s_c = 0.0, 0.0, 0.0
            for d in datos:
                est = str(d[9]).upper()
                mostrar = False
                if solo_abandonos:
                    if "ABANDONADO" in est: mostrar = True
                else:
                    if query == "" or query in str(d[1]).lower() or query in est.lower(): mostrar = True
                
                if mostrar:
                    tag = 'terminado' if "TERMINADO" in est else 'abandonado'
                    self.tabla_historial.insert("", tk.END, values=d, tags=(tag,))
                    if "TERMINADO" in est:
                        s_b += float(str(d[3]).replace('$', ''))
                        s_p += float(str(d[4]).replace('$', ''))
                        s_c += float(str(d[5]).replace('$', ''))
            self.lbl_totales_h.configure(text=f"STAFF: ${s_b:.2f} | PEREZ: ${s_p:.2f} | CAJA: ${s_c:.2f}")
        except Exception as e:
            print(f"Error historial: {e}")

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
        ctk.CTkLabel(filtros_frame, text="📊 ANALÍTICA AVANZADA", font=("Arial", 16, "bold")).pack(side="left", padx=20)
        
        self.combo_mes = ctk.CTkOptionMenu(filtros_frame, width=120,
            values=["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        self.combo_mes.pack(side="left", padx=10)
        
        try:
            boosters = ["Todos"] + [b[1] for b in obtener_boosters_db()]
        except: boosters = ["Todos"]
        self.combo_booster_rep = ctk.CTkOptionMenu(filtros_frame, width=140, values=boosters)
        self.combo_booster_rep.pack(side="left", padx=10)

        ctk.CTkButton(filtros_frame, text="Calcular", width=100, command=self.actualizar_analitica).pack(side="left", padx=10)
        ctk.CTkButton(filtros_frame, text="📥 Exportar Excel Pro", fg_color="#1d6f42", hover_color="#145231",
                      command=self.exportar_excel_avanzado).pack(side="right", padx=20)

        self.graficos_frame = ctk.CTkFrame(main_container, fg_color="#1a1a1a", height=280)
        self.graficos_frame.pack(fill="x", pady=10)
        self.graficos_frame.pack_propagate(False) 

        self.kpi_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=10)

        table_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=10)
        cols = ("booster", "elo", "demora", "pago_b", "ganancia_p", "total")
        self.tabla_rep = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        headers = {"booster": "STAFF", "elo": "ELO FINAL", "demora": "DÍAS", "pago_b": "PAGO STAFF", "ganancia_p": "MI GANANCIA", "total": "TOTAL CLIENTE"}
        for c in cols:
            self.tabla_rep.heading(c, text=headers[c])
            self.tabla_rep.column(c, width=100, anchor="center")

        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tabla_rep.yview)
        self.tabla_rep.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tabla_rep.pack(side="left", fill="both", expand=True)

        self.actualizar_analitica()

    def actualizar_analitica(self):

        for widget in self.kpi_frame.winfo_children(): widget.destroy()
        for i in self.tabla_rep.get_children(): self.tabla_rep.delete(i)
        for widget in self.graficos_frame.winfo_children(): widget.destroy()
        
        booster_seleccionado = self.combo_booster_rep.get()
        datos = obtener_datos_reporte_avanzado(self.combo_mes.get(), booster_seleccionado)
        
        ganancia_neta_perez = 0.0
        pago_total_staff = 0.0
        conteo_terminados = 0
        dias_totales = 0

        if datos:
            for r in datos:
                if r[7] == 'Terminado':
                    conteo_terminados += 1
                    g_row = float(r[13] or 0)
                    p_row = float(r[12] or 0)
                    t_cli = float(r[11] or 0)
                    ganancia_neta_perez += g_row
                    pago_total_staff += p_row
                    
                    try:
                        if r[5] and r[10]:
                            fmt = "%Y-%m-%d %H:%M"
                            ini = datetime.strptime(str(r[5])[:16], fmt)
                            fin = datetime.strptime(str(r[10])[:16], fmt)
                            dias = (fin - ini).days or 1
                            dias_totales += dias
                            d_txt = str(dias)
                        else: d_txt = "N/A"
                    except: d_txt = "-"
                    self.tabla_rep.insert("", "end", values=(r[2], r[8], d_txt, f"${p_row:.2f}", f"${g_row:.2f}", f"${t_cli:.2f}"))

        promedio = dias_totales / conteo_terminados if conteo_terminados > 0 else 0
        
        self.crear_card_mini(self.kpi_frame, "PAGO BOOSTERS", f"${pago_total_staff:.2f}", "#3498db", 0)
        self.crear_card_mini(self.kpi_frame, "GANANCIA PEREZ", f"${ganancia_neta_perez:.2f}", "#2ecc71", 1)
        self.crear_card_mini(self.kpi_frame, "PEDIDOS", f"{conteo_terminados}", "#f1c40f", 2)
        self.crear_card_mini(self.kpi_frame, "PROM. DÍAS", f"{promedio:.1f} d", "#e67e22", 3)

        if ganancia_neta_perez > 0 or pago_total_staff > 0:
            self.dibujar_grafico_financiero(ganancia_neta_perez, pago_total_staff, booster_seleccionado)
        else:
            ctk.CTkLabel(self.graficos_frame, text="Sin datos para graficar", text_color="gray").pack(expand=True)

    def dibujar_grafico_financiero(self, total_perez, total_staff, nombre_filtro):
        plt.close('all')
        plt.rcParams.update({
            'figure.facecolor': '#1a1a1a', 'axes.facecolor': '#1a1a1a',
            'axes.edgecolor': '#444444', 'axes.labelcolor': 'white',
            'xtick.color': 'white', 'ytick.color': 'white', 'text.color': 'white'
        })

        fig, ax = plt.subplots(figsize=(6, 2.8), dpi=100)
        label_izquierda = "Boosters" if nombre_filtro == "Todos" else nombre_filtro
        categorias = [label_izquierda, 'Perez']
        valores = [total_staff, total_perez]
        colores = ['#3498db', '#2ecc71'] 

        barras = ax.bar(categorias, valores, color=colores, width=0.5, zorder=3)

        ax.set_title(f'REPORTE: {label_izquierda.upper()} VS PEREZ', fontsize=11, fontweight='bold', pad=15)
        ax.set_ylabel('Monto USD ($)', fontsize=9, fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)

        for b in barras:
            ax.annotate(f'${b.get_height():,.2f}', 
                        xy=(b.get_x() + b.get_width()/2, b.get_height()),
                        xytext=(0, 5), textcoords="offset points", 
                        ha='center', va='bottom', weight='bold', fontsize=9)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.graficos_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.configure(bg='#1a1a1a', highlightthickness=0)
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()

    def exportar_excel_avanzado(self):
        """Exporta el reporte sumando Staff y Perez para el Total."""
        import pandas as pd
        from datetime import datetime
        
        mes = self.combo_mes.get()
        booster = self.combo_booster_rep.get()
        nombre_sugerido = f"Reporte_{mes}_{booster.replace(' ', '_')}.xlsx"
        
        datos = obtener_datos_reporte_avanzado(mes, booster)
        if not datos: 
            messagebox.showwarning("Sin Datos", "No hay datos para exportar.")
            return

        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=nombre_sugerido)
        if not ruta: return

        lista_procesada = []
        for r in datos:
            if r[7] == 'Terminado':

                try:
                    if r[5] and r[10]:
                        fmt = "%Y-%m-%d %H:%M"
                        ini = datetime.strptime(str(r[5])[:16], fmt)
                        fin = datetime.strptime(str(r[10])[:16], fmt)
                        dias = (fin - ini).days or 1
                    else: dias = 1
                except: dias = 1

                val_staff = float(r[12] or 0)
                val_perez = float(r[13] or 0)
                val_total = val_staff + val_perez 

                lista_procesada.append({
                    "Booster": r[2],
                    "Elo": r[8],
                    "WR": f"{r[9]}%",
                    "Dias": dias,
                    "C_STF": val_staff,
                    "C_PRZ": val_perez,
                    "C_TOT": val_total
                })

        if not lista_procesada: return
        
        df = pd.DataFrame(lista_procesada)

        sum_stf = df["C_STF"].sum()
        sum_prz = df["C_PRZ"].sum()
        sum_tot = df["C_TOT"].sum()

        row_total = pd.DataFrame([{
            "Booster": "TOTAL ACUMULADO >>", "Elo": "", "WR": "", "Dias": "",
            "C_STF": sum_stf, "C_PRZ": sum_prz, "C_TOT": sum_tot
        }])
        df = pd.concat([df, row_total], ignore_index=True)

        df.columns = [
            "Booster", "Elo Final", "WinRate", "Días",
            "PAGO STAFF ($)", "GANANCIA PEREZ ($)", "TOTAL SERVER ($)"
        ]

        df.index = [""] * len(df)

        try:
            with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Cierre')
                ws = writer.sheets['Cierre']
                ws['A1'] = "" # Limpiar esquina
                ws.column_dimensions['A'].width = 25
                ws.column_dimensions['G'].width = 20
            
            messagebox.showinfo("Éxito", "Reporte generado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def crear_card_mini(self, master, titulo, valor, color, col):
        card = ctk.CTkFrame(master, fg_color="#1a1a1a", border_width=1, border_color=color)
        card.grid(row=0, column=col, padx=10, pady=5, sticky="nsew")
        master.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(card, text=titulo, font=("Arial", 11, "bold"), text_color=color).pack(pady=(10,0))
        ctk.CTkLabel(card, text=valor, font=("Arial", 18, "bold")).pack(pady=(5,10))
    
    # =========================================================================
    # 9. SECCIÓN: LEABOARD
    # =========================================================================
    
    def mostrar_leaderboard(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        # Contenedor principal
        main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)
        
        # Título
        ctk.CTkLabel(main_frame, text="🏆 HALL OF FAME - TOP BOOSTERS", 
                     font=("Arial", 28, "bold")).pack(pady=(0, 10))

        # --- NUEVO: RESUMEN MENSUAL V9 ---
        try:
            pago_total, total_peds, wr_avg = obtener_resumen_mensual_db() # Asegúrate de tener esta función en tu db.py
        except:
            pago_total, total_peds, wr_avg = 0, 0, 0

        stats_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", border_width=1, border_color="#5865F2")
        stats_frame.pack(fill="x", pady=(0, 20))
        stats_frame.columnconfigure((0,1,2), weight=1)

        # Col 1: Dinero Staff
        ctk.CTkLabel(stats_frame, text="💰 Total Staff", font=("Arial", 11), text_color="gray").grid(row=0, column=0, pady=(10,0))
        ctk.CTkLabel(stats_frame, text=f"${pago_total:.2f}", font=("Arial", 16, "bold"), text_color="#2ecc71").grid(row=1, column=0, pady=(0,10))
        # Col 2: Entregas
        ctk.CTkLabel(stats_frame, text="📦 Entregas Mes", font=("Arial", 11), text_color="gray").grid(row=0, column=1, pady=(10,0))
        ctk.CTkLabel(stats_frame, text=f"{total_peds}", font=("Arial", 16, "bold")).grid(row=1, column=1, pady=(0,10))
        # Col 3: WR Global
        ctk.CTkLabel(stats_frame, text="📊 WR Promedio", font=("Arial", 11), text_color="gray").grid(row=0, column=2, pady=(10,0))
        ctk.CTkLabel(stats_frame, text=f"{wr_avg:.1f}%", font=("Arial", 16, "bold"), text_color="#f1c40f").grid(row=1, column=2, pady=(0,10))
        
        # --- TABLA DE RANKING ---
        tabla_frame = ctk.CTkFrame(main_frame, fg_color="#1e1e1e", corner_radius=10)
        tabla_frame.pack(expand=True, fill="both", pady=(0, 20))
        
        columnas = ("Rango", "Staff", "Completados", "Avg WR", "Abandonos", "Puntaje")
        self.tabla_rank = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=12)
        
        for col in columnas:
            self.tabla_rank.heading(col, text=col)
            self.tabla_rank.column(col, width=120, anchor="center")
        
        scrollbar = ctk.CTkScrollbar(tabla_frame, orientation="vertical", command=self.tabla_rank.yview)
        self.tabla_rank.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tabla_rank.pack(side="left", expand=True, fill="both", padx=5, pady=5)
        
        # Cargar Datos
        datos = obtener_ranking_staff_db()
        if not datos:
            self.tabla_rank.insert("", "end", values=("Scan...", "Sin actividad este mes", "-", "-", "-", "0 pts"))
        else:
            for i, b in enumerate(datos, start=1):
                if i == 1: color_rank = "🥇 MVP"
                elif i == 2: color_rank = "🥈"
                elif i == 3: color_rank = "🥉"
                else: color_rank = f"#{i}"
                
                wr_formateado = f"{b[2]:.1f}%" if b[2] else "0%"
                fila = (color_rank, b[0], b[1], wr_formateado, b[3], f"{b[4]} pts")
                self.tabla_rank.insert("", "end", values=fila)

        # Botones
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="🔄 Recalcular Mes", command=self.mostrar_leaderboard, 
                      fg_color="#1f538d", height=40).pack(side="left", expand=True, padx=10)

        ctk.CTkButton(btn_frame, text="📢 Publicar Ranking Semanal", command=self.compartir_ranking_discord, 
                      fg_color="#5865F2", hover_color="#4752C4", height=40).pack(side="left", expand=True, padx=10)
    
    def compartir_ranking_discord(self):
        # 1. Configuración
        url = obtener_config_sistema("discord_webhook_ranking") # <--- CAMBIO AQUÍ
        
        if not url:
            # Si no hay URL de ranking específica, intentamos usar la general o damos error
            url = obtener_config_sistema("discord_webhook")
            if not url:
                messagebox.showerror("Error", "No has configurado el Webhook de RANKING en la pestaña 'Tarifas'.")
                return

        # 2. Datos
        ranking = obtener_ranking_staff_db()
        if not ranking:
            messagebox.showinfo("Vacío", "Sin datos para publicar.")
            return

        # 3. Mensaje
        descripcion = "**📊 REPORTE MENSUAL DE RENDIMIENTO**\n\n"
        
        for i, b in enumerate(ranking[:10], start=1):
            # Datos de la DB: (nombre, terminados, avg_wr, abandonos, score)
            nombre = b[0]
            terminados = b[1]
            abandonos = b[3]
            puntaje_final = b[4] # Este YA tiene la resta de -10
            
            # ----------------------------------------------------
            # Cálculo de Liga Promedio (Basado en Dificultad REAL Jugada)
            # 1. Calculamos puntos reales sin castigo por abandonos
            puntos_reales_juego = puntaje_final + (abandonos * 10)
            
            # 2. Calculamos promedio basado en la dificultad real jugada
            if terminados > 0:
                promedio_difficulty = puntos_reales_juego / terminados
            else:
                promedio_difficulty = 0
            
            # 3. Asignamos etiqueta según la dificultad REAL
            if promedio_difficulty >= 30:
                liga_promedio = "💎 Diamante Avg" # 30+ pts
            elif promedio_difficulty >= 13:
                liga_promedio = "🟢 Esmeralda Avg" # 13-29 pts
            elif promedio_difficulty > 0:
                liga_promedio = "🔵 Platino Avg"   # 2-12 pts
            else:
                liga_promedio = "⚪ Unranked"
            # ----------------------------------------------------

            # Medallas
            if i == 1: icon = "🥇"
            elif i == 2: icon = "🥈"
            elif i == 3: icon = "🥉"
            else: icon = f"#{i}"
            
            # FORMATO FINAL:

            descripcion += f"{icon} **{nombre}** — 🏆 `{puntaje_final} Pts`\n"
            descripcion += f"   ✅ Terminados: `{terminados}`  |  ❌ Drop: `{abandonos}`  |  📊 Nivel: `{liga_promedio}`\n\n"

        descripcion += "_Nivel calculado basado en la dificultad de los pedidos tomados._"

        # 4. Enviar
        try:
            noti = DiscordNotifier(url)
            noti.enviar_notificacion(
                titulo="🏆 TABLA DE LÍDERES - STAFF",
                descripcion=descripcion,
                color=0xFFD700,
                campos=[] 
            )
            messagebox.showinfo("Éxito", "Ranking enviado a Discord.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo Discord: {e}")

    # =========================================================================
    # 10. SECCIÓN: POP-UPS (VENTANAS EMERGENTES)
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
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 400, 520); v.attributes("-topmost", True)
        entradas = {}
        campos = [("Booster:", "booster_nombre", val[2]), ("Cuenta:", "user_pass", val[3]), 
                  ("Inicio:", "fecha_inicio", str(val[5])), ("Entrega:", "fecha_limite", str(val[6]))]
        for lab, col, act in campos:
            ctk.CTkLabel(v, text=lab).pack(); e = ctk.CTkEntry(v, width=250); e.insert(0, act); e.pack(); entradas[col] = e
        def save():
            actualizar_pedido_db(id_r, {k: e.get() for k, e in entradas.items()}); v.destroy(); self.mostrar_pedidos()
        ctk.CTkButton(v, text="Guardar", fg_color="#27ae60", command=save).pack(pady=20)

    def abrir_ventana_finalizar(self):
        sel = self.tabla_pedidos.selection()
        if not sel: return
        
        valores_fila = self.tabla_pedidos.item(sel)['values']
        id_r = valores_fila[1]
        nom_booster = valores_fila[2]
        
        tarifas = [t[0] for t in obtener_config_precios()]
        
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 400, 500); v.attributes("-topmost", True)
        
        ctk.CTkLabel(v, text="FINALIZAR PEDIDO", font=("Arial", 14, "bold")).pack(pady=(20,10))
        
        # Inputs
        ctk.CTkLabel(v, text="¿En qué Elo quedó la cuenta?").pack()
        cb_div = ctk.CTkOptionMenu(v, values=tarifas, width=250); cb_div.pack(pady=5)
        
        ctk.CTkLabel(v, text="WinRate Final (%):").pack()
        e_wr = ctk.CTkEntry(v, placeholder_text="Ej: 85"); e_wr.pack(pady=5)

        # --- CHECKBOX DE DISCORD ---
        var_publicar = ctk.BooleanVar(value=True) 
        chk_discord = ctk.CTkCheckBox(
            v, text="📢 Publicar resultado en Discord", 
            variable=var_publicar, fg_color="#5865F2",
            checkbox_height=20, checkbox_width=20
        )
        chk_discord.pack(pady=(15, 5))
        
        def finish():
            try:
                val_wr = e_wr.get()
                if not val_wr:
                    messagebox.showerror("Error", "El campo WinRate está vacío.", parent=v)
                    return

                wr = float(val_wr)
                
                # --- VALIDACIÓN V9 ---
                if wr < 0 or wr > 100:
                    messagebox.showerror("Error", "¡El WinRate debe estar entre 0 y 100%!", parent=v)
                    return

                elo_fin = cb_div.get()
                c, p, g = calcular_pago_real(elo_fin, wr)
                
                if finalizar_pedido_db(id_r, elo_fin, wr, c, p, g, 0, ""):
                    try:
                        # 1. Log Interno e Info Racha
                        mes_actual = datetime.now().strftime("%Y-%m")
                        conn = conectar(); cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE booster_nombre = ? AND estado = 'Terminado' AND strftime('%Y-%m', fecha_fin_real) = ?", (nom_booster, mes_actual))
                        total_mes = cursor.fetchone()[0]; conn.close()
                        
                        registrar_log("PEDIDO_FINALIZADO", f"Orden #{id_r} cerrada. Staff: ${p} | Perez: ${g} | WR: {wr}%")
                        
                        # 2. Notificación Discord (Si está marcado)
                        if var_publicar.get():
                            url = obtener_config_sistema("discord_webhook")
                            if url:
                                noti = DiscordNotifier(url)
                                campos_embed = [
                                    {"name": "👤 Staff", "value": f"**{nom_booster}**\n\n**📌 Quedó en**\n`{elo_fin}`", "inline": True},
                                    {"name": "🔥 Racha Mes", "value": f"{total_mes} Entregas\n\n**🎯 WinRate**\n`{wr}%`", "inline": True},
                                    {"name": "💸 Pago Staff", "value": f"__**${p:.2f}**__", "inline": False}
                                ]
                                noti.enviar_notificacion(titulo=f"✅ ORDEN #{id_r} COMPLETADA", descripcion="", color=COLOR_SUCCESS, campos=campos_embed)
                    except Exception as e: 
                        print(f"Error notificando: {e}")
                    
                    v.destroy(); self.mostrar_pedidos()

            except ValueError:
                messagebox.showerror("Error", "El WinRate debe ser un número (Ej: 85.5)", parent=v)
            except Exception as e:
                messagebox.showerror("Error", f"Fallo: {e}", parent=v)

        ctk.CTkButton(v, text="Confirmar Finalización", fg_color="#2ecc71", width=200, height=40, command=finish).pack(pady=20)

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
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 350, 400); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="NUEVA TARIFA", font=("Arial", 16, "bold")).pack(pady=20)
        e_div = ctk.CTkEntry(v, placeholder_text="Ej: D1", width=200); e_div.pack(pady=5)
        e_cli = ctk.CTkEntry(v, placeholder_text="Precio $", width=200); e_cli.pack(pady=5)
        e_per = ctk.CTkEntry(v, placeholder_text="Margen $", width=200); e_per.pack(pady=5)
        def save():
            if agregar_precio_db(e_div.get().upper(), float(e_cli.get()), float(e_per.get())):
                v.destroy(); self.actualizar_tabla_precios()
        ctk.CTkButton(v, text="Guardar", command=save, fg_color="#2ecc71").pack(pady=20)

    def abrir_ventana_editar_precio(self):
        sel = self.tabla_precios.selection()
        if not sel: return
        datos = self.tabla_precios.item(sel)['values']
        div = datos[0]
        p_cli = str(datos[1]).replace('$','')
        m_per = str(datos[2]).replace('$','')
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 350, 400); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text=f"EDITAR {div}", font=("Arial", 16, "bold")).pack(pady=20)
        e_cli = ctk.CTkEntry(v, width=200); e_cli.insert(0, p_cli); e_cli.pack(pady=5)
        e_per = ctk.CTkEntry(v, width=200); e_per.insert(0, m_per); e_per.pack(pady=5)
        def save():
            old_price = p_cli
            new_price = e_cli.get()
            if actualizar_precio_db(div, float(e_cli.get()), float(e_per.get())):
                registrar_log("CAMBIO_TARIFA", f"División {div}: ${old_price} -> ${new_price}")
                v.destroy(); self.actualizar_tabla_precios()
        ctk.CTkButton(v, text="Actualizar", command=save, fg_color="#3498db").pack(pady=20)
    
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

        txt = ctk.CTkTextbox(txt_frame, width=600, height=400, font=("Consolas", 11), 
                             fg_color="#0f0f0f", text_color="#00ff00", activate_scrollbars=True)
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