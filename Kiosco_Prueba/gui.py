import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from components import RoundedButton

class KioscoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kiosco Concurrente Inteligente")
        self.geometry("900x600")
        self.configure(bg="#FFFFFF")
        self.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#FFFFFF", foreground="#111827", fieldbackground="#FFFFFF", rowheight=28, font=("Arial", 10))
        style.configure("Treeview.Heading", background="#F3F4F6", foreground="#111827", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("Treeview", background=[('selected', '#E5E7EB')], foreground=[('selected', '#111827')])

        self.current_user = None
        self.current_view = "login"
        
        # Referencias de componentes dinámicos
        self.client_tree = None
        self.admin_stock_tree = None
        self.admin_orders_tree = None

        self.container = tk.Frame(self, bg="#FFFFFF")
        self.container.pack(fill="both", expand=True)
        
        self.show_login_frame()
        self.loop_actualizacion_automatica()

    def clear_container(self):
        self.client_tree = None
        self.admin_stock_tree = None
        self.admin_orders_tree = None
        for widget in self.container.winfo_children():
            widget.destroy()

    def loop_actualizacion_automatica(self):
        """ Polling continuo que refresca las pantallas visuales de forma asíncrona """
        if self.current_view == "client" and self.client_tree:
            self.refrescar_tabla_cliente()
        elif self.current_view == "admin" and self.admin_stock_tree and self.admin_orders_tree:
            self.refrescar_tablas_admin()
            
        self.after(1000, self.loop_actualizacion_automatica)

    def refrescar_tabla_cliente(self):
        if not self.client_tree: return
        items_seleccionados = self.client_tree.selection()
        for item in self.client_tree.get_children(): self.client_tree.delete(item)
        for row in db.obtener_productos_cliente():
            self.client_tree.insert("", "end", values=(row[0], row[1], f"${row[2]:.2f}", f"{row[3]} u."))
        if items_seleccionados and self.client_tree.exists(items_seleccionados[0]):
            self.client_tree.selection_set(items_seleccionados[0])

    def refrescar_tablas_admin(self):
        if not self.admin_stock_tree or not self.admin_orders_tree: return
        sel_stock = self.admin_stock_tree.selection()
        sel_orders = self.admin_orders_tree.selection()
        
        for item in self.admin_stock_tree.get_children(): self.admin_stock_tree.delete(item)
        for item in self.admin_orders_tree.get_children(): self.admin_orders_tree.delete(item)
        
        for r in db.obtener_todos_los_productos(): 
            self.admin_stock_tree.insert("", "end", values=(r[0], r[1], f"{r[2]} u.", f"${r[3]:.2f}"))
        for r in db.obtener_todos_los_pedidos(): 
            self.admin_orders_tree.insert("", "end", values=r)
            
        if sel_stock and self.admin_stock_tree.exists(sel_stock[0]): self.admin_stock_tree.selection_set(sel_stock[0])
        if sel_orders and self.admin_orders_tree.exists(sel_orders[0]): self.admin_orders_tree.selection_set(sel_orders[0])

    # --- PANTALLAS ---
    def show_login_frame(self):
        self.current_view = "login"
        self.clear_container()
        frame = tk.Frame(self.container, bg="#FFFFFF")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="Kiosco Multifilos", font=("Arial", 20, "bold"), bg="#FFFFFF", fg="#111827").pack(pady=(0, 20))
        
        tk.Label(frame, text="Usuario", font=("Arial", 10), bg="#FFFFFF", fg="#6B7280").pack(anchor="w", pady=(10, 2))
        username_entry = tk.Entry(frame, font=("Arial", 12), bg="#F3F4F6", relief="flat", width=25)
        username_entry.pack(ipady=6)
        
        tk.Label(frame, text="Contraseña", font=("Arial", 10), bg="#FFFFFF", fg="#6B7280").pack(anchor="w", pady=(10, 2))
        password_entry = tk.Entry(frame, font=("Arial", 12), bg="#F3F4F6", relief="flat", show="*", width=25)
        password_entry.pack(ipady=6)
        
        def ejecutar_login():
            user = username_entry.get().strip()
            password = password_entry.get().strip()
            role = db.verificar_login(user, password)
            if role:
                self.current_user = user
                self.show_admin_frame() if role == 'admin' else self.show_client_frame()
            else:
                messagebox.showerror("Error", "Credenciales incorrectas.")

        RoundedButton(frame, "Iniciar Sesión", ejecutar_login, width=230, height=40, bg_color="#FFFFFF").pack(pady=(25, 10))
        lbl_reg = tk.Label(frame, text="¿No tienes cuenta? Regístrate", font=("Arial", 9, "underline"), bg="#FFFFFF", fg="#4B5563", cursor="hand2")
        lbl_reg.pack()
        lbl_reg.bind("<Button-1>", lambda e: self.show_register_frame())

    def show_register_frame(self):
        self.current_view = "register"
        self.clear_container()
        frame = tk.Frame(self.container, bg="#FFFFFF")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="Nuevo Registro", font=("Arial", 20, "bold"), bg="#FFFFFF", fg="#111827").pack(pady=(0, 20))
        username_entry = tk.Entry(frame, font=("Arial", 12), bg="#F3F4F6", relief="flat", width=25)
        username_entry.pack(ipady=6)
        password_entry = tk.Entry(frame, font=("Arial", 12), bg="#F3F4F6", relief="flat", show="*", width=25)
        password_entry.pack(ipady=6, pady=10)
        
        def ejecutar_registro():
            u, p = username_entry.get().strip(), password_entry.get().strip()
            if u.lower() == "admin" or not u or not p:
                messagebox.showwarning("Invalido", "Complete los campos adecuadamente.")
                return
            exito, msg = db.registrar_usuario(u, p)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.show_login_frame()
            else:
                messagebox.showerror("Error", msg)

        RoundedButton(frame, "Registrar", ejecutar_registro, width=230, height=40, color="#10B981", bg_color="#FFFFFF").pack(pady=10)
        RoundedButton(frame, "Regresar", self.show_login_frame, width=230, height=36, color="#6B7280", bg_color="#FFFFFF").pack()

    def show_client_frame(self):
        self.current_view = "client"
        self.clear_container()
        
        header = tk.Frame(self.container, bg="#F9FAFB", height=60)
        header.pack(fill="x")
        tk.Label(header, text=f"Cliente: {self.current_user}", font=("Arial", 12, "bold"), bg="#F9FAFB").pack(side="left", padx=20)
        RoundedButton(header, "Cerrar Sesión", self.show_login_frame, width=110, height=30, color="#EF4444", bg_color="#F9FAFB").pack(side="right", padx=20, pady=15)
        
        body = tk.Frame(self.container, bg="#FFFFFF")
        body.pack(fill="both", expand=True, padx=30, pady=20)
        
        self.client_tree = ttk.Treeview(body, columns=("ID", "Producto", "Precio", "Stock"), show="headings", height=12)
        self.client_tree.heading("ID", text="ID"); self.client_tree.heading("Producto", text="Producto"); self.client_tree.heading("Precio", text="Precio"); self.client_tree.heading("Stock", text="Stock disponible")
        self.client_tree.column("ID", width=50, anchor="center"); self.client_tree.column("Producto", width=230); self.client_tree.column("Precio", width=90, anchor="center"); self.client_tree.column("Stock", width=120, anchor="center")
        self.client_tree.grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        panel_pedido = tk.Frame(body, bg="#F9FAFB", padx=20, pady=20)
        panel_pedido.grid(row=1, column=2, padx=(20, 0), sticky="nsew")
        
        tk.Label(panel_pedido, text="Cantidad a pedir:", font=("Arial", 10), bg="#F9FAFB").pack(anchor="w")
        qty_entry = tk.Entry(panel_pedido, font=("Arial", 12), width=15)
        qty_entry.pack(anchor="w", pady=5); qty_entry.insert(0, "1")

        def enviar_pedido_cola():
            selected = self.client_tree.selection()
            if not selected:
                messagebox.showwarning("Atención", "Seleccione un artículo.")
                return
            try:
                cantidad = int(qty_entry.get().strip())
                if cantidad <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Cantidad inválida.")
                return
                
            item = self.client_tree.item(selected[0])['values']
            
            # --- USO DE LA COLA ---
            db.encolar_pedido(self.current_user, item[0], item[1], cantidad)
            messagebox.showinfo("Cola Activada", "Su orden fue ingresada en la cola de procesamiento concurrentemente.")

        RoundedButton(panel_pedido, "Hacer Pedido", enviar_pedido_cola, width=160, height=38, color="#2563EB", bg_color="#F9FAFB").pack(pady=20)
        self.refrescar_tabla_cliente()

    def show_admin_frame(self):
        self.current_view = "admin"
        self.clear_container()
        
        header = tk.Frame(self.container, bg="#111827", height=60)
        header.pack(fill="x")
        tk.Label(header, text="Panel de Control (Admin)", font=("Arial", 12, "bold"), bg="#111827", fg="#FFFFFF").pack(side="left", padx=20)
        RoundedButton(header, "Cerrar Sesión", self.show_login_frame, width=110, height=30, color="#EF4444", bg_color="#111827").pack(side="right", padx=20, pady=15)
        
        body = tk.Frame(self.container, bg="#FFFFFF")
        body.pack(fill="both", expand=True, padx=20, pady=15)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=1)
        
        # Panel Izquierdo: Stock
        left_frame = tk.Frame(body, bg="#FFFFFF")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(left_frame, text="Inventario", font=("Arial", 12, "bold"), bg="#FFFFFF").pack(anchor="w")
        
        self.admin_stock_tree = ttk.Treeview(left_frame, columns=("ID", "Producto", "Stock", "Precio"), show="headings", height=8)
        self.admin_stock_tree.heading("ID", text="ID"); self.admin_stock_tree.heading("Producto", text="Producto"); self.admin_stock_tree.heading("Stock", text="Stock"); self.admin_stock_tree.heading("Precio", text="Precio")
        self.admin_stock_tree.column("ID", width=40); self.admin_stock_tree.column("Stock", width=60); self.admin_stock_tree.column("Precio", width=70)
        self.admin_stock_tree.pack(fill="both", expand=True)
        
        form = tk.Frame(left_frame, bg="#F9FAFB", padx=5, pady=5)
        form.pack(fill="x", pady=(10, 0))
        entry_name = tk.Entry(form, width=12); entry_name.grid(row=0, column=0, padx=2)
        entry_qty = tk.Entry(form, width=5); entry_qty.grid(row=0, column=1, padx=2)
        entry_price = tk.Entry(form, width=7); entry_price.grid(row=0, column=2, padx=2)
        
        def añadir_item():
            try:
                db.agregar_producto(entry_name.get(), int(entry_qty.get()), float(entry_price.get()))
                self.refrescar_tablas_admin()
                entry_name.delete(0, tk.END); entry_qty.delete(0, tk.END); entry_price.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Error", "Variables incorrectas.")
                
        RoundedButton(form, "+ Añadir", añadir_item, width=75, height=26, color="#10B981", bg_color="#F9FAFB").grid(row=0, column=3, padx=5)

        # Panel Derecho: Pedidos entrantes
        right_frame = tk.Frame(body, bg="#FFFFFF")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        tk.Label(right_frame, text="Pedidos de la Cola", font=("Arial", 12, "bold"), bg="#FFFFFF").pack(anchor="w")
        
        self.admin_orders_tree = ttk.Treeview(right_frame, columns=("ID", "User", "Prod", "Cant", "Est"), show="headings", height=8)
        self.admin_orders_tree.heading("ID", text="ID"); self.admin_orders_tree.heading("User", text="Cliente"); self.admin_orders_tree.heading("Prod", text="Prod"); self.admin_orders_tree.heading("Cant", text="Cant"); self.admin_orders_tree.heading("Est", text="Estado")
        self.admin_orders_tree.column("ID", width=30); self.admin_orders_tree.column("Cant", width=40); self.admin_orders_tree.column("Est", width=80)
        self.admin_orders_tree.pack(fill="both", expand=True)
        
        def marcar_completado():
            sel = self.admin_orders_tree.selection()
            if sel:
                val = self.admin_orders_tree.item(sel[0])['values']
                if val[4] != "Completado":
                    db.marcar_pedido_completado(val[0])
                    self.refrescar_tablas_admin()
        
        RoundedButton(right_frame, "Marcar Completado", marcar_completado, width=150, height=34, color="#2563EB", bg_color="#FFFFFF").pack(anchor="e", pady=(10, 0))
        self.refrescar_tablas_admin()
