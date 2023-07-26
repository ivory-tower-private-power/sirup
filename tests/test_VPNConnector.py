
import os
import subprocess
import tempfile
import time
import pytest
from sirup.VPNConnector import VPNConnector
from sirup.VPNConnector import check_connection
from sirup.VPNConnector import sudo_read_file


def test_start_vpn_without_pid(mocker):
    connector = VPNConnector("config_file", "auth_file")
    temp_dir = tempfile.gettempdir()
    mocker.patch("subprocess.run")
    cmd = ["sudo", "-S", "openvpn",
           "--config", "config_file",
           "--auth-user-pass", "auth_file",
           "--log", os.path.join(temp_dir, "openvpn.log"),
           "--daemon"]
    connector.start_vpn(pwd="my_password")
    subprocess.run.assert_called_once_with(cmd, input="my_password".encode(), check=True)

def test_start_vpn_with_pid(mocker):
    connector = VPNConnector("config_file", "auth_file")
    temp_dir = tempfile.gettempdir()
    mocker.patch("subprocess.run")
    cmd = ["sudo", "-S", "openvpn",
           "--config", "config_file",
           "--auth-user-pass", "auth_file",
           "--log", os.path.join(temp_dir, "openvpn.log"),
           "--daemon",
           "--writepid", "file.txt"]
    connector.start_vpn(pwd="my_password", proc_id="file.txt")
    subprocess.run.assert_called_once_with(cmd, input="my_password".encode(), check=True)


def test_sudo_read_file_without_sudo(mocker):
    mocker.patch("subprocess.run")
    sudo_read_file("myfile.txt")
    subprocess.run.assert_called_once_with(["cat", "myfile.txt"], capture_output=True, check=True)

def test_sudo_read_file_with_sudo(mocker):
    mocker.patch("subprocess.run")
    sudo_read_file("myfile.txt", "my_password")
    subprocess.run.assert_called_once_with(["sudo", "cat", "myfile.txt"], input="my_password".encode(), capture_output=True, check=True)


@pytest.fixture
def file_to_read(tmp_path):
    target_output = os.path.join(tmp_path, "testfile.txt")
    with open(target_output, 'w+', encoding="utf-8") as file:
        file.writelines(["hello\n", "world\n"])
    return target_output

def test_sudo_read_file_correct_output(file_to_read):
    content = sudo_read_file(file_to_read)
    assert content == ["hello", "world"], "content not read correctly"


@pytest.fixture
def log_file_with_connection(tmp_path):
    target_output = os.path.join(tmp_path, "logfile_test.txt")
    with open(target_output, 'w+', encoding="utf-8") as file:
        file.writelines(["some message\n", "another message\n", "some time and date Initialization Sequence Completed"])
    return target_output

def test_check_connection_returns_true(log_file_with_connection):
    output = check_connection(log_file_with_connection, 1, None)
    assert output, "check_connection does not return True when it should"

def test_check_connection_timeout(file_to_read):
    start_time = time.time()
    output = check_connection(file_to_read, 4, None)
    assert time.time() - start_time >= 4, "timeout not respected"
    assert not output, "check_connection does not return False when it should"


# where should the correctness of the pw be checked? in this class? in the other? in both?
# 