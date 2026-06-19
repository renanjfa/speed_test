import socket
import time

TAMANHO_PACOTE = 500
BASE_STRING = "teste de rede 2026"
DURACAO = 20
HOST = '0.0.0.0'
MARCADOR_FIM = b'\xff\xff\xff\xff'
REPETICOES = 3


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

    return {
        'pacotes_env': pacotes_env,
        'pacotes_rec': pacotes_rec,
        'perdidos': perdidos,
        'bytes': bytes_total,
        'pac_por_seg': pac_por_seg,
        'bits_por_seg': bits_por_seg,
        'tempo': tempo,
    }


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
    return mostrar_metricas("RELATÓRIO TCP - SENDER", seq, pacotes_recebidos, bytes_enviados, tempo)


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
                return mostrar_metricas("RELATÓRIO TCP - RECEIVER", total_env, pacotes, bytes_recebidos, tempo)

            if inicio is None:
                inicio = time.time()
            pacotes += 1
            bytes_recebidos += TAMANHO_PACOTE

    tempo = time.time() - inicio if inicio else DURACAO
    conn.close()
    server.close()
    return mostrar_metricas("RELATÓRIO TCP - RECEIVER", pacotes, pacotes, bytes_recebidos, tempo)


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
    return mostrar_metricas("RELATÓRIO UDP - SENDER", seq, seq, bytes_enviados, tempo)


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
    return mostrar_metricas("RELATÓRIO UDP - RECEIVER", pacotes_enviados, pacotes, bytes_recebidos, tempo)


# ── TABLA RESUMEN ────────────────────────────────────

def mostrar_resumen(resultados, proto, rede, modo):
    print(f"\n{'='*70}")
    print(f"  TABELA COMPARATIVA - {proto.upper()} / {rede.upper()} / {modo.upper()}")
    print(f"{'='*70}")
    print(f"  {'Test':<6} {'Enviados':>12} {'Recebidos':>12} {'Perdidos':>10} {'Bytes':>14} {'Pac/s':>10} {'Velocidade':>14}")
    print(f"  {'-'*64}")

    for i, r in enumerate(resultados, 1):
        print(f"  {i:<6} {r['pacotes_env']:>12,} {r['pacotes_rec']:>12,} {r['perdidos']:>10,} {r['bytes']:>14,} {r['pac_por_seg']:>10,.0f} {format_velocidade(r['bits_por_seg']):>14}")

    avg_env = sum(r['pacotes_env'] for r in resultados) // len(resultados)
    avg_rec = sum(r['pacotes_rec'] for r in resultados) // len(resultados)
    avg_per = sum(r['perdidos'] for r in resultados) // len(resultados)
    avg_byt = sum(r['bytes'] for r in resultados) // len(resultados)
    avg_pac = sum(r['pac_por_seg'] for r in resultados) / len(resultados)
    avg_bit = sum(r['bits_por_seg'] for r in resultados) / len(resultados)

    print(f"  {'-'*64}")
    print(f"  {'MÉDIA':<6} {avg_env:>12,} {avg_rec:>12,} {avg_per:>10,} {avg_byt:>14,} {avg_pac:>10,.0f} {format_velocidade(avg_bit):>14}")
    print(f"{'='*70}")


# ── MENÚ ─────────────────────────────────────────────

def pedir_protocolo():
    while True:
        p = input("  Protocolo (tcp/udp): ").strip().lower()
        if p in ('tcp', 'udp'):
            return p
        print("  Inválido. Digite 'tcp' ou 'udp'.")


def pedir_modo():
    while True:
        m = input("  Modo (sender/receiver): ").strip().lower()
        if m in ('sender', 'receiver'):
            return m
        print("  Inválido. Digite 'sender' ou 'receiver'.")


def pedir_rede():
    while True:
        r = input("  Rede (cabo/wifi): ").strip().lower()
        if r in ('cabo', 'wifi'):
            return r
        print("  Inválido. Digite 'cabo' ou 'wifi'.")


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
        print("  1) Executar bateria de 3 testes")
        print("  0) Sair")
        opcao = input("  Escolha: ").strip()

        if opcao == '0':
            print("Até logo!")
            break

        elif opcao == '1':
            proto = pedir_protocolo()
            modo = pedir_modo()
            rede = pedir_rede()
            porta = pedir_porta()

            ip = None
            if modo == 'sender':
                ip = pedir_ip()

            resultados = []

            for i in range(1, REPETICOES + 1):
                print(f"\n{'#'*50}")
                print(f"  TESTE {i}/{REPETICOES} - {proto.upper()} / {rede.upper()} / {modo.upper()}")
                print(f"{'#'*50}")

                try:
                    if modo == 'sender':
                        if proto == 'tcp':
                            r = sender_tcp(ip, porta)
                        else:
                            r = sender_udp(ip, porta)
                    else:
                        if proto == 'tcp':
                            r = receiver_tcp(porta)
                        else:
                            r = receiver_udp(porta)
                    resultados.append(r)
                except ConnectionRefusedError:
                    print("  [ERRO] Conexão recusada. O outro lado está escutando?")
                except Exception as e:
                    print(f"  [ERRO] {e}")

                if i < REPETICOES:
                    print(f"\n  Próximo teste em 3 segundos...")
                    time.sleep(3)

            if resultados:
                mostrar_resumen(resultados, proto, rede, modo)

        else:
            print("  Opção inválida.")


if __name__ == '__main__':
    main()