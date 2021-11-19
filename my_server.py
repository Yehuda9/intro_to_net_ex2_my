import random
import string
import sys, os
from socket import socket, AF_INET, SOCK_STREAM


def parse_message(m):
    m = str(m, 'utf-8')
    d = {}
    l = m.split('\n')
    for e in l:
        k, v = e.split(':')
        d[k] = v
    return d


def get_dir_from_client():
    pass


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
        message = client_socket.recv(int(length))
        message_dict = parse_message(message)
        if message_dict['action'] == 'new client':
            client_id = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
            os.mkdir(os.path.join(path_to_DB, client_id))
            client_socket.send(bytes(client_id, 'utf-8'))
            if message_dict['path']:
                get_dir_from_client()
        print(message_dict)
