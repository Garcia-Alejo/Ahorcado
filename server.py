import socket
import threading

HOST = '127.0.0.1'
PUERTO = 12345
ERRORES_MAXIMOS = 5

# Datos globales
jugadores = {}
palabras_originales = {}
palabras_adivinadas = {}
historial = {}

def manejar_jugador(conexion, direccion):
    print(f"Jugador conectado: {direccion}")
    conexion.sendall("Bienvenido al juego de ahorcado.\n".encode())
    conexion.sendall("Esperando a otro jugador...\n".encode())

    while len(jugadores) < 2:
        pass

    conexion.sendall("Ambos jugadores conectados. Por favor, envía tu palabra.\n".encode())

    historial[direccion] = {"letras_correctas": [], "letras_incorrectas": [], "palabras": []}

    palabra = conexion.recv(1024).decode().strip().lower()
    palabras_originales[direccion] = palabra
    palabras_adivinadas[direccion] = ["_"] * len(palabra)  # Usamos una lista para facilitar el formato con espacios

    while len(palabras_originales) < 2:
        pass

    for jugador in jugadores:
        if len(palabras_originales[jugador]) > 8:
            oponente = [j for j in jugadores if j != jugador][0]
            pista = f"La palabra tiene más de 8 letras. La primera letra es '{palabras_originales[jugador][0]}' y la última letra es '{palabras_originales[jugador][-1]}'."
            jugadores[oponente].sendall(pista.encode())

    conexion.sendall("¡Las palabras están listas! Comienza el juego.\n".encode())

    oponente = [j for j in jugadores if j != direccion][0]
    errores = 0
    intentos_palabra = 2

    while True:
        # Mostrar la palabra con formato amigable (_ _ _ _ _)
        conexion.sendall(f"Tu palabra para adivinar: {' '.join(palabras_adivinadas[oponente])}\n".encode())
        conexion.sendall("Ingresa una letra o arriesga una palabra completa: ".encode())

        entrada = conexion.recv(1024).decode().strip().lower()

        if len(entrada) > 1:
            historial[direccion]["palabras"].append(entrada)
        else:
            if entrada in palabras_originales[oponente]:  # Letra correcta
                historial[direccion]["letras_correctas"].append(entrada)
            else:  # Letra incorrecta
                historial[direccion]["letras_incorrectas"].append(entrada)

        if len(entrada) > 1:  
            if entrada == palabras_originales[oponente]:
                palabras_adivinadas[oponente] = list(palabras_originales[oponente])  # Convertir la palabra completa en lista
                conexion.sendall("¡Adivinaste la palabra completa! ¡Ganaste!\n".encode())
                jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                break
            else:
                intentos_palabra -= 1
                conexion.sendall(f"Palabra incorrecta. Intentos restantes para adivinar palabra completa: {intentos_palabra}\n".encode())
                if intentos_palabra <= 0:
                    conexion.sendall("Has perdido. Demasiados intentos fallidos para palabras completas.\n".encode())
                    jugadores[oponente].sendall("¡Ganaste! El otro jugador falló demasiadas veces con palabras completas.\n".encode())
                    break
        else:  
            palabra_oponente = palabras_originales[oponente]
            adivinada_actualizada = palabras_adivinadas[oponente]
            error_cometido = True

            for i, caracter in enumerate(palabra_oponente):
                if caracter == entrada:
                    adivinada_actualizada[i] = entrada
                    error_cometido = False

            palabras_adivinadas[oponente] = adivinada_actualizada

            if error_cometido:
                errores += 1
                conexion.sendall(f"Letra incorrecta. Errores: {errores}/{ERRORES_MAXIMOS}\n".encode())
            else:
                conexion.sendall(f"¡Letra correcta! {' '.join(palabras_adivinadas[oponente])}\n".encode())

            if ''.join(palabras_adivinadas[oponente]) == palabra_oponente:
                conexion.sendall("¡Felicidades, adivinaste la palabra y ganaste el juego!\n".encode())
                jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                break
            elif errores >= ERRORES_MAXIMOS:
                conexion.sendall("Has perdido. Demasiados errores.\n".encode())
                jugadores[oponente].sendall("¡Ganaste! El otro jugador cometió demasiados errores.\n".encode())
                break

        conexion.sendall(f"Historial de letras correctas: {', '.join(historial[direccion]['letras_correctas'])}\n".encode())
        conexion.sendall(f"Historial de letras incorrectas: {', '.join(historial[direccion]['letras_incorrectas'])}\n".encode())
        conexion.sendall(f"Historial de palabras: {', '.join(historial[direccion]['palabras'])}\n".encode())

    conexion.sendall("El juego ha terminado. Gracias por jugar.\n".encode())


# Configuración inicial del servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PUERTO))
servidor.listen(2)

print(f"Servidor escuchando en {HOST}:{PUERTO}")

while len(jugadores) < 2:
    conexion, direccion = servidor.accept()
    jugadores[direccion] = conexion
    threading.Thread(target=manejar_jugador, args=(conexion, direccion)).start()
