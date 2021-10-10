import numpy as np
import soundfile as sf
import sounddevice as sd
from math import log10


class Audio:

    # chunk size in milliseconds
    def __init__(self, filename: str = None, data = None, samplerate: int=44100, chunk_size: int=100):
        if filename:
            self._data, self._samplerate = sf.read(filename)
        else:
            self._data = data
            self._samplerate = samplerate
            
        self._samples_per_chunk = int(self._samplerate * (chunk_size/1000.0))
        self._update_dbfs()
            
    def _update_dbfs(self, debug=False):
        step = self._samples_per_chunk
        absolute_data = np.absolute(self._data)
        self._dbfs = []
        
        i = 0
        while i < len(self._data):
            avg = np.average(absolute_data[i:i + step])
            dbfs = 20*log10(avg) # TODO check for Null
            if debug:
                print(dbfs)
            self._dbfs.append(dbfs)
            i += step

    def get_dbfs(self):
        return self._dbfs

    def get_avg_dbfs(self):
        if len(self._dbfs) == 0:
            return None
        return sum(self._dbfs) / len(self._dbfs)

    # loudness in percent
    def amplify(self, loudness: float = 80.0):
        abs_data = np.absolute(self._data)
        max_value = np.max(abs_data)
        factor = (loudness/100.0) / max_value
        self._data = self._data * factor
        self._update_dbfs()

    def truncate_trailing_silence(self, silence_threshold_dbfs: int = -50, kernel_size: int = 5):
        offset = None
        for i, db in enumerate(reversed(self._dbfs)):
            if db > silence_threshold_dbfs and self._next_samples_louder_than(self._dbfs[::-1], i, kernel_size, silence_threshold_dbfs):
                offset = int((len(self._dbfs)-(i-1)) * self._samples_per_chunk)
                sec = offset / self._samplerate
                print(f"detected trailing silence starting at {sec}s")
                break
        
        if offset:
            self._data = self._data[:offset]
            self._update_dbfs()
        else:
            print("no trailing silence could be detected")
            
    # kernel size: the N next values have to be louder than threshold as well (filters noise peaks)
    def truncate_leading_silence(self, silence_threshold_dbfs: int = -50, kernel_size: int = 5):
        offset = None
        for i, db in enumerate(self._dbfs):
            if db > silence_threshold_dbfs and self._next_samples_louder_than(self._dbfs, i, kernel_size, silence_threshold_dbfs):
                if i == 0:
                    print("no leading silence could be detected")
                    return
                    
                offset = (i-1) * self._samples_per_chunk
                sec = offset / self._samplerate
                print(f"detected leading silence from 0s until {sec}s")
                break
        
        self._data = self._data[offset:]
        self._update_dbfs()

    def truncate_silence(self, silence_threshold_dbfs: int = -50, kernel_size: int = 5):
        self.truncate_trailing_silence(silence_threshold_dbfs, kernel_size)
        self.truncate_leading_silence(silence_threshold_dbfs, kernel_size)

    def get_data(self):
        return self._data

    @staticmethod
    def _next_samples_louder_than(data, start_idx: int, n_samples: int, threshold: int):
        if start_idx >= len(data):
            return False
        
        return all(value > threshold for value in data[start_idx:start_idx+n_samples])

    def play(self):
        sd.play(self._data)
        sd.wait()
        

if __name__ == "__main__":
    audio = Audio("commands/internet.wav")
    audio.amplify()
    audio.truncate_silence()
    
    audio.play()

