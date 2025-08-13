# --------------------------------------------------------------------------------------------------------------------------
# Atividade Individual 01 - Desafio 01: Comunicação entre Processos (IPC)

# Aluno(a): Nathalia Ohana Barigchum Leite

# Data: 20/08/2025
# --------------------------------------------------------------------------------------------------------------------------


# A principal biblioteca para este desafio, permite criar e gerenciar processos.
import multiprocessing

# Usada para gerar números aleatórios, cumprindo o requisito de dados variáveis.
import random

# Permite adicionar pausas no programa, simulando tempo de processamento.
import time

# Utilizada para adicionar data e hora aos registros de log.
import datetime

# Importa a biblioteca de sistema
import sys


# --- Função Auxiliar de Log Sincronizado ---
# Esta função foi criada para centralizar e proteger a escrita nos arquivos de log.
def log_message(lock, filename, message):
    """
    Adquire um lock para garantir que apenas um processo escreva no log por vez.
    Isso evita que as mensagens do produtor e do consumidor se misturem no arquivo.
    """
    # O 'with lock:' garante que o lock seja adquirido antes de executar o bloco
    # e liberado automaticamente depois, mesmo que ocorram erros.
    with lock:
        # Abre o arquivo de log de execução geral em modo 'append' ('a'),
        # que adiciona novas linhas ao final do arquivo sem apagar o conteúdo existente.
        with open(filename, "a") as f:
            # Escreve a mensagem formatada no arquivo, adicionando uma quebra de linha.
            f.write(message + "\n")
        # Imprime a mesma mensagem no console para acompanhamento em tempo real.
        print(message)


# --- Processo Produtor ---
# Esta função define o comportamento do processo que gera e envia os dados.
def produtor(pipe_conn, lock, log_filename):
    """
    Representa o processo Produtor.
    Gera dados (números aleatórios) e os envia através do Pipe para o Consumidor.
    """
    # Log para indicar que o processo do produtor foi iniciado com sucesso.
    log_message(lock, log_filename, "[Produtor]: Processo iniciado.")

    # O bloco 'try...finally' garante que, mesmo em caso de erro,
    # o código no 'finally' (como fechar a conexão) será executado.
    try:
        # Este laço 'for' cumpre o requisito de enviar no mínimo 10 itens de dados.
        for i in range(12):
            # Gera um número inteiro aleatório entre 1 e 100.
            dado = random.randint(1, 100)
            # Log informando qual dado está sendo enviado no momento.
            log_message(
                lock, log_filename, f"[Produtor]: Enviando dado: {dado} ({i+1}/12)"
            )
            # Ação principal: envia o dado gerado através do canal de comunicação (Pipe).
            pipe_conn.send(dado)
            # Pausa a execução por um tempo aleatório para simular um processo de produção real.
            time.sleep(random.uniform(0.5, 1.5))

        # Após enviar todos os dados, envia um valor 'None'.
        # 'None' atua como um "sinal de término" para avisar ao consumidor que o trabalho acabou.
        log_message(
            lock,
            log_filename,
            "[Produtor]: Todos os dados foram enviados. Enviando sinal de termino.",
        )
        pipe_conn.send(None)

    # Tratamento de erro para o caso de o consumidor fechar a conexão antes da hora.
    except BrokenPipeError:
        log_message(
            lock,
            log_filename,
            "[Produtor-ERRO]: O consumidor encerrou a conexao prematuramente!",
        )
    finally:
        # Ação crítica: fecha a ponta do pipe do produtor para liberar os recursos do sistema.
        pipe_conn.close()
        log_message(lock, log_filename, "[Produtor]: Conexao fechada. Finalizando.")


# --- Processo Consumidor ---
# Esta função define o comportamento do processo que recebe e processa os dados.
def consumidor(pipe_conn, lock, log_filename):
    """
    Representa o processo Consumidor.
    Fica aguardando dados do Pipe, processa-os e registra tudo em arquivos de log.
    """
    # Log para indicar que o processo do consumidor foi iniciado e está pronto para receber.
    log_message(
        lock, log_filename, "[Consumidor]: Processo iniciado. Aguardando dados..."
    )

    try:
        # Abre o arquivo de log específico do consumidor em modo de escrita ('w').
        # O modo 'w' apaga o conteúdo anterior, garantindo um log limpo a cada nova execução.
        with open("consumer_log.txt", "w") as consumer_log_file:
            # Escreve um cabeçalho no log do consumidor com a hora de início.
            consumer_log_file.write(
                f"### Log de Execucao do Consumidor - {datetime.datetime.now().strftime('%H:%M:%S')} ###\n\n"
            )

            # Inicia um laço infinito que só será interrompido pelo sinal de término.
            while True:
                # Esta linha é bloqueante: o processo para aqui e aguarda até que um dado chegue pelo Pipe.
                dado = pipe_conn.recv()

                # Verifica se o dado recebido é o sinal de término (None) enviado pelo produtor.
                if dado is None:
                    # Se for o sinal, loga a informação e sai do laço com 'break'.
                    log_message(
                        lock, log_filename, "[Consumidor]: Sinal de termino recebido."
                    )
                    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
                    consumer_log_file.write(
                        f"[{hora_atual}] - Sinal de termino recebido. Encerrando.\n"
                    )
                    break

                # Loga a informação de que um dado foi recebido com sucesso.
                log_message(lock, log_filename, f"[Consumidor]: Dado recebido: {dado}")

                # Processamento do dado: verifica se o número é par ou ímpar.
                resultado = "Par" if dado % 2 == 0 else "Impar"
                # Pega a hora atual para o registro do log.
                hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
                # Formata a mensagem que será escrita no log específico do consumidor.
                log_processamento = f"[{hora_atual}] - Dado {dado} recebido e processado como '{resultado}'.\n"

                # Escreve o resultado do processamento no arquivo de log do consumidor.
                consumer_log_file.write(log_processamento)
                # Força a escrita imediata dos dados no arquivo, sem esperar o buffer encher.
                consumer_log_file.flush()

    # Tratamento de erro para o caso de o produtor fechar a conexão inesperadamente.
    except EOFError:
        log_message(
            lock,
            log_filename,
            "[Consumidor-ERRO]: O canal de comunicacao foi fechado inesperadamente!",
        )
    finally:
        # Log que indica o término do processo consumidor.
        log_message(lock, log_filename, "[Consumidor]: Finalizando.")


# --- Bloco Principal de Execução ---
# Este bloco só é executado quando o script é chamado diretamente.
if __name__ == "__main__":

    # Define o nome do arquivo que vai centralizar o log de eventos de ambos os processos.
    EXECUTION_LOG_FILE = "execution_log.txt"

    # Abre o arquivo de log principal em modo de escrita ('w') para limpá-lo antes de iniciar.
    with open(EXECUTION_LOG_FILE, "w") as f:
        # Escreve um cabeçalho no log de execução geral.
        f.write(
            f"### Log de Execucao - {datetime.datetime.now().strftime('%H:%M:%S')} ###\n\n"
        )

    # Cria um objeto Lock. Este objeto será usado para sincronizar o acesso ao log de execução.
    lock = multiprocessing.Lock()

    # Cria um Pipe, que retorna duas pontas de conexão: uma para o produtor e outra para o consumidor.
    conn_produtor, conn_consumidor = multiprocessing.Pipe()

    # Cria o objeto do processo produtor, especificando a função alvo (target)
    # e os argumentos (args) que ela receberá (a ponta do pipe, o lock e o nome do arquivo de log).
    processo_produtor = multiprocessing.Process(
        target=produtor, args=(conn_produtor, lock, EXECUTION_LOG_FILE)
    )
    # Cria o objeto do processo consumidor, passando seus respectivos argumentos.
    processo_consumidor = multiprocessing.Process(
        target=consumidor, args=(conn_consumidor, lock, EXECUTION_LOG_FILE)
    )

    # Inicia a execução do processo produtor. O sistema operacional aloca um novo processo para ele.
    processo_produtor.start()
    # Inicia a execução do processo consumidor.
    processo_consumidor.start()

    # O processo principal (este script) aguarda aqui até que o processo_produtor termine sua execução.
    processo_produtor.join()
    # Em seguida, aguarda também pelo término do processo_consumidor.
    processo_consumidor.join()

    # Mensagem final exibida no console após ambos os processos terem finalizado.
    print(
        "\nExecucao finalizada. Verifique os arquivos 'execution_log.txt' e 'consumer_log.txt'.\n"
    )
