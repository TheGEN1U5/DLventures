from google import genai
from google.genai import types
from dotenv import load_dotenv
import base64
import io
import wave
import json
import re
load_dotenv()

# Configure Gemini
client = genai.Client()

def init_chat():
    with open("sys_instruc.txt") as f:
        sys_instruc=f.read()
    config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=500),
            system_instruction=sys_instruc
        )
    chat = client.chats.create(model="gemini-2.5-flash", config=config)
    return chat

def get_reply(chat, message):
    response = chat.send_message(message)
    return response.text

def pcm_to_wav_base64(pcm_bytes, sample_rate=24000, channels=1, sample_width=2):
    # Create a WAV in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)

    wav_bytes = buffer.getvalue()
    return base64.b64encode(wav_bytes).decode('utf-8')

def get_audio(text):

    contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=text),
                ],
            ),
        ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1.3,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Umbriel"
                )
            )
        ),
    )
    response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=contents,
    config=generate_content_config
    )
    b64_audio = pcm_to_wav_base64(response.candidates[0].content.parts[0].inline_data.data)
    return b64_audio


def send_voice_to_chat(chat, audio_bytes):
    response = chat.send_message(types.Part.from_bytes(
      data=audio_bytes,
      mime_type='audio/webm',
    ))

    return response.text

def get_result(chat, target):
    response = chat.send_message(f"END, the emotion was {target}. Send your response as a dictionary with 3 keys 'emotion_felt', one word answer for the emotion you actually felt, 'reasoning' the reasoning why you felt that emotion include your critiques here the good and bad the user did, 'score' the final score generated according to system instruction")
    cleaned = re.sub(r'^```json\s*|\s*```$', '', response.text.strip())
    return json.loads(cleaned)

