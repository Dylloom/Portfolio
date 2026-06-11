import sqlite3
import threading
import queue
import time

DB_NAME = 'kiosco_avanzado.db'

# 1. COLA CONCURRENTE
order_queue = queue.Queue()

# 2. SEMÁFORO
db_semaphore = threading.BoundedSemaphore(value=1)

# 3. MONITOR
class KioscoMonitor:
    def __init__(self):
        self._lock = threading.Lock()

    def inicializar_tablas(self):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS productos 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cantidad INTEGER, precio REAL, categoria TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, orden_id TEXT, username TEXT, producto_id INTEGER, 
                          nombre_producto TEXT, cantidad INTEGER, precio_unid REAL, estado TEXT, notificado INTEGER DEFAULT 0)''')
            
            c.execute("SELECT * FROM usuarios WHERE username='admin'")
            if not c.fetchone():
                c.execute("INSERT INTO usuarios (username, password, role) VALUES ('admin', '1234', 'admin')")
                
            c.execute("SELECT COUNT(*) FROM productos")
            if c.fetchone()[0] == 0:
                productos_semilla = [
                    ('Alfajor Jorgito Chocolate', 50, 1500.0, 'Alfajores'),
                    ('Alfajor Milka Oreo', 30, 2400.0, 'Alfajores'),
                    ('Alfajor Havanna Premium', 20, 3500.0, 'Alfajores'),
                    ('Coca Cola 500ml', 40, 2600.0, 'Bebidas'),
                    ('Agua Mineral Villavicencio 500ml', 35, 1800.0, 'Bebidas'),
                    ('Energizante Monster 473ml', 25, 3800.0, 'Bebidas'),
                    ('Papas Fritas Lays Clásicas', 15, 3200.0, 'Snacks'),
                    ('Doritos Queso Mega 100g', 15, 3500.0, 'Snacks'),
                    ('Chocolatada Cindor 250ml', 20, 2900.0, 'Lácteos'),
                    ('Chocolate Block 38g', 25, 2100.0, 'Chocolates'),
                    ('Gomitas Mogul Ositos', 40, 1300.0, 'Golosinas'),
                    ('Chupetín Pico Dulce', 100, 500.0, 'Golosinas'),
                    ('Chicles Topline Fresh', 60, 1200.0, 'Golosinas'),
                    ('Barra de Cereal Flow', 45, 1100.0, 'Saludable'),
                    ('Galletitas Oreo', 30, 2200.0, 'Galletitas'),
                    ('Turrón de Maní Arcor', 120, 600.0, 'Golosinas')
                ]
                c.executemany("INSERT INTO productos (nombre, cantidad, precio, categoria) VALUES (?, ?, ?, ?)", productos_semilla)
            conn.commit()
            conn.close()

    def verificar_login(self, username, password):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT role FROM usuarios WHERE username=? AND password=?", (username, password))
            res = c.fetchone()
            conn.close()
            return res[0] if res else None

    def registrar_usuario(self, username, password):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, 'client')", (username, password))
                conn.commit()
                return True, "Registro exitoso."
            except sqlite3.IntegrityError:
                return False, "El usuario ya existe."
            finally:
                conn.close()

    def procesar_carrito_en_lote(self, username, orden_id, items_carrito):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            for p_id, _, cant, _ in items_carrito:
                c.execute("SELECT cantidad, nombre FROM productos WHERE id = ?", (p_id,))
                row = c.fetchone()
                if not row or row[0] < cant:
                    for p_id_b, p_nom_b, cant_b, p_pre_b in items_carrito:
                        c.execute('''INSERT INTO pedidos (orden_id, username, producto_id, nombre_producto, cantidad, precio_unid, estado) 
                                     VALUES (?, ?, ?, ?, ?, ?, 'Rechazado')''', (orden_id, username, p_id_b, p_nom_b, cant_b, p_pre_b))
                    conn.commit()
                    conn.close()
                    return False
            
            for p_id, p_nom, cant, p_pre in items_carrito:
                c.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id = ?", (cant, p_id))
                c.execute('''INSERT INTO pedidos (orden_id, username, producto_id, nombre_producto, cantidad, precio_unid, estado) 
                             VALUES (?, ?, ?, ?, ?, ?, 'En Proceso')''', (orden_id, username, p_id, p_nom, cant, p_pre))
            
            conn.commit()
            conn.close()
            return True

    def obtener_notificaciones_usuario(self, username):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT DISTINCT orden_id, estado FROM pedidos WHERE username=? AND notificado=0", (username,))
            alertas = c.fetchall()
            if alertas:
                c.execute("UPDATE pedidos SET notificado=1 WHERE username=?", (username,))
                conn.commit()
            conn.close()
            return alertas

    def obtener_productos(self):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, nombre, cantidad, precio, categoria FROM productos")
            res = c.fetchall()
            conn.close()
            return res

    def obtener_pedidos_agrupados(self):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''SELECT id, orden_id, username, nombre_producto, cantidad, estado 
                         FROM pedidos ORDER BY id DESC''')
            res = c.fetchall()
            conn.close()
            return res

    def cambiar_estado_pedido(self, orden_id, nuevo_estado):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            if nuevo_estado == "Rechazado":
                c.execute("SELECT producto_id, cantidad, estado FROM pedidos WHERE orden_id=?", (orden_id,))
                items = c.fetchall()
                for prod_id, cant, est_ant in items:
                    if est_ant != "Rechazado":
                        c.execute("UPDATE productos SET cantidad = cantidad + ? WHERE id = ?", (cant, prod_id))
                        
            c.execute("UPDATE pedidos SET estado=?, notificado=0 WHERE orden_id=?", (nuevo_estado, orden_id))
            conn.commit()
            conn.close()

    def agregar_nuevo_producto(self, nombre, cantidad, precio, categoria):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO productos (nombre, cantidad, precio, categoria) VALUES (?, ?, ?, ?)", (nombre, cantidad, precio, categoria))
            conn.commit()
            conn.close()

    # 🛠️ NUEVO MÉTODO DEL MONITOR: Actualizar stock de manera limpia sin duplicar filas
    def modificar_stock_por_id(self, producto_id, nueva_cantidad):
        with self._lock:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE productos SET cantidad = ? WHERE id = ?", (nueva_cantidad, producto_id))
            conn.commit()
            conn.close()

monitor = KioscoMonitor()

def deamon_procesador_carritos():
    while True:
        pedido_completo = order_queue.get()
        if pedido_completo is None: break
        username, orden_id, items_carrito = pedido_completo
        
        with db_semaphore:
            time.sleep(0.5)
            monitor.procesar_carrito_en_lote(username, orden_id, items_carrito)
            
        order_queue.task_done()

threading.Thread(target=deamon_procesador_carritos, daemon=True).start()

# Puentes API vinculados de forma segura con la GUI
def init_db(): monitor.inicializar_tablas()
def verificar_login(u, p): return monitor.verificar_login(u, p)
def registrar_usuario(u, p): return monitor.registrar_usuario(u, p)
def obtener_productos(): return monitor.obtener_productos()
def obtener_pedidos_agrupados(): return monitor.obtener_pedidos_agrupados()
def cambiar_estado_pedido(oid, est): monitor.cambiar_estado_pedido(oid, est)
def agregar_producto(n, c, p, cat): monitor.agregar_nuevo_producto(n, c, p, cat)
def actualizar_stock_producto(p_id, n_cant): monitor.modificar_stock_por_id(p_id, n_cant)
def chequear_alertas(u): return monitor.obtener_notificaciones_usuario(u)
def encolar_carrito(u, oid, items): order_queue.put((u, oid, items))
