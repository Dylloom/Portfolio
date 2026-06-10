import threading
from queue import Queue

# Semáforo para el cerrojo físico
semaforo_nfc = threading.Semaphore(1)
# Cola para enviar mensajes desde el hilo de hardware a la interfaz
cola_mensajes = Queue()

# Configuración General
TITULO_APP = "MiTaller - Control de Acceso"