import io
import logging
from typing import BinaryIO, Tuple
import librosa
import soundfile as sf
import speech_recognition as sr
from aiogram import types
from aiogram.client.bot import Bot

logger = logging.getLogger(__name__)


class AudioTranscriber:

    def __init__(self, bot: Bot, language: str = 'ru-RU', sample_rate: int = 16000):
        self.bot = bot
        self.language = language
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()

    async def load_audio_from_message(self, message: types.Message) -> BinaryIO:
        try:
            with io.BytesIO() as voice_message:
                file_info = await self.bot.get_file(message.voice.file_id)
                await self.bot.download_file(file_info.file_path, destination=voice_message)
                sound_data, sample_rate = librosa.load(voice_message, sr=self.sample_rate)
            
            voice_file = io.BytesIO()
            sf.write(voice_file, sound_data, sample_rate, format='WAV', subtype='PCM_16')
            voice_file.seek(0)
            return voice_file
        except Exception as e:
            logger.error(f"Error loading audio: {str(e)}")
            raise

    def transcribe_audio(self, voice: BinaryIO) -> Tuple[str, bool]:
        """
        Transcribe audio to text
        Returns: (transcribed_text: str, success: bool)
        """
        try:
            with sr.AudioFile(voice) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=self.language)
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