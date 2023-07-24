import getpass
import logging
import os
import subprocess
import time
from random import Random
from .get_ip import get_ip
from .TemporaryFileWithRootPermission import TemporaryFileWithRootPermission


def start_vpn(config, auth, log, proc_id, pwd):
    "Start an open vpn connection."
    cmd = ["sudo", "-S", "openvpn",
           "--config", config,
           "--auth", auth,
           "--log", log,
           "--writepid", proc_id,
           "--daemon"]

    logging.debug("start openvpn")
    subprocess.run(cmd, input=pwd, check=True)

class IPRotator():
    def __init__(self, auth_file, log_file, config_location, seed=123, pwd=None): # pylint: disable=too-many-arguments
        # TODO: docstring for parameters
        # TODO: require types? config_location should be os.path? then remove the pylint constraint above
        self.auth_file = auth_file
        self.log_file = log_file
        self.config_location = config_location
        self.config_files = None 
        self.is_connected = False
        ip = get_ip()
        self.current_ip = ip 
        self.base_ip = ip
        self.current_config_file = None
        self.vpn_process_id = None 
        self.randomizer = Random(seed)

        if pwd is None:
            pwd = getpass.getpass("Please enter your sudo password: ")
        self.pwd = pwd

        self._load_config_files() # TODO: this makes the tests fail. how to fix?
        # TODO: validate password? ie try `sudo ls`, and if it fails, raise an exception?

    def _load_config_files(self):
        "Take all available confg file and put them into a list. Only use _udp connections; tcp and upd give the same IP for a given server."
        # TODO: remove this? ie ask directly for the list of config files?
        files = [f for f in os.listdir(self.config_location) if "-tor" not in f] #ignore tor proxies. could be slow to establish connection.
        files = [os.path.join(self.config_location, f) for f in files]
        self.config_files = files

    def _connect(self, timeout=40):
        "Connect to single server. Fails when no connection after `timeout`."
        if self.current_config_file is None: # set IP for the first time 
            self._set_config_file()

        logging.debug("start _connect")
        # TODO: capture missing config file? missing auth file? how do I do this?

        with TemporaryFileWithRootPermission(suffix=".txt", password=self.pwd) as file_with_process_id:
            start_vpn(self.current_config_file, self.auth_file, self.log_file, file_with_process_id, self.pwd)

            start_time = time.time()
            while time.time() - start_time <= timeout and not self.is_connected:
                time.sleep(3)
                self.is_connected = self._check_connection()
            
            if self.is_connected:
                logging.info("Connected with %s", self.current_config_file)
                self.current_ip = get_ip()
            else:
                raise TimeoutError(f"Could not build connection with {self.current_config_file}")

            logging.debug("reading in vpn pid")
            with open(file_with_process_id, "rb") as file: # TODO: this can be separated into a function and tested separately
                vpn_pid = file.readlines()
                assert len(vpn_pid) == 1, "Unexpected length of file."
                self.vpn_process_id = vpn_pid[0].strip()



    def rotate(self):
        "Rotate to next server"
        self.disconnect()
        self._set_config_file()
        self.connect()

    def connect(self):
        "Connect to the next server in the queue"
        i = 0
        max_trials = 2000 # set to some high value 
        while True:
            try: 
                self._connect()
            except TimeoutError as e:
                i += 1
                if i > max_trials:
                    raise TimeoutError(f"Failed to connect to {max_trials} different servers.") from e 
                logging.info("Handling error %s", e)
                self._set_config_file()
                waiting_time = 10
                if i % 20 == 0:
                    waiting_time = 300 # try to see whether this helps
                    logging.info("Failed to connect %d times; waiting %d", i, waiting_time)
                time.sleep(waiting_time) 
            if self.is_connected:
                break

    def _set_config_file(self):
        "Set or update the config file to the next candidate in the list."
        # TODO: use here, as a util, the function I wrote in the other repo? 
        # (for pop_append?) need to return both the updated list (or not b/c mutable?) and set the config file
        if self.current_config_file is not None:
            self.config_files.append(self.current_config_file) # put the current file to the end of the queue 
        self.current_config_file = os.path.join(self.config_files.pop(0))

    def shuffle_proxies(self):
        "Randomly shuffle the list of proxies. This changes the order by which we iterate through them."
        self.randomizer.shuffle(self.config_files)
        self._set_config_file()


    def disconnect(self, check_ip=False):
        "Disconnect the vpn, get back to base IP."
        cmd = ["sudo", "-S", "kill", self.vpn_process_id]
        subprocess.run(cmd, input=self.pwd.encode(), check=True)
        time.sleep(5)
        self.current_ip = get_ip(echo=True)
        if check_ip: # this is to make sure the IP is the same as when the class was instantiated. 
            # it may not be necessary, and could even a problem in networks with dynamic IPs (like eduroam)
            assert self.current_ip == self.base_ip
        self.is_connected = False


    def _check_connection(self, print_connection=False):
        # TODO: test correctly reading log file; test reaction to different log file messages/print the whole logfile?
        log = self._read_logfile()
        if print_connection:
            for line in log:
                if "Peer Connection Initiated" in line:
                    logging.info(line)
        if "Initialization Sequence Completed" in log[-1]:
            return True 
        return False 


    def _read_logfile(self):
        "read log file from openvpn into a list"
        # TODO: check that log file is read correctly
        cmd = ["sudo", "cat", self.log_file]
        output = subprocess.run(cmd, input=self.pwd.encode(), capture_output=True, check=True)
        content = output.stdout.decode()
        content = content.rstrip().split("\n")
        return content 