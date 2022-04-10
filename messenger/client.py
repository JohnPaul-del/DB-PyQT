import argparse
import socket
import threading
import time

from client_database import ClientDatabase
from common.utils import *
from decos import log
from errors import IncorrectDataRecievedError, ReqFieldMissingError, ServerError
from metaclass import ClientMaker

logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.socket = sock
        self.database = database
        super().__init__()

    def exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name,
        }

    def create_message(self):
        message_to = input('Enter username: ')
        message_text = input('Enter text: ')

        with database_lock:
            if not self.database.check_user(message_to):
                logger.error(f'Send message to unregistered user')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: message_to,
            TIME: time.time(),
            MESSAGE_TEXT: message_text
        }
        logger.debug(f'Message dict created: {message_dict}')

        with database_lock:
            self.database.save_message(self.account_name, message_to, message_text)

        with sock_lock:
            try:
                send_message(self.socket, message_dict)
                logger.info(f'Message sent: {message_to}')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionRefusedError) as err:
                if err.errno:
                    logger.critical('Connection lost')
                    exit(1)
                else:
                    logger.error('Timeout while sending')

    def interactive(self):
        self.user_help()
        while True:
            command = input('Enter command: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.user_help()
            elif command == 'quit':
                with sock_lock:
                    try:
                        send_message(self.socket, self.exit_message())
                    except Exception:
                        pass
                logger.info('Sessions closed by user')
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                    for contact in contacts_list:
                        print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print('Command not available. Enter "help" to see all commands')

    def user_help(self):
        print(f'Commands:\n'
              f'1. message - create and send a message\n'
              f'2. history - Print a history of messages\n'
              f'3. contacts - Contacts list\n'
              f'4. help - Command list\n'
              f'5. quit - Close the connection and exit')

    def print_history(self):
        ask = input('Show messages. in - input messages. out - Output messages. Enter - all messages')
        with database_lock:
            if ask =='in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'Message from {message[0]}({message[3]}): {message[2]}\n')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'Message to {message[1]}({message[3]}): {message[2]}\n')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'Message from {message[0]} to {message[1]}({message[3]}): {message[2]}\n')

    def edit_contacts(self):
        ans = input('Enter del for delete, add for add contact: ')
        if ans == 'del':
            edit = input('Enter contact name for delete: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error(f'Contact is not allowed')
        elif ans == 'add':
            edit = input('Enter contact name for add: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.socket, self.account_name, edit)
                    except ServerError:
                        logger.error('Server unvialable')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.socket = sock
        self.account_name = account_name
        self.database = database
        super().__init__()

    def get_message_from_server(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.socket)
                except IncorrectDataRecievedError:
                    logger.error('Encoding error')
                except (OSError, ConnectionError, ConnectionAbortedError, ConnectionRefusedError, json.JSONDecodeError):
                    logger.critical('Connection lost!')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE \
                    and SENDER in message and DESTINATION in message \
                    and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                        print(f'Message from user: {message[SENDER]},\n{message[MESSAGE_TEXT]}')
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.account_name,
                                                           message[MESSAGE_TEXT],
                                                           )
                            except:
                                logger.error('Database unavailable')
                    else:
                        logger.error(f'Incorrect data received from server: {message}')


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
def process_response_answer(message):
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


def contacts_list_request(sock, name):
    logger.debug(f'Contacts list request for user {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name,
    }

    logger.debug(f'Request is created: {req}')
    send_message(sock, req)
    ans = get_message(sock)
    logger.debug(f'Response: {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    logger.debug(f'Adding contact {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact,
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError(f'Contact creating error')
    print('Successfully created')


def user_list_request(sock, username):
    logger.debug(f'Available users for {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username,
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def remove_contact(sock, username, contact):
    logger.debug(f'Removing contact {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact,
    }
    send_message(sock, req)
    ans = get_message(sock, req)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Delete contact failed')
    print('Successfully deleted')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Available users list request failed')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error(f'Contact list request failed')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    print('Start console client')
    server_address, server_port, client_name = arg_parser()

    if not client_name:
        print('Enter username!')

    logger.info(f'Client has been started. Server: {server_address}. Port: {server_port}. User: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_answer(get_message(transport))
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
        receiver = ClientReader(client_name, transport)
        receiver.daemon = True
        receiver.start()

        user_interface = ClientSender(client_name, transport)
        user_interface.daemon = True
        user_interface.start()
        logger.debug('Successfully started')

        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
