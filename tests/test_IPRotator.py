"""Tests for the sirup.IPRotator module.
"""

import subprocess
from sirup.IPRotator import IPRotator
from sirup.IPRotator import start_vpn


def test_IPRotator():
    pass


def test_class_instantiation_with_mocked_password(mocker):
    mocker.patch("getpass.getpass", return_value="test_password")
    instance = IPRotator(auth_file="file1", log_file="file2", config_location="file3")
    assert instance.pwd == "test_password"

def test_start_vpn(mocker):
    mocker.patch("subprocess.run")
    start_vpn("myconfig", "myauth", "mylog", "myproc_id", "mypwd")
    cmd = ["sudo", "-S", "openvpn",
           "--config", "myconfig",
           "--auth-user-pass", "myauth",
           "--log", "mylog",
           "--writepid", "myproc_id",
           "--daemon"]
    subprocess.run.assert_called_once_with(cmd, input="mypwd".encode(), check=True) 

# def test_class_instantiation_with_provided_password():
#     instance = YourClass(arg1="test", password="test_password")
#     assert instance.password == "test_password"