"Connect to a server with OpenVPN"

# import logging # TODO: add logging properly
import os
import subprocess
import time
from subprocess import PIPE
import requests
from .raise_ovpn_exceptions import raise_ovpn_exceptions
from .TemporaryFileWithRootPermission import TemporaryFileWithRootPermission
from .utils import check_connection
from .utils import get_ip
from .utils import sudo_read_file


class VPNConnector():
    def __init__(self, config_file, auth_file):
        # TODO: docstring for parameters
        # TODO: require types? config_location should be os.path? then remove the pylint constraint above
        self.config_file = config_file
        self.auth_file = auth_file
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
        # DECIDED: use a temporary log file 
        with TemporaryFileWithRootPermission(suffix=".txt", password=pwd) as file_with_process_id:
            self.start_vpn(pwd=pwd, proc_id=file_with_process_id) 
            connected = check_connection(self.log_file, timeout=30, pwd=pwd) # TODO: best to here directly check for 
            # anticipated errors (wrong auth file, wrong config file for now). then it's extendable
            if connected:
                print("connected!")
                vpn_pid = sudo_read_file(file_with_process_id, pwd=pwd)
                self._vpn_process_id = vpn_pid[0].strip()
                try:
                    self.current_ip = get_ip(config_file=self.config_file)
                except requests.ConnectionError as exc: # TODO: use special exception here? 
                    raise requests.ConnectionError("Cannot get IP address") from exc
            else:
                raise TimeoutError("Could not connect to vpn") 
            # TODO: should this be a specific openvpn connection error? not sure
            # TODO: print the log file? last messages of the log file?


    def disconnect(self, pwd):
        "Disconnect the vpn and get back the base IP"
        cmd = ["sudo", "-S", "kill", self._vpn_process_id]
        subprocess.run(cmd, input=pwd.encode(), check=True)
        self.log_file.remove() 
        time.sleep(5)
        self.current_ip = get_ip()
        if self.current_ip != self.base_ip: 
            # is informative, but could be a problem with dynamic IPs (like eduroam). so only raise warning.
            raise RuntimeWarning("Expected to go back to base IP address, but did not")
        self._vpn_process_id = None
