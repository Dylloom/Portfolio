import sqlite3
import threading
import queue
import time

DB_NAME = 'kiosco_concurrente.db'

# =====================================================================
# 1. COLA (Queue)
# =====================================================================
# Canal seguro donde los hilos de los clientes depositan sus pedidos
order_queue = queue.Queue()

# =====================================================================
# 2. SEMÁFORO (Semaphore)
# =====================================================================
# Limita el acceso a la base de datos a un número controlado de hilos simultáneos
db_semaphore = threading.BoundedSemaphore(value=1)

# =====================================================================
# 3. MONITOR (Monitor)
# =====================================================================
# Encapsula el estado de los datos con exclusión mutua y variables de condición
class KioscoMonitor:
    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def inicializar_tablas(self):
        with self._lock:  # Región crítica protegida por el Monitor
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS productos 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cantidad INTEGER, precio REAL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, producto_id INTEGER, 
                          nombre_producto TEXT, cantidad INTEGER, estado TEXT)''')
            
            c.execute("SELECT * FROM usuarios WHERE username='admin'")
            if not c.fetchone():
                c.execute("INSERT INTO usuarios (username, password, role) VALUES ('admin', '1234', 'admin')")
                
            c.execute("SELECT COUNT(*) FROM productos")
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO productos (nombre, cantidad, precio) VALUES ('Alfajor Marley', 45, 950.0)")
                c.execute("INSERT INTO productos (nombre, cantidad, precio) VALUES ('Gaseosa 500ml', 20, 1500.0)")
                c.execute("INSERT INTO productos (nombre, cantidad, precio) VALUES ('Papas Fritas', 15, 1200.0)")
            conn.commit()
            conn.close()

    def verificar_login(self, username, password):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT role FROM usuarios WHERE username=? AND password=?", (username, password))
            result = c.fetchone()
            conn.close()
            return result[0] if result else None

    def registrar_usuario(self, username, password):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, 'client')", (username, password))
                conn.commit()
                return True, "Usuario creado con éxito."
            except sqlite3.IntegrityError:
                return False, "El nombre de usuario ya existe."
            finally:
                conn.close()

    def obtener_productos_disponibles(self):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, nombre, precio, cantidad FROM productos WHERE cantidad > 0")
            res = c.fetchall()
            conn.close()
            return res

    def obtener_todos_los_productos(self):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, nombre, cantidad, precio FROM productos")
            res = c.fetchall()
            conn.close()
            return res

    def obtener_todos_los_pedidos(self):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, username, nombre_producto, cantidad, estado FROM pedidos ORDER BY id DESC")
            res = c.fetchall()
            conn.close()
            return res

    def transaccion_pedido_interno(self, username, producto_id, nombre_producto, cantidad):
        # Operación atómica dentro del Monitor: verifica stock y descuenta en un solo bloque cerrado
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            c.execute("SELECT cantidad FROM productos WHERE id = ?", (producto_id,))
            row = c.fetchone()
            if not row or row[0] < cantidad:
                conn.close()
                return False
            
            # Descontar del inventario y asentar el pedido
            c.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id = ?", (cantidad, producto_id))
            c.execute("INSERT INTO pedidos (username, producto_id, nombre_producto, cantidad, estado) VALUES (?, ?, ?, ?, 'Pendiente')",
                      (username, producto_id, nombre_producto, cantidad))
            conn.commit()
            conn.close()
            
            # Notifica a cualquier hilo interesado de que el estado interno ha cambiado
            self._condition.notify_all()
            return True

    def agregar_producto(self, nombre, cantidad, precio):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)", (nombre, cantidad, precio))
            conn.commit()
            conn.close()
            self._condition.notify_all()

    def marcar_pedido_completado(self, pedido_id):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE pedidos SET estado='Completado' WHERE id=?", (pedido_id,))
            conn.commit()
            conn.close()
            self._condition.notify_all()

# Instancia única del Monitor global
monitor = KioscoMonitor()

# =====================================================================
# HILO TRABAJADOR (Background Worker Thread)
# =====================================================================
def deamon_procesador_pedidos():
    """ Hilo secundario infinito que consume la Cola, respetando Semáforos y Monitores """
    while True:
        # Extrae un elemento de la COLA (bloqueante si está vacía)
        pedido = order_queue.get()
        if pedido is None:
            break
        
        username, prod_id, prod_name, cantidad = pedido
        
        # El hilo solicita permiso al SEMÁFORO antes de operar
        with db_semaphore:
            # Simulamos un retraso intencional (preparación del pedido/red) de 0.8 segundos
            time.sleep(0.8)
            # Invoca de forma segura la región crítica del MONITOR
            monitor.transaccion_pedido_interno(username, prod_id, prod_name, cantidad)
            
        order_queue.task_done()

# Iniciamos el hilo de procesamiento de fondo de inmediato en modo demonio
threading.Thread(target=deamon_procesador_pedidos, daemon=True).start()

# --- Interfaz pública expuesta hacia el archivo GUI ---
def init_db(): monitor.inicializar_tablas()
def verificar_login(u, p): return monitor.verificar_login(u, p)
def registrar_usuario(u, p): return monitor.registrar_usuario(u, p)
def obtener_productos_cliente(): return monitor.obtener_productos_disponibles()
def obtener_todos_los_productos(): return monitor.obtener_todos_los_productos()
def obtener_todos_los_pedidos(): return monitor.obtener_todos_los_pedidos()
def agregar_producto(n, c, p): monitor.agregar_producto(n, c, p)
def marcar_pedido_completado(pid): monitor.marcar_pedido_completado(pid)

def encolar_pedido(username, producto_id, nombre_producto, cantidad):
    """ Coloca el requerimiento en la Cola concurrente, liberando la UI de inmediato """
    order_queue.put((username, producto_id, nombre_producto, cantidad))
