# Game checker

Checks if a new game is available in the store

## Packages

The following Python packages are required:

* aiohttp
* selenium
* requests
* lxml

You can setup a Python environment as follows:

```bash
cd setup_python_env
. setup_python.sh
```

If you want to deactivate that environment, simply execute:

```bash
deactivate
```

## Setup mail account

* You need to create a gmail account
* You need to enable the 2 factor authentication
* You need to create an "App Password" and use that one

## Setup the correct permission to run rtcwake as sudo

* execute `visudo`
* Add the line `myusername ALL = (root) NOPASSWD: /usr/sbin/rtcwake` to the
  sudoers file
