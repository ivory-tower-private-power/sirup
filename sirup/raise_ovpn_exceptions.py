
from .utils import lookup_strings_in_list


def raise_ovpn_exceptions(stdout, stderr, log): 
    """Raise exceptions depending on the output and log of the openvpn commands.
    
    Raises:
        FileNotFoundError: when the authentication file for openvpn cannot be found.
        RuntimeError:
            - when there is a problem with the configuration file
            - in any other case
    """
    base_error_message = None
    if log is not None:
        msg0 = "Options error: --auth-user-pass fails with"
        msg1 = "No such file or directory"
        if lookup_strings_in_list([msg0, msg1], log):
            raise FileNotFoundError("Wrong authentication file.")
        # print other information here for unanticipated situations
        base_error_message = f"""
        Log content:\n {" ".join(log)},
        stdout content:\n {stdout}
        """
    elif stdout != "":
        if "Error opening configuration file:" in stdout:
            raise RuntimeError("Problem with configuration file:")
        base_error_message = f"stdout content: {stdout}"
    else: # unanticipated stderr cases
        base_error_message = f"""
            stderr content:\n {stderr}
            """
    
    if base_error_message is not None:
        raise RuntimeError(base_error_message)
