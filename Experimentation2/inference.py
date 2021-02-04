import os
import sys
import pyaudio
import numpy as np
import subprocess
import soundfile as sf
import librosa
from tqdm import tqdm
import audio.audio_utils as audio
import audio.hparams as hp
from models import *
import torch
import matplotlib.pyplot as plt

# Initialize the global variables
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
sampling_rate = 16000

def soundplot(stream):
    data = np.fromstring(stream.read(sampling_rate),dtype=np.float32)
    return data

def load_wav(duration):
    da=[]
    p=pyaudio.PyAudio()
    stream=p.open(format=pyaudio.paFloat32,channels=1,rate=sampling_rate,input=True)
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

def get_spec(wav):

    # Compute STFT using librosa
    stft = librosa.stft(y=wav, n_fft=hp.hparams.n_fft_den,
                        hop_length=hp.hparams.hop_size_den, win_length=hp.hparams.win_size_den).T
    stft = stft[:-1]														# Tx257

    # Decompose into magnitude and phase representations
    mag = np.abs(stft)
    mag = audio.db_from_amp(mag)
    phase = audio.angle(stft)

    # Normalize the magnitude and phase representations
    norm_mag = audio.normalize_mag(mag)
    norm_phase = audio.normalize_phase(phase)

    # Concatenate the magnitude and phase representations
    spec_ip = np.concatenate((norm_mag, norm_phase), axis=1)				# Tx514

    return spec_ip


def crop_mels(start_idx, noisy_wav):

    end_idx = start_idx + 3200

    # Get the segmented wav (0.2 second)
    noisy_seg_wav = noisy_wav[start_idx: end_idx]
    if len(noisy_seg_wav) != 3200:
        return None

    # Compute the melspectrogram using librosa
    spec = audio.melspectrogram(
        noisy_seg_wav, hp.hparams).T          		# 16x80
    spec = spec[:-1]

    return spec


def get_segmented_mels(start_idx, noisy_wav):

    mels = []
    if start_idx - 1280 < 0:
        return None

    # Get the overlapping continuous segments of noisy mels
    for i in range(start_idx, start_idx + hp.hparams.wav_step_size, 640):
        m = crop_mels(i - 1280, noisy_wav)
        if m is None or m.shape[0] != hp.hparams.mel_step_size:
            return None
        mels.append(m.T)

    mels = np.asarray(mels)

    return mels


def generate_video(stft, resulFile):

    # Reconstruct the predicted wav
    mag = stft[:257, :]
    phase = stft[257:, :]

    denorm_mag = audio.unnormalize_mag(mag)
    denorm_phase = audio.unnormalize_phase(phase)
    recon_mag = audio.amp_from_db(denorm_mag)
    complex_arr = audio.make_complex(recon_mag, denorm_phase)
    wav = librosa.istft(complex_arr, hop_length=hp.hparams.hop_size_den,
                        win_length=hp.hparams.win_size_den)

    # Create the folder to save the results
    result_dir = resulFile
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    # Save the wav file
    audio_output = os.path.join(result_dir, 'result.wav')
    sf.write(audio_output, wav, sampling_rate)

    print("Saved the denoised audio file:", audio_output)
    return


def load_model(combModel):

    model = Model()
    print("Loaded model from: ", combModel)

    if not torch.cuda.is_available():
        checkpoint = torch.load(combModel, map_location='cpu')
    else:
        checkpoint = torch.load(combModel)

    ckpt = {}
    for key in checkpoint['state_dict'].keys():
        if key.startswith('module.'):
            k = key.split('module.', 1)[1]
        else:
            k = key
        ckpt[k] = checkpoint['state_dict'][key]
    model.load_state_dict(ckpt)
    model = model.to(device)

    return model.eval()


def load_lipsync_model(lipsModel):

    lipsync_student = Lipsync_Student()

    if not torch.cuda.is_available():
        lipsync_student_checkpoint = torch.load(
            lipsModel, map_location='cpu')
    else:
        lipsync_student_checkpoint = torch.load(
            lipsModel)

    ckpt = {}
    for key in lipsync_student_checkpoint['state_dict'].keys():
        if key.startswith('module.'):
            k = key.split('module.', 1)[1]
        else:
            k = key
        ckpt[k] = lipsync_student_checkpoint['state_dict'][key]
    lipsync_student.load_state_dict(ckpt)
    lipsync_student = lipsync_student.to(device)

    return lipsync_student.eval()


def predict(duration,lipsModel,combModel,batchSize,resulFile):

    # Load the input wav
    inp_wav = load_wav(duration)
    print('#'*80)
    print('input file loaded')
    print('#'*80)
    print("Input wav: ", inp_wav.shape)
    inp_wav = inp_wav.astype(float)
    plt.plot(inp_wav)
    plt.show()
    sf.write('testerFile.wav', inp_wav, sampling_rate)

    total_steps = inp_wav.shape[0]
    # return inp_wav

    # Get the windows of 1 second wav step segments with a small overlap
    id_windows = [range(i, i + hp.hparams.wav_step_size) for i in range(1280, total_steps,
                                                                         hp.hparams.wav_step_size - hp.hparams.wav_step_overlap) if (i + hp.hparams.wav_step_size <= total_steps)]

    # Load the student lipsync model
    lipsync_student = load_lipsync_model(lipsModel)

    # Load the model
    model = load_model(combModel)

    generated_stft = None
    all_spec_batch = []
    all_mel_batch = []
    skip = False
    for i, window in enumerate(id_windows):

        start_idx = window[0]
        end_idx = start_idx + hp.hparams.wav_step_size

        # Segment the wav (1 second window)
        wav = inp_wav[start_idx: end_idx]

        # Get the corresponding input noisy melspectrograms
        spec_window = get_spec(wav)
        if(spec_window.shape[0] != hp.hparams.spec_step_size):
            skip = True
            break
        all_spec_batch.append(spec_window)

        # Get the melspectrogram for lipsync model
        mel_window = get_segmented_mels(start_idx, inp_wav)
        if(mel_window is None):
            skip = True
            break

        mel_window = np.expand_dims(mel_window, axis=1)
        all_mel_batch.append(mel_window)

    if skip == True or len(all_spec_batch) == 0 or len(all_mel_batch) == 0:
        return None

    all_spec_batch = np.array(all_spec_batch)

    all_mel_batch = np.array(all_mel_batch)

    if all_spec_batch.shape[0] != all_mel_batch.shape[0]:
        return None

    print("Total input segment windows: ", all_spec_batch.shape[0])

    pred_stft = []
    for i in tqdm(range(0, all_spec_batch.shape[0], batchSize)):

        mel_batch = all_mel_batch[i:i+batchSize]
        spec_batch = all_spec_batch[i:i+batchSize]

        # Convert to torch tensors
        inp_mel = torch.FloatTensor(mel_batch).to(device)
        inp_stft = torch.FloatTensor(spec_batch).to(device)

        # Predict the faces using the student lipsync model
        with torch.no_grad():
            faces = lipsync_student(inp_mel)

        # Predict the spectrograms for the corresponding window
        with torch.no_grad():
            pred = model(inp_stft, faces)

        # Detach from gpu
        pred = pred.cpu().numpy()

        pred_stft.extend(pred)

    print("Successfully predicted for all the windows")

    # Convert to numpy array
    pred_stft = np.array(pred_stft)

    # Concatenate all the predictions
    steps = int(hp.hparams.spec_step_size -
                ((hp.hparams.wav_step_overlap/640) * 4))

    if pred_stft.shape[0] == 1:
        generated_stft = pred_stft[0].T
    else:
        generated_stft = pred_stft[0].T[:, :steps]

    for i in range(1, pred_stft.shape[0]):
        # Last batch
        if i == pred_stft.shape[0]-1:
            generated_stft = np.concatenate(
                (generated_stft, pred_stft[i].T), axis=1)
        else:
            generated_stft = np.concatenate(
                (generated_stft, pred_stft[i].T[:, :steps]), axis=1)

    if generated_stft is not None:
        generate_video(generated_stft, resulFile)
    else:
        print("Oops! Couldn't denoise the input file!")


if __name__ == '__main__':
    
    durationR = 5
    lipsModel = r'lipsync\checkpoints\lipsync_student.pth'
    combModel = r'checkpoints\denoising.pt'
    batchSize = 32
    resulFile = r'results'
    inputFile = r'inputs'

    predict(durationR,lipsModel,combModel,batchSize,resulFile)
    # print(sound)
