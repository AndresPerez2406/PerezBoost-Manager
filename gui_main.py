import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime

# --- IMPORTACIONES DE CORE ---
from core.database import (
    actualizar_pedido_db, actualizar_booster_db, actualizar_inventario_db,
    agregar_booster, eliminar_booster, obtener_boosters_db,
    realizar_backup_db, obtener_config_precios, actualizar_precio_db,
    agregar_precio_db, eliminar_precio_db, inicializar_db, conectar,
    obtener_conteo_pedidos_activos, obtener_conteo_stock, obtener_ganancia_proyectada,
    finalizar_pedido_db, registrar_abandono_db
)

class PerezBoostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_db()
        
        self.menu_contextual = None
        self.tabla_inv = None
        self.tabla_pedidos = None
        self.tabla_boosters = None
        self.tabla_precios = None
        self.datos_inventario = []
        self.map_c_id = {}
        self.map_c_note = {}
        self.configurar_menus()
        
        # 1. Configuración de Ventana
        self.title("PerezBoost Manager V7.5 - Gold Edition")
        self.geometry("1240x750")
        ctk.set_appearance_mode("dark")
        self.centrar_ventana(self, 1240, 750)

        # 2. Layout Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 3. Sidebar (MENU LATERAL)
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🚀 PEREZBOOST", 
                                        font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=30)
        
        # Botones de Navegación
        self.crear_boton_menu("🏠 Dashboard", self.mostrar_dashboard, 1)
        self.crear_boton_menu("⚙️ Tarifas", self.mostrar_precios, 2)      
        self.crear_boton_menu("👥 Boosters", self.mostrar_boosters, 3)    
        self.crear_boton_menu("📦 Inventario", self.mostrar_inventario, 4) 
        self.crear_boton_menu("📜 Pedidos Activos", self.mostrar_pedidos, 5)
        self.crear_boton_menu("📊 Historial", self.mostrar_historial, 6)

        # 4. Contenedor Principal
        self.content_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#121212")
        self.content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Iniciar en el Dashboard
        self.mostrar_dashboard()

        self.protocol("WM_DELETE_WINDOW", self.cerrar_con_backup)

    # =========================================================================
    #  UTILIDADES
    # =========================================================================

    def configurar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1e1e1e", foreground="white", 
                        fieldbackground="#1e1e1e", borderwidth=0, font=("Segoe UI", 10), rowheight=35)
        style.configure("Treeview.Heading", background="#333333", foreground="white", 
                        relief="flat", font=("Segoe UI", 11, "bold"))
        # Esto asegura que al seleccionar una fila se siga viendo bien
        style.map("Treeview", background=[('selected', '#1f538d')])
        
        # DEFINICIÓN DE COLORES DE FILA (Si no los pones aquí, a veces no cargan)
        if self.tabla_pedidos:
            self.tabla_pedidos.tag_configure('urgente', foreground='white', background='#8b0000') # Rojo Intenso
            self.tabla_pedidos.tag_configure('alerta', foreground='black', background='#ffa500')   # Naranja
            self.tabla_pedidos.tag_configure('normal', foreground='#2ecc71')                      # Verde

    def lanzar_menu_contextual(self, event):
        # Identificamos qué fila se clickeó según la posición del mouse
        item_id = self.tabla_pedidos.identify_row(event.y)
        
        if item_id:
            # Seleccionamos la fila automáticamente al hacer clic derecho
            self.tabla_pedidos.selection_set(item_id)
            # Mostramos el menú en las coordenadas del mouse
            self.menu_contextual.post(event.x_root, event.y_root)
            
    def centrar_ventana(self, ventana, ancho, alto):
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana.winfo_screenheight() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
        
    def configurar_menus(self):
        # Creamos el objeto del menú una sola vez
        self.menu_contextual = tk.Menu(self, tearoff=0, bg="#1a1a1a", fg="white", 
                                      activebackground="#1f538d", font=("Segoe UI", 10))
        self.menu_contextual.add_command(label="✅ Finalizar Pedido", command=self.abrir_ventana_finalizar)
        self.menu_contextual.add_command(label="📝 Editar Información", command=self.abrir_ventana_editar_pedido)
        self.menu_contextual.add_command(label="⏳ Extender Tiempo", command=self.abrir_ventana_extender_tiempo)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="🚫 Reportar Abandono", command=self.abrir_ventana_reportar_abandono)

    def crear_boton_menu(self, texto, comando, fila):
        boton = ctk.CTkButton(self.sidebar_frame, text=texto, command=comando, 
                              corner_radius=10, height=40, fg_color="#2b2b2b", hover_color="#3d3d3d")
        boton.grid(row=fila, column=0, padx=20, pady=10, sticky="ew")

    def limpiar_pantalla(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def configurar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1e1e1e", foreground="white", 
                        fieldbackground="#1e1e1e", borderwidth=0, font=("Segoe UI", 10), rowheight=35)
        style.configure("Treeview.Heading", background="#333333", foreground="white", 
                        relief="flat", font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[('selected', '#1f538d')])

    def cerrar_con_backup(self):
        realizar_backup_db()
        self.destroy()

    # =========================================================================
    #  SECCIÓN: DASHBOARD
    # =========================================================================

    def mostrar_dashboard(self):
        self.limpiar_pantalla()
        from core.database import obtener_conteo_emergencias
        
        # 1. Obtener datos de salud del negocio
        n_pedidos = obtener_conteo_pedidos_activos()
        n_stock = obtener_conteo_stock()
        ganancia = obtener_ganancia_proyectada()
        
        # 2. Obtener Emergencias
        criticos, proximos = obtener_conteo_emergencias()

        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=20, pady=20)

        # --- SISTEMA DE ALERTA TEMPRANA (BANNER) ---
        if criticos > 0:
            # BANNER ROJO (CRÍTICO)
            banner = ctk.CTkFrame(container, fg_color="#3a1212", border_width=2, border_color="#ff4d4d")
            banner.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(banner, text=f"🚨 ¡EMERGENCIA! Tienes {criticos} pedido(s) VENCIDOS o Vence en 1 DIA. Pide la cuenta.", 
                         font=("Arial", 15, "bold"), text_color="#ff4d4d").pack(pady=10)
        
        if proximos > 0:
            # BANNER NARANJA (ADVERTENCIA)
            banner_adv = ctk.CTkFrame(container, fg_color="#332512", border_width=2, border_color="#ffa500")
            banner_adv.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(banner_adv, text=f"⏳ AVISO: {proximos} pedido(s) Vence en 2-3 DIAS. Presiona al staff.", 
                         font=("Arial", 14, "bold"), text_color="#ffa500").pack(pady=10)

        # --- TARJETAS DASHBOARD ---
        ctk.CTkLabel(container, text="📊 PANEL DE CONTROL", font=("Arial", 28, "bold")).pack(pady=(10, 30))
        
        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack()
        
        self.crear_card(cards_frame, "🚀 EN CURSO", f"{n_pedidos}", "#3498db", 0)
        self.crear_card(cards_frame, "📦 STOCK", f"{n_stock}", "#9b59b6", 1)
        self.crear_card(cards_frame, "💰 PROYECTADO", f"${ganancia:.2f}", "#2ecc71", 2)

        # Botones de Acción
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(btn_frame, text="📋 Generar Reporte", fg_color="#e67e22", command=self.abrir_reporte_diario).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔄 Refrescar", command=self.mostrar_dashboard).pack(side="left", padx=10)

        
    def crear_card(self, master, titulo, valor, color, columna):
        card = ctk.CTkFrame(master, corner_radius=20, fg_color="#1a1a1a", 
                            border_width=2, border_color=color, width=260, height=160)
        card.grid(row=0, column=columna, padx=15, pady=10)
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=titulo, font=("Arial", 14, "bold"), text_color=color).pack(pady=(30, 5))
        ctk.CTkLabel(card, text=valor, font=("Arial", 38, "bold")).pack(pady=5)
    
    def abrir_reporte_diario(self):
        from core.database import conectar
        
        # 1. Obtener datos básicos
        n_pedidos = obtener_conteo_pedidos_activos()
        ganancia_p = obtener_ganancia_proyectada()
        
        conn = conectar()
        cursor = conn.cursor()
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # --- NOTA: He cambiado 'margen_perez' por 'ganancia' ---
            # Si tu columna se llama diferente (ej. ganancia_perez), cámbiala aquí:
            cursor.execute("""
                SELECT SUM(pago_booster), SUM(margen_perez) 
                FROM pedidos 
                WHERE estado = 'Terminado' AND fecha_finalizacion LIKE ?
            """, (f"{hoy}%",))
            
            res = cursor.fetchone()
            pago_staff = res[0] or 0.0
            ganancia_real = res[1] or 0.0
        except Exception as e:
            print(f"Error en consulta de reporte: {e}")
            pago_staff, ganancia_real = 0.0, 0.0
        finally:
            conn.close()

        # 2. Texto del Reporte (Igual que antes)
        reporte_txt = f"""      🚀   **REPORTE PEREZBOOST - {datetime.now().strftime('%d/%m/%Y')}**   🚀
        
        💰 **FINANZAS DEL DÍA (Cerrado hoy):**
        • Ganancia Real: ${ganancia_real:.2f}
        • A pagar a Staff: ${pago_staff:.2f}
        • Total Cobrado: ${ganancia_real + pago_staff:.2f}

        ⚔️ **OPERACIONES ACTIVAS:**
        • Pedidos en curso: {n_pedidos}
        • Ganancia Proyectada: ${ganancia_p:.2f}

        ---
        
        _Generado por PerezBoost Manager V7.5_"""

        # 3. Ventana de visualización
        v = ctk.CTkToplevel(self)
        v.title("Reporte del Día")
        self.centrar_ventana(v, 450, 500)
        v.attributes("-topmost", True)
        
        txt_area = ctk.CTkTextbox(v, width=400, height=300, font=("Consolas", 12))
        txt_area.insert("0.0", reporte_txt)
        txt_area.pack(pady=20, padx=20)

        ctk.CTkButton(v, text="📋 Copiar Reporte", 
                      command=lambda: [self.clipboard_clear(), self.clipboard_append(reporte_txt), 
                                       messagebox.showinfo("Copiado", "Reporte al portapapeles")]).pack(pady=10)
    
    # =========================================================================
    #  SECCIÓN: TARIFAS
    # =========================================================================

    def mostrar_precios(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=15, padx=30, fill="x")
        ctk.CTkLabel(header, text="⚙️ CONFIGURACIÓN DE TARIFAS", font=("Arial", 20, "bold")).pack(side="left")

        cols = ("div", "p_cli", "m_per", "p_boo")
        self.tabla_precios = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        headers = ["DIVISIÓN", "PRECIO CLIENTE", "MARGEN PEREZ", "PAGO BOOSTER"]
        for col, h in zip(cols, headers):
            self.tabla_precios.heading(col, text=h)
            self.tabla_precios.column(col, anchor="center", width=150)

        self.tabla_precios.pack(padx=30, pady=10, fill="both", expand=True)
        self.actualizar_tabla_precios()

        # --- FOOTER CON BOTÓN DE SEGURIDAD ---
        footer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        footer.pack(pady=(5, 20), padx=30, fill="x")
        
        # Acciones de edición
        ctk.CTkButton(footer, text="+ Nueva Tarifa", fg_color="#2ecc71", 
                      command=self.abrir_ventana_nuevo_precio).pack(side="left", padx=5)
        
        ctk.CTkButton(footer, text="📝 Editar", fg_color="#f39c12", 
                      command=self.abrir_ventana_editar_precio).pack(side="left", padx=5)
        
        # Botón de Backup (El guardián de tus datos)
        ctk.CTkButton(footer, text="💾 Backup DB", fg_color="#1f538d", 
                      command=self.ejecutar_backup_manual).pack(side="left", padx=20)
        
        # Eliminar a la derecha
        ctk.CTkButton(footer, text="🗑️ Eliminar", fg_color="#e74c3c", 
                      command=self.eliminar_precio_seleccionado).pack(side="right")

    def ejecutar_backup_manual(self):
        """Ejecuta el respaldo de la base de datos y avisa al usuario."""
        try:
            from core.database import realizar_backup_db
            realizar_backup_db()
            messagebox.showinfo("Seguridad", "✅ Base de datos respaldada con éxito.\nSe ha guardado una copia en la carpeta /backups")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el respaldo: {e}")

    def actualizar_tabla_precios(self):
        for i in self.tabla_precios.get_children(): self.tabla_precios.delete(i)
        for d in obtener_config_precios():
            p_boo = float(d[1]) - float(d[2])
            self.tabla_precios.insert("", tk.END, values=(d[0], f"${d[1]:.2f}", f"${d[2]:.2f}", f"${p_boo:.2f}"))

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
            if actualizar_precio_db(div, float(e_cli.get()), float(e_per.get())):
                v.destroy(); self.actualizar_tabla_precios()
        ctk.CTkButton(v, text="Actualizar", command=save, fg_color="#3498db").pack(pady=20)

    def eliminar_precio_seleccionado(self):
        sel = self.tabla_precios.selection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar tarifa?", parent=self):
            if eliminar_precio_db(self.tabla_precios.item(sel)['values'][0]): self.actualizar_tabla_precios()

    # =========================================================================
    #  SECCIÓN: BOOSTERS (STAFF)
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
    #  SECCIÓN: INVENTARIO (STOCK)
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
        from modules.inventario import obtener_inventario_visual
        self.datos_inventario = obtener_inventario_visual()
        for d in self.datos_inventario:
            if query == "" or query in d[3].lower():
                self.tabla_inv.insert("", tk.END, values=(d[0], d[2], d[3], d[4]))

    def abrir_ventana_registro(self):
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 400, 450); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="AÑADIR CUENTA", font=("Arial", 16, "bold")).pack(pady=20)
        up = ctk.CTkEntry(v, placeholder_text="User:Pass", width=250); up.pack(pady=10)
        elo = ctk.CTkOptionMenu(v, values=["Emerald/Plat", "DIAMANTE"], width=250); elo.pack(pady=10)
        not_ent = ctk.CTkEntry(v, placeholder_text="Notas", width=250); not_ent.pack(pady=10)
        def save():
            from modules.inventario import registrar_cuenta_gui
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
            from modules.inventario import registrar_lote_gui
            registrar_lote_gui(txt.get("1.0", "end"), elo.get())
            v.destroy(); self.mostrar_inventario()
        ctk.CTkButton(v, text="🚀 Importar", command=proc, fg_color="#3498db").pack(pady=20)

    def eliminar_seleccionado(self):
        sel = self.tabla_inv.selection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar cuenta?", parent=self):
            v_id = self.tabla_inv.item(sel)['values'][0]
            id_r = next(d[1] for d in self.datos_inventario if d[0] == v_id)
            from modules.inventario import eliminar_cuenta_gui
            if eliminar_cuenta_gui(id_r): self.mostrar_inventario()

    # =========================================================================
    #  SECCIÓN: PEDIDOS ACTIVOS
    # =========================================================================

    def mostrar_pedidos(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        # Header
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=(15, 5), padx=30, fill="x")
        ctk.CTkLabel(header, text="⚔️ PEDIDOS ACTIVOS", font=("Arial", 20, "bold")).pack(side="left")
        
        self.entry_busqueda = ctk.CTkEntry(header, placeholder_text="Buscar Booster...", width=200)
        self.entry_busqueda.pack(side="right")
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_pedidos).pack(side="right", padx=5)

        cols = ("id_v", "id_r", "booster", "elo", "cuenta", "inicio", "fin", "tiempo") 
        self.tabla_pedidos = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        self.tabla_pedidos.bind("<Button-3>", self.lanzar_menu_contextual)
        self.tabla_pedidos.tag_configure('urgente', foreground='#ff4d4d')
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
        
        # Forzar carga inicial
        self.filtrar_pedidos()

        # Footer de botones
        footer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        footer.pack(pady=(5, 20), padx=30, fill="x")
        ctk.CTkButton(footer, text="⚡ Nuevo", fg_color="#3498db", command=self.abrir_ventana_nuevo_pedido).pack(side="left")
        ctk.CTkButton(footer, text="⏳ Extender", command=self.abrir_ventana_extender_tiempo).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="📝 Editar", fg_color="#f39c12", command=self.abrir_ventana_editar_pedido).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="✅ Finalizar", fg_color="#2ecc71", command=self.abrir_ventana_finalizar).pack(side="right")
        ctk.CTkButton(footer, text="🚫 Abandono", fg_color="#e74c3c", command=self.abrir_ventana_reportar_abandono).pack(side="right", padx=10)
        
    def filtrar_pedidos(self):
        from datetime import datetime
        from core.logic import calcular_tiempo_transcurrido
        from core.database import obtener_pedidos_activos
        
        query = self.entry_busqueda.get().lower()
        # Obtenemos solo la FECHA de hoy (sin horas/minutos para que el cálculo sea exacto)
        hoy = datetime.now().date()
        
        for i in self.tabla_pedidos.get_children():
            self.tabla_pedidos.delete(i)
        
        try:
            datos_raw = obtener_pedidos_activos()
            if not datos_raw: return

            for i, p in enumerate(datos_raw, start=1):
                # p[5] es la fecha límite en la DB
                booster_nom = str(p[1])
                
                if query == "" or query in booster_nom.lower():
                    # 1. Limpieza y conversión de fecha de entrega
                    try:
                        # Cortamos cualquier hora extra y convertimos a objeto date
                        fecha_str = str(p[5]).split(' ')[0].strip()
                        fecha_entrega = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        
                        # 2. Cálculo de días de diferencia
                        dias_diferencia = (fecha_entrega - hoy).days
                        
                        # --- LÓGICA DE SEMÁFORO CORREGIDA ---
                        if dias_diferencia <= 1:
                            tag, ico = 'urgente', "🔴" # Vence hoy o en 1 día
                        elif dias_diferencia <= 3:
                            tag, ico = 'alerta', "🟡"  # Vence en 2 o 3 días
                        else:
                            tag, ico = 'normal', "🟢" # 4 días o más
                    except Exception as e:
                        tag, ico = 'normal', "⚪"
                        print(f"Error procesando fecha del pedido {p[0]}: {e}")

                    # 3. Calculamos tiempo transcurrido desde inicio
                    tiempo_desde_inicio = calcular_tiempo_transcurrido(str(p[4]))

                    # 4. Insertar fila con el orden de columnas de mostrar_pedidos
                    # cols = ("id_v", "id_r", "booster", "elo", "cuenta", "inicio", "fin", "tiempo")
                    fila = (
                        i,
                        p[0],
                        p[1],
                        p[2],
                        p[3],
                        str(p[4]).split(' ')[0],
                        str(p[5]).split(' ')[0],
                        f"{ico} {tiempo_desde_inicio}"
                    )
                    
                    self.tabla_pedidos.insert("", tk.END, values=fila, tags=(tag,))
                    
        except Exception as e:
            print(f"Error en el filtro: {e}")

    # =========================================================================
    #  SECCIÓN: HISTORIAL
    # =========================================================================

    def mostrar_historial(self):
        self.limpiar_pantalla()
        self.configurar_estilo_tabla()
        
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(header, text="📊 HISTORIAL", font=("Arial", 20, "bold")).pack(side="left")

        # --- NUEVO: BOTÓN FILTRO RÁPIDO DE ABANDONOS ---
        ctk.CTkButton(header, text="⚠️ Ver Abandonos", fg_color="#e74c3c", hover_color="#c0392b",
                      width=120, command=lambda: self.filtrar_historial(solo_abandonos=True)).pack(side="right", padx=10)

        self.entry_busqueda_h = ctk.CTkEntry(header, placeholder_text="Filtrar Staff/Estado...", width=200)
        self.entry_busqueda_h.pack(side="right")
        
        ctk.CTkButton(header, text="🔍", width=40, command=self.filtrar_historial).pack(side="right", padx=5)

        # Configuración de tabla (Se mantiene igual)
        cols = ("#", "booster", "cuenta", "pago_b", "perez", "total", "inicio", "fin", "duracion", "estado_oculto")
        self.tabla_historial = ttk.Treeview(self.content_frame, columns=cols, show="headings")
        anchos = [35, 110, 240, 80, 80, 80, 90, 90, 90, 0] 
        
        for col, head, ancho in zip(cols, ["#", "STAFF", "CUENTA", "BOOSTER", "PEREZ", "CLIENTE", "INI", "FIN", "DURACIÓN", ""], anchos):
            self.tabla_historial.heading(col, text=head)
            if col == "estado_oculto": 
                self.tabla_historial.column(col, width=0, stretch=tk.NO)
            else: 
                self.tabla_historial.column(col, width=ancho, anchor="center", stretch=(col=="cuenta"))
        
        self.tabla_historial.tag_configure('terminado', foreground='#2ecc71')
        self.tabla_historial.tag_configure('abandonado', foreground='#e74c3c')
        self.tabla_historial.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Panel de Totales (Se inicializa aquí para que no de error al filtrar)
        self.panel_total_h = ctk.CTkFrame(self.content_frame, fg_color="#1a1a1a", corner_radius=10, height=50)
        self.panel_total_h.pack(pady=15, fill="x", padx=20)
        self.panel_total_h.pack_propagate(False)
        self.lbl_totales_h = ctk.CTkLabel(self.panel_total_h, text="", font=("Arial", 16, "bold"), text_color="#3498db")
        self.lbl_totales_h.pack(expand=True)
        
        self.filtrar_historial()

    def filtrar_historial(self, solo_abandonos=False):
        query = self.entry_busqueda_h.get().lower()
        for i in self.tabla_historial.get_children(): 
            self.tabla_historial.delete(i)
            
        try:
            from modules.pedidos import obtener_historial_visual
            datos, _ = obtener_historial_visual()
            s_b, s_p, s_c = 0.0, 0.0, 0.0
            
            for d in datos:
                est = str(d[9]).upper()
                
                # --- LÓGICA DE FILTRADO MEJORADA ---
                mostrar = False
                if solo_abandonos:
                    if "ABANDONADO" in est: mostrar = True
                else:
                    if query == "" or query in str(d[1]).lower() or query in est.lower():
                        mostrar = True
                
                if mostrar:
                    tag = 'terminado' if "TERMINADO" in est else 'abandonado'
                    self.tabla_historial.insert("", tk.END, values=d, tags=(tag,))
                    
                    # Solo sumamos al total lo que sí se cobró (Terminados)
                    if "TERMINADO" in est:
                        s_b += float(str(d[3]).replace('$', ''))
                        s_p += float(str(d[4]).replace('$', ''))
                        s_c += float(str(d[5]).replace('$', ''))
            
            self.lbl_totales_h.configure(text=f"STAFF: ${s_b:.2f} | PEREZ: ${s_p:.2f} | CAJA: ${s_c:.2f}")
        except Exception as e:
            print(f"Error al filtrar historial: {e}")
            
    # =========================================================================
    #  VENTANAS EMERGENTES (POP-UPS)
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
        if sel:
            id_r = self.tabla_boosters.item(sel)['values'][1]
            if messagebox.askyesno("Confirmar", "¿Eliminar staff?", parent=self):
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
        id_r = self.tabla_pedidos.item(sel)['values'][1]
        tarifas = [t[0] for t in obtener_config_precios()]
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 400, 400); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text="¿Elo Final?").pack(); cb_div = ctk.CTkOptionMenu(v, values=tarifas, width=250); cb_div.pack(pady=10)
        e_wr = ctk.CTkEntry(v, placeholder_text="WR %"); e_wr.pack(pady=10)
        def finish():
            from core.logic import calcular_pago_real
            try:
                wr = float(e_wr.get()); c, p, g = calcular_pago_real(cb_div.get(), wr)
                if finalizar_pedido_db(id_r, cb_div.get(), wr, c, p, g, 0, ""): v.destroy(); self.mostrar_pedidos()
            except: messagebox.showerror("Error", "WR inválido")
        ctk.CTkButton(v, text="Finalizar", fg_color="#2ecc71", command=finish).pack(pady=20)

    def abrir_ventana_extender_tiempo(self):
        sel = self.tabla_pedidos.selection()
        if not sel: return
        id_r = self.tabla_pedidos.item(sel)['values'][1]
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 300, 200); v.attributes("-topmost", True)
        e_dias = ctk.CTkEntry(v, width=100); e_dias.insert(0, "1"); e_dias.pack(pady=20)
        def confirm():
            from datetime import datetime, timedelta
            f_act = str(self.tabla_pedidos.item(sel)['values'][6])
            nueva = (datetime.strptime(f_act, "%Y-%m-%d") + timedelta(days=int(e_dias.get()))).strftime("%Y-%m-%d")
            actualizar_pedido_db(id_r, {"fecha_limite": nueva}); v.destroy(); self.mostrar_pedidos()
        ctk.CTkButton(v, text="Extender", command=confirm).pack()

    def abrir_ventana_nuevo_pedido(self):
        from modules.pedidos import obtener_boosters_db, obtener_elos_en_stock, obtener_cuentas_filtradas_datos
        b_raw = obtener_boosters_db(); elos = obtener_elos_en_stock()
        if not b_raw or not elos: return
        map_b = {b[1]: b[0] for b in b_raw}
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 450, 650); v.attributes("-topmost", True)
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
        cb_e = ctk.CTkOptionMenu(v, values=elos, width=300, command=change_elo); cb_e.pack(pady=10)
        cb_c = ctk.CTkOptionMenu(v, values=[], width=300, command=update_note); cb_c.pack(pady=10)
        e_n = ctk.CTkEntry(v, width=300, state="readonly"); e_n.pack(pady=5)
        e_d = ctk.CTkEntry(v, width=300); e_d.insert(0, "10"); e_d.pack(pady=10)
        if elos: change_elo(elos[0])
        def go():
            from core.logic import calcular_fecha_limite_sugerida; from core.database import crear_pedido
            f_fin = calcular_fecha_limite_sugerida(int(e_d.get())).split(' ')[0]
            if crear_pedido(map_b[cb_b.get()], cb_b.get(), self.map_c_id[cb_c.get()], cb_c.get(), cb_e.get(), f_fin):
                v.destroy(); self.mostrar_pedidos()
        ctk.CTkButton(v, text="Iniciar", fg_color="#2ecc71", command=go).pack(pady=20)

    def abrir_ventana_reportar_abandono(self):
        sel = self.tabla_pedidos.selection()
        if not sel: return
        id_r = self.tabla_pedidos.item(sel)['values'][1]
        v = ctk.CTkToplevel(self); self.centrar_ventana(v, 350, 400); v.attributes("-topmost", True)
        e_elo = ctk.CTkEntry(v, placeholder_text="Elo dejado..."); e_elo.pack(pady=10)
        e_wr = ctk.CTkEntry(v, placeholder_text="WR dejado..."); e_wr.pack(pady=10)
        def confirm():
            if registrar_abandono_db(id_r, e_elo.get().upper(), e_wr.get()): v.destroy(); self.mostrar_pedidos()
        ctk.CTkButton(v, text="Confirmar DROP", fg_color="#e74c3c", command=confirm).pack()
    
    def ejecutar_backup_manual(self):
        try:
            from core.database import realizar_backup_db
            realizar_backup_db()
            messagebox.showinfo("Seguridad", "✅ Base de datos respaldada con éxito.\nRevisa la carpeta /backups")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el respaldo: {e}")

if __name__ == "__main__":
    app = PerezBoostApp()
    app.mainloop()