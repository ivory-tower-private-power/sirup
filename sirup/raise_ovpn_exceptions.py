
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
        raise RuntimeError(f"Log content:\n {" ".join(log)}, stdout content:\n {stdout}")
    elif "Error opening configuration file:" in stdout:
        raise RuntimeError("Problem with configuration file:")    
    elif stdout == "": # unanticipated stderr cases
        raise RuntimeError(f"stderr content:\n {stderr}")
    else:        
        raise RuntimeError(f"stdout content: {stdout}")
