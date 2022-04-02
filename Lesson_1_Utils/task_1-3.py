from ipaddress import ip_address
from subprocess import call
import platform
from tabulate import tabulate


def check_host(list_ip):
    """
    1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
    Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста
    или ip-адресом.
    В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего
    сообщения («Узел доступен», «Узел недоступен»).
    При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
    :param list_ip: List with IP addresses.
    :return: IP avialibility
    """
    result = {
        'Avialable': '',
        'Not Avialable': '',
    }

    for ip_addr in list_ip:
        params = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', params, '1', str(ip_addr)]
        response = call(command)
        if response:
            result['Not Avialable'] += f'{ip_addr}\n'
        else:
            result['Avialable'] += f'{ip_addr}\n'
    return result


def check_range_host(ip_range):

    """
    2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
    Меняться должен только последний октет каждого адреса. По результатам проверки должно выводиться
    соответствующее сообщение.
    :param ip_range:
    :return:
    """
    begining_ip, last_el = tuple(ip_range.split('-'))
    address_bytes = [int(el) for el in begining_ip.split('.')]
    ip_end = (
        address_bytes[0] * (256 ** 3) +
        address_bytes[1] * (256 ** 2) +
        address_bytes[2] * (256 ** 1) +
        int(last_el)
    )
    begining_ip = int(ip_address(begining_ip))
    ip_list = [ip_address(el_ip) for el_ip in range(begining_ip, ip_end + 1)]

    return check_host(ip_list)



def host_range_ping_tab():
    """
    3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
    Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
    (использовать модуль tabulate). Таблица должна состоять из двух колонок и выглядеть примерно так:
    Reachable
    10.0.0.1
    10.0.0.2
    Unreachable
    10.0.0.3
    :return:
    """
    host_list = [
        'ya.ru',
        'vk.com',
        '87.250.250.242',
        '93.186.225.208',
        '192.168.0.1'
    ]
    result = check_host(host_list)
    print(tabulate([result], headers='keys', tablefmt='pipe', stralign='center'))


rnge = '191.168.0.1-4'
result = check_range_host(rnge)
print(tabulate([result], headers='keys', tablefmt='pipe', stralign='center'))

host_range_ping_tab()
