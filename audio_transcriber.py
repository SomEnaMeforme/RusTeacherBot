import logging
from typing import  Tuple
import soundfile as sf
import speech_recognition as sr
from aiogram import types
import whisper
import pathlib
import os
import torch
from aiogram.client.bot import Bot

logger = logging.getLogger(__name__)
FRAMES_PER_SECOND = 44100


class AudioTranscriber:

    def __init__(self, bot: Bot, language: str = 'ru-RU', sample_rate: int = 16000):
        self.bot = bot
        self.language = language
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()
        self.modelSST = whisper.load_model("large")
        self.modelTTS, _ = torch.hub.load(
            'snakers4/silero-models',
            'silero_tts',
            language='ru',
            speaker='v3_1_ru',
            trust_repo=True
        )

    async def load_audio_from_message(self, message: types.Message) -> str:
        try:
            file_id = message.voice.file_id
            file = await self.bot.get_file(file_id)
            file_extension = os.path.splitext(file.file_path)[1]

            voice_file_name = f"{file_id}{file_extension}"
            open(voice_file_name, 'a').close()
            await self.bot.download_file(file.file_path, destination=voice_file_name)

            wav_path = self.convert_to_wav(voice_file_name, file_id)

            os.remove(voice_file_name)

            return wav_path
        except Exception as e:
            logger.error(f"Error loading audio: {str(e)}")
            raise

    def convert_to_wav(self, audio_file_name: str, file_id: str):
        data, samplerate = sf.read(audio_file_name)
        wav_path = f"{file_id}.wav"
        open(wav_path, 'a').close()
        sf.write(wav_path, data, samplerate, format='WAV', subtype='PCM_16')
        dir = pathlib.Path().resolve()
        return os.path.join(dir, wav_path)

    def transcribe_audio(self, voice_file: str) -> Tuple[str, bool]:
        """
        Transcribe audio to text
        Returns: (transcribed_text: str, success: bool)
        """
        try:
                text: str = self.modelSST.transcribe(voice_file)['text']
                os.remove(voice_file)
                return text, True
        except sr.UnknownValueError:
            return "Не удалось распознать речь", False
        except sr.RequestError as e:
            error_msg = f"Ошибка сервера распознавания: {str(e)}"
            logger.error(error_msg)
            return error_msg, False
        except Exception as e:
            logger.error(f"Unexpected error in transcription: {str(e)}")
            return "Произошла непредвиденная ошибка при обработке аудио", False

    def text_to_audio(self, text: str, message: types.Message):
        file_id = message.voice.file_id
        audio_tensor = self.modelTTS.apply_tts(text=text)
        audio_numpy = audio_tensor.numpy()
        wav_path = f"{file_id}_answer.ogg"
        open(wav_path, 'a').close()
        sf.write(wav_path, audio_numpy, self.sample_rate, format='OGG')
        dir = pathlib.Path().resolve()
        return os.path.join(dir, wav_path)