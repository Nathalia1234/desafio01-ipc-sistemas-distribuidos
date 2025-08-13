# --------------------------------------------------------------------------------------------------------------------------
# Atividade Individual 01 - Desafio 01: Comunicação entre Processos (IPC)

# Aluno(a): Nathalia Ohana Barigchum Leite

# RA: 162.604566

# Data: 20/08/2025
# --------------------------------------------------------------------------------------------------------------------------


# Importação das bibliotecas necessárias
import multiprocessing
import random
import time
import datetime
import sys  # Importa a biblioteca de sistema


# --- FUNCAO DE LOG SINCRONIZADA ---
# Helper para escrever no arquivo de log e no console de forma segura
def log_message(lock, filename, message):
    """Adquire um lock para escrever uma mensagem no arquivo de log e no console."""
    with lock:
        # Escreve no arquivo de log de execucao
        with open(filename, "a") as f:
            f.write(message + "\n")
        # Tambem imprime no console para visualizacao em tempo real, se necessario
        print(message)


# --- PROCESSO PRODUTOR ---
def produtor(pipe_conn, lock, log_filename):
    """
    Representa o processo Produtor.
    Envia dados via Pipe e registra suas acoes usando a funcao de log.
    """
    print("\n")
    log_message(lock, log_filename, "[Produtor]: Processo iniciado.")
    try:
        for i in range(12):
            dado = random.randint(1, 100)
            log_message(
                lock, log_filename, f"[Produtor]: Enviando dado: {dado} ({i+1}/12)"
            )
            pipe_conn.send(dado)
            time.sleep(random.uniform(0.5, 1.5))

        log_message(
            lock,
            log_filename,
            "[Produtor]: Todos os dados foram enviados. Enviando sinal de termino.",
        )
        pipe_conn.send(None)

    except BrokenPipeError:
        log_message(
            lock,
            log_filename,
            "[Produtor-ERRO]: O consumidor encerrou a conexao prematuramente!",
        )
    finally:
        pipe_conn.close()
        log_message(lock, log_filename, "[Produtor]: Conexao fechada. Finalizando.")


# --- PROCESSO CONSUMIDOR ---
def consumidor(pipe_conn, lock, log_filename):
    """
    Representa o processo Consumidor.
    Recebe dados, processa, e registra em seu proprio log e no log de execucao geral.
    """
    log_message(
        lock, log_filename, "[Consumidor]: Processo iniciado. Aguardando dados..."
    )

    try:
        with open("consumer_log.txt", "w") as consumer_log_file:
            # CORRECAO DE HORARIO 1: Cabecalho do log do consumidor
            consumer_log_file.write(
                f"### Log de Execucao do Consumidor - {datetime.datetime.now().strftime('%H:%M:%S')} ###\n\n"
            )

            while True:
                dado = pipe_conn.recv()

                if dado is None:
                    log_message(
                        lock, log_filename, "[Consumidor]: Sinal de termino recebido."
                    )
                    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
                    consumer_log_file.write(
                        f"[{hora_atual}] - Sinal de termino recebido. Encerrando.\n"
                    )
                    break

                log_message(lock, log_filename, f"[Consumidor]: Dado recebido: {dado}")

                resultado = "Par" if dado % 2 == 0 else "Impar"
                hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
                log_processamento = f"[{hora_atual}] - Dado {dado} recebido e processado como '{resultado}'.\n"

                consumer_log_file.write(log_processamento)
                consumer_log_file.flush()

    except EOFError:
        log_message(
            lock,
            log_filename,
            "[Consumidor-ERRO]: O canal de comunicacao foi fechado inesperadamente!",
        )
    finally:
        log_message(lock, log_filename, "[Consumidor]: Finalizando.")


# --- BLOCO PRINCIPAL ---
if __name__ == "__main__":

    # Nome do arquivo que centralizara o log de execucao de todos os processos.
    EXECUTION_LOG_FILE = "execution_log.txt"

    # Limpa o arquivo de log no inicio da execucao.
    with open(EXECUTION_LOG_FILE, "w") as f:
        # CORRECAO DE HORARIO 2: Cabecalho do log de execucao geral
        f.write(
            f"### Log de Execucao - {datetime.datetime.now().strftime('%H:%M:%S')} ###\n\n"
        )

    # Cria um Lock para sincronizar o acesso ao arquivo de log.
    lock = multiprocessing.Lock()

    # Cria o Pipe para comunicacao.
    conn_produtor, conn_consumidor = multiprocessing.Pipe()

    # Cria os processos, passando o lock e o nome do arquivo de log como argumentos.
    processo_produtor = multiprocessing.Process(
        target=produtor, args=(conn_produtor, lock, EXECUTION_LOG_FILE)
    )
    processo_consumidor = multiprocessing.Process(
        target=consumidor, args=(conn_consumidor, lock, EXECUTION_LOG_FILE)
    )

    # Inicia e aguarda a finalizacao dos processos.
    processo_produtor.start()
    processo_consumidor.start()

    processo_produtor.join()
    processo_consumidor.join()

    # Mensagem final no console.
    print(
        "\nExecucao finalizada. Verifique os arquivos 'execution_log.txt' e 'consumer_log.txt'.\n"
    )
