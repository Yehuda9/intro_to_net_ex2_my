import os
import sys
import time
from os.path import getsize
from socket import socket, AF_INET, SOCK_STREAM

import utils
import watchdog
from utils import Utils
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class Watcher:

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, path_to_folder, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print('stop')
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    def on_created(self, event):
        util.set_socket(socket(AF_INET, SOCK_STREAM))
        util.get_socket().connect((server_IP, server_port))
        print("Received created event - %s." % event.src_path)
        if os.path.isdir(event.src_path):
            # upload_dir_to_server(server_socket, event.src_path)
            util.upload_path(event.src_path, util.get_size_of_dir(event.src_path)[2])
        else:
            util.upload_file(event.src_path)
        util.get_socket().close()

    def on_modified(self, event):
        print("Received modified event - %s." % event.src_path)
        if not os.path.isdir(event.src_path):
            util.set_socket(socket(AF_INET, SOCK_STREAM))
            util.get_socket().connect((server_IP, server_port))
            util.send_remove_file(event.src_path, util.get_size_of_dir(event.src_path)[2] * 2)
            util.upload_file(event.src_path)
            util.get_socket().close()

    def on_deleted(self, event):
        util.set_socket(socket(AF_INET, SOCK_STREAM))
        util.get_socket().connect((server_IP, server_port))
        print("Received delete event - %s." % event.src_path)
        util.send_remove_file(event.src_path, util.get_size_of_dir(event.src_path)[2])
        util.get_socket().close()

    def on_moved(self, event):
        util.set_socket(socket(AF_INET, SOCK_STREAM))
        util.get_socket().connect((server_IP, server_port))
        print("Received moved event - %s." % event.src_path)
        print("Received moved event - %s." % event.dest_path)
        num_of_requests = util.get_size_of_dir(event.src_path)[2]
        # upload_file(server_socket, event.dest_path, get_size_of_dir(event.src_path)[2])
        if os.path.isdir(event.dest_path):
            util.send_remove_file(event.src_path, num_of_requests)
            # upload_dir_to_server(server_socket, event.dest_path)
            util.upload_path(event.dest_path, util.get_size_of_dir(event.src_path)[2])
        else:
            util.send_remove_file(event.src_path, num_of_requests * 2)
            util.upload_file(event.dest_path)
        util.get_socket().close()


"""
def get_size_of_dir(path):
    s = 0
    d = 0
    f = 0
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            d += len(dirs)
            f += len(files) + len(dirs)
            s += sum(getsize(os.path.join(root, name)) for name in files)
        return s, d, f
    return 0, 0, 1

"""
"""def generate_message(action, path='', size_of_dirs=0, size_of_data=0, num_of_requests=1):
    if action == 'upload file' or action == 'upload path' or action == 'remove file':
        r_path = path.split(rel_folder_name, 1)[1].lstrip(os.path.sep)
        path = os.path.join(rel_folder_name, r_path)
    elif action == 'new client':
        path = os.path.split(path)[-1]
        # path = rel_folder_name
    m = "action:" + action + '\n' + 'id:' + my_id + '\n' + 'path:' + path + '\n' + 'size_of_dirs:' + str(
        size_of_dirs) + '\n' + 'size_of_data:' + str(size_of_data) + '\n' + 'num_of_requests:' + str(num_of_requests)
    m = bytes(m, 'utf-8')
    size = bytes(str(len(m)).zfill(16), 'utf-8')
    to_send = size + m
    print(to_send)
    return to_send


def remove_file(server_socket, path, num_of_requests=1):
    _message = generate_message('remove file', path, 0, 0, num_of_requests)
    server_socket.send(_message)


def upload_path(server_socket, path, num_of_requests=1):
    _message = generate_message('upload path', path, 0, 0, num_of_requests)
    server_socket.send(_message)


def upload_file(server_socket, path_to_file, num_of_requests=1):
    _message = generate_message('upload file', path_to_file, 0, os.path.getsize(path_to_file), num_of_requests)
    # print('file size: ', os.path.getsize(path_to_file))
    server_socket.send(_message)
    with open(path_to_file, 'rb') as f:
        b = f.read()
        if b != b'':
            # print('len(b): ', len(b))
            server_socket.send(b)

"""
"""def upload_dir_to_server(server_socket, path):
    server_socket.send(generate_message('upload path', path, 0, 0, get_size_of_dir(path)[2] + 1))
    for path, dirs, files in os.walk(path):
        for d in dirs:
            path_to_file = os.path.join(path, d)
            # print(path_to_file)
            upload_path(server_socket, path_to_file)
        for file in files:
            path_to_file = os.path.join(path, file)
            # print(path_to_file)
            upload_file(server_socket, path_to_file)

"""
if __name__ == '__main__':
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    path_to_folder = sys.argv[3]
    rel_folder_name = path_to_folder.split(os.sep)[-1]
    time_between_syncs = sys.argv[4]
    my_id = '0'
    util = utils.Utils('client', socket(AF_INET, SOCK_STREAM), rel_folder_name, my_id)
    util.get_socket().connect((server_IP, server_port))
    if len(sys.argv) == 6:
        my_id = sys.argv[5]
        util.set_id(my_id)
        # create new folder and get all the files from the server.
    else:
        s, d, f = util.get_size_of_dir(path_to_folder)
        # f = num of files and subdirs + new client + rootdir
        message = util.generate_message('new client', path_to_folder, d, s, f + 2)
        util.get_socket().send(message)
        my_id = util.get_socket().recv(128).decode('utf-8')
        util.set_id(my_id)
        # print(my_id)
        util.upload_dir_to_server(path_to_folder)
    w = Watcher()
    w.run()
