import time
import sqlite3
from config import semaforo_nfc, cola_mensajes
from registro import registrar_acceso
from database import DB_NAME

def simulacion_nfc_thread(usuario, forzar_fallo=False):
    """Hilo encargado del hardware. Guarda logs correctos o erróneos en registro_acceso."""
    with semaforo_nfc:
        cola_mensajes.put("Acercar a la puerta")
        time.sleep(1.2)
        
        cola_mensajes.put("Leyendo NFC...")
        time.sleep(1.2)
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if forzar_fallo:
            cola_mensajes.put("ERROR: Acceso Denegado")
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO registro_acceso (fecha_hora, tipo_acceso, estado) VALUES (?, ?, ?)", 
                    (timestamp, "NFC_CARD", f"Denegado ({usuario})")
                )
                conn.commit()
                conn.close()
            except sqlite3.Error:
                pass
            time.sleep(2.0)
        else:
            cola_mensajes.put("Puerta abierta")
            registrar_acceso(usuario) 
            time.sleep(2.0)
        
        cola_mensajes.put("TERMINADO")

def monitor_sistema_thread():
    """Hilo de monitoreo en segundo plano. """
    while True:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registro_acceso")
            total_logs = cursor.fetchone()[0]
            conn.close()
            print(f"[MONITOR] Base de datos activa. Eventos en registro_acceso: {total_logs}")
        except sqlite3.Error as e:
            print(f"[MONITOR] Error: {e}")
            
        time.sleep(10)
