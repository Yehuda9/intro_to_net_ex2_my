import random
import string
import sys, os
from socket import socket, AF_INET, SOCK_STREAM


def parse_message(m):
    m = str(m, 'utf-8')
    print('m: ', m)
    d = {}
    l = m.split('\n')
    for e in l:
        # print(e)
        try:
            k, v = e.split(':', 1)
            d[k] = v
        except:
            print('error parsing')
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
            t = client_socket.recv(1024)
            print(t)
            print('except')

        _message = client_socket.recv(_length)
        _message_dict = parse_message(_message)
        if 'upload file' in _message_dict['action']:
            _get_file(_message_dict)
            size_received += int(_message_dict['size_of_data'])
        elif 'upload path' in _message_dict['action']:
            get_path(_message_dict)
        print("size_received: ", size_received)


def _get_path(_message_dict):
    os.makedirs(os.path.join(os.getcwd(), 'DB', _message_dict['id'], _message_dict['path']), exist_ok=True)
    # os.mkdirs(os.path.join(path_to_DB, _message_dict['id'], _message_dict['path']))


def _get_file(_message_dict):
    f = open(_message_dict['path'], 'wb')
    """size_of_data = int(_message_dict['size_of_data'])
    bytes_recd = 0
    while bytes_recd < size_of_data:
        chunk = client_socket.recv(min(size_of_data - bytes_recd, 2048))
        if chunk == b'':
            break
        f.write(chunk)
        bytes_recd += len(chunk)
        print('recv ', bytes_recd, ' from socket')"""
    print("size of data: ", int(_message_dict['size_of_data']))
    d = client_socket.recv(int(_message_dict['size_of_data']))
    if int(_message_dict['size_of_data']) != len(d):
        print('read error!!!!!!!!!!!!!!!', int(_message_dict['size_of_data']) - len(d))
    f.write(d)
    print('len(d): ', len(d))
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
        num_of_requests = int(message_dict['num_of_requests'])
        for i in range(num_of_requests):
            print(message_dict['action'])
            if 'new client' in message_dict['action']:
                # if message_dict['action'].contains('new client'):
                client_id = ''.join(
                    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
                os.mkdir(os.path.join(path_to_DB, client_id))
                client_socket.send(bytes(client_id, 'utf-8'))
                # get_path(message_dict)
                if message_dict['path'] != '':
                    pass
                    # message_dict['id'] = client_id
                    # get_path(message_dict)
                    # get_dir_from_client(message_dict, int(message_dict['size_of_data']))
            if 'upload file' in message_dict['action']:
                _get_file(message_dict)
            elif 'upload path' in message_dict['action']:
                print('upload path!!!!!!!!!!')
                _get_path(message_dict)
            if i == num_of_requests - 1:
                break
            length = client_socket.recv(16)
            print('len: ', length)
            length = length.decode('utf-8')
            """if not length:
                break"""
            print(length)
            message = client_socket.recv(int(length))
            message_dict = parse_message(message)
        client_socket.close()
        # print(message_dict)
