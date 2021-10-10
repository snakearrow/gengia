import argparse
import os
import sys
from pathlib import Path
from ContRecorder import ContRecorder
from CommandRecorder import CommandRecorder
from Settings import Settings
from Setup import Setup


def run_setup():
    setup = Setup()
    
def run_record():
    rec = CommandRecorder("commands")
    rec.start()
    
def run():
    rec = ContRecorder("commands")
    rec.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", help="run setup", action="store_true")
    parser.add_argument("--record", help="record voice commands", action="store_true")
    args = parser.parse_args()
    
    config_file = str(Path.home()) + "./gengia/config"
    
    if args.setup:
        run_setup()
        sys.exit(0)
    
    elif not os.path.isfile(config_file):
        print(f"Seems like the config file {config_file} is missing.\nPlease start Gengia with --setup first.")
        sys.exit(1)
        
    settings = Settings()
    
    if args.record:
        run_record()
    else:
        run()

