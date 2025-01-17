import os
import shutil
import subprocess
import sounddevice as sd
import queue
import vosk
import json
import threading
import requests
from openai import OpenAI
import google.generativeai as genai

# Load configuration from config.json
with open("config.json", "r") as file:
    config = json.load(file)

# Vosk model setup
script_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(script_dir, "models")

# Ensure the 'models' directory is cleared and recreated
if os.path.exists(models_dir):
    print("Clearing existing 'models' directory to ensure the latest version.")
    shutil.rmtree(models_dir)  # Remove the existing directory
os.makedirs(models_dir, exist_ok=True)  # Recreate the directory

# Check if a model download URL is provided
if config["options"]["vosk_model_download_url"]:
    print("Model download URL found. Please download the model manually.")
    print("1. Visit the following URL to download the model:")
    print("   " + config["options"]["vosk_model_download_url"])
    print("2. Extract the contents of the downloaded file into the 'models' directory.")
    print("3. Restart the add-on.")
    exit(1)

# Automatically find the first model folder in the 'models' directory
available_models = [f for f in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, f))]
if not available_models:
    raise FileNotFoundError("No models found in the 'models' directory. Please add a model and restart.")

# Use the first available model
model_name = available_models[0]
model_path = os.path.join(models_dir, model_name)

samplerate = config["options"]["vosk_samplerate"]
model = vosk.Model(model_path)
recognizer = vosk.KaldiRecognizer(model, samplerate)

# Queues for audio and commands
audio_queue = queue.Queue()
command_queue = queue.Queue()
openai_client = OpenAI(api_key=config["options"]["ai_model_token"])

# Timer for returning to active listening
timeout_timer = None

def reset_timeout(callback, timeout=60):
    """Resets or starts a timer to return to active listening."""
    global timeout_timer
    if timeout_timer:
        timeout_timer.cancel()
    timeout_timer = threading.Timer(timeout, callback)
    timeout_timer.start()

def return_to_listening():
    """Function to return to active listening after timeout."""
    print("Idle time is over. Returning to active listening.")
    global active
    active = False

def call_homeassistant_service(entity_id):
    """Calls a Home Assistant service for a button press."""
    url = f"{config['options']['homeassistant_url']}/api/services/button/press"
    headers = {
        "Authorization": f"Bearer {config['options']['token']}",
        "Content-Type": "application/json",
    }
    data = {"entity_id": entity_id}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Command sent to Home Assistant for {entity_id}.")
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error calling Home Assistant: {e}")

def speak_via_homeassistant(text):
    """Text-to-speech using Home Assistant."""
    url = f"{config['options']['homeassistant_url']}/api/services/tts/speak"
    headers = {
        "Authorization": f"Bearer {config['options']['token']}",
        "Content-Type": "application/json",
    }
    data = {
        "media_player_entity_id": config["options"]["media_player"],
        "message": text,
        "cache": False,
        "entity_id": config["options"]["tts_entity"]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("Text successfully sent to Home Assistant.")
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error connecting to Home Assistant: {e}")

def handle_command(text):
    """Handles commands dynamically based on config."""
    for command in config["options"]["commands"]:
        if any(phrase in text for phrase in command["phrases"]):
            entity_id = command["entity_id"]
            print(f"Triggering entity_id: {entity_id}")
            call_homeassistant_service(entity_id)
            speak_via_homeassistant(f"Executing command for {entity_id}.")
            return True
    return False

def ask_ai_model(question):
    """Queries the AI model based on the configuration."""
    ai_model = config.get("ai_model", "openai")
    if ai_model == "openai":
        return ask_chatgpt(question)
    elif ai_model == "gemini":
        return ask_gemini(question)
    else:
        print("Unsupported AI model specified in configuration.")
        speak_via_homeassistant("The specified AI model is not supported.")

def ask_gemini(question):
    """Send a query to Google Generative AI (Gemini)."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(question)
        answer = response.text
        print(f"Gemini: {answer}")
        speak_via_homeassistant(answer)  # Speak the response
        return answer
    except Exception as e:
        print(f"Error querying Gemini: {e}")
        speak_via_homeassistant("An error occurred while querying Gemini.")
        return "Error contacting the Gemini server."

def ask_chatgpt(prompt):
    """Send a query to ChatGPT via OpenAI API."""
    try:
        # Create a request to GPT-4 or GPT-3.5
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Or "gpt-3.5-turbo"
            store=True,
            messages=[
                {"role": "system", "content": "You are an assistant answering questions."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        print(f"ChatGPT: {answer}")
        speak_via_homeassistant(answer)
        return answer
    except Exception as e:
        print(f"Error querying ChatGPT: {e}")
        return "Error contacting the OpenAI API."

def audio_processing():
    """Continuous audio processing."""
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype="int16",
                           channels=1, callback=lambda indata, frames, time, status: audio_queue.put(bytes(indata))):
        print("Listening... Say activation phrase to activate.")
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get('text', '').lower()
                if text:
                    command_queue.put(text)

def command_handler():
    """Handles recognized commands."""
    global active
    active = False
    while True:
        reset_timeout(return_to_listening, timeout=config["options"]["timeouts"]["return_to_listening"])
        text = command_queue.get()
        print(f"Recognized text: {text}")

        if not active:
            if any(phrase in text for phrase in config["options"]["activation_phrases"]):
                print("Activated. Listening for your commands.")
                active = True
        else:
            if any(phrase in text for phrase in config["options"]["deactivation_phrases"]):
                print("Deactivating.")
                active = False
                continue
            if handle_command(text):
                continue
            if any(phrase in text for phrase in config["options"]["ai_question_phrases"]):
                print("Listening for your question.")
                speak_via_homeassistant("Please, ask your question.")
                question = command_queue.get()
                ask_ai_model(question)
            else:
                print(f"Unknown command: {text}")
                speak_via_homeassistant(f"Unknown command: {text}")

def main():
    """Main function"""
    audio_thread = threading.Thread(target=audio_processing, daemon=True)
    audio_thread.start()
    command_handler()

if __name__ == "__main__":
    main()
