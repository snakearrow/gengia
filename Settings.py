import os
from pathlib import Path
import json


class Settings:

    _working_dir = None
    _device = None
    
    def __init__(self):
        config_file = str(Path.home()) + "/.gengia/config"
        with open(config_file, "r") as fp:
            config_data = json.load(fp)
            
        self._working_dir = config_data["WorkingDir"]
        self._device = config_data["Device"]
        
if __name__ == "__main__":
    s = Settings()

