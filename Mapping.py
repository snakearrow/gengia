import json
import os
import time
from pathlib import Path
import pyautogui


class Mapping:

    _mapping = None
    _known_commands = ["execute", "click", "press", "keyDown", "keyUp", "wait"]
    
    def __init__(self):
        mapping_file = str(Path.home()) + "/.gengia/mappings.json"
        if not os.path.isfile(mapping_file):
            print(f"Mappings file {mapping_file} not found")
            return
            
        with open(mapping_file, "r") as fp:
            self._mapping = json.load(fp)
        

    def execute_for_file(self, filename: str):
        command = Path(filename).stem
        for value in self._mapping:
            if command.lower() == value.lower():
                for cmd in self._mapping[value]:
                    if cmd not in self._known_commands:
                        print(f"ERR: command {cmd} for file {filename} unknown")
                        break
                    params = self._mapping[value][cmd]
                    if cmd == "execute":
                        os.system(params)
                    elif cmd == "wait":
                        time.sleep(int(params))
                    elif cmd == "click":
                        x, y = params.split(",")
                        pyautogui.click(x=int(x), y=int(y))
                    elif cmd == "keyDown":
                        pyautogui.keyDown(params)
                    elif cmd == "press":
                        pyautogui.press(params)
                    elif cmd == "keyUp":
                        pyautogui.keyUp(params)


if __name__ == "__main__":
    m = Mapping()
    m.execute_for_file("/home/nordraak/.gengia/commands/mails.wav")
