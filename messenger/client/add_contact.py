import sys
import logging

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger('client')


class AddContactDialog(QDialog):
    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.setFixedSize(350, 120)
        self.SetWindowTitle('Chosen contacts to add')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Chosen contacts to add', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.button_refresh = QPushButton('Refresh contacts list', self)
        self.button_refresh.setFixedSize(100, 30)
        self.button_refresh.move(60, 60)

        self.button_ok = QPushButton('Add contact', self)
        self.button_ok.setFixedSize(100, 30)
        self.button_ok.move(230, 20)

        self.button_cancel = QPushButton('Cancel', self)
        self.button_cancel.setFixedSize(100, 30)
        self.button_cancel.move(230, 60)
        self.button_cancel.clicked.connect(self.close)

        self.possible_contact_update()
        self.button_refresh.clicked.connect(self.update_possible_contacts)

    def possible_contact_update(self):
        self.selector.clear()
        contact_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())

        users_list.remove(self.transport.username)

        self.selector.addItems(users_list - contact_list)

    def update_possible_contacts(self):
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Users list has been updated successfully')
            self.possible_contact_update()
