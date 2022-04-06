from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker

from common.variables import *
import datetime


class ServerStorage:
    class AllUsers:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    class ActiveUser:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    def __init__(self):
        self.database_engine = create_engine(SERVER_DATABASE,
                                             echo=False,
                                             pool_recycle=7200,
                                             )
        self.metadata = MetaData()
        user_table = Table('Users',
                           self.metadata,
                           Column('id', Integer, primary_key=True),
                           Column('name', String, unique=True),
                           Column('last_login', DateTime),
                           )

        active_users_table = Table('ActiveUsers',
                                   self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('last_login', DateTime),
                                   )

        user_login_history = Table('UserLoginHistory',
                                   self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.name')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String),
                                   )

        self.metadata.create_all(self.database_engine)

        mapper(self.AllUsers, user_table)
        mapper(self.ActiveUser, active_users_table)
        mapper(self.LoginHistory, user_login_history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        _result = self.session.query(self.AllUsers).filter_by(name=username)

        if _result.count():
            user = _result.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUser(user.id,
                                          ip_address,
                                          port,
                                          datetime.datetime.now(),
                                          )
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id,
                                    datetime.datetime.now(),
                                    ip_address,
                                    port,
                                    )
        self.session.add(history)
        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUser).filter_by(name=user.id).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(self.AllUsers.name,
                                   self.AllUsers.last_login,
                                   )
        return query.all()

    def active_users_list(self):
        query = self.session.query(self.AllUsers.name,
                                   self.ActiveUser.ip_address,
                                   self.ActiveUser.port,
                                   self.ActiveUser.login_time,
                                   ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port,
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()


if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('cl_1', '4.4.4.4', 4444)
    test_db.user_login('cl_2', '4.4.4.3', 4443)

    print(test_db.active_users_list())

    test_db.user_logout('cl_1')

    print(test_db.active_users_list())

    test_db.login_history('cl_1')

    print(test_db.users_list())
