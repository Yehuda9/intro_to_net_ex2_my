import os
import random
import string
import sys
from socket import socket, AF_INET, SOCK_STREAM

import utils
from utils import *

"""def recv_all(n):
    if n == 0:
        return b''
    data = b''
    while len(data) < n:
        packet = client_socket.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
"""

"""def parse_message(m):
    m = str(m, 'utf-8')
    # print('m: ', m)
    d = {}
    l = m.split('\n')
    for e in l:
        try:
            k, v = e.split(':', 1)
            d[k] = v
        except:
            print('error parsing')
    if not d['action'] == 'new client':
        d['path'] = os.path.join(os.getcwd(), 'DB', d['id'], d['path'])
    print(d)
    return d
"""

"""def remove_dir(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for dir in dirs:
                print('recursive call')
                remove_dir(os.path.join(root, dir))
                # print('1 os.rmdir(' + os.path.join(root, dir) + ')')
                # os.rmdir(os.path.join(root, dir))
            for file in files:
                os.remove(os.path.join(root, file))
            print('2 os.rmdir(' + root + ')')
            os.rmdir(root)
"""

"""def _remove_file(_message_dict):
    if os.path.isdir(_message_dict['path']):
        # pass
        remove_dir(_message_dict['path'])
    else:
        try:
            os.remove(_message_dict['path'])
        except FileNotFoundError:
            pass
"""

"""def _get_path(_message_dict):
    os.makedirs(_message_dict['path'], exist_ok=True)
"""

"""def _get_file(_message_dict):
    os.makedirs(os.path.dirname(_message_dict['path']), exist_ok=True)
    f = open(_message_dict['path'], 'wb')
    # print("size of data: ", int(_message_dict['size_of_data']))
    d = recv_all(int(_message_dict['size_of_data']))
    if int(_message_dict['size_of_data']) != len(d):
        print('read error!!!!!!!!!!!!!!!', int(_message_dict['size_of_data']) - len(d))
    f.write(d)
    # print('len(d): ', len(d))
    f.close()
"""


class Client:
    def __init__(self, id):
        self.__id = id
        self.__requests = []
        self.__computers = set()

    def get_id(self):
        return self.__id

    def get_computers(self):
        return self.__computers

    def add_new_request(self, request):
        self.__requests.append(request)

    def add_new_computer(self, computer):
        self.__computers.add(computer)

    def get_computer_at_i(self, i):
        return self.__computers[i]

    def get_request_at_i(self, i):
        return self.__requests.__getitem__(i)


class Computer:
    def __init__(self, path, ip, index=1):
        self.__ip = ip
        self.__path = path
        self.__index = index

    def get_path(self):
        return self.__path

    def get_index(self):
        return self.__index

    def decrease_index(self, num):
        self.__index += num

    def __eq__(self, other):
        if not isinstance(other, Computer):
            return NotImplemented
        return self.__path == other.get_path() and self.__ip == other.get_path()

    def __hash__(self):
        return hash((self.__ip, self.__path, self.__index))


if __name__ == '__main__':
    path_to_DB = os.path.join("./", "DB/")
    os.makedirs(os.path.dirname(path_to_DB), exist_ok=True)
    my_port = int(sys.argv[1])
    # server = socket(AF_INET, SOCK_STREAM)
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(('', my_port))
    server.listen(5)
    util = utils.Utils('server', None)
    clients = {}
    while True:
        client_socket, client_address = server.accept()
        util.set_socket(client_socket)
        print('accept Connection from: ', client_address)
        length = util.recv_all(16)
        # print(length)
        length = length.decode('utf-8')
        # print(length)
        message = util.recv_all(int(length))
        message_dict = util.parse_message(message)
        num_of_requests = int(message_dict['num_of_requests'])
        for i in range(num_of_requests):
            print(message_dict['action'])
            if 'new client' in message_dict['action']:
                client_id = ''.join(
                    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
                os.mkdir(os.path.join(path_to_DB, client_id))
                util.set_id(client_id)
                client_socket.send(bytes(client_id, 'utf-8'))
                clients[client_id] = Client(client_id)
                clients[client_id].add_new_request(message_dict)
                clients[client_id].add_new_computer(Computer(message_dict['path'], client_address[0]))
            if 'exists client' in message_dict['action']:
                if not message_dict['id'] in clients.keys():
                    raise "client not exists"
                """dir_name = os.walk(os.path.join('.' + os.path.sep + 'DB', message_dict['id']))
                dir_name = dir_name[1]
                dir_name = dir_name[0]"""
                clients[message_dict['id']].add_new_request(message_dict)
                clients[message_dict['id']].add_new_computer(Computer(message_dict['path'], client_address[0]))
                util.set_rel_folder_name(clients[message_dict['id']].get_request_at_i(0)['path'])
                util.upload_dir_to_server(os.path.join('.' + os.path.sep + 'DB', message_dict['id'], clients[message_dict['id']].get_request_at_i(0)['path']))
            if 'upload file' in message_dict['action']:
                util.get_file(message_dict)
            if 'remove file' in message_dict['action']:
                util.remove_file(message_dict)
            elif 'upload path' in message_dict['action']:
                # print('upload path!!!!!!!!!!')
                util.get_path(message_dict)
            # print(i, num_of_requests)
            if i == num_of_requests - 1:
                break
            length = util.recv_all(16)
            # print('len: ', length)
            if not length:
                break
            length = length.decode('utf-8')
            # print(length)
            message = util.recv_all(int(length))
            message_dict = util.parse_message(message)
        util.get_socket().close()
        print('close connection')
