import configparser
import sys
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout)
import psycopg2
import os

# Função para conectar ao banco de dados
def conectar_ao_banco(host, database, user, password):
    try:
        conn = psycopg2.connect(host=host,
                                database=database,
                                user=user,
                                password=password)
        return conn
    except psycopg2.Error as e:
        QMessageBox.critical(None, 'Erro', f'Erro ao conectar ao banco de dados: {e}')
        return None

# Funções para gerenciar o arquivo de configuração
def ler_config():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        return config['DATABASE']
    except (FileNotFoundError, KeyError):
        return None

def salvar_config(host, database, user, password):
    config = configparser.ConfigParser()
    config['DATABASE'] = {
        'host': host,
        'database': database,
        'user': user,
        'password': password
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

class ConfigConexao(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Configurar Conexão')

        # Labels e campos de entrada para os dados de conexão
        self.lbl_host = QLabel('Host:')
        self.txt_host = QLineEdit()
        self.lbl_database = QLabel('Banco de Dados:')
        self.txt_database = QLineEdit()
        self.lbl_user = QLabel('Usuário:')
        self.txt_user = QLineEdit()
        self.lbl_password = QLabel('Senha:')
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)

        # Botões para testar a conexão e carregar configuração
        self.btn_conectar = QPushButton('Conectar')
        self.btn_conectar.clicked.connect(self.testar_conexao)
        self.btn_carregar_config = QPushButton('Carregar Conexão Salva')
        self.btn_carregar_config.clicked.connect(self.carregar_configuracao)

        # Layout dos botões
        hbox = QHBoxLayout()
        hbox.addWidget(self.btn_conectar)
        hbox.addWidget(self.btn_carregar_config)

        vbox = QVBoxLayout()
        vbox.addWidget(self.lbl_host)
        vbox.addWidget(self.txt_host)
        vbox.addWidget(self.lbl_database)
        vbox.addWidget(self.txt_database)
        vbox.addWidget(self.lbl_user)
        vbox.addWidget(self.txt_user)
        vbox.addWidget(self.lbl_password)
        vbox.addWidget(self.txt_password)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def testar_conexao(self):
        try:
            host = self.txt_host.text()
            database = self.txt_database.text()
            user = self.txt_user.text()
            password = self.txt_password.text()

            conn = conectar_ao_banco(host, database, user, password)
            if conn:
                conn.close()
                self.salvar_configuracao(host, database, user, password)
                QMessageBox.information(self, 'Sucesso', 'Conexão bem-sucedida e salva!')
                self.abrir_janela_principal(host, database, user, password)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao conectar ao banco de dados: {e}')

    def salvar_configuracao(self, host, database, user, password):
        salvar_config(host, database, user, password)

    def carregar_configuracao(self):
        try:
            config = ler_config()
            self.txt_host.setText(config['host'])
            self.txt_database.setText(config['database'])
            self.txt_user.setText(config['user'])
            self.txt_password.setText(config['password'])
            QMessageBox.information(self, 'Sucesso', 'Configuração carregada com sucesso!')
        except (FileNotFoundError, KeyError):
            QMessageBox.warning(self, 'Aviso', 'Nenhuma configuração salva encontrada.')

    def abrir_janela_principal(self, host, database, user, password):
        self.close()
        self.janela_principal = AtualizadorBancoDados(host, database, user, password)
        self.janela_principal.show()

class AtualizadorBancoDados(QWidget):
    def __init__(self, host, database, user, password):
        super().__init__()
        self.host = host
        self.database = database
        self.user = user
        self.password = password

        self.setWindowTitle('EXTERMINADOR DE SENHAS')
        self.setWindowIcon(QIcon('icon.ico'))
        self.setGeometry(100, 100, 500, 300)

        # Labels e campos de entrada para as datas
        self.lbl_data_inicio = QLabel('Data de Início:')
        self.txt_data_inicio = QLineEdit('2024-11-01 00:00:01.001-0300')
        self.lbl_data_fim = QLabel('Data de Fim:')
        self.txt_data_fim = QLineEdit('2024-11-01 23:59:59.001-0300')

        # Botão para executar a atualização
        self.btn_atualizar = QPushButton('Atualizar')
        self.btn_atualizar.clicked.connect(self.atualizar_banco_dados)

        # Logo
        self.lbl_logo = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.lbl_logo.setPixmap(pixmap)
        else:
            QMessageBox.warning(self, 'Aviso', 'NÃO EXECUTAR DURANTE HORARIO DE ATENDIMENTO!.')

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.lbl_logo)
        vbox.addWidget(self.lbl_data_inicio)
        vbox.addWidget(self.txt_data_inicio)
        vbox.addWidget(self.lbl_data_fim)
        vbox.addWidget(self.txt_data_fim)
        vbox.addWidget(self.btn_atualizar)
        self.setLayout(vbox)

    def obter_linhas_afetadas(self, cursor, data_inicio, data_fim):
        # Obtendo os nomes das colunas
        cursor.execute("SELECT * FROM movsenha LIMIT 0")
        colunas = [desc[0] for desc in cursor.description]

        # Obtendo as linhas afetadas
        cursor.execute("""
            SELECT * FROM movsenha
            WHERE (dtentrada BETWEEN %s AND %s);
        """, (data_inicio, data_fim))
        linhas_afetadas = cursor.fetchall()

        return colunas, linhas_afetadas

    def gerar_log(self, colunas, linhas_afetadas):
        with open('log_atualizacao.txt', 'w') as logfile:
            logfile.write("Colunas:\n")
            logfile.write(", ".join(colunas) + '\n\n')
            logfile.write("Linhas afetadas:\n")
            for linha in linhas_afetadas:
                logfile.write(", ".join(map(str, linha)) + '\n')
            logfile.write(f"\nTotal de linhas afetadas: {len(linhas_afetadas)}\n")

    def atualizar_banco_dados(self):
        conn = None
        try:
            conn = conectar_ao_banco(self.host, self.database, self.user, self.password)
            if conn:
                cursor = conn.cursor()
                data_inicio = self.txt_data_inicio.text()
                data_fim = self.txt_data_fim.text()

                # Obtenha as colunas e linhas afetadas para o log
                colunas, linhas_afetadas = self.obter_linhas_afetadas(cursor, data_inicio, data_fim)
                self.gerar_log(colunas, linhas_afetadas)

                # Atualize o banco de dados
                cursor.execute("""
                    UPDATE movsenha SET situacao = '3'
                    WHERE (dtentrada BETWEEN %s AND %s);
                """, (data_inicio, data_fim))
                conn.commit()

                QMessageBox.information(self, 'Sucesso', f'Banco de dados atualizado com sucesso! {cursor.rowcount} linhas foram afetadas.')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao atualizar o banco de dados: {e}')
        finally:
            if conn:
                conn.close()

# Execução do aplicativo
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigConexao()
    window.show()
    sys.exit(app.exec_())