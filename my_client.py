import sys, os
from os.path import getsize
from socket import socket, AF_INET, SOCK_STREAM


def get_size_of_dir(path):
    s = 0
    d = 0
    for root, dirs, files in os.walk(path):
        d += len(dirs)
        s += sum(getsize(os.path.join(root, name)) for name in files)
    return s, d


def generate_message(action, path='', size_of_dirs=0, size_of_data=0, _id=''):
    m = "action: " + action + '\n' + 'id:' + _id + '\n' + 'path:' + path + '\n' + 'size_of_dirs: ' + str(
        size_of_dirs) + '\n' + 'size_of_data: ' + str(size_of_data)
    size = str(len(m)).zfill(16)
    to_send = size + m
    return to_send


def upload_path(path):
    _message = generate_message('upload path', path)
    server_socket.send(bytes(_message, 'utf-8'))


def upload_file(path_to_file):
    _message = generate_message('upload file', path_to_file, 0, getsize(path_to_file), my_id)
    server_socket.send(_message)


def upload_dir_to_server():
    for path, dirs, files in os.walk(path_to_folder):
        for d in dirs:
            path_to_file = os.path.join(path, d)
            upload_path(path_to_file)
        for file in files:
            path_to_file = os.path.join(path, file)
            upload_file(path_to_file)


if __name__ == '__main__':
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    path_to_folder = sys.argv[3]
    rel_folder_name = path_to_folder.split(os.sep)[-1]
    time_between_syncs = sys.argv[4]
    if len(sys.argv) == 6:
        client_ID = sys.argv[5]
        # create new folder and get all the files from the server.
    else:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.connect((server_IP, server_port))
        s, d = get_size_of_dir(path_to_folder)
        message = generate_message('new client', path_to_folder, d, s)
        server_socket.send(bytes(message, 'utf-8'))
        my_id = server_socket.recv(128).decode('utf-8')
        upload_dir_to_server()
