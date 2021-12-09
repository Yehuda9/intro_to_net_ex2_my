import os
import time


class Utils:
    def __init__(self, connection, s, rel_folder_name='', id='0', comp_id='0'):
        """
        Util's constructor
        :param connection: server or client
        :param s: socket
        :param rel_folder_name: name of relative folder name
        :param id: client id
        :param comp_id: computer id
        """
        self.__client_computer_id = comp_id
        self.__connection = connection
        self.__socket = s
        self.__rel_folder_name = rel_folder_name
        self.__id = id
        self.__ignore_wd = {}

    def get_ignore_wd(self):
        return self.__ignore_wd

    def get_connection(self):
        return self.__connection

    def set_client_computer_id(self, comp_id):
        self.__client_computer_id = comp_id

    def get_client_computer_id(self):
        return self.__client_computer_id

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

    def set_rel_folder_name(self, rel_folder_name):
        self.__rel_folder_name = rel_folder_name

    def recv_all(self, n):
        """
        :param n: number of bytes to receive
        :return: n bytes received from socket
        """
        data = b''
        if n == 0:
            return data
        while len(data) < n:
            packet = self.get_socket().recv(n - len(data))
            if not packet or packet == b'':
                break
            data += packet
        return data

    def parse_message(self, m):
        """
        parse message to dict
        :param m: message from socket in bytes, 'key1:value1\n...\nkey1:value1'
        :return: dict of message
        """
        m = str(m, 'utf-8')
        d = {}
        l = m.split('\n')
        for e in l:
            try:
                k, v = e.split(':', 1)
                d[k] = v
            except Exception:
                pass

        if self.is_client():
            # if client parse message, add relative folder name to received path
            d['path'] = os.path.join(self.__rel_folder_name, d['path'])
            d['new_path'] = os.path.join(self.__rel_folder_name, d['new_path'])
        elif not d['action'] == 'new client':
            # if server parse message, add cwd and client id to received path
            d['path'] = os.path.join(os.getcwd(), 'DB', d['id'], d['path'])
            d['new_path'] = os.path.join(os.getcwd(), 'DB', d['id'], d['new_path'])
        print(d)
        return d

    def remove_dir(self, path):
        """
        remove directory recursively
        :param path: path to directory we need to remove
        """
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for dir in dirs:
                    # recursive call for each directory
                    self.remove_dir(os.path.join(root, dir))
                for file in files:
                    p = os.path.join(root, file)
                    self.update_ignore_wd(p, 'open')
                    # remove file
                    os.remove(p)
                    self.update_ignore_wd(p, 'close')
                self.update_ignore_wd(root, 'open')
                # remove empty dir
                os.rmdir(root)
                self.update_ignore_wd(root, 'close')

    def update_ignore_wd(self, p, c_o):
        """
        save path, path status and current time
        :param p: path to ignore event
        :param c_o: close or open
        """
        if self.is_client():
            self.__ignore_wd[p] = (time.time(), c_o)

    def remove_file(self, _message_dict):
        """
        remove file or directory
        :param _message_dict: message_dict
        """
        if os.path.isdir(_message_dict['path']):
            # if path is directory remove directory
            self.remove_dir(_message_dict['path'])
        else:
            # remove file
            self.update_ignore_wd(_message_dict['path'], 'open')
            try:
                os.remove(_message_dict['path'])
            except FileNotFoundError:
                pass
            finally:
                self.update_ignore_wd(_message_dict['path'], 'close')

    def make_path(self, _message_dict):
        """
        :param _message_dict: message_dict
        """
        self.update_ignore_wd(_message_dict['path'], 'open')
        os.makedirs(_message_dict['path'], exist_ok=True)
        self.update_ignore_wd(_message_dict['path'], 'close')

    def get_file(self, _message_dict):
        """
        create file we received
        :param _message_dict: message_dict
        """
        # receive file from socket
        d = self.recv_all(int(_message_dict['size_of_data']))
        self.update_ignore_wd(_message_dict['path'], 'open')
        # make root dir for file
        os.makedirs(os.path.dirname(_message_dict['path']), exist_ok=True)
        f = None
        try:
            f = open(_message_dict['path'], 'wb')
        except Exception:
            self.update_ignore_wd(_message_dict['path'], 'close')
            return
        # write the file:
        try:
            f.write(d)
        except Exception:
            f.write(b'')
        f.close()
        self.update_ignore_wd(_message_dict['path'], 'close')

    def get_size_of_dir(self, path):
        """
        :param path:path to the dor we want to check
        :return: number of all files and directories in path, recursively
        """
        f = 0
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                f += len(files) + len(dirs)
            if f > 0:
                return f
        return 1

    def generate_message(self, action, path='', size_of_data=0, num_of_requests=1, new_path=''):
        """
        generate all messages we need to send according to our protocol
        :param action: the action we need to do
        :param path: the path to the file/directory we need to update
        :param size_of_data: size of the file/directory we want to send
        :param num_of_requests: number of actions we will send
        :param new_path: new path (relevant to "move file" action)
        :return: the message we want to send
        """
        # change the path to match the receiver's folder
        if action == 'upload file' or action == 'upload path' or action == 'remove file' or action == 'move file':
            d_path = new_path
            try:
                r_path = path.split(self.__rel_folder_name, 1)[1].lstrip(os.path.sep)
            except:
                r_path = path.split(self.__id, 1)[1].lstrip(os.path.sep)
            try:
                d_path = new_path.split(self.__rel_folder_name, 1)[1].lstrip(os.path.sep)
            except Exception:
                try:
                    d_path = new_path.split(self.__id, 1)[1].lstrip(os.path.sep)
                except Exception:
                    pass
            path = r_path
            new_path = d_path
        # combine all information to one message
        m = "action:" + action + '\n' + 'id:' + self.__id + '\n' + 'path:' + path + '\n' + 'size_of_data:' + str(
            size_of_data) + '\n' + 'num_of_requests:' + str(
            num_of_requests) + '\n' + 'computer_id:' + self.__client_computer_id + '\n' + 'new_path:' + new_path
        # change message to bytes, check the length and return it together
        m = bytes(m, 'utf-8')
        size = bytes(str(len(m)).zfill(16), 'utf-8')
        to_send = size + m
        print(to_send)
        return to_send

    def send_move_file(self, path, new_path, num_of_requests=1):
        """
        sends the source and destination path of a file that moved
        :param path: the old path
        :param new_path: the path we need to move the file to
        :param num_of_requests: number of actions we will send
        """
        _message = self.generate_message('move file', path, 0, num_of_requests, new_path)
        self.get_socket().send(_message)

    def send_remove_file(self, path, num_of_requests=1):
        """
        send the path of the file we want to remove
        :param path: the file we need to remove
        :param num_of_requests: number of actions we will send
        """
        _message = self.generate_message('remove file', path, 0, num_of_requests)
        self.get_socket().send(_message)

    def upload_path(self, path, num_of_requests=1):
        """
        sends path
        :param path: the path to send
        :param num_of_requests: number of actions we will send
        """
        _message = self.generate_message('upload path', path, 0, num_of_requests)
        self.get_socket().send(_message)

    def upload_file(self, path_to_file, num_of_requests=1):
        """
        sends file
        :param path_to_file: path to the file we want to send
        :param num_of_requests: number of changes to send
        """
        try:
            size = os.path.getsize(path_to_file)
        except FileNotFoundError:
            size = 0
        _message = self.generate_message('upload file', path_to_file, size, num_of_requests)
        # sends the file's information
        self.get_socket().send(_message)
        # sends the file
        f = None
        try:
            f = open(path_to_file, 'rb')
            b = f.read()
            if b != b'':
                self.get_socket().send(b)
            f.close()
        except IOError as e:
            pass
        finally:
            try:
                f.close()
            except:
                pass

    def send_dir(self, path):
        """
        sends all directory
        :param path: the directory path
        """
        # size of dir to upload
        n = self.get_size_of_dir(path)
        for path, dirs, files in os.walk(path):
            # iterating threw all directories
            for d in dirs:
                path_to_file = os.path.join(path, d)
                # send the directory
                self.upload_path(path_to_file, n)
                n -= 1
            # iterating threw all files
            for file in files:
                path_to_file = os.path.join(path, file)
                # send the file
                self.upload_file(path_to_file, n)
                n -= 1
