import random
import string
import sys
from socket import socket, AF_INET, SOCK_STREAM

from utils import *


class Client:
    def __init__(self, c_id):
        """
        :param c_id: id of client
        """
        self.__id = c_id
        self.__computers = {}

    def get_id(self):
        return self.__id

    def get_computers(self):
        return self.__computers

    def add_new_computer(self, comp):
        """
        adds new computer to the computers array that the server saves
        :param comp: the instance of the computer
        """
        self.__computers[comp.get_id()] = comp

    def get_computer_by_id(self, comp_id):
        return self.__computers[comp_id]

    def add_request(self, comp_id, req):
        """
        add request to all computer's request array accept computer id
        :param comp_id: computer id
        :param req: request as dict
        """
        for comp in self.__computers.values():
            if comp.get_id() != comp_id:
                comp.add_new_request(req)


class Computer:
    def __init__(self, c_id):
        """
        :param c_id: computer id
        """
        self.__id = c_id
        self.__requests = []

    def get_id(self):
        return self.__id

    def get_requests(self):
        """
        return all request that the computer need to update
        :return: request array
        """
        return self.__requests

    def add_new_request(self, req):
        self.__requests.append(req)

    def clear_requests(self):
        if len(self.__requests) > 0:
            self.__requests.clear()

    def __eq__(self, other):
        if not isinstance(other, Computer):
            return NotImplemented
        return self.__id == other.get_id()

    def __hash__(self):
        return hash(self.__id)


def generate_comp(d):
    """
    generate id for computer, send it to client and save computer in the server
    :param d: client id
    """
    # generate id for client computer
    comp_id = ''.join(
        random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(64))
    # sends to the client new computer id
    try:
        client_socket.send(bytes(comp_id, 'utf-8'))
    except Exception:
        pass
    com = Computer(comp_id)
    # add new client's computer to client value in clients dict
    clients[d].add_new_computer(com)


def send_changes(message_dict):
    """
    send all changes in the computers list to the client and clear the list
    :param message_dict: message_dict
    """
    comp = clients[message_dict['id']].get_computer_by_id(message_dict['computer_id'])
    # num of changes from server is length of requests list
    n = len(comp.get_requests())
    for req in comp.get_requests():
        # for each requests, send the request back to client
        if req['action'] == 'upload file':
            util.upload_file(req['path'], n)
        if req['action'] == 'remove file':
            util.send_remove_file(req['path'], n)
        if req['action'] == 'upload path':
            util.upload_path(req['path'], n)
        if req['action'] == 'move file':
            util.send_move_file(req['path'], req['new_path'], n)
        n -= 1
    # clear request list
    comp.clear_requests()


if __name__ == '__main__':
    path_to_DB = os.path.join("./", "DB/")
    # creates the dir
    os.makedirs(os.path.dirname(path_to_DB), exist_ok=True)
    my_port = int(sys.argv[1])
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(('', my_port))
    server.listen(5)
    util = Utils('server', None)
    clients = {}

    while True:
        client_socket, client_address = server.accept()
        util.set_socket(client_socket)
        # receive length of message
        length = util.recv_all(16)
        length = length.decode('utf-8')
        # receive all message
        message = util.recv_all(int(length))
        message_dict = util.parse_message(message)

        num_of_requests = int(message_dict['num_of_requests'])
        for i in range(num_of_requests):
            # add new request to client's computers
            if message_dict['action'] != 'new client' and message_dict['action'] != 'exists client' and \
                    message_dict['action'] != 'requests_updates':
                client = clients[message_dict['id']]
                client.add_request(message_dict['computer_id'], message_dict)
            util.set_id(message_dict['id'])
            # handle request from client
            if 'new client' in message_dict['action']:
                client_id = ''.join(
                    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128))
                print(client_id)
                # make directory in the name of client id
                os.mkdir(os.path.join(path_to_DB, client_id))
                # set util object id to client id
                util.set_id(client_id)
                # send to client its new id
                try:
                    client_socket.send(bytes(client_id, 'utf-8'))
                except Exception:
                    pass
                # save new client to clients dict
                clients[client_id] = Client(client_id)
                generate_comp(client_id)
            if 'exists client' == message_dict['action']:
                if not message_dict['id'] in clients.keys():
                    break
                generate_comp(message_dict['id'])
                # send client folder from server to client
                util.send_dir(os.path.join('.' + os.path.sep + 'DB', message_dict['id']))
            if 'upload file' == message_dict['action']:
                # get file from client
                util.get_file(message_dict)
            if 'remove file' == message_dict['action']:
                # remove file or directory from server
                util.remove_file(message_dict)
            if 'upload path' == message_dict['action']:
                # get path name from client and create it
                util.make_path(message_dict)
            if 'move file' == message_dict['action']:
                # move file or directory location
                a = message_dict['path'].replace('\\\\', '\\')
                b = message_dict['new_path'].replace('\\\\', '\\')
                try:
                    os.renames(a, b)
                except:
                    pass
            if 'requests_updates' in message_dict['action']:
                # client asks for changes from server
                send_changes(message_dict)

            if i == num_of_requests - 1:
                break
            # gets the next message
            # receive length of message
            length = util.recv_all(16)
            if not length:
                break
            length = length.decode('utf-8')
            # receive all message
            message = util.recv_all(int(length))
            message_dict = util.parse_message(message)
        # close connection ready for next client to connect
        util.get_socket().close()
