import os
from pathlib import Path
import json


class Settings:

    _data_dir = None
    _device = None
    
    def __init__(self):
        config_file = str(Path.home()) + "/.gengia/config.json"
        with open(config_file, "r") as fp:
            config_data = json.load(fp)
        
        self._device = config_data["Device"]
        self._data_dir = str(Path.home()) + "/.gengia"
        
    def get_data_dir(self):
        return self._data_dir
    
    def get_device(self):
        return self._device


if __name__ == "__main__":
    s = Settings()

