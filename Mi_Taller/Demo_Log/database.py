import sqlite3

DB_NAME = "seguridad_taller.db"

def inicializar_base_datos():
    """Crea la base de datos y las tablas basadas en el diagrama de entidad-relación."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla: usuarios (Añadido 'password' para mantener la lógica de autenticación)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            ID_Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT UNIQUE NOT NULL,
            Rol TEXT NOT NULL,
            UID_NFC TEXT,
            password TEXT NOT NULL
        )
    """)
    
    # Tabla: registro_acceso
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_acceso (
            ID_log INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            tipo_acceso TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)
    
    # Tabla: permisos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permisos (
            id_permisos INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_expiracion TEXT
        )
    """)
    
    # Tabla: app
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app (
            id_app INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            version TEXT NOT NULL
        )
    """)
    
    # Insertar usuarios iniciales con sus respectivos Roles y UIDs simulados
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        usuarios_defecto = [
            ("admin", "admin", "NFC-ADMIN-01", "1234"), 
            ("andy", "usuario", "NFC-USER-02", "tonotos67")
        ]
        cursor.executemany("INSERT INTO usuarios (Nombre, Rol, UID_NFC, password) VALUES (?, ?, ?, ?)", usuarios_defecto)
        
    # Insertar información de la app si está vacía
    cursor.execute("SELECT COUNT(*) FROM app")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO app (nombre, version) VALUES (?, ?)", ("MiTaller", "1.0.0"))
        
    conn.commit()
    conn.close()

def registrar_usuario(usuario, password):
    """Inserta un nuevo usuario estándar de forma segura."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Se registra por defecto con el Rol 'usuario' y un UID NFC temporal
        cursor.execute(
            "INSERT INTO usuarios (Nombre, Rol, UID_NFC, password) VALUES (?, ?, ?, ?)", 
            (usuario, "usuario", "NFC-TEMP", password)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"Error en SQLite al registrar: {e}")
        return False

def obtener_rol(usuario):
    """Obtiene el rol actual de un usuario para validar sus accesos de administrador."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT Rol FROM usuarios WHERE Nombre = ?", (usuario,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else "usuario"
    except sqlite3.Error:
        return "usuario"

def cambiar_rol_usuario(id_usuario, nuevo_rol):
    """Modifica el permiso/rol de un usuario (Toggle temporal)."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET Rol = ? WHERE ID_Usuario = ?", (nuevo_rol, id_usuario))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error al cambiar rol: {e}")
        return False

def eliminar_usuario_db(id_usuario):
    """Elimina permanentemente un usuario por su ID."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE ID_Usuario = ?", (id_usuario,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error al eliminar usuario: {e}")
        return False

def obtener_registros_acceso():
    """Devuelve el historial de la tabla registro_acceso ordenado por el más reciente."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT fecha_hora, tipo_acceso, estado FROM registro_acceso ORDER BY ID_log DESC")
    filas = cursor.fetchall()
    conn.close()
    return filas

def obtener_todo_db():
    """Devuelve un diccionario con el volcado total de las nuevas tablas del diagrama."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT ID_Usuario, Nombre, Rol, UID_NFC, password FROM usuarios ORDER BY ID_Usuario ASC")
    usuarios = cursor.fetchall()
    
    cursor.execute("SELECT ID_log, fecha_hora, tipo_acceso, estado FROM registro_acceso ORDER BY ID_log ASC")
    accesos = cursor.fetchall()

    cursor.execute("SELECT id_permisos, fecha_expiracion FROM permisos ORDER BY id_permisos ASC")
    permisos = cursor.fetchall()

    cursor.execute("SELECT id_app, nombre, version FROM app ORDER BY id_app ASC")
    app = cursor.fetchall()
    
    conn.close()
    return {"usuarios": usuarios, "accesos": accesos, "permisos": permisos, "app": app}
