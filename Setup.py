import os
import sounddevice as sd
import sys
import time
import json
from pathlib import Path
from progress.bar import ChargingBar


class Setup:

    _working_dir = None
    _selected_device = None

    def __init__(self):
        print(31*"-")
        print("| Welcome to the Gengia Setup |")
        print(31*"-")
        print("")
        
        cur_dir = os.getcwd()
        print(f"* The working directory is: {cur_dir}")
        answer = input("  Would you like to change the working directory? [y/N] ")
        if answer == "y":
            print("  Please enter the new working directory (it will be created if it does not exist): ")
            answer = input()
            if not os.path.isdir(answer):
                try:
                    os.makedirs(answer, exist_ok=True)
                    cur_dir = answer
                    print(f"  Great, the new working directory is: {cur_dir}")
                except os.error as e:
                    print(e)
                    sys.exit(1)
        
        self._working_dir = cur_dir
        
        print("")
        print("* Now, we will select the device to record audio with.\n  Press Enter to view a list of available devices.")
        input()
        devices = sd.query_devices()
        i = 0
        for device in devices:
            print(f"  {i}  {device['name']}")
            i += 1
        
        while True:
            answer = input("Select the number of the device to use: ")
            selected = int(answer)
            if selected < 0 or selected >= i:
                print(f"Error: Selected device {selected} does not exist, please choose another one")
                continue
                
            for i, device in enumerate(devices):
                if i == selected:
                    self._selected_device = device['name']
                    break
            
            sd.default.device = self._selected_device
            
            print("  To check if this device works, we will record and playback some audio.")
            input("  Press Enter to start recording. After recording, the recorded audio will be played back.")
            duration = 10
            bar = ChargingBar('Recording', max=duration, check_tty=False)
            recording = sd.rec(int(duration * 44100), samplerate=44100, channels=2)
            for i in range(duration):
                time.sleep(1)
                bar.next()
            sd.wait()
            sd.play(recording)
            bar = ChargingBar('Playback', max=duration, check_tty=False)
            sd.play(recording)
            for i in range(duration):
                time.sleep(1)
                bar.next()
            sd.wait()
            print("")
            answer = input("  Continue? If no, you can select another device. [Y/n] ")
            if answer == "n":
                continue
                
            print(f"Great, will use device: {self._selected_device}")
            break
        
        self._write_config()
        print("*  The setup is finished. You can now start to use Gengia.")
        
    def _write_config(self):
        config_file = str(Path.home()) + "/.gengia"
        os.makedirs(config_file, exist_ok=True)
        config_file += "/config"
        data = {"WorkingDir": self._working_dir, "Device": self._selected_device}
        with open(config_file, "w") as fp:
            json.dump(data, fp)
        print(f"Wrote {config_file}")

