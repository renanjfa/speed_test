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