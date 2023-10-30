
import os
import subprocess
import time
import warnings
from random import Random
from subprocess import PIPE
from unittest import mock
import pytest
import requests
from sirup import utils


## Define fixtures
@pytest.fixture
def list_instance():
    return [1, 2, 3, 4, 5]

@pytest.fixture
def rotation_list_instance(list_instance):
    instance = utils.RotationList(list_instance)
    return instance


## Tests

@mock.patch("sirup.utils.requests.Session.get")
def test_get_ip(mock_get):
    # breakpoint()
    class TestResponse:
        def __init__(self, **kwargs):
            self.__dict__ = kwargs
    # Normal case
    working_response = TestResponse(**{
        'text': '122.44.33',
        'status_code': 200,
        'encoding': 'ISO-8859-1',
        'reason': 'OK',
        'elapsed': 'OK'
    })
    mock_get.return_value = working_response
    # mock_session.return_value = 200
    result = utils.get_ip()
    mock_get.assert_called_once_with("https://ifconfig.me", timeout=3)
    assert result == "122.44.33", "returns incorrect IP"

    # ConnectionError
    mock_get.reset_mock()
    failed_response = TestResponse(**{
        'text': '',
        'status_code': 404,
        'encoding': 'ISO-8859-1',
        'reason': 'OK',
        'elapsed': 'OK'
    })
    mock_get.side_effect = requests.ConnectionError
    mock_get.return_value = failed_response
    with pytest.raises(requests.ConnectionError):
        result = utils.get_ip()
    mock_get.assert_called_once_with("https://ifconfig.me", timeout=3)

    # Other exceptions
    mock_get.reset_mock()
    mock_get.side_effect = Exception
    mock_get.return_value = failed_response
    with pytest.raises(requests.ConnectionError):
        result = utils.get_ip()
    mock_get.assert_called_once_with("https://ifconfig.me", timeout=3)


def test_lookup_strings_in_list():
    strings_to_check = ["message 1", "message 2"]
    list_of_strings = ["here is message 1 and here is message 2", 
                        "here is message 1 but not the other",
                        "none"]

    result = utils.lookup_strings_in_list(strings_to_check=strings_to_check, list_of_strings=list_of_strings)
    assert result, "returns False when True expected"

    list_of_strings = ["here is message 1 but not the other",
                        "none"]
    result = utils.lookup_strings_in_list(strings_to_check=strings_to_check, list_of_strings=list_of_strings)
    assert not result, "returns True when False expected"


def test_sudo_read_file_without_sudo(mocker):
    mocker.patch("subprocess.run")
    utils.sudo_read_file("myfile.txt")
    subprocess.run.assert_called_once_with(["cat", "myfile.txt"], capture_output=True, check=True)

def test_sudo_read_file_with_sudo(mocker):
    mocker.patch("subprocess.run")
    utils.sudo_read_file("myfile.txt", "my_password")
    subprocess.run.assert_called_once_with(["sudo", "-S", "cat", "myfile.txt"], input="my_password".encode(), capture_output=True, check=True)


@pytest.fixture
def file_to_read(tmp_path):
    target_output = os.path.join(tmp_path, "testfile.txt")
    with open(target_output, 'w+', encoding="utf-8") as file:
        file.writelines(["hello\n", "world\n"])
    return target_output

def test_sudo_read_file_correct_output(file_to_read):
    content = utils.sudo_read_file(file_to_read)
    assert content == ["hello", "world"], "content not read correctly"


@pytest.fixture
def log_file_with_connection(tmp_path):
    target_output = os.path.join(tmp_path, "logfile_test")
    with open(target_output, 'w+', encoding="utf-8") as file:
        file.writelines(["some message\n", "another message\n", "some time and date Initialization Sequence Completed"])
    return target_output

@mock.patch("time.sleep")
def test_check_connection_returns_true(mock_sleep, log_file_with_connection):
    output = utils.check_connection(log_file_with_connection, 1, None)
    assert output, "check_connection does not return True when it should"
    mock_sleep.assert_called_once_with(2)


def test_check_connection_timeout(file_to_read):
    start_time = time.time()
    expected_timeout = 0.05
    output = utils.check_connection(file_to_read, expected_timeout, None, expected_timeout/2)
    assert time.time() - start_time >= expected_timeout, "timeout not respected"
    assert not output, "does not return False when it should"


def test_list_files_with_full_path(tmp_path):
    all_files = ["udp_file_1", "udp_file_2", "tcp_file_1"]
    for f in all_files:
        (tmp_path / f).touch()

    # With rule    
    def filter_rule(x):
        return x if "udp" in x else False
    
    output = utils.list_files_with_full_path(tmp_path, filter_rule)
    expected = [os.path.join(tmp_path, "udp_file_1"), os.path.join(tmp_path, "udp_file_2")]
    # different python versions order the output differently. test without the order
    assert all(i in expected for i in output), "does not apply filter rule correctly"
    assert all(i in output for i in expected), "does not apply filter rule correctly"

    # Without rule 
    filter_rule = None 
    output = utils.list_files_with_full_path(tmp_path, filter_rule)
    expected = [os.path.join(tmp_path, f) for f in all_files]
    assert len(output) == len(expected), "different number of elements"
    assert all([e in output for e in expected]), "not all expected elements" #pylint: disable=use-a-generator 


def test_RotationList_pop_append(list_instance, rotation_list_instance):
    assert rotation_list_instance == list_instance

    first = rotation_list_instance.pop_append()
    assert first == 1, "does not pop first element"
    assert rotation_list_instance[-1] == 1, "does not re-append correctly"


def test_RotationList_shuffle(list_instance, rotation_list_instance):
    randomizer = Random(3)
    rotation_list_instance.shuffle(randomizer)
    assert len(rotation_list_instance) == len(list_instance), "shuffling changes length"
    assert sum(x != y for x, y in zip(list_instance, rotation_list_instance)) > 0, "shuffle does not change order"


def test_RotationList_repr(list_instance, rotation_list_instance):
    result = repr(rotation_list_instance)
    expected = f"RotationList({list_instance})"
    assert result == expected, "__repr__ returns incorrect string"


@mock.patch("subprocess.run")
@mock.patch("sirup.utils.get_vpn_pids") #patch the get_vpn_pids here
def test_kill_all_connections(mock_get_vpn_pids, mock_run):
    pwd = "my_password"

    # an alternative would be here: https://stackoverflow.com/questions/25692440/mocking-a-subprocess-call-in-python
    mock_get_vpn_pids.return_value = ["123", "456"]
    expected_kill_cmd = ["sudo", "-S", "kill", "-15", "123", "456"]
    mock_run.return_value.returncode = 0

    # Call
    utils.kill_all_connections(pwd)

    # Assert
    mock_run.assert_called_once_with(expected_kill_cmd, input=pwd.encode(), capture_output=True, check=False)

    # # Test also the non-zero exits status
    mock_run.reset_mock()
    mock_run.return_value.returncode = 1

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        utils.kill_all_connections(pwd)
        assert len(w) == 1
        assert issubclass(w[-1].category, UserWarning)
        assert "returned with exit status 1" in str(w[-1].message)


@mock.patch("subprocess.Popen")
def test_get_vpn_pids(mock_popen):
    expected_pgrep_cmd = ["pgrep", "openvpn"]
    mock_popen.return_value.communicate.return_value = ("123\n456\n", "error")
    # Call
    pids = utils.get_vpn_pids()
    # Assert
    mock_popen.assert_called_once_with(expected_pgrep_cmd, stdout=PIPE, text=True)
    assert pids == ["123", "456"], "Returns wrong pids"


@mock.patch("subprocess.Popen")
def test_check_password(mock_popen):
    # Test when password is wrong
    process = mock_popen.return_value.__enter__.return_value
    process.returncode = 1
    process.communicate.return_value = (b"", b"nothing")

    with pytest.raises(RuntimeError, match="Wrong password"):
        utils.check_password("wrong_password")

    mock_popen.assert_called_once_with(['sudo', "ls"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    process.communicate.assert_called_once_with(input="wrong_password\n".encode())

    # Test when correct password provided
    mock_popen.reset_mock()
    process.reset_mock()
    process.communicate.reset_mock() 

    process.communicate.return_value = (b"", b"All good!")
    process.returncode = 0
    assert utils.check_password("my_password"), "fails to recognize correct password"
    process.communicate.assert_called_once_with(input="my_password\n".encode())