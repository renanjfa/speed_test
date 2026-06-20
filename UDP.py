import socket
import time
from globals import DURACAO, TAMANHO_PACOTE, HOST, MARCADOR_FIM
import utils as u

def sender_udp(host, porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    destino = (host, porta)
    print(f"[UDP] Enviando para {host}:{porta} por {DURACAO}s...")

    seq = 0
    bytes_enviados = 0
    inicio = time.time()

    while time.time() - inicio < DURACAO:
        sock.sendto(u.construir_pacote(seq), destino)
        seq += 1
        bytes_enviados += TAMANHO_PACOTE

    for _ in range(10):
        sock.sendto(u.construir_pacote_fim(seq), destino)
        time.sleep(0.01)

    sock.close()
    tempo = time.time() - inicio
    u.mostrar_metricas("RELATÓRIO UDP - SENDER", seq, seq, bytes_enviados, tempo)
    print(f"  (Pacotes perdidos serão calculados no receiver)")


def receiver_udp(porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, porta))
    print(f"[UDP] Escutando na porta {porta}... Aguardando dados.")

    pacotes = 0
    bytes_recebidos = 0
    pacotes_enviados = 0
    inicio = None

    while True:
        data, addr = sock.recvfrom(TAMANHO_PACOTE + 100)

        if data[:4] == MARCADOR_FIM:
            try:
                pacotes_enviados = int(data[4:].rstrip(b'\x00').decode())
            except Exception:
                pacotes_enviados = pacotes
            break

        if inicio is None:
            inicio = time.time()
        pacotes += 1
        bytes_recebidos += len(data)

    tempo = time.time() - inicio if inicio else DURACAO
    sock.close()
    u.mostrar_metricas("RELATÓRIO UDP - RECEIVER", pacotes_enviados, pacotes, bytes_recebidos, tempo)