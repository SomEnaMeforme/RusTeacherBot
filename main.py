import logging
import os
from typing import Dict, List, Optional
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

import config
from datetime import datetime

from answer_creator import AnswerCreator
from botstats import User, Session, Message, get_db_session, get_session_statistics
from audio_transcriber import AudioTranscriber


logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot: Bot = Bot(token=config.BOTTOKEN)
dp: Dispatcher = Dispatcher()
transcriber = AudioTranscriber(bot, language=config.LANGUAGE, sample_rate=config.SAMPLE_RATE)
interlocutor = AnswerCreator()
active_sessions: Dict[int, int] = {}


def error_check(text: str) -> tuple[bool, str]:
    """
    Returns: (has_error: bool, error_description: str)
    """
    return False, ""


def get_keyboard() -> ReplyKeyboardMarkup:
    kb: List[List[KeyboardButton]] = [
        [KeyboardButton(text="Завершить диалог")],
        [KeyboardButton(text="Показать статистику")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@dp.message(F.voice)
async def voice_message_handler(message: types.Message) -> None:
    user_id: int = message.from_user.id
    db = get_db_session()
    
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            user = User(telegram_id=user_id, username=message.from_user.username)
            db.add(user)
            db.commit()
        
        if user_id not in active_sessions:
            session = Session(user_id=user.id)
            db.add(session)
            db.commit()
            active_sessions[user_id] = session.id
        
        voice = await transcriber.load_audio_from_message(message)
        text, success = transcriber.transcribe_audio(voice)
        
        has_errors, error_description = error_check(text)
        answer = create_answer(text)
        
        session_id = active_sessions[user_id]
        messages = [
            Message(
                session_id=session_id,
                content=text,
                is_user=True,
                has_errors=has_errors,
                error_description=error_description
            ),
            Message(
                session_id=session_id,
                content=answer,
                is_user=False
            )
        ]
        
        db.add_all(messages)
        db.commit()
        
        response_text = answer
        if not success:
            response_text = f"🎙️ {text}"
        elif has_errors:
            response_text = f"⚠️ {error_description}\n\n{answer}"
        path_to_voice = transcriber.text_to_audio(response_text, message)
        voice_file = FSInputFile(path=path_to_voice)
        await message.answer_voice(voice=voice_file)
        os.remove(path_to_voice)
        
    except Exception as e:
        logger.error(f"Error processing voice message: {str(e)}")
        await message.reply("Произошла ошибка при обработке голосового сообщения.", 
                          reply_markup=get_keyboard())
    finally:
        db.close()


@dp.message(F.text == "Завершить диалог")
async def end_dialog(message: types.Message) -> None:
    user_id: int = message.from_user.id
    if user_id in active_sessions:
        db = get_db_session()
        session = db.query(Session).get(active_sessions[user_id])
        session.end_time = datetime.utcnow()
        db.commit()
        del active_sessions[user_id]
        await message.reply("Диалог завершен.", reply_markup=get_keyboard())
    else:
        await message.reply("Активный диалог не найден.", reply_markup=get_keyboard())


@dp.message(F.text == "Показать статистику")
async def show_statistics(message: types.Message) -> None:
    user_id: int = message.from_user.id
    stats: Optional[Dict[str, any]] = get_session_statistics(user_id)

    if not stats:
        await message.reply("Статистика отсутствует.", reply_markup=get_keyboard())
        return

    stats_text = f"📊 Статистика:\n\n"
    stats_text += f"📝 Всего сессий: {stats['total_sessions']}\n"
    stats_text += f"💬 Всего сообщений: {stats['total_messages']}\n"
    stats_text += f"❌ Количество ошибок: {stats['total_errors']}\n"
    stats_text += f"📈 Процент ошибок: {stats['error_rate']:.1f}%\n"

    await message.reply(stats_text, reply_markup=get_keyboard())

def create_answer(message: str) -> str:
    return interlocutor.create_answer(message)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())