import librosa
from threading import Lock
from dtw import accelerated_dtw
import librosa.display
import os
from concurrent import futures
from scipy.spatial.distance import correlation


class Comparer:
    
    def __init__(self, directory: str, threshold=3.0):
        self._dir = directory
        self._mfccs = {}
        self._lock = Lock()
        self._threshold = threshold

    def _load_thread(self, filename: str):
        print(f"processing {filename}")

        y, sr = librosa.load(filename)
        mfcc = librosa.feature.mfcc(y, sr)
        with self._lock:
            self._mfccs[filename] = mfcc

    def load(self):
        all_files = []
        for root, _, files in os.walk(self._dir):
            for f in files:
                if f.endswith(".wav"):
                    all_files.append(os.path.join(root, f))
        print(f"found {len(all_files)} files")

        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            for f in all_files:
                executor.submit(self._load_thread, f)

        print("Initialization done")
        return len(all_files)

    @staticmethod
    def _compare_thread(mfcc, f_mfcc):
        dist, _, _, _ = accelerated_dtw(mfcc.T, f_mfcc.T, dist=correlation)
        return dist

    def compare(self, filename: str):
        y, sr = librosa.load(filename)
        mfcc = librosa.feature.mfcc(y, sr)
        
        min_dist = 999999.0
        matched_filename = None
        future_results = {}
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            for f, f_mfcc in self._mfccs.items():
                future_results[f] = executor.submit(self._compare_thread, mfcc, f_mfcc)

        for f, dist in future_results.items():
            result = dist.result()
            print(f"dist of {f}: {result}")
            if result < min_dist:
                min_dist = result
                matched_filename = f

        if matched_filename and min_dist <= self._threshold:
            print(f"Matched {matched_filename} with dist {min_dist}")
            return matched_filename

        print("No match")
        return None


if __name__ == "__main__":
    c = Comparer("commands")
    c.load()
    c.compare("tmp/internet.wav")
