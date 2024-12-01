import socket
import threading
import time

HOST = '127.0.0.1'
PUERTO = 12345
ERRORES_MAXIMOS = 5

# Datos globales
jugadores = {}
palabras_originales = {}
palabras_adivinadas = {}
historial = {}
turno_actual = None  # Controla de quién es el turno (dirección del jugador)

def manejar_jugador(conexion, direccion):
    global turno_actual
    print(f"Jugador conectado: {direccion}")
    conexion.sendall("Bienvenido al juego de ahorcado.\n".encode())
    conexion.sendall("Esperando a otro jugador...\n".encode())

    # Esperar hasta que se conecten los dos jugadores
    while len(jugadores) < 2:
        time.sleep(0.5)  # Evitar bucles excesivos

    conexion.sendall("Ambos jugadores conectados. Por favor, envía tu palabra.\n".encode())
    
    # Recibir palabra del jugador
    palabra = conexion.recv(1024).decode().strip().lower()
    palabras_originales[direccion] = palabra
    palabras_adivinadas[direccion] = ["_"] * len(palabra)

    historial[direccion] = {"letras_correctas": [], "letras_incorrectas": [], "palabras": []}

    # Esperar a que ambos jugadores envíen sus palabras
    while len(palabras_originales) < 2:
        time.sleep(0.5)

    conexion.sendall("¡Las palabras están listas! Comienza el juego.\n".encode())

    # Identificar al oponente
    oponente = [j for j in jugadores if j != direccion][0]

    while True:
        if turno_actual == direccion:
            conexion.sendall(f"Es tu turno. Tu palabra para adivinar: {' '.join(palabras_adivinadas[oponente])}\n".encode())
            conexion.sendall("Ingresa una letra o una palabra completa: ".encode())

            entrada = conexion.recv(1024).decode().strip().lower()

            if len(entrada) > 1:  # Intento de palabra completa
                if entrada == palabras_originales[oponente]:
                    palabras_adivinadas[oponente] = list(palabras_originales[oponente])
                    conexion.sendall("¡Adivinaste la palabra completa! ¡Ganaste!\n".encode())
                    jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                    break
                else:
                    conexion.sendall("Palabra incorrecta. Turno perdido.\n".encode())
            else:  # Intento de una letra
                if entrada in palabras_originales[oponente]:
                    for i, caracter in enumerate(palabras_originales[oponente]):
                        if caracter == entrada:
                            palabras_adivinadas[oponente][i] = entrada
                    conexion.sendall("¡Letra correcta!\n".encode())
                else:
                    conexion.sendall("Letra incorrecta. Turno perdido.\n".encode())

            # Verificar si el juego terminó
            if ''.join(palabras_adivinadas[oponente]) == palabras_originales[oponente]:
                conexion.sendall("¡Felicidades, adivinaste la palabra y ganaste el juego!\n".encode())
                jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                break

            # Cambiar de turno
            turno_actual = oponente
        else:
            conexion.sendall("Es el turno del otro jugador. Espera...\n".encode())
            time.sleep(1)  # Esperar para evitar mensajes repetitivos

    conexion.sendall("El juego ha terminado. Gracias por jugar.\n".encode())


# Configuración inicial del servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PUERTO))
servidor.listen(2)

print(f"Servidor escuchando en {HOST}:{PUERTO}")

while len(jugadores) < 2:
    conexion, direccion = servidor.accept()
    jugadores[direccion] = conexion
    if len(jugadores) == 1:
        turno_actual = direccion  # El primer jugador comienza
    threading.Thread(target=manejar_jugador, args=(conexion, direccion)).start()