
from .utils import list_of_strings_contains_two_strings


def raise_ovpn_exceptions(stdout, stderr, log): #pylint: disable=unused-argument
    "Raise exceptions depending on the output and log of the openvpn commands."
    base_error_message = None
    if log is not None:
        msg0 = "Options error: --auth-user-pass fails with"
        msg1 = "No such file or directory"
        if list_of_strings_contains_two_strings([msg0, msg1], log):
            raise FileNotFoundError("Wrong authentication file.")
        base_error_message = f"""
        Log content: {log},
        stdout content: {stdout}
        """
    elif stdout != "":
        if "Error opening configuration file:" in stdout:
            raise RuntimeError("Problem with configuration file.")
        base_error_message = f"stdout content: {stdout}"
    else: # other unknown cases
        base_error_message = f"""
            Log content: {log},
            stdout content: {stdout}
            """
    
    if base_error_message is not None:
        raise RuntimeError(base_error_message)
