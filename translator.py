import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
from langdetect import detect
import os
import tempfile
from pydub import AudioSegment


class PortableSpeechTranslator:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def convert_to_wav(self, audio_file):
        """
        Convert audio to WAV format if it's not already WAV.
        Returns path to WAV file.
        """
        base, ext = os.path.splitext(audio_file)
        ext = ext.lower()
        if ext != '.wav':
            wav_file = base + ".wav"
            audio = AudioSegment.from_file(audio_file)
            audio.export(wav_file, format="wav")
            return wav_file
        return audio_file

    def transcribe_audio(self, audio_file):
        """Convert speech to text from an audio file."""
        try:
            wav_file = self.convert_to_wav(audio_file)  # convert first
            with sr.AudioFile(wav_file) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            print(f"Error in transcribe_audio: {e}")
            return None

    def detect_language(self, text):
        """Detect the language of the given text."""
        try:
            return detect(text)
        except Exception as e:
            print(f"Language detection error: {e}")
            return "unknown"

    def translate_text(self, text, target_lang):
        """Translate text to the target language using GoogleTranslator."""
        try:
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            return translated
        except Exception as e:
            print(f"Translation error: {e}")
            return None

    def text_to_speech(self, text, lang_code, output_path=None):
        """Convert text to speech and save as an audio file."""
        try:
            supported_langs = ['af', 'ar', 'bn', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo',
                               'es', 'et', 'fi', 'fr', 'gu', 'hi', 'hr', 'hu', 'id', 'is', 'it', 'ja',
                               'jw', 'kn', 'ko', 'la', 'lv', 'mk', 'ml', 'mr', 'my', 'ne', 'nl', 'no',
                               'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw', 'ta',
                               'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-CN', 'zh-TW']

            if lang_code not in supported_langs:
                print(f"TTS does not support language code: {lang_code}")
                return None

            tts = gTTS(text=text, lang=lang_code)
            if not output_path:
                output_path = tempfile.mktemp(suffix=".mp3")
            tts.save(output_path)
            return output_path
        except Exception as e:
            print(f"TTS error: {e}")
            return None

    def process_speech(self, audio_file, target_lang_code):
        """
        Full pipeline: transcribe audio, detect source language,
        translate text, and generate translated speech audio.
        """
        original_text = self.transcribe_audio(audio_file)
        if not original_text:
            print("No speech could be transcribed.")
            return None

        detected_lang = self.detect_language(original_text)
        translated_text = self.translate_text(original_text, target_lang_code)
        if not translated_text:
            print("Translation failed.")
            return None

        base, _ = os.path.splitext(audio_file)
        translated_audio_path = f"{base}_translated_{target_lang_code}.mp3"
        tts_path = self.text_to_speech(translated_text, target_lang_code, translated_audio_path)
        if not tts_path:
            print("Failed to generate translated audio.")
            return None

        return {
            'original_text': original_text,
            'detected_language': detected_lang,
            'translated_text': translated_text,
            'target_language': target_lang_code,
            'translated_audio_file': translated_audio_path.replace("\\", "/")
        }
