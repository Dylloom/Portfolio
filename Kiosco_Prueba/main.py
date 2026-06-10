import database as db
from gui import KioscoApp

if __name__ == "__main__":
    # Inicializa el entorno controlado del monitor
    db.init_db()
    
    # Inicia la ventana gráfica con Polling
    app = KioscoApp()
    app.mainloop()
