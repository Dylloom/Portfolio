import database as db
from gui import KioscoApp

if __name__ == "__main__":
    # Inicializa las tablas con la carga masiva de productos
    db.init_db()
    
    # Arranca el bucle gráfico principal
    app = KioscoApp()
    app.mainloop()
