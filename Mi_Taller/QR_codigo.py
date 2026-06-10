import qrcode
#Ejemplo de QR para link

#Define el link que quieres convertir en QR
url_destino = "https://www.google.com"

#Configura los parámetros del código QR
qr = qrcode.QRCode(
    version=1,  # Tamaño del QR (del 1 al 40). 1 es el más pequeño.
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # Tolerancia a errores
    box_size=10,  # Tamaño de cada "cuadrado" del QR en píxeles
    border=4,     # Grosor del borde blanco
)

#Añade la información al objeto QR
qr.add_data(url_destino)
qr.make(fit=True) #Ajusta el tamaño mínimo (version) del codigo QR

# Crea la imagen con los colores que quieras
# (Se puedes cambiar el color del QR y del fondo aquí)
imagen_qr = qr.make_image(fill_color="black", back_color="white")

# Guarda la imagen, en el mismo lugar donde se ejecuta
nombre_archivo = "mi_codigo_qr.png"
imagen_qr.save(nombre_archivo)

print(f"¡Listo! El código QR ha sido guardado como '{nombre_archivo}'")
