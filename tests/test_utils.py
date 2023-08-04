
import os
import subprocess
import time
from random import Random
from unittest import mock
import pytest
import requests
from sirup import utils


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


def test_list_of_strings_contains_two_strings():
    strings_to_check = ["message 1", "message 2"]
    list_of_strings = ["here is message 1 and here is message 2", 
                        "here is message 1 but not the other",
                        "none"]

    result = utils.list_of_strings_contains_two_strings(strings_to_check=strings_to_check, list_of_strings=list_of_strings)
    assert result, "returns False when True expected"

    list_of_strings = ["here is message 1 but not the other",
                        "none"]
    result = utils.list_of_strings_contains_two_strings(strings_to_check=strings_to_check, list_of_strings=list_of_strings)
    assert not result, "returns True when False expected"


def test_sudo_read_file_without_sudo(mocker):
    mocker.patch("subprocess.run")
    utils.sudo_read_file("myfile.txt")
    subprocess.run.assert_called_once_with(["cat", "myfile.txt"], capture_output=True, check=True)

def test_sudo_read_file_with_sudo(mocker):
    mocker.patch("subprocess.run")
    utils.sudo_read_file("myfile.txt", "my_password")
    subprocess.run.assert_called_once_with(["sudo", "cat", "myfile.txt"], input="my_password".encode(), capture_output=True, check=True)


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

def test_check_connection_returns_true(log_file_with_connection):
    output = utils.check_connection(log_file_with_connection, 1, None)
    assert output, "check_connection does not return True when it should"

def test_check_connection_timeout(file_to_read):
    start_time = time.time()
    output = utils.check_connection(file_to_read, 4, None)
    assert time.time() - start_time >= 4, "timeout not respected"
    assert not output, "check_connection does not return False when it should"


def test_list_files_with_full_path(tmp_path):
    all_files = ["udp_file_1", "udp_file_2", "tcp_file_1"]
    for f in all_files:
        (tmp_path / f).touch()

    # With rule    
    def filter_rule(x):
        return x if "udp" in x else False
    
    output = utils.list_files_with_full_path(tmp_path, filter_rule)
    expected = [os.path.join(tmp_path, "udp_file_1"), os.path.join(tmp_path, "udp_file_2")]
    assert output == expected, "does not apply filter rule correctly"

    # Without rule 
    filter_rule = None 
    output = utils.list_files_with_full_path(tmp_path, filter_rule)
    expected = [os.path.join(tmp_path, f) for f in all_files]
    assert len(output) == len(expected), "different number of elements"
    assert all([e in output for e in expected]), "not all expected elements" #pylint: disable=use-a-generator 

def test_RotationList_pop_append():
    mylist = [1, 2, 3, 4, 5]
    instance = utils.RotationList(mylist)
    assert instance == mylist

    first = instance.pop_append()
    assert first == 1, "does not pop first element"
    assert instance[-1] == 1, "does not re-append correctly"

def test_RotationList_shuffle():
    mylist = [1, 2, 3, 4, 5]
    instance = utils.RotationList(mylist)
    randomizer = Random(3)
    instance.shuffle(randomizer)
    assert len(instance) == len(mylist), "shuffling changes length"
    assert sum(x != y for x, y in zip(mylist, instance)) > 0, "shuffle does not change order"