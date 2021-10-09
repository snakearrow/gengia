import sounddevice
import soundfile
import numpy as np
import matplotlib.pyplot as plt
import os
from progress.bar import Bar
from time import sleep
from math import log10
from Audio import Audio


def record(background_noise_threshold: int):
    fs = 44100
    
    print(f"recording with background noise threshold: {background_noise_threshold} dBFS")
    while True:
        rec_name = input("Name of command: ")
        duration = input("Duration in seconds (default=2): ")
        if duration == "":
            duration = 2.0
        else:
            duration = int(duration)
        
        print(f"Will record for {duration} seconds. Press Enter to start")
        input()
        print("Recording...", end='', flush=True)
        recording = sounddevice.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
        sounddevice.wait()
        print(" done", flush=True)
        # post-process audio file: amplify and truncate silence
        audio = Audio(data=recording, samplerate=fs)
        audio.amplify()
        audio.truncate_silence(background_noise_threshold)
        audio.play()
        soundfile.write(f"commands/{rec_name}.wav", audio.get_data(), fs)


def monitor_background_noise(duration_sec: int = 5):
    fs = 44100
    duration = duration_sec
    print("Starting background noise detection. Please say: 'this is a test'")
    bar = Bar('Recording', max=duration, check_tty=False)
    recording = sounddevice.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
    for i in range(duration):
        sleep(1)
        bar.next()
    sounddevice.wait()
    bar.finish()

    audio = Audio(data=recording, samplerate=fs)
    audio.amplify()
    
    chunk_size = 10
    step = int(fs * (chunk_size/1000.0))
    # seems like some microphones do automatic adjustment of noise levels, so cut the adjustment
    # in the beginning
    absolute_data = np.absolute(audio.get_data())[44100:]
    dbfs = []
    i = 0
    while i < len(absolute_data):
        avg = np.average(absolute_data[i:i + step])
        if avg > 0.0:
            value = 20 * log10(avg)
            dbfs.append(value)
        i += step
    
    plt.plot(range(0, len(dbfs)), dbfs)
    #plt.ion()
    plt.show()
    max_value = max(dbfs)
    min_value = min(dbfs)
    mean_value = (max_value + min_value) / 2.0
    print(f"min dBFS: {min_value}, max dBFS: {max_value}, mean: {mean_value} dBFS")
    # filter dBFSs so that only possible silence is present
    dbfs_silence = []
    for db in dbfs:
        if db <= mean_value:
            dbfs_silence.append(db)
    
    avg_dbfs = sum(dbfs_silence) / len(dbfs_silence)
    max_dbfs = max(dbfs_silence)
    print(f"background noise on average at {avg_dbfs} dBFS with peak {max_dbfs} dBFS")
    return avg_dbfs, max_dbfs


if __name__ == "__main__":
    os.makedirs("commands", exist_ok=True)
    sounddevice.default.samplerate = 44100
    sounddevice.default.device = 'pulse'
    avg_dbfs, _ = monitor_background_noise()
    #input()
    record(int(avg_dbfs+5))
