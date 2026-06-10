import sqlite3
from datetime import datetime
from database import DB_NAME

def registrar_acceso(usuario):
    """Guarda el acceso en el log .txt y en la nueva tabla 'registro_acceso'."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] ACCESO: El usuario '{usuario}' ha abierto la puerta.\n"
    
    # 1. Registro en archivo de texto plano
    try:
        with open("log_accesos.txt", "a", encoding="utf-8") as archivo:
            archivo.write(linea)
    except Exception as e:
        print(f"Error al escribir en el archivo log: {e}")
        
    # 2. Registro en la tabla relacional 'registro_acceso'
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO registro_acceso (fecha_hora, tipo_acceso, estado) VALUES (?, ?, ?)", 
            (timestamp, "NFC_CARD", f"Permitido ({usuario})")
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error al registrar acceso en SQLite: {e}")
