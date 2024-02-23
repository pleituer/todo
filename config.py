import json
import os

with open(os.environ["todo_configPath"], "r") as f:
    CONFIG = json.load(f)