import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from components import RoundedButton
import time

class KioscoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kiosco Multicompra Concurrente")
        self.geometry("1050x650") # <- CORREGIDO: Eliminado el error de geometría "1000(650)"
        self.configure(bg="#FFFFFF")
        self.resizable(False, False)
        
        self.current_user = None
        self.current_view = "login"
        self.carrito_actual = []
        
        self.tree_productos_cliente = None
        self.tree_carrito_cliente = None
        self.tree_admin_stock = None
        self.tree_admin_pedidos = None

        self.container = tk.Frame(self, bg="#FFFFFF")
        self.container.pack(fill="both", expand=True)
        
        self.aplicar_estilos()
        self.show_login_frame()
        self.loop_refresco_asincrono()

    def aplicar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#FFFFFF", foreground="#111827", fieldbackground="#FFFFFF", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", background="#F3F4F6", foreground="#111827", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("Treeview", background=[('selected', '#E5E7EB')], foreground=[('selected', '#111827')])

    def loop_refresco_asincrono(self):
        if self.current_view == "client_shop" and self.tree_productos_cliente:
            self.refrescar_catalogo_cliente()
        elif self.current_view == "admin_stock" and self.tree_admin_stock:
            self.refrescar_stock_admin()
        elif self.current_view == "admin_orders" and self.tree_admin_pedidos:
            self.refrescar_pedidos_admin()
        self.after(1500, self.loop_refresco_asincrono)

    def lanzar_alertas_usuario(self, username):
        alertas = db.chequear_alertas(username)
        for orden_id, estado in alertas:
            if estado == "En Proceso":
                messagebox.showinfo("Estado de Pedido", f"📦 ¡Tu pedido #{orden_id} fue aceptado y está EN PROCESO!")
            elif estado == "Terminado":
                messagebox.showinfo("Estado de Pedido", f"✅ ¡Tu pedido #{orden_id} está TERMINADO! Pasa a retirarlo.")
            elif estado == "Rechazado":
                messagebox.showerror("Estado de Pedido", f"❌ Tu pedido #{orden_id} ha sido RECHAZADO (Sin stock disponible o cancelado).")

    def cambiar_pantalla(self, vista_nombre):
        self.current_view = vista_nombre
        for w in self.container.winfo_children(): 
            w.destroy()
        
        self.tree_productos_cliente = None
        self.tree_carrito_cliente = None
        self.tree_admin_stock = None
        self.tree_admin_pedidos = None

    def show_login_frame(self):
        self.cambiar_pantalla("login")
        f = tk.Frame(self.container, bg="#FFFFFF")
        f.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(f, text="Kiosco 24 Horas", font=("Arial", 22, "bold"), bg="#FFFFFF", fg="#111827").pack(pady=10)
        
        tk.Label(f, text="Usuario", bg="#FFFFFF", fg="#6B7280").pack(anchor="w")
        e_user = tk.Entry(f, font=("Arial", 12), bg="#F3F4F6", relief="flat", width=28)
        e_user.pack(ipady=5, pady=5)
        
        tk.Label(f, text="Contraseña", bg="#FFFFFF", fg="#6B7280").pack(anchor="w")
        e_pass = tk.Entry(f, font=("Arial", 12), bg="#F3F4F6", relief="flat", show="*", width=28)
        e_pass.pack(ipady=5, pady=5)
        
        def login():
            u, p = e_user.get().strip(), e_pass.get().strip()
            role = db.verificar_login(u, p)
            if role:
                self.current_user = u
                if role == "admin":
                    self.show_admin_orders_frame()
                else:
                    self.show_client_home_frame()
            else:
                messagebox.showerror("Error", "Datos inválidos.")

        RoundedButton(f, "Ingresar", login, width=250, height=40).pack(pady=15)
        lbl = tk.Label(f, text="Registrar una nueva cuenta", font=("Arial", 9, "underline"), bg="#FFFFFF", fg="#4B5563", cursor="hand2")
        lbl.pack()
        lbl.bind("<Button-1>", lambda e: self.show_register_frame())

    def show_register_frame(self):
        self.cambiar_pantalla("register")
        f = tk.Frame(self.container, bg="#FFFFFF")
        f.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(f, text="Registro de Clientes", font=("Arial", 20, "bold"), bg="#FFFFFF").pack(pady=15)
        
        e_user = tk.Entry(f, font=("Arial", 12), bg="#F3F4F6", relief="flat", width=28)
        e_user.pack(ipady=5, pady=5)
        
        e_pass = tk.Entry(f, font=("Arial", 12), bg="#F3F4F6", relief="flat", show="*", width=28)
        e_pass.pack(ipady=5, pady=5)
        
        def registrar():
            u, p = e_user.get().strip(), e_pass.get().strip()
            if not u or not p or u.lower() == "admin": 
                return
            exito, msg = db.registrar_usuario(u, p)
            if exito: 
                messagebox.showinfo("Listo", msg)
                self.show_login_frame()
            else: 
                messagebox.showerror("Error", msg)

        RoundedButton(f, "Crear Cuenta", registrar, width=250, height=40, color="#10B981").pack(pady=10)
        RoundedButton(f, "Volver", self.show_login_frame, width=250, height=36, color="#6B7280").pack()

    def show_client_home_frame(self):
        self.cambiar_pantalla("client_home")
        
        h = tk.Frame(self.container, bg="#F9FAFB", height=60)
        h.pack(fill="x")
        tk.Label(h, text=f"👋 ¡Hola, {self.current_user}!", font=("Arial", 14, "bold"), bg="#F9FAFB").pack(side="left", padx=20)
        RoundedButton(h, "Cerrar Sesión", self.show_login_frame, width=110, height=30, color="#EF4444", bg_color="#F9FAFB").pack(side="right", padx=20, pady=15)

        body = tk.Frame(self.container, bg="#FFFFFF")
        body.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(body, text="Bienvenido al Kiosco Autoservicio", font=("Arial", 18, "bold"), bg="#FFFFFF").pack(pady=10)
        tk.Label(body, text="Desde aquí puedes armar tus pedidos agregando múltiples tipos de golosinas,\nbebidas y snacks a tu carrito simultáneamente.", font=("Arial", 11), bg="#FFFFFF", fg="#4B5563").pack(pady=10)
        
        RoundedButton(body, "🛒 Ir a Comprar Ahora", self.show_client_shop_frame, width=220, height=45, color="#2563EB").pack(pady=20)
        self.lanzar_alertas_usuario(self.current_user)

    def show_client_shop_frame(self):
        self.cambiar_pantalla("client_shop")
        self.carrito_actual = []
        
        h = tk.Frame(self.container, bg="#F3F4F6", height=50)
        h.pack(fill="x")
        tk.Label(h, text="Arma tu Pedido (Múltiples Productos)", font=("Arial", 12, "bold"), bg="#F3F4F6").pack(side="left", padx=15)
        RoundedButton(h, "🎛️ Volver al Inicio", self.show_client_home_frame, width=140, height=28, color="#4B5563", bg_color="#F3F4F6").pack(side="right", padx=15, pady=10)

        main_body = tk.Frame(self.container, bg="#FFFFFF")
        main_body.pack(fill="both", expand=True, padx=15, pady=15)
        main_body.columnconfigure(0, weight=3)
        main_body.columnconfigure(1, weight=2)

        izq = tk.Frame(main_body, bg="#FFFFFF")
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(izq, text="Productos en Góndola", font=("Arial", 11, "bold"), bg="#FFFFFF").pack(anchor="w", pady=5)
        
        self.tree_productos_cliente = ttk.Treeview(izq, columns=("ID", "Nombre", "Precio", "Stock", "Cat"), show="headings", height=12)
        self.tree_productos_cliente.heading("ID", text="ID")
        self.tree_productos_cliente.heading("Nombre", text="Producto")
        self.tree_productos_cliente.heading("Precio", text="Precio")
        self.tree_productos_cliente.heading("Stock", text="Stock")
        self.tree_productos_cliente.heading("Cat", text="Categoría")
        
        self.tree_productos_cliente.column("ID", width=35)
        self.tree_productos_cliente.column("Nombre", width=180)
        self.tree_productos_cliente.column("Precio", width=70)
        self.tree_productos_cliente.column("Stock", width=60)
        self.tree_productos_cliente.column("Cat", width=90)
        self.tree_productos_cliente.pack(fill="both", expand=True)

        form = tk.Frame(izq, bg="#FFFFFF")
        form.pack(fill="x", pady=10)
        
        def agregar_al_carrito():
            sel = self.tree_productos_cliente.selection()
            if not sel: 
                messagebox.showwarning("Selección", "Por favor, selecciona un producto de la góndola.")
                return
                
            item = self.tree_productos_cliente.item(sel[0])['values']
            p_id = item[0]
            nombre = item[1]
            precio = item[2]
            
            for i, (id_c, _, c_ant, _) in enumerate(self.carrito_actual):
                if id_c == p_id:
                    self.carrito_actual[i] = (p_id, nombre, c_ant + 1, precio)
                    self.refrescar_tabla_carrito_local()
                    return
            self.carrito_actual.append((p_id, nombre, 1, precio))
            self.refrescar_tabla_carrito_local()

        RoundedButton(form, "➕ Añadir (+1)", agregar_al_carrito, width=140, height=32, color="#10B981").pack(side="left")

        der = tk.Frame(main_body, bg="#F9FAFB", padx=10, pady=10)
        der.grid(row=0, column=1, sticky="nsew")
        tk.Label(der, text="Mi Carrito de Compras", font=("Arial", 11, "bold"), bg="#F9FAFB").pack(anchor="w")
        
        self.tree_carrito_cliente = ttk.Treeview(der, columns=("Nombre", "Cant", "Subtotal"), show="headings", height=8)
        self.tree_carrito_cliente.heading("Nombre", text="Item")
        self.tree_carrito_cliente.heading("Cant", text="Cant")
        self.tree_carrito_cliente.heading("Subtotal", text="Subtotal")
        
        self.tree_carrito_cliente.column("Nombre", width=120)
        self.tree_carrito_cliente.column("Cant", width=45)
        self.tree_carrito_cliente.column("Subtotal", width=70)
        self.tree_carrito_cliente.pack(fill="both", expand=True, pady=5)
        
        self.lbl_total = tk.Label(der, text="Total: $0.00", font=("Arial", 12, "bold"), bg="#F9FAFB", fg="#111827")
        self.lbl_total.pack(anchor="e", pady=5)

        def quitar_del_carrito():
            sel = self.tree_carrito_cliente.selection()
            if not sel:
                return
            idx = self.tree_carrito_cliente.index(sel[0])
            p_id, nombre, cant, precio = self.carrito_actual[idx]
            
            if cant > 1:
                self.carrito_actual[idx] = (p_id, nombre, cant - 1, precio)
            else:
                self.carrito_actual.pop(idx)
            self.refrescar_tabla_carrito_local()

        def despachar_carrito_completo():
            if not self.carrito_actual: 
                messagebox.showwarning("Vacío", "El carrito está vacío.")
                return
            
            orden_id = f"ORD-{int(time.time())}"
            db.encolar_carrito(self.current_user, orden_id, self.carrito_actual)
            
            messagebox.showinfo("En Cola", f"Tu orden conjunta #{orden_id} ha sido encolada de forma asíncrona.")
            self.carrito_actual = []
            self.refrescar_tabla_carrito_local()

        btn_container = tk.Frame(der, bg="#F9FAFB")
        btn_container.pack(fill="x", pady=5)

        RoundedButton(btn_container, "➖ Quitar (-1)", quitar_del_carrito, width=110, height=36, color="#EF4444", bg_color="#F9FAFB").pack(side="left")
        RoundedButton(btn_container, "🚀 Confirmar Pedido", despachar_carrito_completo, width=160, height=36, color="#2563EB", bg_color="#F9FAFB").pack(side="right")
        
        self.refrescar_catalogo_cliente()

    def refrescar_catalogo_cliente(self):
        if not self.tree_productos_cliente: 
            return
        
        id_seleccionado = None
        sel = self.tree_productos_cliente.selection()
        if sel:
            id_seleccionado = self.tree_productos_cliente.item(sel[0])['values'][0]

        for i in self.tree_productos_cliente.get_children(): 
            self.tree_productos_cliente.delete(i)
            
        for r in db.obtener_productos():
            nodo = self.tree_productos_cliente.insert("", "end", values=(r[0], r[1], f"${r[3]:.2f}", f"{r[2]} u.", r[4]))
            if id_seleccionado is not None and int(r[0]) == int(id_seleccionado):
                self.tree_productos_cliente.selection_set(nodo)

    def refrescar_tabla_carrito_local(self):
        for i in self.tree_carrito_cliente.get_children(): 
            self.tree_carrito_cliente.delete(i)
        total = 0.0
        for p_id, nombre, cant, precio_str in self.carrito_actual:
            precio = float(str(precio_str).replace('$', ''))
            sub = cant * precio
            total += sub
            self.tree_carrito_cliente.insert("", "end", values=(nombre, cant, f"${sub:.2f}"))
        self.lbl_total.config(text=f"Total: ${total:.2f}")

    def dibujar_menu_navegacion_admin(self):
        nav = tk.Frame(self.container, bg="#111827", width=180)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        
        tk.Label(nav, text="PANEL ADMIN", font=("Arial", 11, "bold"), bg="#111827", fg="#9CA3AF").pack(pady=20)
        
        RoundedButton(nav, "📋 Ver Pedidos", self.show_admin_orders_frame, width=150, height=35, color="#1F2937", bg_color="#111827").pack(pady=10)
        RoundedButton(nav, "📦 Gestionar Stock", self.show_admin_stock_frame, width=150, height=35, color="#1F2937", bg_color="#111827").pack(pady=10)
        
        tk.Frame(nav, bg="#374151", height=1).pack(fill="x", pady=20)
        RoundedButton(nav, "Salir", self.show_login_frame, width=150, height=32, color="#EF4444", bg_color="#111827").pack(side="bottom", pady=20)

    def abir_popup_detalle_pedido(self, orden_id, cliente):
        """Abre una ventana flotante limpia que detalla el contenido de la orden elegida."""
        popup = tk.Toplevel(self)
        popup.title(f"Detalle de Orden: {orden_id}")
        popup.geometry("500x400")
        popup.configure(bg="#FFFFFF")
        popup.grab_set() # Bloquea la ventana de atrás hasta cerrar el popup
        
        tk.Label(popup, text=f"📦 Contenido de la Orden", font=("Arial", 14, "bold"), bg="#FFFFFF", fg="#111827").pack(anchor="w", padx=15, pady=(15, 2))
        tk.Label(popup, text=f"Cliente: {cliente}  |  Código: {orden_id}", font=("Arial", 10), bg="#FFFFFF", fg="#4B5563").pack(anchor="w", padx=15, pady=(0, 10))
        
        # Tabla interna del Popup
        tree_detalle = ttk.Treeview(popup, columns=("Producto", "Cant", "Precio", "Subtotal"), show="headings", height=8)
        tree_detalle.heading("Producto", text="Producto")
        tree_detalle.heading("Cant", text="Cant.")
        tree_detalle.heading("Precio", text="Precio Unit.")
        tree_detalle.heading("Subtotal", text="Subtotal")
        
        tree_detalle.column("Producto", width=180)
        tree_detalle.column("Cant", width=60, anchor="center")
        tree_detalle.column("Precio", width=90, anchor="e")
        tree_detalle.column("Subtotal", width=90, anchor="e")
        tree_detalle.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Cargar los artículos reales filtrados por esa orden en particular
        total_orden = 0.0
        todos_los_pedidos = db.obtener_pedidos_agrupados()
        for r in todos_los_pedidos:
            # Filtramos en base al esquema original: r[1] = Cód Orden, r[3] = Producto, r[4] = Cant, r[5] = Estado
            # Nota: Si tu db.obtener_productos guarda los precios unitarios, puedes adaptarlo. Aquí calculamos un estimado visual.
            if r[1] == orden_id:
                # Buscamos o simulamos el precio unitario del catálogo real para rellenar
                nombre_prod = r[3]
                cantidad = int(r[4])
                
                # Buscaremos el precio del producto en la DB original
                precio_unitario = 0.0
                for p in db.obtener_productos():
                    if p[1] == nombre_prod:
                        precio_unitario = float(p[3])
                        break
                
                subtotal = cantidad * precio_unitario
                total_orden += subtotal
                tree_detalle.insert("", "end", values=(nombre_prod, cantidad, f"${precio_unitario:.2f}", f"${subtotal:.2f}"))
                
        tk.Label(popup, text=f"Monto Estimado Total: ${total_orden:.2f}", font=("Arial", 12, "bold"), bg="#FFFFFF", fg="#2563EB").pack(anchor="e", padx=15, pady=10)
        RoundedButton(popup, "Cerrar Ventana", popup.destroy, width=140, height=32, color="#6B7280", bg_color="#FFFFFF").pack(pady=(0, 15))

    def show_admin_orders_frame(self):
        self.cambiar_pantalla("admin_orders")
        self.dibujar_menu_navegacion_admin()
        
        derecha = tk.Frame(self.container, bg="#FFFFFF", padx=20, pady=20)
        derecha.pack(side="right", fill="both", expand=True)
        tk.Label(derecha, text="Gestión Integral de Pedidos de la Cola", font=("Arial", 15, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 15))
        
        # MODIFICADO: Columnas simplificadas para ver las órdenes de manera individual (sin duplicados visuales)
        self.tree_admin_pedidos = ttk.Treeview(derecha, columns=("Orden", "Cliente", "Estado"), show="headings")
        self.tree_admin_pedidos.heading("Orden", text="Código de Orden")
        self.tree_admin_pedidos.heading("Cliente", text="Cliente")
        self.tree_admin_pedidos.heading("Estado", text="Estado de la Orden")
        
        self.tree_admin_pedidos.column("Orden", width=150, anchor="center")
        self.tree_admin_pedidos.column("Cliente", width=150, anchor="center")
        self.tree_admin_pedidos.column("Estado", width=120, anchor="center")
        self.tree_admin_pedidos.pack(fill="both", expand=True)

        btn_bar = tk.Frame(derecha, bg="#FFFFFF")
        btn_bar.pack(fill="x", pady=15)
        
        def revisar_pedido_seleccionado():
            sel = self.tree_admin_pedidos.selection()
            if not sel:
                messagebox.showwarning("Atención", "Selecciona una orden de la lista para revisar.")
                return
            valores = self.tree_admin_pedidos.item(sel[0])['values']
            self.abir_popup_detalle_pedido(valores[0], valores[1])

        def cambiar_a(estado):
            sel = self.tree_admin_pedidos.selection()
            if not sel: 
                messagebox.showwarning("Atención", "Selecciona una orden de la lista primero.")
                return
            orden_id = self.tree_admin_pedidos.item(sel[0])['values'][0]
            db.cambiar_estado_pedido(orden_id, estado)
            self.refrescar_pedidos_admin()

        # NUEVO BOTÓN: Abre el desplegable/pop-up informativo
        RoundedButton(btn_bar, "🔍 Revisar Detalle", revisar_pedido_seleccionado, width=150, height=35, color="#2563EB").pack(side="left", padx=5)
        RoundedButton(btn_bar, "⚙️ Aceptar (En Proceso)", lambda: cambiar_a("En Proceso"), width=160, height=35, color="#F59E0B").pack(side="left", padx=5)
        RoundedButton(btn_bar, "✅ Terminar Pedido", lambda: cambiar_a("Terminado"), width=160, height=35, color="#10B981").pack(side="left", padx=5)
        RoundedButton(btn_bar, "❌ Rechazar / Cancelar", lambda: cambiar_a("Rechazado"), width=160, height=35, color="#EF4444").pack(side="left", padx=5)
        
        self.refrescar_pedidos_admin()

    def show_admin_stock_frame(self):
        self.cambiar_pantalla("admin_stock")
        self.dibujar_menu_navegacion_admin()
        
        derecha = tk.Frame(self.container, bg="#FFFFFF", padx=20, pady=20)
        derecha.pack(side="right", fill="both", expand=True)
        tk.Label(derecha, text="Inventario & Reabastecimiento de Kiosco", font=("Arial", 15, "bold"), bg="#FFFFFF").pack(anchor="w", pady=(0, 15))
        
        self.tree_admin_stock = ttk.Treeview(derecha, columns=("ID", "Producto", "Stock", "Precio", "Cat"), show="headings", height=10)
        self.tree_admin_stock.heading("ID", text="ID")
        self.tree_admin_stock.heading("Producto", text="Producto")
        self.tree_admin_stock.heading("Stock", text="Stock")
        self.tree_admin_stock.heading("Precio", text="Precio")
        self.tree_admin_stock.heading("Cat", text="Categoría")
        
        self.tree_admin_stock.column("ID", width=40)
        self.tree_admin_stock.column("Stock", width=80)
        self.tree_admin_stock.column("Precio", width=80)
        self.tree_admin_stock.pack(fill="both", expand=True)

        f_add = tk.LabelFrame(derecha, text="Insertar / Reabastecer Producto Nuevo", bg="#FFFFFF", padx=10, pady=10)
        f_add.pack(fill="x", pady=15)
        
        tk.Label(f_add, text="Nombre:", bg="#FFFFFF").grid(row=0, column=0, sticky="w")
        e_name = tk.Entry(f_add, width=15)
        e_name.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(f_add, text="Cant:", bg="#FFFFFF").grid(row=0, column=2, sticky="w")
        e_qty = tk.Entry(f_add, width=8)
        e_qty.grid(row=0, column=3, padx=5, pady=2)
        
        tk.Label(f_add, text="Precio ($):", bg="#FFFFFF").grid(row=0, column=4, sticky="w")
        e_price = tk.Entry(f_add, width=8)
        e_price.grid(row=0, column=5, padx=5, pady=2)
        
        tk.Label(f_add, text="Categoría:", bg="#FFFFFF").grid(row=0, column=6, sticky="w")
        e_cat = tk.Entry(f_add, width=12)
        e_cat.grid(row=0, column=7, padx=5, pady=2)
        e_cat.insert(0, "Golosinas")

        def guardar_producto():
            try:
                name = e_name.get().strip()
                qty = int(e_qty.get().strip())
                price = float(e_price.get().strip())
                cat = e_cat.get().strip()
                if not name or qty < 0 or price < 0: 
                    raise ValueError
                db.agregar_producto(name, qty, price, cat)
                self.refrescar_stock_admin()
                e_name.delete(0, tk.END)
                e_qty.delete(0, tk.END)
                e_price.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Error", "Campos incorrectos.")

        RoundedButton(f_add, "➕ Registrar Item", guardar_producto, width=140, height=28, color="#10B981", bg_color="#FFFFFF").grid(row=0, column=8, padx=10)
        self.refrescar_stock_admin()

    def refrescar_pedidos_admin(self):
        if not self.tree_admin_pedidos: 
            return
        
        # Conservar selección por código de orden
        id_seleccionado = None
        sel = self.tree_admin_pedidos.selection()
        if sel:
            id_seleccionado = self.tree_admin_pedidos.item(sel[0])['values'][0]

        for i in self.tree_admin_pedidos.get_children(): 
            self.tree_admin_pedidos.delete(i)
            
        # MODIFICADO: Agrupamos las líneas repetidas en la vista principal usando un set para evitar duplicados
        ordenes_procesadas = set()
        for r in db.obtener_pedidos_agrupados():
            # Estructura devuelta por base de datos: (ID, Cod_Orden, Cliente, Producto, Cant, Estado)
            orden_id = r[1]
            cliente = r[2]
            estado = r[5]
            
            if orden_id not in ordenes_procesadas:
                ordenes_procesadas.add(orden_id)
                nodo = self.tree_admin_pedidos.insert("", "end", values=(orden_id, cliente, estado))
                if id_seleccionado is not None and str(orden_id) == str(id_seleccionado):
                    self.tree_admin_pedidos.selection_set(nodo)

    def refrescar_stock_admin(self):
        if not self.tree_admin_stock: 
            return
        
        id_seleccionado = None
        sel = self.tree_admin_stock.selection()
        if sel:
            id_seleccionado = self.tree_admin_stock.item(sel[0])['values'][0]

        for i in self.tree_admin_stock.get_children(): 
            self.tree_admin_stock.delete(i)
            
        for r in db.obtener_productos():
            nodo = self.tree_admin_stock.insert("", "end", values=(r[0], r[1], f"{r[2]} u.", f"${r[3]:.2f}", r[4]))
            if id_seleccionado is not None and int(r[0]) == int(id_seleccionado):
                self.tree_admin_stock.selection_set(nodo)
