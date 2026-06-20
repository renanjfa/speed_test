import socket
import time
from globals import DURACAO, TAMANHO_PACOTE, HOST, MARCADOR_FIM
import utils as u

def sender_tcp(host, porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, porta))
    print(f"[TCP] Conectado a {host}:{porta}. Enviando por {DURACAO}s...")

    seq = 0
    bytes_enviados = 0
    inicio = time.time()

    while time.time() - inicio < DURACAO:
        sock.sendall(u.construir_pacote(seq))
        seq += 1
        bytes_enviados += TAMANHO_PACOTE

    sock.sendall(u.construir_pacote_fim(seq))
    tempo = time.time() - inicio

    try:
        sock.settimeout(5)
        dados = sock.recv(64)
        pacotes_recebidos = int(dados.decode().strip())
    except Exception:
        pacotes_recebidos = seq

    sock.close()
    u.mostrar_metricas("RELATÓRIO TCP - SENDER", seq, pacotes_recebidos, bytes_enviados, tempo)


def receiver_tcp(porta):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, porta))
    server.listen(1)
    print(f"[TCP] Escutando na porta {porta}... Aguardando conexão.")

    conn, addr = server.accept()
    print(f"[TCP] {addr} conectado. Recebendo dados...")

    pacotes = 0
    bytes_recebidos = 0
    inicio = None
    buffer = b''

    while True:
        data = conn.recv(4096)
        if not data:
            break

        buffer += data

        while len(buffer) >= TAMANHO_PACOTE:
            pacote = buffer[:TAMANHO_PACOTE]
            buffer = buffer[TAMANHO_PACOTE:]

            if pacote[:4] == MARCADOR_FIM:
                total_env = int(pacote[4:].rstrip(b'\x00').decode())
                conn.sendall(str(pacotes).encode())
                tempo = time.time() - inicio if inicio else DURACAO
                conn.close()
                server.close()
                u.mostrar_metricas("RELATÓRIO TCP - RECEIVER", total_env, pacotes, bytes_recebidos, tempo)
                return

            if inicio is None:
                inicio = time.time()
            pacotes += 1
            bytes_recebidos += TAMANHO_PACOTE

    tempo = time.time() - inicio if inicio else DURACAO
    conn.close()
    server.close()
    u.mostrar_metricas("RELATÓRIO TCP - RECEIVER", pacotes, pacotes, bytes_recebidos, tempo)