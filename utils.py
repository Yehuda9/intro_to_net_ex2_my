import os
import sys
import time
from os.path import getsize
from socket import socket, AF_INET, SOCK_STREAM

import watchdog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer



class Utils:

    def __init__(self, connection, s, rel_folder_name='', id='0'):
        self.__connection = connection
        self.__socket = s
        self.__rel_folder_name = rel_folder_name
        self.__id = id

    def is_client(self):
        if self.__connection == 'client':
            return True
        return False

    def get_socket(self):
        return self.__socket

    def set_socket(self, s):
        self.__socket = s

    def set_id(self, id):
        self.__id = id

    def recv_all(self, n):
        if n == 0:
            return b''
        data = b''
        while len(data) < n:
            packet = self.get_socket().recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def parse_message(self, m):
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

    def remove_dir(self, path):
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for dir in dirs:
                    print('recursive call')
                    self.remove_dir(os.path.join(root, dir))
                    # print('1 os.rmdir(' + os.path.join(root, dir) + ')')
                    # os.rmdir(os.path.join(root, dir))
                for file in files:
                    os.remove(os.path.join(root, file))
                print('2 os.rmdir(' + root + ')')
                os.rmdir(root)

    def remove_file(self, _message_dict):
        if os.path.isdir(_message_dict['path']):
            # pass
            self.remove_dir(_message_dict['path'])
        else:
            try:
                os.remove(_message_dict['path'])
            except FileNotFoundError:
                pass

    def get_path(self, _message_dict):
        os.makedirs(_message_dict['path'], exist_ok=True)

    def get_file(self, _message_dict):
        os.makedirs(os.path.dirname(_message_dict['path']), exist_ok=True)
        f = open(_message_dict['path'], 'wb')
        # print("size of data: ", int(_message_dict['size_of_data']))
        d = self.recv_all(int(_message_dict['size_of_data']))
        if int(_message_dict['size_of_data']) != len(d):
            print('read error!!!!!!!!!!!!!!!', int(_message_dict['size_of_data']) - len(d))
        f.write(d)
        # print('len(d): ', len(d))
        f.close()

    def get_size_of_dir(self, path):
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

    def generate_message(self, action, path='', size_of_dirs=0, size_of_data=0, num_of_requests=1):
        if action == 'upload file' or action == 'upload path' or action == 'remove file':
            r_path = path.split(self.__rel_folder_name, 1)[1].lstrip(os.path.sep)
            path = os.path.join(self.__rel_folder_name, r_path)
        elif action == 'new client':
            path = os.path.split(path)[-1]
            # path = rel_folder_name
        m = "action:" + action + '\n' + 'id:' + self.__id + '\n' + 'path:' + path + '\n' + 'size_of_dirs:' + str(
            size_of_dirs) + '\n' + 'size_of_data:' + str(size_of_data) + '\n' + 'num_of_requests:' + str(
            num_of_requests)
        m = bytes(m, 'utf-8')
        size = bytes(str(len(m)).zfill(16), 'utf-8')
        to_send = size + m
        print(to_send)
        return to_send

    def send_remove_file(self, path, num_of_requests=1):
        _message = self.generate_message('remove file', path, 0, 0, num_of_requests)
        self.get_socket().send(_message)


    def upload_path(self, path, num_of_requests=1):
        _message = self.generate_message('upload path', path, 0, 0, num_of_requests)
        self.get_socket().send(_message)

    def upload_file(self, path_to_file, num_of_requests=1):
        _message = self.generate_message('upload file', path_to_file, 0, os.path.getsize(path_to_file), num_of_requests)
        # print('file size: ', os.path.getsize(path_to_file))
        self.get_socket().send(_message)
        with open(path_to_file, 'rb') as f:
            b = f.read()
            if b != b'':
                # print('len(b): ', len(b))
                self.get_socket().send(b)

    def upload_dir_to_server(self, path):
        self.get_socket().send(self.generate_message('upload path', path, 0, 0, self.get_size_of_dir(path)[2] + 1))
        for path, dirs, files in os.walk(path):
            for d in dirs:
                path_to_file = os.path.join(path, d)
                # print(path_to_file)
                self.upload_path(path_to_file)
            for file in files:
                path_to_file = os.path.join(path, file)
                # print(path_to_file)
                self.upload_file(path_to_file)
