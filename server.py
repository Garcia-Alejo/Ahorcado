import socket
import threading

# Configuración del servidor
HOST = '127.0.0.1'  # Localhost
PUERTO = 12345
ERRORES_MAXIMOS = 5

# Datos globales
jugadores = {}
palabras_originales = {}
palabras_adivinadas = {}

def manejar_jugador(conexion, direccion):
    print(f"Jugador conectado: {direccion}")
    conexion.sendall("Bienvenido al juego de ahorcado.\n".encode())
    conexion.sendall("Esperando a otro jugador...\n".encode())

    # Esperar a que ambos jugadores se conecten
    while len(jugadores) < 2:
        pass

    conexion.sendall("Ambos jugadores conectados. Por favor, envía tu palabra.\n".encode())

    # Recibir palabra del jugador
    palabra = conexion.recv(1024).decode().strip().lower()
    palabras_originales[direccion] = palabra
    palabras_adivinadas[direccion] = "_" * len(palabra)

    # Avisar cuando ambos jugadores hayan enviado la palabra
    while len(palabras_originales) < 2:
        pass

    conexion.sendall("¡Las palabras están listas! Comienza el juego.\n".encode())

    oponente = [j for j in jugadores if j != direccion][0]
    errores = 0

    # Ciclo del juego
    while True:
        conexion.sendall(f"Tu palabra para adivinar: {palabras_adivinadas[oponente]}\n".encode())
        conexion.sendall("Ingresa una letra: ".encode())

        letra = conexion.recv(1024).decode().strip().lower()
        if len(letra) != 1 or not letra.isalpha():
            conexion.sendall("Por favor, ingresa solo una letra válida.\n".encode())
            continue

        palabra_oponente = palabras_originales[oponente]
        adivinada_actualizada = list(palabras_adivinadas[oponente])
        error_cometido = True

        # Revisar si la letra está en la palabra del oponente
        for i, caracter in enumerate(palabra_oponente):
            if caracter == letra:
                adivinada_actualizada[i] = letra
                error_cometido = False

        palabras_adivinadas[oponente] = ''.join(adivinada_actualizada)

        if error_cometido:
            errores += 1
            conexion.sendall(f"Letra incorrecta. Errores: {errores}/{ERRORES_MAXIMOS}\n".encode())
        else:
            conexion.sendall(f"¡Letra correcta! {palabras_adivinadas[oponente]}\n".encode())

        # Verificar si el jugador ganó o perdió
        if palabras_adivinadas[oponente] == palabra_oponente:
            conexion.sendall("¡Felicidades, adivinaste la palabra y ganaste el juego!\n".encode())
            jugadores[oponente].sendall("Lo siento, el otro jugador adivinó tu palabra. Has perdido.\n".encode())
            break
        elif errores >= ERRORES_MAXIMOS:
            conexion.sendall("Has perdido. Demasiados errores.\n".encode())
            jugadores[oponente].sendall("¡Ganaste! El otro jugador cometió demasiados errores.\n".encode())
            break

    # Avisar que el juego terminó para ambos jugadores
    conexion.sendall("El juego ha terminado. Gracias por jugar.\n".encode())
    jugadores[oponente].sendall("El juego ha terminado. Gracias por jugar.\n".encode())
    conexion.close()

# Configuración inicial del servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PUERTO))
servidor.listen(2)

print(f"Servidor escuchando en {HOST}:{PUERTO}")

# Aceptar conexiones de jugadores
while len(jugadores) < 2:
    conexion, direccion = servidor.accept()
    jugadores[direccion] = conexion
    threading.Thread(target=manejar_jugador, args=(conexion, direccion)).start()
