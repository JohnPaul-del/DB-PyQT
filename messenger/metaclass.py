import dis

class ServerMaker(type):
    def __init__(self, class_name, bases, class_dict):
        methods = []
        attributes = []

        for func in class_dict:
            try:
                ret = dis.get_instructions(class_dict[func])
            except TypeError:
                pass
            else:
                for el in ret:
                    if el.opname == 'LOAD_GLOBAL':
                        if el.argval not in methods:
                            methods.append(el.argval)
                    elif el.opname == 'LOAD_ATTR':
                        if el.argval not in attributes:
                            attributes.append(el.argval)

            if 'connect' in methods:
                raise TypeError('Server does not support connect method')
            super().__init__(class_name, bases, class_dict)


class ClientMaker(type):
    def __init__(self, class_name, bases, class_dict):
        methods = []

        for func in class_dict:
            try:
                ret = dis.get_instructions(class_dict[func])
            except TypeError:
                pass
            else:
                for el in ret:
                    if el.opname == 'LOAD_GLOBAL':
                        if el.argval not in methods:
                            methods.append(el.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('Unknown command')

        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Socket functions are empty')
        super().__init__(class_name, bases, class_dict)
