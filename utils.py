from globals import TAMANHO_PACOTE, BASE_STRING, MARCADOR_FIM


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