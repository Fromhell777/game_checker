#!/bin/bash

# This script needs to be sourced

# Create the python virtual environment
python3 -m venv .venv

# Activate the environment
. .venv/bin/activate

# Install packages
python3 -m pip install selenium
python3 -m pip install selenium_async
python3 -m pip install aiohttp
python3 -m pip install requests
python3 -m pip install lxml
