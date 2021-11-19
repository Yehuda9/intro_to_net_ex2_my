import random
import string
import sys, os
from socket import socket, AF_INET, SOCK_STREAM


def parse_message(m):
    m = str(m, 'utf-8')
    d = {}
    l = m.split('\n')
    for e in l:
        # print(e)
        try:
            k, v = e.split(':', 1)
            d[k] = v
        except:
            pass
    print(d)
    return d


def get_dir_from_client(_dict, size):
    size_received = 0
    while size_received < size:
        _length = client_socket.recv(16)
        print(_length)
        _length = _length.decode('utf-8')
        print(_length)
        _length = _length.lstrip('0').rstrip('\n')
        """numeric_filter = filter(str.isdigit, _length)
        _length = "".join(numeric_filter)"""
        print(_length)
        try:
            _length = int(_length)
        except BaseException:
            print('except')

        _message = client_socket.recv(_length)
        _message_dict = parse_message(_message)
        if 'upload file' in _message_dict['action']:
            get_file(_message_dict)
            size_received += int(_message_dict['size_of_data'])
        elif 'upload path' in _message_dict['action']:
            get_path(_message_dict)
        print("size_received: ",size_received)


def get_path(_message_dict):
    os.makedirs(os.path.join(os.getcwd(), 'DB', _message_dict['id'], _message_dict['path']), exist_ok=True)
    # os.mkdirs(os.path.join(path_to_DB, _message_dict['id'], _message_dict['path']))


def get_file(_message_dict):
    f = open(_message_dict['path'], 'wb')
    d = client_socket.recv(int(_message_dict['size_of_data']))
    f.write(d)
    f.close()


if __name__ == '__main__':
    path_to_DB = os.path.join("./", "DB/")
    os.makedirs(os.path.dirname(path_to_DB), exist_ok=True)
    my_port = int(sys.argv[1])
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(('', my_port))
    server.listen(5)
    while True:
        client_socket, client_address = server.accept()
        print('accept Connection from: ', client_address)
        length = client_socket.recv(16).decode('utf-8')
        print(length)
        message = client_socket.recv(int(length))
        message_dict = parse_message(message)
        if 'new client' in message_dict['action']:
            # if message_dict['action'].contains('new client'):
            client_id = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
            os.mkdir(os.path.join(path_to_DB, client_id))
            client_socket.send(bytes(client_id, 'utf-8'))
            # get_path(message_dict)
            if message_dict['path'] != '':
                get_dir_from_client(message_dict, int(message_dict['size_of_data']))
        # print(message_dict)
