import socket
import time

TAMANHO_PACOTE = 500
BASE_STRING = "teste de rede 2026"
DURACAO = 20
HOST = '0.0.0.0'
MARCADOR_FIM = b'\xff\xff\xff\xff'


def construir_pacote(seq_num):
    conteudo = f"{seq_num}|{BASE_STRING}|".encode('utf-8')
    return conteudo.ljust(TAMANHO_PACOTE, b'\x00')[:TAMANHO_PACOTE]


def construir_pacote_fim(total_enviados):
    conteudo = MARCADOR_FIM + str(total_enviados).encode('utf-8')
    return conteudo.ljust(TAMANHO_PACOTE, b'\x00')[:TAMANHO_PACOTE]


def format_velocidade(bits_por_seg):
    if bits_por_seg >= 1_000_000_000:
        return f"{bits_por_seg / 1_000_000_000:.2f} Gbit/s"
    elif bits_por_seg >= 1_000_000:
        return f"{bits_por_seg / 1_000_000:.2f} Mbit/s"
    else:
        return f"{bits_por_seg / 1_000:.2f} Kbit/s"


def mostrar_metricas(titulo, pacotes_env, pacotes_rec, bytes_total, tempo):
    bits = bytes_total * 8
    perdidos = pacotes_env - pacotes_rec
    pac_por_seg = pacotes_rec / tempo if tempo > 0 else 0
    bits_por_seg = bits / tempo if tempo > 0 else 0

    print(f"\n{'='*50}")
    print(f"  {titulo}")
    print(f"{'='*50}")
    print(f"  Pacotes enviados:      {pacotes_env:,}")
    print(f"  Pacotes recebidos:     {pacotes_rec:,}")
    print(f"  Pacotes perdidos:      {perdidos:,}")
    print(f"  Bytes trafegados:      {bytes_total:,}")
    print(f"  Vel. média (pac/s):    {pac_por_seg:,.0f}")
    print(f"  Vel. média (bit/s):    {format_velocidade(bits_por_seg)}")
    print(f"  Duração:               {tempo:.2f}s")
    print(f"{'='*50}")


# ── TCP ──────────────────────────────────────────────

def sender_tcp(host, porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, porta))
    print(f"[TCP] Conectado a {host}:{porta}. Enviando por {DURACAO}s...")

    seq = 0
    bytes_enviados = 0
    inicio = time.time()

    while time.time() - inicio < DURACAO:
        sock.sendall(construir_pacote(seq))
        seq += 1
        bytes_enviados += TAMANHO_PACOTE

    sock.sendall(construir_pacote_fim(seq))
    tempo = time.time() - inicio

    try:
        sock.settimeout(5)
        dados = sock.recv(64)
        pacotes_recebidos = int(dados.decode().strip())
    except Exception:
        pacotes_recebidos = seq

    sock.close()
    mostrar_metricas("RELATÓRIO TCP - SENDER", seq, pacotes_recebidos, bytes_enviados, tempo)


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
                mostrar_metricas("RELATÓRIO TCP - RECEIVER", total_env, pacotes, bytes_recebidos, tempo)
                return

            if inicio is None:
                inicio = time.time()
            pacotes += 1
            bytes_recebidos += TAMANHO_PACOTE

    tempo = time.time() - inicio if inicio else DURACAO
    conn.close()
    server.close()
    mostrar_metricas("RELATÓRIO TCP - RECEIVER", pacotes, pacotes, bytes_recebidos, tempo)


# ── UDP ──────────────────────────────────────────────

def sender_udp(host, porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    destino = (host, porta)
    print(f"[UDP] Enviando para {host}:{porta} por {DURACAO}s...")

    seq = 0
    bytes_enviados = 0
    inicio = time.time()

    while time.time() - inicio < DURACAO:
        sock.sendto(construir_pacote(seq), destino)
        seq += 1
        bytes_enviados += TAMANHO_PACOTE

    for _ in range(10):
        sock.sendto(construir_pacote_fim(seq), destino)
        time.sleep(0.01)

    sock.close()
    tempo = time.time() - inicio
    mostrar_metricas("RELATÓRIO UDP - SENDER", seq, seq, bytes_enviados, tempo)
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
    mostrar_metricas("RELATÓRIO UDP - RECEIVER", pacotes_enviados, pacotes, bytes_recebidos, tempo)


# ── MENÚ ─────────────────────────────────────────────

def pedir_protocolo():
    while True:
        p = input("  Protocolo (tcp/udp): ").strip().lower()
        if p in ('tcp', 'udp'):
            return p
        print("  Inválido. Digite 'tcp' ou 'udp'.")


def pedir_ip():
    while True:
        ip = input("  IP destino: ").strip()
        if ip:
            return ip
        print("  IP não pode ficar vazio.")


def pedir_porta():
    while True:
        try:
            p = int(input("  Porta: ").strip())
            if 1 <= p <= 65535:
                return p
            print("  Porta deve estar entre 1 e 65535.")
        except ValueError:
            print("  Digite um número válido.")


def main():
    while True:
        print(f"\n{'='*50}")
        print("  FERRAMENTA DE TESTE DE DESEMPENHO DE REDE")
        print(f"{'='*50}")
        print("  1) Sender  (enviar pacotes)")
        print("  2) Receiver (receber pacotes)")
        print("  0) Sair")
        opcao = input("  Escolha: ").strip()

        if opcao == '0':
            print("Até logo!")
            break

        elif opcao == '1':
            proto = pedir_protocolo()
            ip = pedir_ip()
            porta = pedir_porta()
            try:
                if proto == 'tcp':
                    sender_tcp(ip, porta)
                else:
                    sender_udp(ip, porta)
            except ConnectionRefusedError:
                print("  [ERRO] Conexão recusada. O receiver está escutando?")
            except Exception as e:
                print(f"  [ERRO] {e}")

        elif opcao == '2':
            proto = pedir_protocolo()
            porta = pedir_porta()
            try:
                if proto == 'tcp':
                    receiver_tcp(porta)
                else:
                    receiver_udp(porta)
            except OSError as e:
                print(f"  [ERRO] {e}")

        else:
            print("  Opção inválida.")


if __name__ == '__main__':
    main()