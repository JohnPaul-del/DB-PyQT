import socket
import argparse
import sys
import json
import logging
import select
import time

import logs.server_log_cnf
from errors import IncorrectDataRecievedError
from common.variables import *
from common.utils import *
from decos import log

logger = logging.getLogger('server')


def main():
    listen_address, listen_port = args_parser()

    logger.info(f'Server {listen_address}:{listen_port} is running')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))
    transport.settimeout(0.5)

    clients = []
    messages = []
    names = {}

    transport.listen(MAX_CONNECTIONS)
    while True:
        try:
            client, client_address = transport.accept()
        except OSError:
            pass
        else:
            logger.info(f'Connecting to {client_address}')
            clients.append(client)

        recv_data_list = []
        send_data_list = []
        errors_list = []
        try:
            if clients:
                recv_data_list, send_data_list, errors_list = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if recv_data_list:
            for message_client in recv_data_list:
                try:
                    process_client_message(get_message(message_client), messages, message_client, clients, names)
                except (ConnectionError, ConnectionRefusedError, ConnectionAbortedError):
                    logger.info(f'Client {message_client.getpeername()} has been disconnected')
                    clients.remove(message_client)

        for mes in messages:
            try:
                process_message(mes, names, send_data_list)
            except (ConnectionError, ConnectionRefusedError, ConnectionAbortedError):
                logger.info(f'Connection with {mes[DESTINATION]} has been failed')
                clients.remove(names[mes[DESTINATION]])
                del names[mes[DESTINATION]]
        messages.clear()


@log
def process_client_message(message, messages_list, client, clients, names):
    logger.debug(f'Message from client {message}')

    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Username already in use'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    elif ACTION in message and message[ACTION] == MESSAGE \
            and DESTINATION in message and TIME in message \
            and SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[ACCOUNT_NAME])
        names[ACCOUNT_NAME].close()
        del names[ACCOUNT_NAME]
        return
    else:
        response = RESPONSE_400
        response[ERROR] = 'Invalid request'
        send_message(client, response)


@log
def process_message(message, names, listen_socks):
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        logger.info(f'Message has been sent to {message[DESTINATION]} from {message[SENDER]}')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        logger.error(f'User {message[DESTINATION]} is not authorized')


@log
def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    names = parser.parse_args(sys.argv[1:])
    listen_address = names.a
    listen_port = names.p

    if not 1023 < listen_port < 65536:
        logger.critical(f'Port {listen_port} out of range')
        exit(1)
    return listen_address, listen_port


if __name__ == '__main__':
    main()
