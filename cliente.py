import socket

# Configuración del cliente
HOST = '127.0.0.1'  # Localhost
PUERTO = 12345

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PUERTO))

while True:
    # Recibir mensajes del servidor
    mensaje = cliente.recv(1024).decode()
    print(mensaje)

    # Verificar si se necesita entrada del usuario
    if "Ingresa una letra" in mensaje or "envía tu palabra" in mensaje:
        respuesta = input("> ")
        cliente.sendall(respuesta.encode())

    # Terminar la conexión si el juego ha terminado
    if "El juego ha terminado" in mensaje:
        print("Desconectando...")
        break

cliente.close()
