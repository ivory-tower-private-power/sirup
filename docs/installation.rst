Installation
=============

Requirements 
--------------
`sirup` requires python versions >= 3.7 and <=3.11 and a linux operating system. 

The `openvpn` software can be installed as described `here <https://community.openvpn.net/openvpn/wiki/OpenvpnSoftwareRepos>`_.


The user also needs to have `root` access to the machine (ie, to be able to run `sudo` commands in the command line). This is a security barrier built into `OpenVPN`, and it is best not to change it. 

Lastly, `sirup` requires an account with a VPN service provider such as ProtonVPN or Surfshark -- it is to whose servers `sirup` connects. See :ref:`getting_started` for details.


Installation
--------------

The installation currently works only with pip from github:

.. code-block:: console

    python -m pip install 'sirup @ git+https://github.com/ivory-tower-private-power/sirup'


