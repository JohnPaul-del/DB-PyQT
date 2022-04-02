import sys
import json
import socket
import time
import argparse
import logging
import threading

import logs.client_log_cnf
from common.variables import *
from common.utils import *
from errors import IncorrectDataRecievedError, ReqFieldMissingError, ServerError
from decos import log

logger = logging.getLogger('client')


def main():
    print('Start consol client')
    server_address, server_port, client_name = arg_parser()

    if not client_name:
        print('Enter username!')

    logger.info(f'Client has been started. Server: {server_address}. Port: {server_port}. User: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = proccess_response_answer(get_message(transport))
        logger.info(f'Connection established. {answer}')
    except json.JSONDecodeError:
        logger.error(f'Could not decode JSON')
        exit(1)
    except ServerError as error:
        logger.error(f'Connection failed. Server return {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        logger.error(f'Not enough arguments {missing_error.missing_field}')
        exit(1)
    except (ConnectionError, ConnectionRefusedError):
        logger.critical(f'Connection failed. {server_address}:{server_port} unreachable')
        exit(1)
    else:
        receiver = threading.Thread(target=get_message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()
        logger.debug('Successfully started')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


@log
def exit_message(account):
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account,
    }


@log
def get_message_from_server(sock, username):
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE \
                    and SENDER in message and DESTINATION in message \
                    and MESSAGE_TEXT in message and message[DESTINATION] == username:
                print(f'Message from user: {message[SENDER]},\n{message[MESSAGE_TEXT]}')
            else:
                logger.error(f'Incorrect data received from server: {message}')
        except IncorrectDataRecievedError:
            logger.error('Encoding error')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionRefusedError, json.JSONDecodeError):
            logger.critical('Connection lost!')
            break


@log
def create_message(sock, account_name='guest'):
    message_to = input('Enter username: ')
    message_text = input('Enter text: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: message_to,
        TIME: time.time(),
        MESSAGE_TEXT: message_text
    }
    logger.debug(f'Message dict created: {message_dict}')
    try:
        send_message(sock, message_dict)
        logger.info(f'Message sent: {message_to}')
    except (OSError, ConnectionError, ConnectionAbortedError, ConnectionRefusedError):
        logger.critical('Connection lost')
        exit(1)


@log
def interactive(sock, username):
    user_help()
    while True:
        command = input('Enter command: ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'help':
            user_help()
        elif command == 'quit':
            send_message(sock, exit_message(username))
            print('Connection closed')
            logger.info('Sessions closed by user')
            time.sleep(0.5)
            break
        else:
            print('Command not available. Enter "help" to see all commands')


@log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name,
        },
    }
    logger.debug(f'{PRESENCE} has been created for user: {account_name}')
    return out


@log
def proccess_response_answer(message):
    logger.debug(f'Message from server: {message}')
    if RESPONSE in message:
        if message.RESPONSE == 200:
            return '200: OK'
        elif message.RESPONSE == 400:
            raise ServerError(f'400: {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    a_parser = argparse.ArgumentParser()
    a_parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    a_parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    a_parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = a_parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        logger.critical(f'Port {server_port} is out of range. Client disconnected')
        exit(1)

    return server_address, server_port, client_name


def user_help():
    print(f'Commands:\n'
          f'1. message - create and send a message\n'
          f'2. help - Command list\n'
          f'3. quit - Close the connection and exit')


if __name__ == '__main__':
    main()
