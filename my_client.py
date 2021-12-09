import os
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM

import watchdog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import utils


class PausingObserver(watchdog.observers.Observer):
    def __init__(self, *args):
        Observer.__init__(self, *args)
        self._is_paused = False

    def dispatch_events(self, *args, **kwargs):
        if not getattr(self, '_is_paused', False):
            super(PausingObserver, self).dispatch_events(*args, **kwargs)

    def pause(self):
        pass

    def resume(self):
        time.sleep(self.timeout)  # allow interim events to be queued
        self.event_queue.queue.clear()
        self._is_paused = False

    """@contextlib.contextmanager
    def ignore_events(self):
        self.pause()
        yield
        self.resume()
"""


class Watcher:

    def __init__(self):
        self.event_handler = None
        self.observer = Observer()
        self.__in_req = False

    def requests_updates(self):
        print("start requests_updates")
        self.event_handler.set_in_req(True)
        m = util.generate_message('requests_updates')
        try:
            util.get_socket().send(m)
            handle_req()
        except Exception as e:
            util.set_socket(socket(AF_INET, SOCK_STREAM))
            print('connect requests_updates')
            try:
                util.get_socket().connect((server_IP, server_port))
                util.get_socket().send(m)
                handle_req()
            except:
                pass
            util.get_socket().close()
        self.event_handler.set_in_req(False)
        print("finish requests_updates")

    def run(self):
        self.event_handler = Handler()
        self.observer.schedule(self.event_handler, path_to_folder, recursive=True)
        self.observer.start()
        try:
            i = 0
            while True:
                time.sleep(1)
                i += 1
                if i == 5:
                    i = 0
                    copy = util.get_ignore_wd().copy()
                    for a in copy.keys():
                        if copy[a][1] == 'close' \
                                and copy[a][0] + 3 < time.time():
                            util.get_ignore_wd().pop(a)
                    print(self.event_handler.get_in_event(), self.event_handler.get_in_req())
                    if not self.event_handler.get_in_event() and not self.event_handler.get_in_req():
                        self.requests_updates()
        except KeyboardInterrupt:
            print('stop Watcher line 27')
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.__in_event = False
        self.__in_req = False

    def get_in_req(self):
        return self.__in_req

    def set_in_req(self, b):
        self.__in_req = b

    def set_in_event(self, b):
        self.__in_event = b

    def is_start_with(self, p):
        for key in util.get_ignore_wd().keys():
            if key.startswith(p):
                return True
        return False

    def get_in_event(self):
        return self.__in_event

    def is_open(self, p):
        historical_size = -1
        while historical_size != os.path.getsize(p):
            historical_size = os.path.getsize(p)
            time.sleep(0.05)
        """if os.path.exists(p):
            try:
                os.rename(p, p)
                return False
            except OSError as e:
                return True
        return False"""

    def on_any_event(self, event):
        i = 0
        while self.__in_req:
            i += 1
            print(i)
            continue

    def on_created(self, event):
        self.__in_event = True
        print(util.get_ignore_wd())
        # self.is_open(event.src_path)
        p = event.src_path
        # p = p.replace('\\', '\\\\')
        if not self.is_start_with(p) or (
                p in util.get_ignore_wd().keys() and util.get_ignore_wd()[p][1] == 'close'
                and util.get_ignore_wd()[p][
                    0] + 3 < time.time()):
            util.set_socket(socket(AF_INET, SOCK_STREAM))
            print('connect on_created')
            print("Received created event - %s." % p)
            util.get_socket().connect((server_IP, server_port))
            if os.path.isdir(event.src_path):
                # upload_dir_to_server(server_socket, event.src_path)
                util.upload_path(event.src_path, util.get_size_of_dir(event.src_path)[2])
            else:
                util.upload_file(event.src_path)
            util.get_socket().close()
        self.__in_event = False

    def on_modified(self, event):
        self.__in_event = True
        print(util.get_ignore_wd())
        # self.is_open(event.src_path)
        p = event.src_path
        # p = p.replace('\\', '\\\\')
        if not self.is_start_with(p) or (
                p in util.get_ignore_wd().keys() and util.get_ignore_wd()[p][1] == 'close'
                and util.get_ignore_wd()[p][
                    0] + 3 < time.time()):
            print("Received modified event - %s." % p)
            if not os.path.isdir(event.src_path):
                util.set_socket(socket(AF_INET, SOCK_STREAM))
                print('connect on_modified')
                util.get_socket().connect((server_IP, server_port))
                util.send_remove_file(event.src_path, util.get_size_of_dir(event.src_path)[2] * 2)
                util.upload_file(event.src_path)
                util.get_socket().close()
        self.__in_event = False

    def on_deleted(self, event):
        self.__in_event = True
        print(util.get_ignore_wd())
        p = event.src_path
        # p = p.replace('\\', '\\\\')
        if not self.is_start_with(p) or (
                p in util.get_ignore_wd().keys() and util.get_ignore_wd()[p][1] == 'close'
                and util.get_ignore_wd()[p][
                    0] + 3 < time.time()):
            util.set_socket(socket(AF_INET, SOCK_STREAM))
            print("Received delete event - %s." % p)
            print('connect on_deleted')
            util.get_socket().connect((server_IP, server_port))
            util.send_remove_file(event.src_path, util.get_size_of_dir(event.src_path)[2])
            util.get_socket().close()
        self.__in_event = False

    def on_moved(self, event):
        self.__in_event = True
        util.set_socket(socket(AF_INET, SOCK_STREAM))
        print('connect on_moved')
        util.get_socket().connect((server_IP, server_port))
        print("Received moved event - %s." % event.src_path)
        print("Received moved event - %s." % event.dest_path)
        num_of_requests = util.get_size_of_dir(event.src_path)[2] + 1
        # upload_file(server_socket, event.dest_path, get_size_of_dir(event.src_path)[2])
        util.send_move_file(event.src_path, event.dest_path)
        """if os.path.isdir(event.dest_path):
            util.send_remove_file(event.src_path, num_of_requests)
            # upload_dir_to_server(server_socket, event.dest_path)
            util.upload_path(event.dest_path, util.get_size_of_dir(event.src_path)[2])
        else:
            util.send_remove_file(event.src_path, num_of_requests)
            util.upload_file(event.dest_path)"""
        util.get_socket().close()
        self.__in_event = False


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


def handle_req():
    length = util.recv_all(16)
    if length is not None:
        length = length.decode('utf-8')
        message = util.recv_all(int(length))
        message_dict = util.parse_message(message)
        num_of_requests = int(message_dict['num_of_requests'])
        for i in range(num_of_requests):
            if 'upload file' in message_dict['action']:
                util.get_file(message_dict)
            if 'remove file' == message_dict['action']:
                util.remove_file(message_dict)
            elif 'upload path' in message_dict['action']:
                util.get_path(message_dict)
            if 'move_file' == message_dict['action']:
                util.get_ignore_wd()[message_dict['path']] = (time.time(), 'open')
                util.get_ignore_wd()[message_dict['new_path']] = (time.time(), 'open')
                os.renames(message_dict['path'], message_dict['new_path'])
                util.get_ignore_wd()[message_dict['path']] = (time.time(), 'close')
                util.get_ignore_wd()[message_dict['new_path']] = (time.time(), 'close')

            if i == num_of_requests - 1:
                break
            length = util.recv_all(16)
            if not length:
                break
            length = length.decode('utf-8')
            message = util.recv_all(int(length))
            message_dict = util.parse_message(message)


if __name__ == '__main__':
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    path_to_folder = sys.argv[3]
    rel_folder_name = path_to_folder.split(os.sep)[-1]
    time_between_syncs = sys.argv[4]
    my_id = '0'
    util = utils.Utils('client', socket(AF_INET, SOCK_STREAM), path_to_folder, my_id)
    util.get_socket().connect((server_IP, server_port))
    if len(sys.argv) == 6:
        my_id = sys.argv[5]
        util.set_id(my_id)
        s, d, f = util.get_size_of_dir(path_to_folder)
        util.set_rel_folder_name(path_to_folder)
        message = util.generate_message('exists client', path_to_folder, 0, 0, 1)
        util.get_socket().send(message)
        computer_id = util.get_socket().recv(64).decode('utf-8')
        util.set_client_computer_id(computer_id)
        handle_req()
        util.get_socket().close()
        # create new folder and get all the files from the server.
    else:
        s, d, f = util.get_size_of_dir(path_to_folder)
        # f = num of files and subdirs + new client + rootdir
        message = util.generate_message('new client', path_to_folder, d, s, f + 1)
        util.get_socket().send(message)
        my_id = util.get_socket().recv(128).decode('utf-8')
        util.set_id(my_id)
        computer_id = util.get_socket().recv(64).decode('utf-8')
        util.set_client_computer_id(computer_id)
        # print(my_id)
        util.upload_dir_to_server(path_to_folder)
    util.get_ignore_wd().clear()
    w = Watcher()
    w.run()
