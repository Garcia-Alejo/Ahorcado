import socket
import threading
HOST = '127.0.0.1'
PUERTO = 12345

def cliente_ahorcado():
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST, PUERTO))
        print("Conectado al servidor.")

        while True:
            mensaje_servidor = cliente.recv(1024).decode()
            if not mensaje_servidor:
                print("Conexión cerrada por el servidor.")
                break
            print(f"Servidor: {mensaje_servidor}")

            if "envía tu palabra" in mensaje_servidor.lower():
                palabra = input("Introduce tu palabra para el juego: ").strip()
                cliente.sendall(palabra.encode())
            elif "ingresa una letra" in mensaje_servidor.lower() :
                entrada = input("").strip()
                cliente.sendall(entrada.encode())

    except ConnectionError as e:
        print(f"Error de conexión: {e}")
    finally:
        cliente.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    cliente_ahorcado()
