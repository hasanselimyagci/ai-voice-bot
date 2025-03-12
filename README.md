# ai-voice-bot
A simple voice dialogue web application where a user can talk to an AI voice agent through a microphone, and the agent replies in real time. Using Deepgram for speech-to-text, OpenAI GPT-4o for respose generation and Elevenlabs for text-to-speech conversion.

#### Install dependencies

Install the project dependencies.

```bash
pip install -r requirements.txt
```

#### Edit the config file

Copy the code from `sample.env` and create a new file called `.env`. Paste in the code and enter your API key you generated in the [Deepgram console](https://console.deepgram.com/).

```js
DEEPGRAM_API_KEY=%api_key%
```

#### Run the application

You need to run both app.py (port 8000) and app_socketio.py (port 5001). Once running, you can access the application in your browser at <http://127.0.0.1:8000>

```bash
python app.py
python app_socketio.py
```
