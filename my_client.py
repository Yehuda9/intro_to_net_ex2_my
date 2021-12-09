import sys
from socket import socket, AF_INET, SOCK_STREAM

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from utils import *


class Watcher:

    def __init__(self):
        """
        Watcher constructor.
        """
        self.event_handler = None
        self.observer = Observer()
        self.__in_req = False

    def requests_updates(self):
        """
        request updates from the server
        """
        print("start requests_updates")
        self.event_handler.set_in_req(True)
        # m is the message we will send to the server to get the updates
        m = util.generate_message('requests_updates')
        try:
            # if there is an open socket - use it
            util.get_socket().send(m)
            handle_req()
        except Exception as e:
            util.set_socket(socket(AF_INET, SOCK_STREAM))
            try:
                util.get_socket().connect((server_IP, server_port))
                util.get_socket().send(m)
                handle_req()
            except:
                pass
            util.get_socket().close()
        self.event_handler.set_in_req(False)
        print("finish requests_updates")

    def run(self, t):
        """
        run function activate the watchdog, every x seconds ask the server for updates, x is client parameter
        """
        # activates watchdog
        self.event_handler = Handler()
        self.observer.schedule(self.event_handler, path_to_folder, recursive=True)
        self.observer.start()
        try:
            i = 0
            while True:
                time.sleep(1)
                i += 1
                if i == t:
                    i = 0
                    copy = util.get_ignore_wd().copy()
                    # delete the non relevant requests from the dictionary of actions we got from the server
                    for a in copy.keys():
                        if copy[a][1] == 'close' and copy[a][0] + 3 < time.time():
                            util.get_ignore_wd().pop(a)
                    # checks if we can ask for updates without overriding another socket
                    if not self.event_handler.get_in_event() and not self.event_handler.get_in_req():
                        self.requests_updates()
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    def __init__(self):
        """
        Handler constructor- initialize if we are in event or getting requests from the server at the moment
        """
        self.__in_event = False
        self.__in_req = False

    def get_in_req(self):
        """
        getter for checking if we are getting requests from the server at the moment
        :return: true/false
        """
        return self.__in_req

    def set_in_req(self, b):
        """
        setter for updating if we are getting requests from the server at the moment
        """
        self.__in_req = b

    def get_in_event(self):
        """
        getter for checking if we are are handling changes in our local directory
        :return: true/false
        """
        return self.__in_event

    def set_in_event(self, b):
        """
        setter for updating if we are handling changes in our local directory
        """
        self.__in_event = b

    def is_start_with(self, p):
        """
        checks if the path is a substring of path we need to ignore at the moment
        :param p: path
        :return: true if it's substring and false if not
        """
        for key in util.get_ignore_wd().keys():
            if key.startswith(p):
                return True
        return False

    def wait_for_handle_req_fin(self):
        """
        enters while loop until the we finish handling all updates we got from the server
        """
        i = 0
        while self.__in_req:
            i += 1
            continue

    def on_created(self, event):
        """
        sends the the file/directory that has been created to the server (if needed)
        :param event: event for creating file/directory
        """
        p = event.src_path
        """checks if we need to send the event or ignore it (if its an event we got from the server in the last 3
        seconds)"""
        if not self.is_start_with(p) or (
                p in util.get_ignore_wd().keys() and util.get_ignore_wd()[p][1] == 'close'
                and util.get_ignore_wd()[p][
                    0] + 2 < time.time()):
            # checks if the computer isn't handling updates at the moment
            self.wait_for_handle_req_fin()
            self.__in_event = True
            util.set_socket(socket(AF_INET, SOCK_STREAM))
            print("Received created event - %s." % p)
            util.get_socket().connect((server_IP, server_port))
            # sends the file or the directory - accordingly
            if os.path.isdir(event.src_path):
                util.upload_path(event.src_path, util.get_size_of_dir(event.src_path))
            else:
                util.upload_file(event.src_path)
            util.get_socket().close()
        self.__in_event = False

    def on_modified(self, event):
        """
        sends the the file/directory that has been modified to the server (if needed)
        :param event: event for modifying file/directory
        """
        p = event.src_path
        """checks if we need to send the event or ignore it (if its an event we got from the server in the last 3
        seconds)"""
        if not self.is_start_with(p) or (
                p in util.get_ignore_wd().keys() and util.get_ignore_wd()[p][1] == 'close'
                and util.get_ignore_wd()[p][
                    0] + 2 < time.time()):
            # checks if the computer isn't handling updates at the moment
            self.wait_for_handle_req_fin()
            self.__in_event = True
            print("Received modified event - %s." % p)
            # check if the modify event is on file (we don't need to modify directory)
            if not os.path.isdir(event.src_path):
                util.set_socket(socket(AF_INET, SOCK_STREAM))
                util.get_socket().connect((server_IP, server_port))
                # in modify we will tell the server to delete the file and then upload new one
                util.send_remove_file(event.src_path, util.get_size_of_dir(event.src_path) * 2)
                util.upload_file(event.src_path)
                util.get_socket().close()
        self.__in_event = False

    def on_deleted(self, event):
        """
        sends the the path to the file/directory that has been deleted to the server (if needed)
        :param event: event for deleting file/directory
        """
        p = event.src_path
        """checks if we need to send the event or ignore it (if its an event we got from the server in the last 3
                seconds)"""
        if not self.is_start_with(p) or (
                p in util.get_ignore_wd().keys() and util.get_ignore_wd()[p][1] == 'close'
                and util.get_ignore_wd()[p][
                    0] + 2 < time.time()):
            # checks if the computer isn't handling updates at the moment
            self.wait_for_handle_req_fin()
            self.__in_event = True
            print("Received delete event - %s." % p)
            util.set_socket(socket(AF_INET, SOCK_STREAM))
            # sends the path to delete to the server
            util.get_socket().connect((server_IP, server_port))
            util.send_remove_file(event.src_path, util.get_size_of_dir(event.src_path))
            util.get_socket().close()
        self.__in_event = False

    def on_moved(self, event):
        """
        sends the the path to the file/directory that has been moved to the server
        :param event: event for moving file/directory
        """
        # checks if the computer isn't handling updates at the moment
        self.wait_for_handle_req_fin()
        self.__in_event = True
        print("Received moved event - %s." % event.src_path)
        print("Received moved event - %s." % event.dest_path)
        # sends the source path and the destination path to the server
        util.set_socket(socket(AF_INET, SOCK_STREAM))
        util.get_socket().connect((server_IP, server_port))
        num_of_requests = util.get_size_of_dir(event.dest_path)
        util.send_move_file(event.src_path, event.dest_path, num_of_requests)
        util.get_socket().close()
        self.__in_event = False


def handle_req():
    """
    handling the updated the client got from the server
    """
    # first, gets the length of the next message
    length = util.recv_all(16)
    if length is not None:
        length = length.decode('utf-8')
        # gets the information about the update we need to get
        message = util.recv_all(int(length))
        # parse the message
        message_dict = util.parse_message(message)
        num_of_requests = int(message_dict['num_of_requests'])
        # iterating through all updates
        for i in range(num_of_requests):
            action = message_dict['action']
            if action == 'upload file':
                util.get_file(message_dict)
            elif action == 'remove file':
                util.remove_file(message_dict)
            elif action == 'upload path':
                util.make_path(message_dict)
            elif action == 'move file':
                util.get_ignore_wd()[message_dict['path']] = (time.time(), 'open')
                util.get_ignore_wd()[message_dict['new_path']] = (time.time(), 'open')
                os.renames(message_dict['path'], message_dict['new_path'])
                util.get_ignore_wd()[message_dict['path']] = (time.time(), 'close')
                util.get_ignore_wd()[message_dict['new_path']] = (time.time(), 'close')

            if i == num_of_requests - 1:
                break
            # gets the next update
            length = util.recv_all(16)
            if not length:
                break
            length = length.decode('utf-8')
            message = util.recv_all(int(length))
            message_dict = util.parse_message(message)


if __name__ == '__main__':
    # saves arguments to main
    server_IP = sys.argv[1]
    server_port = int(sys.argv[2])
    path_to_folder = sys.argv[3]
    rel_folder_name = path_to_folder.split(os.sep)[-1]
    time_between_syncs = int(sys.argv[4])
    my_id = '0'
    # create util instance for this client
    util = Utils('client', socket(AF_INET, SOCK_STREAM), path_to_folder, my_id)
    util.get_socket().connect((server_IP, server_port))
    # checks if we connected from exist client
    if len(sys.argv) == 6:
        my_id = sys.argv[5]
        util.set_id(my_id)
        util.set_rel_folder_name(path_to_folder)
        os.makedirs(path_to_folder, exist_ok=True)
        message = util.generate_message('exists client', path_to_folder, 0, 1)
        # sends to the server request to get id for the current computer
        util.get_socket().send(message)
        computer_id = util.get_socket().recv(64).decode('utf-8')
        util.set_client_computer_id(computer_id)
        # sync the folder from the server
        handle_req()
        util.get_socket().close()
        # clear all requests we got from the server for syncing
        util.get_ignore_wd().clear()
    # if it is a new client
    else:
        f = util.get_size_of_dir(path_to_folder)
        message = util.generate_message('new client', path_to_folder, 0, f + 1)
        try:
            util.get_socket().send(message)
        except Exception:
            pass
        # gets id for the client
        my_id = util.get_socket().recv(128).decode('utf-8')
        util.set_id(my_id)
        # gets id for the computer
        computer_id = util.get_socket().recv(64).decode('utf-8')
        util.set_client_computer_id(computer_id)
        # sync the folder to the server
        util.send_dir(path_to_folder)
    # creates Watcher instance and activate the watchdog
    w = Watcher()
    w.run(time_between_syncs)
