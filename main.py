import TCP as tcp
import UDP as udp
import menu as m

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
            proto = m.pedir_protocolo()
            ip = m.pedir_ip()
            porta = m.pedir_porta()
            try:
                if proto == 'tcp':
                    tcp.sender_tcp(ip, porta)
                else:
                    udp.sender_udp(ip, porta)
            except ConnectionRefusedError:
                print("  [ERRO] Conexão recusada. O receiver está escutando?")
            except Exception as e:
                print(f"  [ERRO] {e}")

        elif opcao == '2':
            proto = m.pedir_protocolo()
            porta = m.pedir_porta()
            try:
                if proto == 'tcp':
                    tcp.receiver_tcp(porta)
                else:
                    udp.receiver_udp(porta)
            except OSError as e:
                print(f"  [ERRO] {e}")

        else:
            print("  Opção inválida.")


if __name__ == '__main__':
    main()