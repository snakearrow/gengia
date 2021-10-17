import os
import sounddevice as sd
import sys
import time
import json
from pathlib import Path
from progress.bar import ChargingBar


class Setup:

    _data_dir = None
    _selected_device = None

    def __init__(self):
        print(31*"-")
        print("| Welcome to the Gengia Setup |")
        print(31*"-")
        print("")
        
        data_dir = str(Path.home()) + "/.gengia"
        print(f"* The Gengia data directory is: {data_dir}")
        if not os.path.isdir(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except:
                print(f"Could not create directory {data_dir}, exiting.")
                sys.exit(1)
                
        else:
            print(f"It seems like the folder {data_dir} already exists.")
            print("Re-running the setup will delete and newly create the setup files!")
            answer = input("Continue? [y/N] ")
            if answer == "" or answer == "N":
                sys.exit(0)
        
        self._data_dir = data_dir
        
        print("")
        print("* Let's first select the device to record audio with.\n  Press Enter to view a list of available devices.")
        input()
        devices = sd.query_devices()
        i = 0
        for device in devices:
            print(f"  {i}  {device['name']}")
            i += 1
        
        n_devices = i
        while True:
            answer = input("Select the number of the device to use: ")
            selected = int(answer)
            if selected < 0 or selected >= n_devices:
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
            bar.finish()
            
            bar = ChargingBar('Playback', max=duration, check_tty=False)
            sd.play(recording)
            for i in range(duration):
                time.sleep(1)
                bar.next()
            sd.wait()
            bar.finish()
            print("")
            answer = input("  Continue? If no, you can select another device. [Y/n] ")
            if answer == "n":
                continue
                
            print(f"Great, will use device: {self._selected_device}")
            break
        
        self._write_config()
        print("*  The setup is finished. You can now start to use Gengia, e.g. by recording some commands with 'gengia --record'.")
    
    
    def _write_config(self):
        config_file = self._data_dir + "/config.json"
        data = {"Device": self._selected_device}
        with open(config_file, "w") as fp:
            json.dump(data, fp)
        print(f"Wrote {config_file}")

