import tkinter as tk
from gui import InterfazNFC
from database import inicializar_base_datos
from hardware import monitor_sistema_thread
import threading

if __name__ == "__main__":
    # 1. Inicializar la Base de Datos SQLite
    inicializar_base_datos()
    
    # 2. Iniciar el NUEVO hilo de monitorización en segundo plano (Daemon)
    hilo_auditor = threading.Thread(target=monitor_sistema_thread, daemon=True)
    hilo_auditor.start()
    
    # 3. Lanzar la Interfaz Gráfica principal
    root = tk.Tk()
    app = InterfazNFC(root)
    root.mainloop()