import numpy as np
import torch
torch.set_num_threads(1)
import pyaudio
from silero_vad import load_silero_vad
import os
import wave

model = load_silero_vad()
audio = pyaudio.PyAudio()


# Taken from utils_vad.py
def validate(model,
             inputs: torch.Tensor):
    with torch.no_grad():
        outs = model(inputs)
    return outs

# Provided by Alexander Veysov
def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()  # depends on the use case
    return sound

def kill_stream():
    audio.terminate()


def detect_voice():
    
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    SAMPLE_RATE = 16000
    CHUNK = int(SAMPLE_RATE / 2)

    num_samples = 512

    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    data = []
    voiced_confidences = []

    silence = 0
    speech = False
    #print("Started Recording")
    audio_buffer = b''

    while silence<70:
        
        audio_chunk = stream.read(num_samples)
        
        # in case you want to save the audio later
        #int_audio = (np.array(audio_chunk) * 32767).astype(np.int16)
        data.append(audio_chunk)
        audio_buffer+=audio_chunk
        
        audio_int16 = np.frombuffer(audio_chunk, np.int16)

        audio_float32 = int2float(audio_int16)
        
        # get the confidences and add them to the list to plot them later
        new_confidence = model(torch.from_numpy(audio_float32), 16000).item()
        #timestamp = get_speech_timestamps(audio_int16, model=model)
        voiced_confidences.append(new_confidence)
        if speech and new_confidence < 0.5:
            silence+=1
        if new_confidence >= 0.5:
            silence=0
            speech = True

        
    #print("Stopped the recording")


    output_file = os.path.join("audio", f"recording.wav")
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_buffer)

    stream.stop_stream()    # "Stop Audio Recording
    stream.close()          # "Close Audio Recording
    #audio.terminate()
    
#if __name__ == "__main__":
#    detect_voice()