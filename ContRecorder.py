import sounddevice as sd
import queue
import numpy as np
import time
import socket
from collections import deque
import threading
import soundfile
import os
import tempfile
from timeit import default_timer as timer
from Comparer import Comparer
from Audio import Audio
from Mapping import Mapping


class ContRecorder:

    def __init__(self, path_to_commands: str, device: str):
        self._comparer = Comparer(path_to_commands)
        n_files = self._comparer.load()
        if n_files <= 0:
            print(f"WARN: Could not find any command audio files in {path_to_commands}")
            print(f"Consider recording some audio commands first.")
        
        self._data_queue = queue.Queue()
        self._background_noise_queue = queue.Queue()
        self._samplerate = 44100
        sd.default.device = device
        self._current_background_noise = None
        self._working = False
        self._speaking = False
        self._done = False
        self._min_length_command = 1.0 # minimum length of a command in seconds
        self._enough_background_noise_samples = False

    def _audio_callback(self, data, frames, time, status):
        self._data_queue.put(data.copy())
        self._background_noise_queue.put(data.copy())

    def _background_noise_monitor_thread(self, every=1.0):
        # monitor every X seconds
        start_ts = timer()
        buf = []
        self._enough_background_noise_samples = False
        n_samples = 0
        while not self._done:
            buf.append(self._background_noise_queue.get())
            stop_ts = timer()
            if stop_ts - start_ts >= every and not self._speaking:
                data = np.concatenate(buf).ravel()
                audio = Audio(data=data)
                avg = sum(audio.get_dbfs()) / len(audio.get_dbfs())
                self._current_background_noise = avg
                print(f"{avg:.1f}")
                buf = []
                start_ts = timer()
                n_samples += 1
                if n_samples >= 3:
                    self._enough_background_noise_samples = True
        
        print("background noise thread quitting")

    def _command_thread(self, command):
        self._working = True
        # amplify & truncate silence
        audio = Audio(data=command)
        audio.amplify()
        audio.truncate_silence(self._current_background_noise)
        tmpdir = tempfile.gettempdir()
        filename = f"{tmpdir}/recorded_{time.time()}.wav"
        soundfile.write(filename, audio.get_data(), self._samplerate)
        print(f"wrote {filename}")
        matched_filename = self._comparer.compare(filename)
        os.remove(filename)
        self._working = False
        if not matched_filename:
            return
        # TODO: what to do on command, use Mappings class
        return

    def start(self):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        addr = ("localhost", 49173)
        sock.bind(addr)
        print(f"listening for start command on {addr}")
        while True:
            msg, _ = sock.recvfrom(128)
            msg = msg.decode()
            if msg == "start":
                self._done = False
                self._listen()
    
    def _listen(self):
        with sd.InputStream(channels=1, samplerate=self._samplerate, callback=self._audio_callback):
            background_noise_thread = threading.Thread(target=self._background_noise_monitor_thread)
            background_noise_thread.start()

            command = np.array([])
            buf = np.array([])
            chunk_size = 250 # in milliseconds
            step = int(self._samplerate * (chunk_size/1000.0))
            
            start_ts = None
            
            while not self._done:
                while self._working:
                    time.sleep(0.01)

                try:
                    data = self._data_queue.get()
                    buf = np.append(buf, data)
                    
                    if self._current_background_noise and self._enough_background_noise_samples and not self._speaking:
                        data = buf[-step:]
                        audio = Audio(data=data, chunk_size=chunk_size)
                        avg_dbfs = audio.get_avg_dbfs()
                        if avg_dbfs and avg_dbfs >= self._current_background_noise+30.0: # TODO: the greater the background noise, the greater this value should be
                            print(f"avg dbfs: {avg_dbfs}, background noise: {self._current_background_noise}")
                            self._speaking = True
                            print(f"{time.time()} start")
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
                            self._speaking = False
                            t = threading.Thread(target=self._command_thread, args=(command.copy(),))
                            t.start()
                            t.join()
                            self._done = True
                            buf = np.array([])
                            command = np.array([])
                            
                except queue.Empty:
                    continue


if __name__ == "__main__":
    c = ContRecorder("commands")
    c.start()
