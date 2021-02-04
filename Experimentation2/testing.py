import librosa
import sounddevice as sd
import matplotlib.pyplot as plt
import soundfile as sf
import pyaudio
import numpy as np

into = r'results\result.wav'

sampling_rate = 16000

def soundplot(stream):
    data = np.fromstring(stream.read(sampling_rate),dtype=np.int16)
    return data

def load_wav(duration):
    da=[]
    p=pyaudio.PyAudio()
    stream=p.open(format=pyaudio.paInt16,channels=1,rate=sampling_rate,input=True)
    for i in range(duration):
        #if i%10==0: print(i) 
        print(i)
        d=soundplot(stream)
        da.append(soundplot(stream)) 
    stream.stop_stream()
    stream.close()
    p.terminate()
    print('Recording Completed')
    return np.array(da).reshape(-1)

sound = load_wav(5)
sound = sound.astype(np.float)
sf.write('testerFile.wav',sound,16000)
print(sound)