
import pytest
from sirup.raise_ovpn_exceptions import raise_ovpn_exceptions


def test_missing_auth_user_file():
    log = ["WARNING: cannot stat file '/some/wrong/file': No such file or directory (errno=2)",
           "Options error: --auth-user-pass fails with '/some/wrong/file': No such file or directory (errno=2)"]
    stdout = "Some stdout message"
    stderr = ""
    with pytest.raises(FileNotFoundError) as e:
        raise_ovpn_exceptions(stdout, stderr, log)
    e.match("Wrong authentication file\\.")
    

def test_missing_configuration_file():
    stdout = "First part. Error opening configuration file: cannot find some/path/to/file"
    log = None
    stderr = ""
    with pytest.raises(RuntimeError) as e:
        raise_ovpn_exceptions(stdout, stderr, log)
    e.match("Problem with configuration file\\:")
    
def test_other_nonempty_log_file():
    log = ["Unexpected message line",
           "Another message line"]
    stdout = ""
    stderr = ""
    with pytest.raises(RuntimeError) as e:
        raise_ovpn_exceptions(stdout, stderr, log) 
    e.match(" ".join(log))

def test_other_stdout_message():
    stdout = "One message part. Another message part"
    log = None 
    stderr = ""
    with pytest.raises(RuntimeError) as e:
        raise_ovpn_exceptions(stdout, stderr, log)
    e.match(stdout)

def test_all_other_cases():
    log = None 
    stdout = ""
    stderr = "stderr message."
    with pytest.raises(RuntimeError) as e:
        raise_ovpn_exceptions(stdout, stderr, log)
    assert e.match("stderr message\\.")