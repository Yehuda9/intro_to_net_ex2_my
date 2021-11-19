import socket
import sys
import os
import watchdog
import random
import string


# create(path,file): write file to path.
# modified(old_path,new_path,file): delete old path on server then like create.
# delete(path): delete path.
def create(id):
    print(id)
    file_path = client_socket.recv(1024)
    path = path_to_DB + id + "/" + file_path.decode('utf-8')
    print(path)
    file = open(path, 'wb')
    while True:
        file_data = client_socket.recv(1024)
        if file_data == 'fin':
            break
        file.write(file_data)


def sign_new_client():
    d = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
    os.mkdir(path_to_DB + d)
    send(bytes(d, 'utf-8'))
    # To-Do: func to sync whole new folder from client to server.


def send(d):
    # print("sent: ", d)
    client_socket.send(d)
    # client_socket.close()
    # receive()


def update_usr_dir(id, data):
    """
    except one of: create, modify, delete.
    :param id: user id
    :return: None
    """
    action = client_socket.recv(1024)
    action = action.decode('utf-8')
    if action == 'created':
        create(id)
    elif action == 'modified':
        pass
    elif action == 'deleted':
        pass


def upload_file():
    clt_id = client_socket.recv(128).decode('utf-8')
    print(clt_id, end=' ')
    t = b''
    received = b'0'
    while True:
        d = client_socket.recv(1024)
        print(d, end=' ')
        # print(d.decode('utf-8'))
        if d.__contains__(b'*'):
            file_size, rest = d.split(b'*', 1)
            file_size = int(received) + int(file_size)
            break
        received += d
    if rest.__contains__(b'*'):
        path, rest = rest.split(b'*', 1)
        # file_size -= len(rest)
    else:
        received = rest
        while True:
            d = client_socket.recv(1024)
            print(d, end=' ')
            if d.__contains__(b'*'):
                path, rest = d.split(b'*', 1)
                path = received + path
                break
            received += d
    file_header = rest
    file_size -= len(file_header)
    path = os.path.join('.' + os.sep, 'DB', clt_id, path.decode('utf-8'))
    print('')
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        f = open(path, 'wb')
    except IOError:
        return
        # with open(path, 'wb') as f:
    f.write(file_header)
    # print(file_header.decode('utf-8'))
    while True:
        b = client_socket.recv(1024)
        if b == b'':
            break
        # print("got pack from client")
        f.write(b)
        # print("write pack to file")
        # print(b.decode('utf-8'))


def delete_file():
    print('delete_file')
    _id = client_socket.recv(128).decode('utf-8')
    b = client_socket.recv(1024).decode('utf-8')
    # b = b.lstrip('*')
    print(b)
    b, rest = b.split('*', 1)
    print(bytes(b, 'utf-8'))
    print(rest)
    path = os.path.join('.' + os.sep, 'DB', _id, b)
    print('delete: ', path)
    try:
        os.remove(path)
    except IOError:
        pass


def get_dir_from_client():
    a = client_socket.recv(10)
    if a != b'uploadPath':
        return
    a = client_socket.recv(128)
    received = b'0'

    while True:
        d = client_socket.recv(1024)
        if d.__contains__(b'*'):
            path, rest = d.split(b'*', 1)
            break
        received += d
    if rest.__contains__(b'*'):
        pass


# server run #
path_to_DB = os.path.join("./", "DB/")
os.makedirs(os.path.dirname(path_to_DB), exist_ok=True)
# os.mkdir(path_to_DB)

my_port = int(sys.argv[1])
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', my_port))
server.listen(5)



while True:
    client_socket, client_address = server.accept()
    print('accept Connection from: ', client_address)
    data = client_socket.recv(16).decode('utf-8')
    data = int(data)
    data = client_socket.recv(data)
    print(str(data, 'utf-8'))
    parse_message(data)
    if data == b'new client':
        client_id = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
        os.mkdir(os.path.join(path_to_DB, client_id))
        send(bytes(client_id, 'utf-8'))
        get_dir_from_client()
    elif data == b'uploadFile':
        upload_file()
    elif data == b'delete    ':
        delete_file()
    print("close connection")
    client_socket.close()
