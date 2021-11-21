import os
import random
import string
import sys
from socket import socket, AF_INET, SOCK_STREAM


def recv_all(n):
    if n == 0:
        return b''
    data = b''
    while len(data) < n:
        packet = client_socket.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def parse_message(m):
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


def remove_dir(path):
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


def _remove_file(_message_dict):
    if os.path.isdir(_message_dict['path']):
        # pass
        remove_dir(_message_dict['path'])
    else:
        try:
            os.remove(_message_dict['path'])
        except FileNotFoundError:
            pass


def _get_path(_message_dict):
    os.makedirs(_message_dict['path'], exist_ok=True)


def _get_file(_message_dict):
    os.makedirs(os.path.dirname(_message_dict['path']), exist_ok=True)
    f = open(_message_dict['path'], 'wb')
    # print("size of data: ", int(_message_dict['size_of_data']))
    d = recv_all(int(_message_dict['size_of_data']))
    if int(_message_dict['size_of_data']) != len(d):
        print('read error!!!!!!!!!!!!!!!', int(_message_dict['size_of_data']) - len(d))
    f.write(d)
    # print('len(d): ', len(d))
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
        length = recv_all(16)
        # print(length)
        length = length.decode('utf-8')
        # print(length)
        message = recv_all(int(length))
        message_dict = parse_message(message)
        num_of_requests = int(message_dict['num_of_requests'])
        for i in range(num_of_requests):
            print(message_dict['action'])
            if 'new client' in message_dict['action']:
                client_id = ''.join(
                    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
                os.mkdir(os.path.join(path_to_DB, client_id))
                client_socket.send(bytes(client_id, 'utf-8'))
            if 'upload file' in message_dict['action']:
                _get_file(message_dict)
            if 'remove file' in message_dict['action']:
                _remove_file(message_dict)
            elif 'upload path' in message_dict['action']:
                # print('upload path!!!!!!!!!!')
                _get_path(message_dict)
            # print(i, num_of_requests)
            if i == num_of_requests - 1:
                break
            length = recv_all(16)
            # print('len: ', length)
            if not length:
                break
            length = length.decode('utf-8')
            # print(length)
            message = recv_all(int(length))
            message_dict = parse_message(message)
        client_socket.close()
        print('close connection')
