import subprocess
import os
import time 
from getpass import getpass
from random import Random 
import logging 
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry 

# TODO: copy over documentation/comment from the rotate_surfshark file.


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
                logging.info(f"IP is: {response.text}")
            return response.text
        else:
            requests.ConnectionError("Failed to get the IP address")
    except Exception as e:
        logging.info(f"Got an exception: {e}")
        requests.ConnectionError("Failed to get the IP address")


class IPRotator():
    def __init__(self, auth_file, log_file, config_location, seed=123):
        self.auth_file = auth_file
        self.log_file = log_file
        self.config_location = config_location
        self.config_files = None 
        self.is_connected = False
        ip = get_ip()
        self.current_ip = ip 
        self.base_ip = ip
        self.current_config_file = None
        self.vpn_process = None 
        self.randomizer = Random(seed)

        pwd = getpass("Please enter your sudo password: ")
        self.raw_pwd = pwd 
        # this is just to have the password in a format that can be passed to the next process
        piped_password = subprocess.Popen(['echo', pwd], stdout=subprocess.PIPE) 
        self.pwd = piped_password 

        self._load_config_files()

    def _load_config_files(self):
        "Take all available confg file and put them into a list. Only use _udp connections; tcp and upd give the same IP for a given server."
        # files = [f for f in os.listdir(self.config_location) if "surfshark" in f and "_udp" in f]
        files = [f for f in os.listdir(self.config_location) if not "-tor" in f] #ignore tor proxies. could be slow to establish connection.
        files = [os.path.join(self.config_location, f) for f in files]
        self.config_files = files

    def _connect(self, timeout=40):
        "Connect to single server. Fails when no connection after `timeout`."
        if self.current_config_file is None: # set IP for the first time 
            self._set_config_file()
        
        cmd = ["sudo", "-S", "openvpn", "--config", self.current_config_file, "--auth-user-pass", self.auth_file, "--log", self.log_file]
        proc = subprocess.Popen(
            cmd, stdin=self.pwd.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setpgrp
        )
        
        start_time = time.time()
        while time.time() - start_time <= timeout and not self.is_connected:
            time.sleep(3)
            self.is_connected = self._check_connection()
        
        if self.is_connected:
            logging.info(f"Connected with {self.current_config_file}")
            self.current_ip = get_ip()
        else:
            raise TimeoutError(f"Could not build connection with {self.current_config_file}")

        self.vpn_process = proc 

    def rotate(self):
        "Rotate to next server"
        self.disconnect()
        self._set_config_file()
        self.connect()

    def connect(self):
        "Connect to the next server in the queue"
        i = 0 
        max_trials = 5
        while True:
            try: 
                self._connect()
            except TimeoutError as e:
                if i > max_trials:
                    raise TimeoutError(f"Failed to connect to {max_trials} different servers.")
                else:
                    logging.info(f"Handling error {e}")
                    self._set_config_file()
                    time.sleep(10) 
                    i += 1
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


    def disconnect(self):
        "Disconnect the vpn, get back to base IP."
        pgid = os.getpgid(self.vpn_process.pid)
        subprocess.check_output(f"sudo -S kill {pgid}".split(), stdin=self.pwd.stdout) 
        time.sleep(5)
        self.current_ip = get_ip(echo=True)
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
        else:
            return False 


    def _read_logfile(self):
        "read log file from openvpn into a list"
        cmd = f"sudo -S cat {self.log_file}".split()
        content = subprocess.check_output(
            cmd, stdin=self.pwd.stdout, text=True
        )
        content = content.rstrip().split("\n")
        return content 


