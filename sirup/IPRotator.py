import logging
import os
import subprocess
import time
from getpass import getpass
from random import Random
from subprocess import PIPE
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_ip(echo=False):
    "Query the current IP address of the computer."
    # sources:
    # https://stackoverflow.com/questions/23013220/max-retries-exceeded-with-url-in-requests,
    # https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        response = session.get("https://ifconfig.me", timeout=3)
        if response.ok:
            if echo:
                logging.info("IP is: %s", response.text)
            return response.text
        raise requests.ConnectionError("Failed to get the IP address")
    except Exception as e:
        logging.info("Got an exception: %s", e)
        raise requests.ConnectionError("Failed to get the IP address")


class IPRotator():
    def __init__(self, auth_file, log_file, config_location, seed=123):
        # TODO: docstring for parameters
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
        self.pid_file = "vpn_pid.txt" # TODO: where to store log files and pid files?

        self.pwd = getpass("Please enter your sudo password: ")

        self._load_config_files()

    def _load_config_files(self):
        "Take all available confg file and put them into a list. Only use _udp connections; tcp and upd give the same IP for a given server."
        files = [f for f in os.listdir(self.config_location) if "-tor" not in f] #ignore tor proxies. could be slow to establish connection.
        files = [os.path.join(self.config_location, f) for f in files]
        self.config_files = files

    def _connect(self, timeout=40):
        "Connect to single server. Fails when no connection after `timeout`."
        if self.current_config_file is None: # set IP for the first time 
            self._set_config_file()
        
        cmd = ["sudo", "-S", "openvpn",
               "--config", self.current_config_file, 
               "--auth-user-pass", self.auth_file,
               "--log", self.log_file,
               "--writepid", self.pid_file,
               "--daemon"]
        
        with subprocess.Popen(cmd, stdin=PIPE) as proc:
            proc.communicate(input=self.pwd.encode())

        
        start_time = time.time()
        while time.time() - start_time <= timeout and not self.is_connected:
            time.sleep(3)
            self.is_connected = self._check_connection()
        
        if self.is_connected:
            logging.info("Connected with %s", self.current_config_file)
            self.current_ip = get_ip()
        else:
            raise TimeoutError(f"Could not build connection with {self.current_config_file}")

        with open(self.pid_file, "rb") as file:
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
        with subprocess.Popen(cmd, stdin=PIPE) as proc:
            proc.communicate(input=self.pwd.encode())
        time.sleep(5)
        self.current_ip = get_ip(echo=True)
        if check_ip: # this is to make sure the IP is the same as when the class was instantiated. 
            # it may not be necessary, and could even a problem in networks with dynamic IPs (like eduroam)
            assert self.current_ip == self.base_ip
        self.is_connected = False


    def _check_connection(self, print_connection=False):
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
        cmd = ["sudo", "cat", self.log_file]
        with subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, text=True) as process:
            content, _ = process.communicate(input=self.pwd)

        content = content.rstrip().split("\n")
        return content 