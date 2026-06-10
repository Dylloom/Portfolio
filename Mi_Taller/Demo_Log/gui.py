import tkinter as tk
from tkinter import messagebox
import threading  # MODULO CLAVE: Permite ejecutar tareas en segundo plano sin congelar la ventana gráfica
from auth import verificar_credenciales
from hardware import simulacion_nfc_thread
from database import (
    obtener_registros_acceso, obtener_todo_db, registrar_usuario, 
    obtener_rol, cambiar_rol_usuario, eliminar_usuario_db
)
from config import cola_mensajes, TITULO_APP

# ==========================================
#  PALETA DE COLORES (Estilo Dark Mode Premium)
# ==========================================
COLOR_BG = "#1E1E2E"        # Color de fondo de las ventanas principales
COLOR_CARD = "#252538"      # Color de fondo para las tarjetas contenedoras contenedores
COLOR_TEXT = "#CDD6F4"      # Color de los títulos y texto principal (blanco suave)
COLOR_SUBTEXT = "#A6ADC8"   # Color para aclaraciones o subtítulos (gris)
COLOR_INPUT = "#11111B"     # Color de fondo para los campos de entrada de datos (Entry)
COLOR_GREEN = "#A6E3A1"     # Color verde de éxito (Aperturas, confirmaciones)
COLOR_RED = "#F38BA8"       # Color rojo de alerta (Fallos, eliminaciones)
COLOR_PURPLE = "#CBA6F7"    # Color púrpura identificativo para logs de accesos
COLOR_BLUE = "#89B4FA"      # Color azul para visualización y gestión del sistema

# ==========================================
#  COMPONENTE PERSONALIZADO: BotonRedondeado
# ==========================================
class BotonRedondeado(tk.Canvas):
    """
    Simula un botón estilizado con esquinas suavizadas usando un objeto Canvas de Tkinter.
    Evita el aspecto clásico y rígido de los botones nativos del sistema operativo.
    """
    def __init__(self, parent, text, command, bg, fg, width, height, radius=18, font=("Arial", 10, "bold")):
        self.w = width
        self.h = height
        # Inicializa el lienzo (Canvas) ajustándolo al color de fondo de la ventana padre
        super().__init__(parent, width=self.w, height=self.h, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command = command # Acción/Función que se ejecutará al pulsar el botón
        self.bg = bg           # Color de fondo del botón
        self.fg = fg           # Color de la fuente del botón
        self.radius = radius   # Nivel de redondeado periférico
        self.text_str = text   # Texto que mostrará el botón
        self.font = font       # Tipo y tamaño de letra
        self.estado = "normal" # Control del estado del botón ('normal' o 'disabled')
        self.dibujar()

    def dibujar(self):
        """Calcula los puntos vectoriales del polígono para trazar las curvas del botón."""
        self.delete("all")
        r = self.radius
        # Lista de coordenadas matemáticas que forman la silueta redondeada en base a las dimensiones dadas
        points = [r, 0, r, 0, self.w-r, 0, self.w-r, 0, self.w, 0, self.w, r, self.w, r, self.w, self.h-r, self.w, self.h-r, self.w, self.h, self.w-r, self.h, self.w-r, self.h, r, self.h, r, self.h, 0, self.h, 0, self.h-r, 0, self.h-r, 0, r, 0, r, 0, 0]
        # Dibuja la figura y posiciona el texto exactamente en el centro geométrico del botón
        self.rect_id = self.create_polygon(points, fill=self.bg, smooth=True)
        self.text_id = self.create_text(self.w // 2, self.h // 2, text=self.text_str, fill=self.fg, font=self.font)
        
        # Si el botón no está deshabilitado, enlaza el click izquierdo ("<Button-1>") con el comando
        if self.estado == "normal":
            self.tag_bind(self.rect_id, "<Button-1>", lambda e: self.command())
            self.tag_bind(self.text_id, "<Button-1>", lambda e: self.command())

    def configurar_estado(self, nuevo_estado, nuevo_bg=None):
        """Cambia dinámicamente la disponibilidad del botón (útil para bloquear accesos durante procesos)."""
        self.estado = nuevo_estado
        if nuevo_estado == "disabled":
            self.bg = "#45475A" # Tono gris oscuro que denota inactividad
        else:
            self.bg = nuevo_bg or "#27AE60"
        self.dibujar()


# ==========================================
#  CLASE PRINCIPAL: InterfazNFC (Controlador GUI)
# ==========================================
class InterfazNFC:
    def __init__(self, root):
        """Prepara el escenario gráfico inicial de la aplicación."""
        self.root = root
        self.root.title(TITULO_APP)
        self.root.geometry("380x660")
        self.root.configure(bg=COLOR_BG)
        
        self.usuario_actual = None # Almacenará la sesión del usuario que ingrese con éxito
        
        # Contenedor dinámico principal donde se irán montando y desmontando las diferentes pantallas
        self.contenedor = tk.Frame(self.root, bg=COLOR_BG)
        self.contenedor.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Carga la pantalla de bienvenida/identificación por defecto
        self.pantalla_login()

    def limpiar_pantalla(self):
        """Remueve todos los componentes gráficos activos dentro del contenedor para cambiar de vista de forma limpia."""
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    # --- SCREEN 1: LOGIN (Identificación) ---
    def pantalla_login(self):
        """Construye los campos de formulario para iniciar sesión."""
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        # Encabezado visual
        tk.Label(card, text="🛡️", font=("Arial", 36), bg=COLOR_CARD).pack(pady=(20, 5))
        tk.Label(card, text="CONTROL DE ACCESO", font=("Arial", 14, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack()
        tk.Label(card, text="Por favor, identifíquese", font=("Arial", 9), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=(0, 20))
        
        # Input Usuario
        tk.Label(card, text="Usuario", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.entry_user = tk.Entry(card, font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.entry_user.pack(fill="x", padx=30, pady=(5, 15), ipady=6)
        
        # Input Contraseña
        tk.Label(card, text="Contraseña", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.entry_pass = tk.Entry(card, show="*", font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.entry_pass.pack(fill="x", padx=30, pady=(5, 20), ipady=6)
        
        # Botones de Acción
        btn_ingresar = BotonRedondeado(card, text="INGRESAR", command=self.intentar_login, bg=COLOR_GREEN, fg=COLOR_INPUT, width=220, height=40)
        btn_ingresar.pack(pady=5)

        btn_ir_registro = BotonRedondeado(card, text="CREAR CUENTA NUEVA", command=self.pantalla_registro, bg=COLOR_BLUE, fg=COLOR_INPUT, width=220, height=35)
        btn_ir_registro.pack(pady=10)

    def intentar_login(self):
        """Valida los textos introducidos contrastándolos con las funciones de autenticación de la base de datos."""
        user = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        if verificar_credenciales(user, password):
            self.usuario_actual = user
            self.pantalla_puerta() # Redirige a la pantalla operativa si las credenciales coinciden
        else:
            messagebox.showerror("Error", "Credenciales incorrectas.")

    # --- SCREEN 2: REGISTRO DE USUARIOS NUEVOS ---
    def pantalla_registro(self):
        """Crea la interfaz de registro. Cualquier cuenta creada aquí ingresará por defecto como rol común."""
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        tk.Label(card, text="📝", font=("Arial", 36), bg=COLOR_CARD).pack(pady=(20, 5))
        tk.Label(card, text="NUEVO REGISTRO", font=("Arial", 14, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack()
        tk.Label(card, text="El acceso de administrador está restringido", font=("Arial", 8), fg=COLOR_RED, bg=COLOR_CARD).pack(pady=(0, 20))

        tk.Label(card, text="Elige un Usuario", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.reg_user = tk.Entry(card, font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.reg_user.pack(fill="x", padx=30, pady=(5, 15), ipady=6)
        
        tk.Label(card, text="Elige una Contraseña", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.reg_pass = tk.Entry(card, show="*", font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.reg_pass.pack(fill="x", padx=30, pady=(5, 25), ipady=6)

        btn_confirmar = BotonRedondeado(card, text="REGISTRARSE", command=self.intentar_registro, bg=COLOR_GREEN, fg=COLOR_INPUT, width=220, height=40)
        btn_confirmar.pack(pady=5)

        btn_volver = BotonRedondeado(card, text="VOLVER AL LOGIN", command=self.pantalla_login, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=220, height=35)
        btn_volver.pack(pady=10)

    def intentar_registro(self):
        """Valida campos vacíos e intenta añadir la nueva cuenta en SQLite."""
        nuevo_usuario = self.reg_user.get().strip()
        nueva_pass = self.reg_pass.get().strip()

        if not nuevo_usuario or not nueva_pass:
            messagebox.showwarning("Campos Vacíos", "Por favor completa todos los datos.")
            return

        exito = registrar_usuario(nuevo_usuario, nueva_pass)
        if exito:
            messagebox.showinfo("Éxito", f"¡Usuario '{nuevo_usuario}' registrado con éxito!")
            self.pantalla_login()
        else:
            messagebox.showerror("Error", "Ese nombre de usuario ya se encuentra registrado.")

    # --- SCREEN 3: PANEL DE CONTROL DE OPERACIONES (Puerta / NFC) ---
    def pantalla_puerta(self):
        """
        Esta es la vista de control central. 
        Implementa una evaluación basada en el Rol del usuario para ocultar o desvelar las funciones críticas de Admin.
        """
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        rol_actual = obtener_rol(self.usuario_actual)
        tk.Label(card, text=f"Usuario activo: {self.usuario_actual} ({rol_actual.upper()})", font=("Arial", 9, "italic"), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=10)

        self.label_estado = tk.Label(card, text="Listo para operar", font=("Arial", 13, "bold"), fg=COLOR_SUBTEXT, bg=COLOR_CARD)
        self.label_estado.pack(pady=(15, 5))
        
        # Botones comunes compartidos por cualquier nivel de usuario
        self.btn_abrir = BotonRedondeado(card, text="ABRIR PUERTA", command=lambda: self.ejecutar_proceso_nfc(forzar_fallo=False), bg=COLOR_GREEN, fg=COLOR_INPUT, width=240, height=45, radius=18)
        self.btn_abrir.pack(pady=8)

        self.btn_fallar = BotonRedondeado(card, text="SIMULAR FALLO NFC", command=lambda: self.ejecutar_proceso_nfc(forzar_fallo=True), bg=COLOR_RED, fg=COLOR_INPUT, width=240, height=45, radius=18)
        self.btn_fallar.pack(pady=8)

        # -------------------------------------------------------------
        # SEGURIDAD DE ACCESO: BLINDAJE DE HERRAMIENTAS ADMINISTRATIVAS
        # -------------------------------------------------------------
        # Si el usuario que inició sesión no cuenta con rol "admin" en la BD,
        # estas líneas de código se omiten por completo, bloqueando físicamente los botones de la pantalla.
        if rol_actual == "admin":
            tk.Label(card, text="Herramientas de Admin", font=("Arial", 8, "bold"), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=(15,0))
            
            self.btn_admin = BotonRedondeado(card, text="VER REGISTROS ACCESO", command=self.abrir_ventana_logs, bg=COLOR_PURPLE, fg=COLOR_INPUT, width=240, height=35, radius=15)
            self.btn_admin.pack(pady=4)
            
            self.btn_admin_todo = BotonRedondeado(card, text="VER BD COMPLETA (TABLAS)", command=self.abrir_ventana_bd_completa, bg=COLOR_BLUE, fg=COLOR_INPUT, width=240, height=35, radius=15)
            self.btn_admin_todo.pack(pady=4)

            self.btn_gestion_usr = BotonRedondeado(card, text="GESTIONAR USUARIOS", command=self.abrir_ventana_gestion_usuarios, bg=COLOR_GREEN, fg=COLOR_INPUT, width=240, height=35, radius=15)
            self.btn_gestion_usr.pack(pady=4)

    # ---------------------------------------------------------------------------------
    #  MANEJO DE HILOS (MULTITHREADING ARQUITECTURA)
    # ---------------------------------------------------------------------------------
    def ejecutar_proceso_nfc(self, forzar_fallo):
        """
        ZONA DE USO DE HILOS #1: Lanzamiento del proceso de Hardware de forma paralela.
        
        ¿Por qué se usa un hilo aquí? 
        El proceso de lectura y validación NFC físico o simulado involucra retardos (`time.sleep`). 
        Si ejecutáramos esa tarea directamente en el mismo flujo de la GUI, la interfaz visual se congelaría por completo, 
        el usuario vería un cartel de "No responde" y no se procesarían los gráficos.
        """
        # 1. Deshabilitamos de inmediato todos los botones disponibles en la pantalla para impedir dobles clicks
        self.btn_abrir.configurar_estado("disabled")
        self.btn_fallar.configurar_estado("disabled")
        if hasattr(self, 'btn_admin'): self.btn_admin.configurar_estado("disabled")
        if hasattr(self, 'btn_admin_todo'): self.btn_admin_todo.configurar_estado("disabled")
        if hasattr(self, 'btn_gestion_usr'): self.btn_gestion_usr.configurar_estado("disabled")
        
        # 2. CREACIÓN DEL HILO SECUNDARIO (TRABAJADOR / WORKER THREAD):
        # Apunta a la función importada `simulacion_nfc_thread` y le transmite los parámetros requeridos.
        hilo_hardware = threading.Thread(target=simulacion_nfc_thread, args=(self.usuario_actual, forzar_fallo))
        
        # 3. ARRANQUE DEL HILO: 
        # Empieza a correr de manera simultánea e independiente en la memoria de la computadora.
        hilo_hardware.start()
        
        # 4. LLAMADO DEL ESCUCHADOR GRÁFICO:
        # Pone a la interfaz a monitorear qué está haciendo el hilo secundario sin interferir en su velocidad.
        self.escuchar_cola()

    def escuchar_cola(self):
        """
        ZONA DE USO DE HILOS #2: Escuchador recurrente (Polling Loop) asíncrono.
        
        Tkinter NO es "Thread-Safe" (no es seguro modificar la pantalla directamente desde un hilo secundario ya que colapsa). 
        Por ello, el hilo secundario escribe sus avances en un conducto protegido llamado `cola_mensajes` (Queue).
        Esta función se encarga de revisar esa cola de manera constante y segura desde el hilo principal de los gráficos.
        """
        try:
            # Intenta obtener de forma inmediata el mensaje que el hilo secundario depositó en la cola
            mensaje = cola_mensajes.get_nowait()
            
            # Si el mensaje recibido indica el fin absoluto del proceso de hardware
            if mensaje == "TERMINADO":
                self.label_estado.config(text="Listo para operar", fg=COLOR_SUBTEXT)
                
                # Despierta y restaura el estado "normal" e interactivo de los botones
                self.btn_abrir.configurar_estado("normal", COLOR_GREEN)
                self.btn_fallar.configurar_estado("normal", COLOR_RED)
                if obtener_rol(self.usuario_actual) == "admin":
                    if hasattr(self, 'btn_admin'): self.btn_admin.configurar_estado("normal", COLOR_PURPLE)
                    if hasattr(self, 'btn_admin_todo'): self.btn_admin_todo.configurar_estado("normal", COLOR_BLUE)
                    if hasattr(self, 'btn_gestion_usr'): self.btn_gestion_usr.configurar_estado("normal", COLOR_GREEN)
                return  # Finaliza el bucle de escucha ya que el hilo trabajador concluyó.
            
            # Si el hilo envió un texto que contiene fallos, pinta la etiqueta de estado de color rojo
            if "ERROR" in mensaje:
                self.label_estado.config(text=mensaje, fg=COLOR_RED)
            else:
                # Si el hilo envió un paso exitoso, pinta la etiqueta de estado de color verde
                self.label_estado.config(text=mensaje, fg=COLOR_GREEN)
                
            # PROGRAMACIÓN TEMPORAL: Planifica volver a llamar a esta función dentro de 100 milisegundos
            self.root.after(100, self.escuchar_cola)
        except:
            # Si la cola está vacía (el hilo aún está procesando y no ha escrito nada), 
            # captura el salto de excepción y vuelve a programar la revisión en 100 milisegundos.
            self.root.after(100, self.escuchar_cola)

    # --- VENTANA SUB-MODAL 1: HISTORIAL DE LOGS ---
    def abrir_ventana_logs(self):
        """Despliega una subventana flotante exclusiva para ver la bitácora de accesos registrados."""
        ventana_logs = tk.Toplevel(self.root)
        ventana_logs.title("Logs de Accesos")
        ventana_logs.geometry("420x420")
        ventana_logs.configure(bg=COLOR_BG)
        ventana_logs.transient(self.root) # Bloquea la ventana principal por detrás
        ventana_logs.grab_set()

        tk.Label(ventana_logs, text="HISTORIAL DE REGISTROS DE ACCESO", font=("Arial", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=15)
        frame_scroll = tk.Frame(ventana_logs, bg=COLOR_BG)
        frame_scroll.pack(expand=True, fill="both", padx=20, pady=5)

        # Barra de desplazamiento vertical para los registros extensos
        scroll = tk.Scrollbar(frame_scroll)
        scroll.pack(side="right", fill="y")

        lista = tk.Listbox(frame_scroll, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, highlightthickness=0, font=("Consolas", 9), yscrollcommand=scroll.set)
        lista.pack(expand=True, fill="both", side="left")
        scroll.config(command=lista.yview)

        # Consulta estructurada de datos a la BD
        registros = obtener_registros_acceso()
        for fecha, tipo, estado in registros:
            lista.insert("end", f" [{fecha}] {tipo} -> {estado}")

        if not registros:
            lista.insert("end", " No se registran eventos en registro_acceso.")

        btn_cerrar = BotonRedondeado(ventana_logs, text="CERRAR VENTANA", command=ventana_logs.destroy, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=150, height=35)
        btn_cerrar.pack(pady=15)

    # --- VENTANA SUB-MODAL 2: PANEL DE CONTROL DE USUARIOS (CRUD) ---
    def abrir_ventana_gestion_usuarios(self):
        """Permite a los administradores del sistema ascender roles o dar de baja cuentas de usuario."""
        ventana_gestion = tk.Toplevel(self.root)
        ventana_gestion.title("Gestión de Usuarios")
        ventana_gestion.geometry("460x450")
        ventana_gestion.configure(bg=COLOR_BG)
        ventana_gestion.transient(self.root)
        ventana_gestion.grab_set()

        tk.Label(ventana_gestion, text="GESTIÓN DE PERMISOS TEMPORALES", font=("Arial", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=15)
        
        frame_scroll = tk.Frame(ventana_gestion, bg=COLOR_BG)
        frame_scroll.pack(expand=True, fill="both", padx=20, pady=5)

        scroll = tk.Scrollbar(frame_scroll)
        scroll.pack(side="right", fill="y")

        lista_usr = tk.Listbox(frame_scroll, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, highlightthickness=0, font=("Consolas", 10), yscrollcommand=scroll.set)
        lista_usr.pack(expand=True, fill="both", side="left")
        scroll.config(command=lista_usr.yview)

        # Arreglo dinámico en memoria RAM para sincronizar el índice visual con la clave primaria ID de SQLite
        usuarios_cache = []

        def cargar_usuarios():
            """Recarga y mapea la lista de usuarios reflejando los últimos cambios."""
            lista_usr.delete(0, "end")
            usuarios_cache.clear()
            datos = obtener_todo_db()
            for row in datos["usuarios"]:
                uid, nombre, rol, nfc, _ = row
                usuarios_cache.append((uid, nombre, rol))
                # Inserta una línea formateada espaciada con operadores monótonos para legibilidad en consola
                lista_usr.insert("end", f" ID: {uid:<3} | User: {nombre:<10} | Rol: {rol.upper()}")

        cargar_usuarios()

        def alternar_rol():
            """Intercambia el nivel de autorización (de admin a usuario común o viceversa)."""
            seleccion = lista_usr.curselection()
            if not seleccion:
                messagebox.showwarning("Atención", "Selecciona un usuario de la lista.")
                return
            uid, nombre, rol = usuarios_cache[seleccion[0]]
            
            # Regla de seguridad elemental: el usuario actual no puede auto-degradarse de privilegios
            if nombre == self.usuario_actual:
                messagebox.showerror("Error", "No puedes revocar tus propios permisos.")
                return
            
            nuevo_rol = "usuario" if rol == "admin" else "admin"
            if cambiar_rol_usuario(uid, nuevo_rol):
                messagebox.showinfo("Éxito", f"Permisos actualizados para '{nombre}' a {nuevo_rol.upper()}.")
                cargar_usuarios()
                self.pantalla_puerta() # Refresca el panel de fondo por si hubo cambios de jerarquía

        def eliminar_usuario():
            """Borra permanentemente la fila del usuario seleccionado en la Base de Datos."""
            seleccion = lista_usr.curselection()
            if not seleccion:
                messagebox.showwarning("Atención", "Selecciona un usuario de la lista.")
                return
            uid, nombre, _ = usuarios_cache[seleccion[0]]
            
            if nombre == self.usuario_actual:
                messagebox.showerror("Error", "No puedes eliminar tu propia cuenta en ejecución.")
                return
            
            if messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar permanentemente a '{nombre}'?"):
                if eliminar_usuario_db(uid):
                    messagebox.showinfo("Éxito", f"Usuario '{nombre}' eliminado correctamente.")
                    cargar_usuarios()

        # Construcción de botones inferiores de comando
        frame_btns = tk.Frame(ventana_gestion, bg=COLOR_BG)
        frame_btns.pack(pady=20)

        btn_permiso = BotonRedondeado(frame_btns, text="DAR/QUITAR ADMIN", command=alternar_rol, bg=COLOR_BLUE, fg=COLOR_INPUT, width=170, height=35)
        btn_permiso.pack(side="left", padx=5)

        btn_borrar = BotonRedondeado(frame_btns, text="ELIMINAR USUARIO", command=eliminar_usuario, bg=COLOR_RED, fg=COLOR_INPUT, width=150, height=35)
        btn_borrar.pack(side="left", padx=5)


    # --- VENTANA SUB-MODAL 3: INSPECTOR DE BASE DE DATOS COMPLETA ---
    def abrir_ventana_bd_completa(self):
        """Genera un volcado analítico textual (Dump) de la totalidad relacional de las tablas de SQLite."""
        ventana_todo = tk.Toplevel(self.root)
        ventana_todo.title("Inspección Total Base de Datos")
        ventana_todo.geometry("540x520")
        ventana_todo.configure(bg=COLOR_BG)
        ventana_todo.transient(self.root)
        ventana_todo.grab_set()

        tk.Label(ventana_todo, text="DATABASE RELATIONAL DUMP (4 TABLES)", font=("Consolas", 11, "bold"), fg=COLOR_BLUE, bg=COLOR_BG).pack(pady=12)

        # Contenedor especial aislado para contener el módulo de texto text de terminal
        frame_text = tk.Frame(ventana_todo, bg=COLOR_INPUT)
        frame_text.pack(expand=True, fill="both", padx=20, pady=5)

        scroll_y = tk.Scrollbar(frame_text)
        scroll_y.pack(side="right", fill="y")

        # Widget de Texto principal con colores contrastados explícitos para corregir pantallas oscuras vacías
        consola = tk.Text(frame_text, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, selectbackground=COLOR_BLUE, bd=0, highlightthickness=0, font=("Consolas", 9), yscrollcommand=scroll_y.set, wrap="none")
        consola.pack(expand=True, fill="both", side="left", padx=10, pady=10)
        scroll_y.config(command=consola.yview)

        try:
            # Adquiere el diccionario maestro con la lectura masiva de SQLite
            datos = obtener_todo_db()
            
            # --- 1. Formateo de la Tabla: usuarios ---
            texto_dump = "=== TABLA: usuarios ===\n"
            texto_dump += f"{'ID_Usuario':<12} | {'Nombre':<12} | {'Rol':<10} | {'UID_NFC':<12} | {'Password':<10}\n"
            texto_dump += "-" * 65 + "\n"
            for u in datos["usuarios"]:
                texto_dump += f"{u[0]:<12} | {u[1]:<12} | {u[2]:<10} | {u[3]:<12} | {u[4]:<10}\n"
                
            # --- 2. Formateo de la Tabla: registro_acceso ---
            texto_dump += "\n=== TABLA: registro_acceso ===\n"
            texto_dump += f"{'ID_log':<8} | {'fecha_hora':<20} | {'tipo_acceso':<12} | {'estado':<18}\n"
            texto_dump += "-" * 65 + "\n"
            if datos["accesos"]:
                for a in datos["accesos"]:
                    texto_dump += f"{a[0]:<8} | {a[1]:<20} | {a[2]:<12} | {a[3]:<18}\n"
            else:
                texto_dump += " (Sin registros de acceso guardados)\n"

            # --- 3. Formateo de la Tabla: permisos ---
            texto_dump += "\n=== TABLA: permisos ===\n"
            texto_dump += f"{'id_permisos':<12} | {'fecha_expiracion':<20}\n"
            texto_dump += "-" * 36 + "\n"
            if datos["permisos"]:
                for p in datos["permisos"]:
                    texto_dump += f"{p[0]:<12} | {p[1]:<20}\n"
            else:
                texto_dump += " (No hay registros explícitos de expiración activa)\n"

            # --- 4. Formateo de la Tabla: app ---
            texto_dump += "\n=== TABLA: app ===\n"
            texto_dump += f"{'id_app':<8} | {'nombre':<15} | {'version':<10}\n"
            texto_dump += "-" * 36 + "\n"
            for app in datos["app"]:
                texto_dump += f"{app[0]:<8} | {app[1]:<15} | {app[2]:<10}\n"

        except Exception as e:
            # Captura de errores ante incongruencias de columnas o esquemas de la BD
            texto_dump = f"❌ ERROR AL LEER ESQUEMA:\n{str(e)}"

        # Vuelca el bloque gigante de texto formateado en el control visual y congela su edición (Disabled)
        consola.insert("1.0", texto_dump)
        consola.config(state="disabled")

        # Botón fijo inferior para cerrar la ventana modal de inspección
        btn_cerrar = BotonRedondeado(ventana_todo, text="CERRAR INSPECTOR", command=ventana_todo.destroy, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=160, height=35)
        btn_cerrar.pack(pady=15, side="bottom")
