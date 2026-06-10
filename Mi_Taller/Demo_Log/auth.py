import sqlite3
from database import DB_NAME

def verificar_credenciales(usuario, password):
    """Verifica las credenciales consultando la nueva estructura de la base de datos."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE Nombre = ?", (usuario,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado and resultado[0] == password:
            return True
        return False
    except sqlite3.Error as e:
        print(f"Error en autenticación SQLite: {e}")
        return False
