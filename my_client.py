import sys, os
from os.path import getsize
from socket import socket, AF_INET, SOCK_STREAM
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Watcher:

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, path_to_folder, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):
    def on_created(self, event):
        print("Received created event - %s." % event.src_path)
        # upload_file(event.src_path)

    def on_modified(self, event):
        print("Received modified event - %s." % event.src_path)
        # remove_file(event.src_path)
        # upload_file(event.src_path)

    def on_deleted(self, event):
        print("Received delete event - %s." % event.src_path)
        # remove_file(event.src_path)

    def on_moved(self, event):
        print("Received moved event - %s." % event.dest_path)
        print("Received moved event - %s." % event.src_path)
        # remove_file(event.src_path)
        # upload_file(event.dest_path)


def get_size_of_dir(path):
    s = 0
    d = 0
    f = 0
    for root, dirs, files in os.walk(path):
        d += len(dirs)
        f += len(files) + len(dirs)
        s += sum(getsize(os.path.join(root, name)) for name in files)
    return s, d, f


def generate_message(action, path='', size_of_dirs=0, size_of_data=0, num_of_requests=1):
    if action == 'upload file' or action == 'upload path':
        r_path = path.split(rel_folder_name, 1)[1].lstrip(os.path.sep)
        path = os.path.join(os.getcwd(), r'DB', my_id, rel_folder_name, r_path)
    elif action == 'new client':
        path = rel_folder_name
    m = "action:" + action + '\n' + 'id:' + my_id + '\n' + 'path:' + path + '\n' + 'size_of_dirs:' + str(
        size_of_dirs) + '\n' + 'size_of_data:' + str(size_of_data) + '\n' + 'num_of_requests:' + str(num_of_requests)
    m = bytes(m, 'utf-8')
    size = bytes(str(len(m)).zfill(16), 'utf-8')
    to_send = size + m
    print(to_send)
    return to_send


def upload_path(path):
    _message = generate_message('upload path', path)
    server_socket.send(_message)


def upload_file(path_to_file):
    _message = generate_message('upload file', path_to_file, 0, os.path.getsize(path_to_file))
    print('file size: ', os.path.getsize(path_to_file))
    server_socket.send(_message)
    with open(path_to_file, 'rb') as f:
        b = f.read()
        print('len(b): ',len(b))
        server_socket.send(b)
        """return
        while True:
            b = f.read(1024)
            if b == b'':
                break
            server_socket.send(b)"""


def upload_dir_to_server():
    server_socket.send(generate_message('upload path', rel_folder_name))
    for path, dirs, files in os.walk(path_to_folder):
        for d in dirs:
            path_to_file = os.path.join(path, d)
            print(path_to_file)
            upload_path(path_to_file)
        for file in files:
            path_to_file = os.path.join(path, file)
            print(path_to_file)
            upload_file(path_to_file)


if __name__ == '__main__':
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    path_to_folder = sys.argv[3]
    rel_folder_name = path_to_folder.split(os.sep)[-1]
    time_between_syncs = sys.argv[4]
    my_id = '0'
    if len(sys.argv) == 6:
        my_id = sys.argv[5]
        # create new folder and get all the files from the server.
    else:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.connect((server_IP, server_port))
        s, d, f = get_size_of_dir(path_to_folder)
        # f = num of files and subdirs + new client + rootdir
        message = generate_message('new client', path_to_folder, d, s, f + 2)
        server_socket.send(message)
        my_id = server_socket.recv(128).decode('utf-8')
        print(my_id)
        upload_dir_to_server()
    w = Watcher()
    w.run()
