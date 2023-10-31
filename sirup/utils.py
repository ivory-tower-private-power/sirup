import logging
import os
import subprocess
import time
import warnings
from subprocess import PIPE
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .TemporaryFileWithRootPermission import TemporaryFileWithRootPermission


def get_ip(echo=False, config_file=None):
    """Query the current IP address of the computer.

    The function calls `https://ifconfig.me` and retrieves the IP address.

    Args:
        echo (bool, optional): If `True`, logging prints the retrieved IP address
        config_file (str, optional): Name of the vpn configuration file currently in use.
            If supplied, logging prints the name of the config file if the IP address cannot
            be retrieved
    """
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
        if response.status_code == 200:
            if echo:
                logging.info("IP is: %s", response.text)
            return response.text
        # raise requests.ConnectionError("Failed to get the IP address")
        msg = "Failed to get the IP address"
        if config_file is not None:
            msg = f"{msg}. The config file is {config_file}."
        logging.info(msg)
        return 1234
    except Exception as e:
        logging.info("Got an exception: %s", e)
        raise requests.ConnectionError("Failed to get the IP address")
    

def lookup_strings_in_list(strings_to_check, list_of_strings): 
    """Scan a list of strings for presence of one or multiple strings in the same element. 

    Args:
        strings_to_check (list): the strings to look for.
        list_of_strings (list): the strings to scan.

    Returns:
        bool: `True` if there is at least one element in `list_of_strings` that contains all strings in `strings_to_check`.

    Example:
        >>> from sirup.utils import lookup_strings_in_list
        >>> lookup_strings_in_list(["hello", "world"], ["hello, wonderful world", "hello universe"])
        True
    """
    elements_contain_two_strings = [all([s in element for s in strings_to_check]) for element in list_of_strings] #pylint: disable=use-a-generator
    return any(elements_contain_two_strings)


def check_connection(log_file, timeout, pwd, waiting_time=2):
    """Wait and test for established connection until `timeout`.

    The function repeatedly scans the log file of the openvpn process and looks for a string
    that indicates that the vpn connection was established. It exits when the string is found
    or `timeout` is reached.

    Args:
        log_file (str): path to the log file of the vpn process.
        timeout (int): maximum time to wait for a successful conection.
        pwd (str): user root password.
        waiting_time (int, optional): Number of seconds to wait between consecutive scans.

    Returns:
        bool: indicates whether connection is established.
    """
    start_time = time.time()
    connected = False
    while time.time() - start_time < timeout and not connected:
        time.sleep(waiting_time)
        log = sudo_read_file(file=log_file, pwd=pwd)
        connected = "Initialization Sequence Completed" in log[-1]

    return connected 

def sudo_read_file(file, pwd=None):
    """Read a file with root permission to a list.
    
    Args:
        file (str or TemporaryFileWithRootPermission): the file to read
        pwd (str, optional): root password for the file. If file is 
            a `TemporaryFileWithRootPermission` and no password is provided, the password 
            is taken from the `TemporaryFileWithRootPermission` object.

    Returns:
        list: Content of the file, each line is one element in the list. 
    """ 
    if isinstance(file, TemporaryFileWithRootPermission):
        file = file.file_name
        if pwd is None:
            pwd = file.password
    cmd = ["cat", file]
    if pwd is None:
        output = subprocess.run(cmd, capture_output=True, check=True)
    else:
        cmd.insert(0, "sudo")
        cmd.insert(1, "-S")
        output = subprocess.run(cmd, input=pwd.encode(), capture_output=True, check=True)
    
    content = output.stdout.decode()
    content = content.rstrip().splitlines()
    return content 

def check_password(pwd): # TODO: use this only in the rotator class and test it when writing this.
    "Run simple command to see if password is correct"
    with subprocess.Popen(['sudo', "ls"], stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
        _, _ = proc.communicate(input=f"{pwd}\n".encode())
        if proc.returncode != 0:
            raise RuntimeError("Wrong password")
        
    return True

def list_files_with_full_path(directory, rule=None):
    """Collect all files in a directory and return a list of them with their full path.

    Args:
        directory (str): directory path
        rule (lambda, optional): a lambda function that returns a `bool`. If supplied, `list_files_with_full_path`
          filters the files in the directory by whether `rule` returns `True`.

    Returns:
        list: files, possibly filtered, with the full path. 
    """
    files = os.listdir(directory)
    if rule is not None:
        files = [rule(f) for f in files if rule(f)]
    files_with_full_path = [os.path.join(directory, f) for f in files]
    return files_with_full_path 


class RotationList(list):
    "Custom list for IP rotation."
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def pop_append(self):
        "Pop first element and append it at the end."
        el = self.pop(0)
        self.append(el)
        return el
    
    def shuffle(self, randomizer):
        """Randomly shuffle the list of proxies. This changes the order by which we iterate through them.

        Args:
            randomizer (random.Random): pseudo-random number generator.        
        """
        randomizer.shuffle(self)


def get_vpn_pids():
    """Extract all openvpn process ids on the machine. 

    Returns:
        list: all openvpn process IDs.
    """
    pgrep_command = ["pgrep", "openvpn"]
    pgrep_process = subprocess.Popen(pgrep_command, stdout=subprocess.PIPE, text=True) #pylint: disable=consider-using-with
    pgrep_output, _ = pgrep_process.communicate()

    openvpn_pids = pgrep_output.strip().split('\n')
    return openvpn_pids


def kill_all_connections(pwd):
    """Kill all openvpn connections on the machine
    
    Args:
        pwd (str): root password to the machine.    
    """

    openvpn_pids = get_vpn_pids()

    if openvpn_pids == [""]:
        logging.info("No openvpn processes found to be killed.")
    else:
        kill_command = ["sudo", "-S", "kill", "-15"] + openvpn_pids
        rc = subprocess.run(kill_command, input=pwd.encode(), capture_output=True, check=False)
        if rc.returncode != 0:
            msg = f"Killing vpn connections returned with exit status {rc.returncode}"
            warnings.warn(msg, UserWarning)
            # logging.info(msg)