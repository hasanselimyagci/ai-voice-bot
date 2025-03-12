import os
from os import PathLike
from time import time
import datetime
import asyncio
from typing import Union
import openai
from dotenv import load_dotenv
from deepgram import Deepgram
import pygame
from pygame import mixer
import elevenlabs
from elevenlabs.client import ElevenLabs
import pyaudio
from vad import detect_voice, kill_stream

load_dotenv()

# Initialize APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
deepgram = Deepgram(DEEPGRAM_API_KEY)
gpt_client = openai.Client(api_key=OPENAI_API_KEY)
el_client = ElevenLabs(api_key= ELEVENLABS_API_KEY)

mixer.init() # mixer is a pygame module for playing audio
pa = pyaudio.PyAudio() # save temp audio stream

context = "Sen, bir Türkçe sesli asistan olarak çalışacak şekilde yapılandırıldın. Görevin, kullanıcılardan gelen Türkçe soruları anlamak ve OpenAI GPT-4 modelini kullanarak doğru ve anlamlı cevaplar üretmektir. Cevapların her zaman anlaşılır ve doğal olmalıdır. Kullanıcıdan gelen her türlü soruya, olabildiğince kısa ve öz cevaplar vermeye odaklan. Eğer bir soruyu anlamıyorsan, kullanıcıdan ek bilgi iste. Ayrıca, bilmediğin bir konuda tahminde bulunmaktan kaçın ve sadece emin olduğun konularda cevap ver. Lütfen her zaman Türkçe yaz ve konuş, dil bilgisine dikkat et. Sadece bilgilendirici ve yararlı içerik üretmeye çalış."
conversation = {"Conversation": []}
RECORDING_PATH = "audio/recording.wav"


def request_gpt(prompt: str) -> str:
    """Send a prompt to the OpenAI API and return the response.
    Args:
        - state: The current state of the app.
        - prompt: The prompt to send to the API.
    Returns:
        The response from the API.
    """
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


async def transcribe(file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]):
    """Transcribe audio using Deepgram API.
    Args:
        - file_name: The name of the file to transcribe.
    Returns:
        The response from the API.
    """
    with open(file_name, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        options = {"model": "nova-2", "language":"tr-TR"}
        response = await deepgram.transcription.prerecorded(source, options=options)
        return response["results"]["channels"][0]["alternatives"][0]["words"]
    

def log(log: str):
    """Print and write to status.txt"""
    print(log)
    with open("log_file.txt", "a+") as f:
        f.write(log)


if __name__ == "__main__":
    while True:
        # Record audio
        log("Listening...")
        detect_voice()
        log("Done listening")

        # Transcribe audio
        current_time = time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        words = loop.run_until_complete(transcribe(RECORDING_PATH))
        string_words = " ".join(
            word_dict.get("word") for word_dict in words if "word" in word_dict
        )
        if "kapat" in string_words:
            log("Chat is ended by user")
            break
        transcription_time = time() - current_time
        log(f"Finished transcribing in {transcription_time:.2f} seconds.")

        # Add user part to convo history
        with open("conv_history.txt", "a", encoding='utf-8') as f:
            dt = datetime.datetime.now()
            f.write(f"\n{dt} --- USER: {string_words}")

        # Get response from gpt
        current_time = time()
        context += f"\nSoru: {string_words}\nCevap: "
        response = request_gpt(context)
        context += response
        gpt_time = time() - current_time
        log(f"Finished generating response in {gpt_time:.2f} seconds.")

        # Convert response to audio
        current_time = time()
        audio = el_client.text_to_speech.convert(
            text=response,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_turbo_v2_5",
            language_code="tr",
            optimize_streaming_latency=1
        )
        elevenlabs.save(audio, "audio/response.wav")
        audio_time = time() - current_time
        log(f"Finished generating audio in {audio_time:.2f} seconds.")

        ## Play response
        log("Speaking...")
        sound = mixer.Sound("audio/response.wav")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))

        ## Add bot response to convo history
        with open("conv_history.txt", "a", encoding="utf-8") as f:
            dt = datetime.datetime.now()
            f.write(f"\n{dt} --- BOT: {response}")
        log(f"\n --- USER: {string_words}\n --- BOT: {response}\n")

    kill_stream()