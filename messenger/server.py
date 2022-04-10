import argparse
import configparser
import os.path
import select
import socket
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from common.utils import *
from decos import log
from main_descriptors import Port
from metaclass import ServerMaker
from server_db import ServerStorage
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow

logger = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()

class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.address = listen_address
        self.port = listen_port
        self.database = database

        self.clients = []
        self.messages = []
        self.names = {}

        super().__init__()

    def init_socket(self):
        logger.info(f'Server started. {self.address}:{self.port}')

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.address, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Connection established with client {client_address}')
                self.clients.append(client)
            recv_data_list = []
            send_data_list = []
            try:
                if self.clients:
                    recv_data_list, send_data_list, errors_list = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if recv_data_list:
                for message_client in recv_data_list:
                    try:
                        self.process_client_message(get_message(message_client), message_client)
                    except (ConnectionError, ConnectionRefusedError, ConnectionAbortedError):
                        logger.info(f'Client {message_client.getpeername()} has been disconnected')
                        self.clients.remove(message_client)

            for mes in self.messages:
                try:
                    self.process_message(mes, send_data_list)
                except (ConnectionError, ConnectionRefusedError, ConnectionAbortedError):
                    logger.info(f'Connection with {mes[DESTINATION]} has been failed')
                    self.clients.remove(self.names[mes[DESTINATION]])
                    del self.names[mes[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f'Message has been sent to {message[DESTINATION]} from {message[SENDER]}')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(f'User {message[DESTINATION]} is not authorized')

    def process_client_message(self, message, client):
        global new_connection
        logger.debug(f'Message from client {message}')

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                )
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Username already in use'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE \
                and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message\
                and self.names[message[SENDER]] == client:
            self.messages.append(message)
            self.database.process_message(message[SENDER],
                                          message[DESTINATION],
                                          )
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message\
                and self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return
        elif ACTION in message and message[ACTION] == GET_CONTACTS \
            and USER in message and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)
        elif ACTION in message and message[ACTION] == ADD_CONTACT \
            and ACCOUNT_NAME in message and USER in message \
            and self.names[message[USER]] == client:
            self.database.add_contact(message[USER],
                                      message[ACCOUNT_NAME],
                                      )
            send_message(client, RESPONSE_200)
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT \
            and ACCOUNT_NAME in message and USER in message \
            and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER],
                                         message[ACCOUNT_NAME],
                                         )
            send_message(client, RESPONSE_200)
        elif ACTION in message and message[ACTION] == USERS_REQUEST \
            and ACCOUNT_NAME in message and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_message(client, response)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Invalid request'
            send_message(client, response)


@log
def args_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    names = parser.parse_args(sys.argv[1:])
    listen_address = names.a
    listen_port = names.p
    return listen_address, listen_port


def main():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")


    listen_address, listen_port = args_parser(
        config['SETTINGS']['Default_port'],
        config['SETTINGS']['Listen_address'],
    )

    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file'],
        ))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server running')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Error', 'Port must be an integer')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Config has been successfully saved')
            else:
                message.warning(config_window,
                                'Error',
                                'Port must be from 1024 to 65546',
                                )
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
