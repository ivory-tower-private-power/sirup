"Connect to a server with OpenVPN"

# import logging # TODO: add logging properly
import os
import subprocess
import time
from subprocess import PIPE
from .get_ip import get_ip
from .TemporaryFileWithRootPermission import TemporaryFileWithRootPermission


def sudo_read_file(file, pwd=None): # TODO: move this to utils?
    "Read a file with root permission" 
    # TODO: the if check here is not covered in tests
    if isinstance(file, TemporaryFileWithRootPermission):
        file = file.file_name
    cmd = ["cat", file]
    if pwd is None:
        output = subprocess.run(cmd, capture_output=True, check=True)
    else:
        cmd.insert(0, "sudo")
        output = subprocess.run(cmd, input=pwd.encode(), capture_output=True, check=True)
    
    content = output.stdout.decode()
    content = content.rstrip().split("\n")
    return content 


def check_connection(log_file, timeout, pwd):
    "Wait and test for established connection until `timeout`."
    start_time = time.time()
    connected = False
    while time.time() - start_time < timeout and not connected:
        time.sleep(2)
        log = sudo_read_file(file=log_file, pwd=pwd)
        connected = "Initialization Sequence Completed" in log[-1]

    return connected 
    
def check_password(pwd): # TODO: use this only in the rotator class and test it when writing this.
    "Run simple command to see if password is correct"
    with subprocess.Popen(['sudo', "-S", "ls"], stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
        _, stderr = proc.communicate(input=f"{pwd}\n".encode())
        if proc.returncode != 0:
            raise RuntimeError("Wrong password")
        # print(stdout)
        print(stderr.decode())


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

        # TODO: assert that file exists etc..? or just raise an exception?

    def start_vpn(self, pwd, proc_id=None):
        "Start an open vpn connection."
        self.log_file = TemporaryFileWithRootPermission(password=pwd, suffix=".log")
        self.log_file.create(file_name="openvpn")
        cmd = ["sudo", "-S", "openvpn",
            "--config", self.config_file,
            "--auth-user-pass", self.auth_file,
            "--log", self.log_file.file_name,
            "--daemon"]
        
        if proc_id is not None:
            cmd.extend(["--writepid", proc_id])
        subprocess.run(cmd, input=pwd.encode(), check=True)
        # Wrong inputs to openvpn (auth or config file) are printed to console;
        # the log file is only created when openvpn "finds" the destination server
        # If this is not the case, capture it here. It's hacky, but I don't know
        # a better way right now.
        if not os.path.exists(self.log_file.file_name): # FIXME: this makes the test_start_vpn* fail 
            raise FileNotFoundError("Openvpn connection failed. Are the supplied file names correct?")

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
                self.current_ip = get_ip()
            else:
                raise TimeoutError("Could not connect to vpn") 
            # TODO: should this be a specific openvpn connection error? not sure


    def disconnect(self):
        # TODO: kill process
        self.log_file.remove()
        raise NotImplementedError()
