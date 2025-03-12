import logging
import torch
import os
import numpy as np
import base64
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    DeepgramClientOptions
)
import openai
import elevenlabs
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
import datetime

load_dotenv()

app_socketio = Flask("app_socketio")
socketio = SocketIO(app_socketio, cors_allowed_origins=['http://127.0.0.1:8000'])

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Configurations 
config = DeepgramClientOptions(
    verbose=logging.WARN,  # logging.INFO or logging.DEBUG
    options={"keepalive": "true"}
)
deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
gpt_client = openai.Client(api_key=OPENAI_API_KEY)
el_client = ElevenLabs(api_key= ELEVENLABS_API_KEY)

dg_connection = None

def log(log: str):
    """Print and write to status.txt"""
    print(log)
    with open("log_file.txt", "a+") as f:
        f.write(log)

def gpt_response(prompt):
    """Send a prompt from to OpenAI API and return the response"""
    log('Generating AI response')
    response = gpt_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ],
        model="gpt-4o-mini",
    )
    return response.choices[0].message.content    
    

def initialize_deepgram_connection():
    global dg_connection
    # Initialize Deepgram client and connection
    dg_connection = deepgram.listen.live.v("1")
    global user_sentence
    global silence
    global context
    silence = 0
    user_sentence = ""
    context = """Soracagim sorulari sadece 1-2 cümlede cevaplandir. Egelenceli bir karakter ol."""
    
    def on_open(self, open, **kwargs):
        log(f"\n\n{open}\n\n")
        socketio.emit('transcription_update', {'transcription': "Listening..."})

    def on_message(self, result, **kwargs):
        global user_sentence
        global silence
        global context
        transcript = result.channel.alternatives[0].transcript
        if silence <= 2 and len(transcript) > 0:
            silence = 0
            socketio.emit("audio_stop", {"info": "Interference.."})
            log(result.channel.alternatives[0].transcript)
            socketio.emit('transcription_update', {'transcription': "Listening..."})
            if result.is_final:
                user_sentence = user_sentence + " " + transcript
            
        if len(user_sentence) > 0 and len(transcript) <= 0: 
                silence+=1
        
        if silence>2:
            silence = 0
            with open("convo_history.txt", "a+", encoding="utf-8") as f:
                dt = datetime.datetime.now()
                f.write(f"\n{dt} --- USER: {user_sentence[1:]}")
            socketio.emit('transcription_update', {'transcription': "Thinking..."}) 
            context += f"\nSoru: {user_sentence}\nCevap: "   
            response = gpt_response(context)
            user_sentence = ""
            with open("convo_history.txt", "a+", encoding="utf-8") as f:
                dt = datetime.datetime.now()
                f.write(f"\n{dt} --- BOT: {response}")
            context += response
            socketio.emit('transcription_update', {'transcription': "Speaking..."})
            send_audio_stream(response)
            

    def on_close(self, close, **kwargs):
        log(f"\n\n{close}\n\n")

    def on_error(self, error, **kwargs):
        log(f"\n\n{error}\n\n")

    dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    # Define the options for the live transcription
    options = LiveOptions(model="nova-2", language="tr", utterance_end_ms="1000", interim_results=True)

    if dg_connection.start(options) is False: # THIS CAUSES ERROR
        log("Failed to start connection")
        exit()

@socketio.on('audio_stream')
def handle_audio_stream(data):
    if dg_connection:
        dg_connection.send(data)


@socketio.on('toggle_transcription')
def handle_toggle_transcription(data):
    log("toggle_transcription", data)
    socketio.emit('transcription_update', {'transcription': ":)"})
    action = data.get("action")
    if action == "start":
        log("Starting Deepgram connection")
        initialize_deepgram_connection()

@socketio.on('connect')
def server_connect():
    log('Client connected')

@socketio.on('restart_deepgram')
def restart_deepgram():
    log('Restarting Deepgram connection')
    initialize_deepgram_connection()

@socketio.on('speak')
def send_audio_stream(response):
    """Generate speech from gpt-response and send the stream to client side"""
    log('Generating the speech')
    audio = el_client.text_to_speech.convert(
            text=response,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_turbo_v2_5",
            language_code="tr",
        )
    buf = b''
    for chunk in audio:
        if isinstance(chunk, bytes):
            buf+= chunk
    print(len(buf))
    socketio.emit("audio_chunks", {"audio": buf})
                    
        
if __name__ == '__main__':
    logging.info("Starting SocketIO server.")
    socketio.run(app_socketio, debug=True, allow_unsafe_werkzeug=True, port=5001)
