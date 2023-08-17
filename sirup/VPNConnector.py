"Connect to a server with OpenVPN"

# import logging # TODO: add logging properly
import logging
import os
import subprocess
import time
from subprocess import PIPE
import requests
from .raise_ovpn_exceptions import raise_ovpn_exceptions
from .TemporaryFileWithRootPermission import TemporaryFileWithRootPermission
from .utils import check_connection
from .utils import get_ip
from .utils import get_vpn_pids
from .utils import sudo_read_file


class VPNConnector():
    def __init__(self, config_file, auth_file, track_ip=True):
        """Initialize an VPNConnector object.

        Args:
            config_file (str): Full path and file name of the ovpn configuration file to connect to a server. 
            auth_file (str): Full path and file name of the file with the authentication credentials for VPN connections.
            track_ip (bool, optional): If True, the IP address is queried after each `connect` and `disconnect`. 
                For long-running programs, it is better to set track_ip=False in order to respect the query limits 
                of the IP address API.
        """
        self.config_file = config_file
        self.auth_file = auth_file
        self.current_ip = None 
        self.base_ip = None 
        self.track_ip = track_ip
        if track_ip:
            ip = get_ip()
            self.current_ip = ip 
            self.base_ip = ip
        self._vpn_process_id = None # if not connected, this should be None

    def is_connected(self):
        "Return True if a VPN connection is active."
        return self._vpn_process_id is not None

    def start_vpn(self, pwd, proc_id=None):
        "Start an OpenVPN connection."
        self.log_file = TemporaryFileWithRootPermission(password=pwd, suffix=".log")
        self.log_file.create(file_name="openvpn")
        cmd = ["sudo", "-S", "openvpn",
            "--config", self.config_file,
            "--auth-user-pass", self.auth_file,
            "--log", self.log_file.file_name,
            "--daemon"]
        
        if proc_id is not None:
            cmd.extend(["--writepid", proc_id])
        with subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
            stdout, stderr = proc.communicate(pwd.encode()) 
            if proc.returncode != 0: 
                log = None 
                if os.path.exists(self.log_file.file_name):
                    log = sudo_read_file(file=self.log_file.file_name, pwd=pwd) # what happens if the log file does not exist?
                raise_ovpn_exceptions(stdout.decode(), stderr.decode(), log)
                # process the log file, stdout and stderr here 

    def connect(self, pwd):
        """Connect to a server.

        Args:
            pwd (str): User root password. This is necessary for openvpn.
        """
        with TemporaryFileWithRootPermission(suffix=".txt", password=pwd) as file_with_process_id:
            self.start_vpn(pwd=pwd, proc_id=file_with_process_id) 
            connected = check_connection(self.log_file, timeout=30, pwd=pwd) # TODO: best to here directly check for 
            # anticipated errors (wrong auth file, wrong config file for now). then it's extendable
            if connected:
                logging.info("Connected with %d.", self.auth_file)
                vpn_pid = sudo_read_file(file_with_process_id, pwd=pwd)
                self._vpn_process_id = vpn_pid[0].strip()
                if self.track_ip:
                    try:
                        self.current_ip = get_ip(config_file=self.config_file)
                    except requests.ConnectionError as exc: # TODO: use special exception here? 
                        raise requests.ConnectionError("Cannot get IP address") from exc
            else: 
                raise TimeoutError("Could not connect to vpn") 
            # TODO: print the log file? last messages of the log file?


    def disconnect(self, pwd):
        """Disconnect from the currentserver. If self.track_ip is True, also get back the base IP.
        """
        openvpn_pids = get_vpn_pids()

        if self._vpn_process_id in openvpn_pids:
            cmd = ["sudo", "-S", "kill", self._vpn_process_id]
            subprocess.run(cmd, input=pwd.encode(), check=True)
            self.log_file.remove() 
            time.sleep(5)
        
        if self.track_ip:
            self.current_ip = get_ip()
            if self.current_ip != self.base_ip: 
                # is informative, but could be a problem with dynamic IPs (like eduroam). so only raise warning.
                raise RuntimeWarning("Expected to go back to base IP address, but did not")
        self._vpn_process_id = None
