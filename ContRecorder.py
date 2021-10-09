import sounddevice as sd
import queue
import numpy as np
import time
from collections import deque
import threading
import soundfile
import os
from timeit import default_timer as timer
import pyautogui
from Comparer import Comparer
from Audio import Audio

class ContRecorder:

    def __init__(self):
        self._comparer = Comparer("commands")
        self._comparer.load()
        self._data_queue = queue.Queue()
        self._background_noise_queue = queue.Queue()
        self._samplerate = 44100
        sd.default.device = 'pulse'
        self._current_background_noise = None
        self._working = False
        self._speaking = False
        self._min_length_command = 1.0 # minimum length of a command in seconds
        os.makedirs("tmp", exist_ok=True)

    def _audio_callback(self, data, frames, time, status):
        self._data_queue.put(data.copy())
        self._background_noise_queue.put(data.copy())

    def _background_noise_monitor_thread(self, every=1.5):
        # monitor every X seconds
        start_ts = timer()
        buf = []
        while True:
            buf.append(self._background_noise_queue.get())
            stop_ts = timer()
            if stop_ts - start_ts >= every and not self._speaking:
                data = np.concatenate(buf).ravel()
                audio = Audio(data=data)
                avg = sum(audio.get_dbfs()) / len(audio.get_dbfs())
                self._current_background_noise = avg
                #print(avg)
                buf = []
                start_ts = timer()

    def _command_thread(self, command):
        self._working = True
        # amplify & truncate silence
        audio = Audio(data=command)
        audio.amplify()
        audio.truncate_silence(self._current_background_noise)
        filename = f"tmp/recorded_{time.time()}.wav"
        soundfile.write(filename, audio.get_data(), self._samplerate)
        print(f"wrote {filename}")
        matched_filename = self._comparer.compare(filename)
        os.remove(filename)
        self._working = False
        if not matched_filename:
            return
        # TODO: what to do on command
        return

    def start(self):
        with sd.InputStream(channels=1, samplerate=self._samplerate, callback=self._audio_callback):
            t = threading.Thread(target=self._background_noise_monitor_thread)
            t.start()

            command = np.array([])
            buf = np.array([])
            chunk_size = 100 # in milliseconds
            step = int(self._samplerate * (chunk_size/1000.0))
            
            start_ts = None
            enough_data = False
            
            while True:
                while self._working:
                    time.sleep(0.01)

                try:
                    data = self._data_queue.get()
                    buf = np.append(buf, data)
                    
                    if self._current_background_noise and not self._speaking:
                        data = buf[-step:]
                        audio = Audio(data=data, chunk_size=chunk_size)
                        avg_dbfs = audio.get_avg_dbfs()
                        if avg_dbfs >= self._current_background_noise+10.0:
                            self._speaking = True
                            print(f"{time.time()}  start")
                            start_ts = timer()
                            command = np.append(command, buf[-step*2:])
                            continue
                            
                    elif self._speaking:
                        stop = False
                        command = np.append(command, data)
                        stop_ts = timer()
                        diff = stop_ts - start_ts
                        if diff < self._min_length_command:
                            continue
                        
                        if diff >= 3.0:
                            print("timeout")
                            stop = True
                        else:
                            data = buf[-step*5:]
                            audio = Audio(data=data, chunk_size=chunk_size)
                            avg_dbfs = audio.get_avg_dbfs()
                            if avg_dbfs <= self._current_background_noise+2.0:
                                print("stop")
                                stop = True
                        
                        if stop:
                            self._working = True
                            #audio = Audio(data=command)
                            #audio.amplify()
                            #audio.truncate_silence()
                            self._speaking = False
                            t = threading.Thread(target=self._command_thread, args=(command.copy(),))
                            t.start()
                            buf = np.array([])
                            command = np.array([])
                            
                except queue.Empty:
                    continue


if __name__ == "__main__":
    c = ContRecorder()
    c.start()
