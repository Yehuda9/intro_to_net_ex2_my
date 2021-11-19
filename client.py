import os
import socket
import sys
import time
from os.path import getsize

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def send_file(change, src_path, dest_path):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_IP, server_port))
    s.send(bytes(client_ID, "utf-8"))
    s.send(bytes(change, "utf-8"))
    s.send(bytes(src_path, "utf-8"))
    if change == 'modified' or change == 'moved':
        s.send(bytes(dest_path, "utf-8"))
    if change != 'deleted':
        file = open(dest_path, "rb")
        files_bytes = file.read()
        s.send(files_bytes)
        s.send(bytes('fin', "utf-8"))
    data = s.recv(100)
    print("Server sent: ", data)
    s.close()


def open_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_IP, server_port))
    # sock.send(client_ID.encode('utf-8'))
    return sock


def remove_file(path_to_file):
    print('remove_file')
    sock = open_socket()
    print('open socket')
    path_split = path_to_file.split(rel_folder_name)
    path_to_send = rel_folder_name + path_split[1]
    to_send = bytes("delete    " + client_ID + path_to_send + '*', 'utf-8')
    print(to_send)
    sock.send(to_send)


# path- all path. example:C:\Users\Avita\PycharmProjects\intro_to_net_ex2\user\ex1
# rel_folder_name- main folder to backup. example: user
def upload_file(path_to_file):
    sock = open_socket()
    # print("path = ", path_to_file)
    path_split = path_to_file.split(rel_folder_name)
    path_to_send = rel_folder_name + path_split[1]
    # print("p = :", path_to_send)
    to_send = bytes("uploadFile" + client_ID + str(os.path.getsize(path_to_file)) + "*" + path_to_send + "*", 'utf-8')
    print(to_send)
    sock.send(to_send)
    print("open ", path_to_file, end='\n')
    os.makedirs(os.path.dirname(path_to_file), exist_ok=True)
    # f = open(path_to_file, 'rb')
    try:
        f = open(path_to_file, 'rb')
    except IOError:
        sock.close()
        return
    # send the file in pipeline
    while True:
        package = f.read(1024)
        if package == b'':
            break
        sock.send(package)
    sock.close()


def upload_path(path):
    to_send = "action: upload_path" \
              "size_in_bytes: " "" \
              "dirs: " "" \
              "path: " + path + \
              "id: " + client_ID
    leading_zero = 16 - len(str(len(to_send)))
    size = str(len(to_send)).zfill(leading_zero)
    to_send = size + '\n' + to_send
    s.send(bytes(to_send, 'utf-8'))


def get_size_of_dir(path):
    s = 0
    d = 0
    for root, dirs, files in os.walk(path):
        d += len(dirs)
        s += sum(getsize(os.path.join(root, name)) for name in files)
    return s, d


def upload_dir_to_server():
    size_of_files, number_of_dirs = get_size_of_dir(path_to_folder)
    to_send = "action: upload_dir_to_server" \
              "size_in_bytes: " + str(size_of_files) + "" \
                                                       "dirs: " + str(number_of_dirs) + "" \
                                                                                        "path: " + path_to_folder + \
              "id: " + client_ID
    to_send = str(len(to_send)) + '\n' + to_send
    s.send(bytes(to_send, 'utf-8'))
    received_bytes = 0
    for path, dirs, files in os.walk(path_to_folder):
        upload_path(path)
        for file in files:
            path_to_file = os.path.join(path, file)
            upload_file(path_to_file)


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
        upload_file(event.src_path)

    def on_modified(self, event):
        print("Received modified event - %s." % event.src_path)
        remove_file(event.src_path)
        upload_file(event.src_path)

    def on_deleted(self, event):
        print("Received delete event - %s." % event.src_path)
        remove_file(event.src_path)

    def on_moved(self, event):
        print("Received moved event - %s." % event.dest_path)
        print("Received moved event - %s." % event.src_path)
        remove_file(event.src_path)
        upload_file(event.dest_path)

    """@staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            print("Received created event - %s." % event.src_path)
            upload_file(event.src_path)

        elif event.event_type == 'modified' and event.event_type != 'created':
            print("Received modified event - %s." % event.src_path)
            remove_file(event.src_path)
            upload_file(event.src_path)

        elif event.event_type == 'deleted':
            print("Received delete event - %s." % event.src_path)
            remove_file(event.src_path)

        elif event.event_type == 'moved':
            print("Received moved event - %s." % event.dest_path)
            print("Received moved event - %s." % event.src_path)
            remove_file(event.src_path)
            upload_file(event.dest_path)
"""


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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_IP, server_port))
        s.send(b'0000000000000010\nnew client')
        client_ID = s.recv(128).decode("utf-8")
        if not client_ID.isidentifier():
            print('not valid id!!!!!!!!!!!!!!!!')
            print(client_ID)
            pass
        print("new client ID: ", client_ID)
        # s.close()
        upload_dir_to_server()

    # print("problem")
    w = Watcher()
    w.run()
