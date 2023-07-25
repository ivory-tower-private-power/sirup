import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_ip(echo=False):
    "Query the current IP address of the computer."
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
        if response.ok:
            if echo:
                logging.info("IP is: %s", response.text)
            return response.text
        raise requests.ConnectionError("Failed to get the IP address")
    except Exception as e:
        logging.info("Got an exception: %s", e)
        raise requests.ConnectionError("Failed to get the IP address")