# ai-voice-bot
A simple voice dialogue web application where a user can talk to an AI voice agent through a microphone, and the agent replies in real time. Using Deepgram for speech-to-text, OpenAI GPT-4o for respose generation and Elevenlabs for text-to-speech conversion.


## Setup and Execution Instructions

#### Install dependencies

Install the project dependencies.

```bash
pip install -r requirements.txt
```

#### Edit the config file

Enter your API keys in the .env file.

```js
DEEPGRAM_API_KEY=%api_key%
ELEVENLABS_API_KEY=%api_key%
OPENAI_API_KEY=%api_key%
```

#### Run the application

You need to run both app.py (port 8000) and app_socketio.py (port 5001). Once running, you can access the application in your browser at <http://127.0.0.1:8000>

```bash
python app.py
python app_socketio.py
```

## Technical Decisions and Challanges

- Why Socket.IO? Socket.IO enables real-time, bidirectional communication between the client and the server.
- Why Flask? Flask is a lightweight and flexible web framework that allows you to build applications quickly.
- Parameters in Deepgram: Utterance rate and is_final flag mimicing VAD for end of user's turn detection.
- Prompt engineering for GPT-4o: Used a brief instruction and kept the default values for temperature, max tokens or frequency penalty.

### Challenges

- Silero VAD: Inconsistent speech probability on local and web voice acitivity
- Sending audio stream chunks to client side (js): Documentation of Elevenlabs is not comprehensive enough
- Wrong start: It was challenging to test the idea and sdk'S locally and then to adapt the project to a server-client architecture

