import socket
import argparse
import select
import threading

from common.utils import *
from decos import log
from metaclass import ServerMaker
from main_descriptors import Port
from server_db import ServerStorage

logger = logging.getLogger('server')


class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.address = listen_address
        self.port = listen_port
        self.database = database

        self.clients = []
        self.messages = []
        self.names = {}

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
        logger.debug(f'Message from client {message}')

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Username already in use'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE \
                and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names[ACCOUNT_NAME].close()
            del self.names[ACCOUNT_NAME]
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Invalid request'
            send_message(client, response)


@log
def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    names = parser.parse_args(sys.argv[1:])
    listen_address = names.a
    listen_port = names.p
    return listen_address, listen_port


def user_help():
    print(f'Available commands:'
          f'users - All users list'
          f'connected - Active users list'
          f'log - Login history'
          f'exit = Shutdown server'
          f'help - Help for available commands')


def main():
    listen_address, listen_port = args_parser()

    database = ServerStorage()

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.main_loop()

    user_help()

    while True:
        command = input('Enter command: ')
        if command == 'help':
            user_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'User {user[0]}. Last login {user[1]}')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(f'User {user[0]} connected at {user[3]}')
        elif command == 'log':
            username = input('Enter username or press Enter for print all history')
            for user in sorted(database.login_history(username)):
                print(f'User {user[0]}({user[2]}:{user[3]}) connected at {user[1]}')
        else:
            print(f'Invalid command')


if __name__ == '__main__':
    main()
