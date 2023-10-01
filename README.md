# garage-door
Monitor garage door

## Setup
- create a virtual env with python 3.9: `python3.9 -m venv ./venv`
- activate environment: `source ./venv/bin/activate` 
- Install packages: `pip install -r requirements.txt`
- Copy [settings.example.sh](./dev_tools/settings.example.sh) into new settings file and enter the environment variables
- Inject envvars into shell with `source /path/to/settings/file`

## Run
Run the script with `python main.py`
