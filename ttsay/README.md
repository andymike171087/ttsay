# Voice Assistant TTSay

Voice Assistant TTSay is a Home Assistant add-on that integrates with Vosk for speech recognition and Home Assistant for automation control. It allows you to control your smart home devices and interact with AI models like OpenAI's GPT or Gemini via voice commands.

---

## Installation

### Add the repository to Home Assistant

1. Go to your Home Assistant Add-on Store.
2. Add this repository:
   [`https://github.com/andymike171087/ttsay`](https://github.com/andymike171087/ttsay)

   [![Open your Home Assistant instance and show the dashboard of a Supervisor add-on.](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=ttsay&repository_url=https%3A%2F%2Fgithub.com%2Fandymike171087%2Fttsay)

### Install the add-on

1. After adding the repository, find the **TTSay Voice Assistant** add-on in the store.
2. Install the add-on.

---

## Configuration

### Required Options

You need to configure the following options in the add-on:

```json
{
  "homeassistant_url": "http://homeassistant.local:8123",
  "token": "your_long_lived_access_token",
  "tts_entity": "tts.google_translate_uk_com",
  "media_player": "media_player.your_device",
  "vosk_model_path": "models/vosk-model-small-en-us-0.15",
  "vosk_model_download_url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
  "vosk_samplerate": 16000,
  "ai_model": "openai",
  "ai_model_token": "your_openai_api_key",
  "activation_phrases": ["hey assistant", "activate assistant"],
  "deactivation_phrases": ["stop", "enough", "pause"],
  "ai_question_phrases": ["question", "can you answer", "listen"],
  "commands": [
    {
      "phrases": ["start vacuum", "turn on vacuum"],
      "entity_id": "button.start_vacuum"
    },
    {
      "phrases": ["stop vacuum", "turn off vacuum"],
      "entity_id": "button.stop_vacuum"
    }
  ],
  "timeouts": {
    "return_to_listening": 60
  }
}
```

### How to Obtain Required Values

1. **Home Assistant Token**:  
   Go to your Home Assistant user profile and generate a **Long-Lived Access Token**.
2. **TTS Entity**:  
   Use the entity ID of your TTS integration, such as `tts.google_translate_uk_com`.
3. **Media Player**:  
   Use the entity ID of the media player where you want the assistant to speak.
4. **Vosk Model Path and Download URL**:  
   Go to the [Vosk Models page](https://alphacephei.com/vosk/models), right-click on the model name (e.g., "vosk-model-small-en-us-0.15"), and copy its download link.  
   Paste the link into the `vosk_model_download_url` option and the model name into the `vosk_model_path`.

---

## Usage

### Starting the Add-on

1. After installation, go to the **TTSay Voice Assistant** add-on page.
2. Configure the add-on options as described above.
3. Start the add-on.

### Testing Voice Commands

1. Speak the activation phrase (e.g., "Hey Assistant").
2. Give commands or ask questions.

---

## Notes

- If you don't provide a custom model URL, the add-on will use the default English model pre-packaged with the add-on.
- The assistant runs continuously, listening for activation phrases.

---

## Troubleshooting

- Ensure the `vosk_model_path` matches the folder structure in the `/config/addons/` directory.
- Verify your Home Assistant token and URLs.
- Check the add-on logs for errors.

