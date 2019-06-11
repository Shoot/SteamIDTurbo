# SteamIDTurbo
Rapidly checks to see if a vanity URL is available. If it is, it claims it. Heavy work in progress. This is more a proof of concept, as it is very slow.

## Installation
1. Install the latest version of Python from [here](https://www.python.org/downloads/)
2. Use the `pip` command to install the requirements
```bash
pip install requests
pip install pycryptodomex
```

## Usage
1. Make a new file called `ids.txt` and put the vanity URLs you want to target. Maximum of 100.
2. Put your Steam username and password in `user.json`, alongside your API key from [here](https://steamcommunity.com/dev/apikey)
3. Open terminal in your program's directory, and type `py app.py` to start it.
