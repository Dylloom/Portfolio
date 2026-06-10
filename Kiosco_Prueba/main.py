import database as db
from gui import KioscoApp

if __name__ == "__main__":
    db.init_db()
    app = KioscoApp()
    app.mainloop()
