import librosa
import soundfile as sf
import sounddevice as sd
import time
import matplotlib.pyplot as plt

def read_file(path):
    audio,samples = librosa.load(path,sr=44100)
    print(audio)
    return audio,samples

if __name__=='__main__':
    audio,sample_rate = read_file('noisyAudio.wav') 
    plt.plot(audio)
    plt.show()