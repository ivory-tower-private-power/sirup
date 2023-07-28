import logging
import subprocess
import time
from subprocess import PIPE
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .TemporaryFileWithRootPermission import TemporaryFileWithRootPermission


def get_ip(echo=False):
    "Query the current IP address of the computer."
    # sources:
    # https://stackoverflow.com/questions/23013220/max-retries-exceeded-with-url-in-requests,
    # https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html
    session = requests.Session() 
    retry = Retry(total=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter) # TODO: why did I add this in the first place? can I do without? 
    session.mount("http://", adapter) # need to update the tests for this 

    try:
        response = session.get("https://ifconfig.me", timeout=3)
        if response.status_code == 200:
            if echo:
                logging.info("IP is: %s", response.text)
            return response.text
        raise requests.ConnectionError("Failed to get the IP address")
    except Exception as e:
        logging.info("Got an exception: %s", e)
        raise requests.ConnectionError("Failed to get the IP address")
    

def list_of_strings_contains_two_strings(strings_to_check, list_of_strings): 
    "Test whether two strings in `strings_to_check` are contained in at least one of the list of strings"
    elements_contain_two_strings = [all([s in element for s in strings_to_check]) for element in list_of_strings] #pylint: disable=use-a-generator
    return any(elements_contain_two_strings)


def check_connection(log_file, timeout, pwd):
    "Wait and test for established connection until `timeout`."
    start_time = time.time()
    connected = False
    while time.time() - start_time < timeout and not connected:
        time.sleep(2)
        log = sudo_read_file(file=log_file, pwd=pwd)
        connected = "Initialization Sequence Completed" in log[-1]

    return connected 

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

def check_password(pwd): # TODO: use this only in the rotator class and test it when writing this.
    "Run simple command to see if password is correct"
    with subprocess.Popen(['sudo', "-S", "ls"], stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
        _, stderr = proc.communicate(input=f"{pwd}\n".encode())
        if proc.returncode != 0:
            raise RuntimeError("Wrong password")
        # print(stdout)
        print(stderr.decode())