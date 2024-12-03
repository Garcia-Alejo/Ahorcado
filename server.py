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
uso_revelar = {}  # Controla si cada jugador ya usó el comando 'revelar'


def manejar_jugador(conexion, direccion):
    global turno_actual, avisado_turno, juego_activo
    print(f"Jugador conectado: {direccion}")
    conexion.sendall("Bienvenido al juego de ahorcado.\n".encode())
    conexion.sendall("Esperando a otro jugador...\n".encode())

    try:
        # Esperar hasta que ambos jugadores estén conectados
        while len(jugadores) < 2:
            pass

        conexion.sendall("Ambos jugadores conectados. Por favor, envía tu palabra.\n".encode())
        palabra = conexion.recv(1024).decode().strip().lower()

        # Validar la palabra
        if not palabra.isalpha():
            conexion.sendall("La palabra debe contener solo letras. Conexión cerrada.\n".encode())
            conexion.close()
            return

        palabras_originales[direccion] = palabra
        palabras_adivinadas[direccion] = ["_"] * len(palabra)
        historial[direccion] = {"letras_correctas": [], "letras_incorrectas": [], "palabras": []}
        uso_revelar[direccion] = False  # Inicializar el uso del comando 'revelar' como falso

        # Esperar hasta que ambos jugadores envíen sus palabras
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
                conexion.sendall(
                    "Ingresa una letra, una palabra completa, o usa 'revelar X' para descubrir una letra específica: ".encode()
                )
                entrada = conexion.recv(1024).decode().strip().lower()

                if entrada.startswith("revelar"):
                    # Verificar si ya usó 'revelar'
                    if uso_revelar[direccion]:
                        conexion.sendall("Ya has usado tu única oportunidad de revelar una letra.\n".encode())
                        turno_actual = oponente  # Cambiar el turno inmediatamente
                        conexion.sendall("Es el turno del otro jugador. Espera...\n".encode())
                        continue  # Saltar el turno

                    # Verificar si la palabra a adivinar tiene más de 8 caracteres
                    if len(palabras_originales[oponente]) <= 8:
                        conexion.sendall("No puedes usar 'revelar' porque la palabra tiene 8 o menos caracteres.\n".encode())
                        turno_actual = oponente  # Cambiar el turno inmediatamente
                        conexion.sendall("Es el turno del otro jugador. Espera...\n".encode())
                        continue  # Saltar el turno

                    try:
                        posicion = int(entrada.split()[1]) - 1
                        if 0 <= posicion < len(palabras_originales[oponente]) and palabras_adivinadas[oponente][posicion] == "_":
                            palabras_adivinadas[oponente][posicion] = palabras_originales[oponente][posicion]
                            conexion.sendall(f"Letra revelada: {palabras_originales[oponente][posicion]} en la posición {posicion + 1}.\n".encode())
                            uso_revelar[direccion] = True  # Marcar que ya usó 'revelar'
                        else:
                            conexion.sendall("Posición inválida o ya revelada.\n".encode())
                            turno_actual = oponente  # Cambiar el turno inmediatamente
                            conexion.sendall("Es el turno del otro jugador. Espera...\n".encode())
                            continue  # Saltar el turno
                    except (ValueError, IndexError):
                        conexion.sendall("Comando 'revelar' inválido. Usa 'revelar X', donde X es un número válido.\n".encode())
                        turno_actual = oponente  # Cambiar el turno inmediatamente
                        conexion.sendall("Es el turno del otro jugador. Espera...\n".encode())            
                        continue  # Saltar el turno
                elif len(entrada) > 1:
                    if entrada == palabras_originales[oponente]:
                        conexion.sendall("¡Felicidades, adivinaste la palabra completa y ganaste el juego!\n".encode())
                        jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                        juego_activo = False
                        break
                    else:
                        conexion.sendall("Palabra incorrecta. Turno perdido.\n".encode())
                        turno_actual = oponente  # Cambiar el turno inmediatamente
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
                        turno_actual = oponente  # Cambiar el turno inmediatamente

                # Comprobar si se adivinó toda la palabra
                if ''.join(palabras_adivinadas[oponente]) == palabras_originales[oponente]:
                    conexion.sendall("¡Felicidades, adivinaste la palabra y ganaste el juego!\n".encode())
                    jugadores[oponente].sendall("El otro jugador adivinó tu palabra. Has perdido.\n".encode())
                    juego_activo = False
                    break

                turno_actual = oponente  # Cambiar el turno inmediatamente
            else:
                if not avisado_turno.get(direccion, False):
                    conexion.sendall("Es el turno del otro jugador. Espera...\n".encode())
                    avisado_turno[direccion] = True
    except ConnectionResetError:
        print(f"Jugador {direccion} se desconectó.")
        jugadores.pop(direccion, None)
        juego_activo = False
    finally:
        conexion.close()
        print(f"Conexión con {direccion} cerrada.")


# Configuración inicial del servidor
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
