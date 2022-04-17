import argparse

from PyQt5.QtWidgets import QApplication

from client.database import ClientDatabase
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from common.errors import ServerError
from common.utils import *
from common.variables import *

logger = logging.getLogger('client')


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


if __name__ == '__main__':
    server_address, server_port, client_name = arg_parser()

    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    logger.info(f'Client {server_address}:{server_port} has been started by {client_name}')
    database = ClientDatabase(client_name)

    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Chat - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
