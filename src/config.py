import json
import os

CONFIG_NAME = "trueConfig.json"

with open(os.path.join(os.environ["todoPath"], CONFIG_NAME), "r") as f:
    CONFIG = json.load(f)