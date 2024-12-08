import socket
import threading

HOST = '127.0.0.1'
PUERTO = 12345

# Variables globales
jugadores = {}
palabras_originales = {}
palabras_adivinadas = {}
historial = {}
turno_actual = None
avisado_turno = {}
juego_activo = True
uso_revelar = {}


def manejar_jugador(conexion, direccion):
    global turno_actual, avisado_turno, juego_activo
    print(f"Jugador conectado: {direccion}")
    conexion.sendall("Bienvenido al juego de ahorcado.\n".encode())
    conexion.sendall("Esperando a otro jugador...\n".encode())

    try:
        while len(jugadores) < 2:
            pass

        conexion.sendall("Ambos jugadores conectados. Por favor, envía tu palabra.\n".encode())
        palabra = conexion.recv(1024).decode().strip().lower()

        if not palabra.isalpha():
            conexion.sendall("La palabra debe contener solo letras. Conexión cerrada.\n".encode())
            conexion.close()
            return

        palabras_originales[direccion] = palabra
        palabras_adivinadas[direccion] = ["_"] * len(palabra)
        historial[direccion] = {"letras_correctas": [], "letras_incorrectas": [], "palabras": []}
        uso_revelar[direccion] = False

        while len(palabras_originales) < 2:
            pass

        conexion.sendall("¡Las palabras están listas! Comienza el juego.\n".encode())
        oponente = [j for j in jugadores if j != direccion][0]

        while juego_activo:
            if turno_actual == direccion:
                avisado_turno[direccion] = False
                conexion.sendall(
                    f"Es tu turno. Tu palabra para adivinar: {' '.join(palabras_adivinadas[oponente])}\n".encode()
                )
                conexion.sendall(f"Historial de letras correctas: {', '.join(historial[direccion]['letras_correctas'])}\n".encode())
                conexion.sendall(f"Historial de letras incorrectas: {', '.join(historial[direccion]['letras_incorrectas'])}\n".encode())

                if len(palabras_originales[oponente]) > 8:
                    conexion.sendall("Puedes usar el comando 'revelar X' para descubrir una letra.\n".encode())
                
                conexion.sendall("Ingresa una letra, una palabra completa o usa 'revelar X': ".encode())
                entrada = conexion.recv(1024).decode().strip().lower()

                if entrada.startswith("revelar"):
                    if len(palabras_originales[oponente]) <= 8:
                        conexion.sendall("No puedes usar 'revelar' porque la palabra tiene 8 o menos caracteres. Turno perdido.\n".encode())
                        turno_actual = oponente
                    elif uso_revelar[direccion]:
                        conexion.sendall("Ya has usado tu única oportunidad de revelar una letra. Turno perdido.\n".encode())
                        turno_actual = oponente
                    else:
                        try:
                            posicion = int(entrada.split()[1]) - 1
                            if 0 <= posicion < len(palabras_originales[oponente]) and palabras_adivinadas[oponente][posicion] == "_":
                                palabras_adivinadas[oponente][posicion] = palabras_originales[oponente][posicion]
                                conexion.sendall(f"Letra revelada: {palabras_originales[oponente][posicion]} en la posición {posicion + 1}.\n".encode())
                                uso_revelar[direccion] = True
                            else:
                                conexion.sendall("Posición inválida o ya revelada. Turno perdido.\n".encode())
                                turno_actual = oponente
                        except (ValueError, IndexError):
                            conexion.sendall("Comando 'revelar' inválido. Usa 'revelar X', donde X es un número válido. Turno perdido.\n".encode())
                            turno_actual = oponente
                elif len(entrada) > 1:
                    if entrada == palabras_originales[oponente]:
                        conexion.sendall("¡Felicidades, adivinaste la palabra completa y ganaste el juego!\n".encode())
                        jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                        juego_activo = False
                        break
                    else:
                        conexion.sendall("Palabra incorrecta. Turno perdido.\n".encode())
                        turno_actual = oponente
                else:
                    if entrada in historial[direccion]["letras_correctas"] or entrada in historial[direccion]["letras_incorrectas"]:
                        conexion.sendall("Letra ya enviada anteriormente. Pierdes el turno.\n".encode())
                        turno_actual = oponente
                    else:
                        if entrada in palabras_originales[oponente]:
                            historial[direccion]["letras_correctas"].append(entrada)
                            for i, caracter in enumerate(palabras_originales[oponente]):
                                if caracter == entrada:
                                    palabras_adivinadas[oponente][i] = entrada
                            conexion.sendall("¡Letra correcta!\n".encode())
                        else:
                            historial[direccion]["letras_incorrectas"].append(entrada)
                            conexion.sendall("Letra incorrecta. Turno perdido.\n".encode())
                            turno_actual = oponente

                if ''.join(palabras_adivinadas[oponente]) == palabras_originales[oponente]:
                    conexion.sendall("¡Felicidades, adivinaste la palabra y ganaste el juego!\n".encode())
                    jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                    juego_activo = False

        while True:
            try:
                mensaje = conexion.recv(1024).decode().strip().lower()
                if mensaje == "salir":
                    conexion.sendall("Gracias por jugar. Cerrando conexión...\n".encode())
                    break
                else:
                    conexion.sendall("El juego ha terminado. Escribe 'salir' para desconectar.\n".encode())
            except ConnectionResetError:
                break

    finally:
        conexion.close()
        print(f"Conexión con {direccion} cerrada.")


servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PUERTO))
servidor.listen(2)

print(f"Servidor escuchando en {HOST}:{PUERTO}")

while len(jugadores) < 2:
    conexion, direccion = servidor.accept()
    jugadores[direccion] = conexion
    if len(jugadores) == 1:
        turno_actual = direccion
    avisado_turno[direccion] = False
    threading.Thread(target=manejar_jugador, args=(conexion, direccion)).start()
