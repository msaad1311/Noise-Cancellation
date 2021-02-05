import librosa
import sounddevice as sd
import matplotlib.pyplot as plt
import soundfile as sf
import pyaudio
import numpy as np
import math
from sklearn.preprocessing import MinMaxScaler

into = r'results\result.wav'
sampling_rate = 16000
chunk = int(sampling_rate/20)

def soundplot(stream):
    data = np.fromstring(stream.read(chunk),dtype=np.float32)
    return data

def start_strem(duration):
    da=[]
    p=pyaudio.PyAudio()
    stream=p.open(format=pyaudio.paFloat32,channels=1,rate=sampling_rate,
                  input=True,frames_per_buffer=chunk)
    
    for i in range(0,int(sampling_rate/chunk * duration)):
        #if i%10==0: print(i) 
        print(i)
        # d=soundplot(stream)
        da.append(soundplot(stream)) 
    stream.stop_stream()
    stream.close()
    p.terminate()
    print('Recording Completed')
    return np.array(da).reshape(-1)

def get_noise_from_sound(signal,noise,SNR):
    RMS_s=math.sqrt(np.mean(signal**2))
    print('rms of signal:',RMS_s)
    #required RMS of noise
    RMS_n=math.sqrt(RMS_s**2/(pow(10,SNR/10)))
    print('rms of noise:',RMS_n)
    
    #current RMS of noise
    RMS_n_current=math.sqrt(np.mean(noise**2))
    print('rms of noise2:',RMS_n_current)
    print('factor:',RMS_n/RMS_n_current )
    noise=noise*(RMS_n/RMS_n_current)
    
    return noise

def scaled(inputs,ranges):
    scaler = MinMaxScaler(feature_range=ranges)
    foo = scaler.fit_transform(inputs.reshape(-1,1))
    return foo,scaler

def mixer(clean,noisy,snr,scaler):
    if(len(noisy)>len(clean)):
        noisy=noisy[0:len(clean)] 
    sf.write('noiseTester0.wav',noisy,16000)
    noisy = get_noise_from_sound(clean,noisy,SNR=snr)
    sf.write('noiseTester1.wav',noisy,16000)
    sf.write('cleanTester0.wav',clean,16000)
    mixed = clean+noisy
    sf.write('mixedTester0.wav',mixed,16000)
    if scaler != None:
        mixed = scaler.inverse_transform(mixed)
    return mixed

cleanAudio1 = start_strem(5)
print('#'*80)
print('input file loaded')
print('#'*80)
print("Input wav: ", cleanAudio1.shape)

noiseAudio,sampleRate = librosa.load(r'audio\dogBarking.wav',sr=16000)
cleanAudio,cleanScaler = scaled(cleanAudio1,(-1,1))
noiseAudio,noiseScaler = scaled(noiseAudio,(-1,1))

inp_wav = mixer(cleanAudio,noiseAudio,20,None)