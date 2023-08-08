import getpass
import logging
import time
from random import Random
import requests
from .utils import RotationList
from .utils import kill_all_connections
from .utils import list_files_with_full_path
from .VPNConnector import VPNConnector


class IPRotator():
    def __init__(self, # pylint: disable=too-many-arguments
                 auth_file,
                 config_location,
                 pwd=None,
                 seed=123,
                 config_file_rule=None):
        """Initialize an IPRotator object.

        Args:
            auth_file (str): Path to the file containing authentication credentials for VPN connections.
            config_location (str): Path to the directory where VPN configuration files are stored.
            pwd (str, optional): Sudo password. If not provided, the user will be prompted to enter it.
            seed (int, optional): Seed for the random number generator to shuffle config files. 
            config_file_rule (str, optional): Rule to filter config files in the config_location.
        """
        # TODO: how to deal with properties from the VPNconnector? ie IP, is connected, base IP, ...
        
        config_files = list_files_with_full_path(config_location, config_file_rule)
        self.config_queue = RotationList(config_files)
        self.auth_file = auth_file
        self.randomizer = Random(seed)
        if pwd is None:
            pwd = getpass.getpass("Please enter your sudo password: ")
        self.pwd = pwd       # TODO: validate password? ie try `sudo ls`, and if it fails, raise an exception?
        self.connector = None # TODO: better name?
        kill_all_connections(pwd)

    def connect(self, shuffle=False, max_trials=2000):
        """Connect to the server associated with the first config_file in the list.

        Args:
            shuffle (bool, optional): If True, shuffle the config files before connecting.
            max_trials (int, optional): Maximum number of connection attempts before raising an exception.
        """
        i = 0 
        if shuffle:
            self.config_queue.shuffle(self.randomizer)
        # try to connect; if it fails, change the server and retry
        while True:
            connector = VPNConnector(self.config_queue.pop_append(), self.auth_file)
            try:
                connector.connect(pwd=self.pwd)
            except TimeoutError as e:
                i += 1
                if i >= max_trials:
                    raise TimeoutError(f"Failed to connect to {max_trials} different servers.") from e 
                waiting_time = 10
                if i % 20 == 0:
                    waiting_time = 300 # try to see whether this helps
                    logging.info("Failed to connect %d times; waiting %d", i, waiting_time)
                time.sleep(waiting_time)
            except requests.ConnectionError:
                kill_all_connections(self.pwd)
                time.sleep(5)
            
            if connector.is_connected():
                break

        self.connector = connector

    
    def disconnect(self):
        """Disconnect from the current server.
        """
        self.connector.disconnect(self.pwd)
        self.connector = None

    def rotate(self):
        """Rotate to the next server.
        """
        self.disconnect()
        self.connect()