import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
    WebAppInfo,
)

from config import BOT_TOKEN
from storage import get_user_day, advance_user_day, reset_user_day
from workouts import WARMUP, WORKOUTS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


WELCOME_TEXT = (
    "Привет! Я твой тренировочный бот \U0001f4aa\n\n"
    "Программа рассчитана на 90 дней (9 циклов по 10 дней).\n"
    "Нажимай кнопку каждый день — я пришлю разминку и тренировку.\n\n"
    "Условия: дома, гриф 17 кг.\n"
    "Отдых между подходами: 3–5 минут.\n\n"
    "Поехали \U0001f447"
)

DONE_TEXT = "Отлично! Увидимся на следующей тренировке \U0001f4aa"


# Mini App URL for Telegram WebApp
WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:8080")


# ============================================================
# Callback data
# ============================================================

class DayCallback(CallbackData, prefix="day"):
    action: str  # "train" | "explain" | "done" | "main"
    day: int = 0


# ============================================================
# Keyboards
# ============================================================

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu with workout button + Mini App button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="\U0001f4aa Получить тренировку дня",
                callback_data=DayCallback(action="main", day=0).pack()
            )],
            [InlineKeyboardButton(
                text="\U0001f4ca Статистика и календарь",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )],
        ]
    )


def workout_keyboard(day: int) -> InlineKeyboardMarkup:
    """Keyboard under the workout message.
    Training days: show both "explain" and "done" buttons.
    Rest days: show only "done" button.
    Day 10: show only "done" button.
    """
    day_data = WORKOUTS[day]
    buttons = []

    # Show "explain" button only for training days with explanations
    if not day_data["is_rest"] and day_data["explanations"] is not None:
        buttons.append([InlineKeyboardButton(
            text="\U0001f4d6 Как делать упражнения",
            callback_data=DayCallback(action="explain", day=day).pack()
        )])

    # Done button text differs for rest vs training days
    done_text = "\u2705 Понял" if day_data["is_rest"] else "\u2705 Готово"
    buttons.append([InlineKeyboardButton(
        text=done_text,
        callback_data=DayCallback(action="done", day=day).pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_keyboard(day: int) -> InlineKeyboardMarkup:
    """Keyboard inside the explanations view."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="\u2b05\ufe0f Назад к тренировке",
                callback_data=DayCallback(action="train", day=day).pack()
            )],
        ]
    )


# ============================================================
# Command handlers
# ============================================================

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(WELCOME_TEXT, reply_markup=get_main_keyboard())


@dp.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Handle /reset command."""
    reset_user_day(message.from_user.id)
    await message.answer(
        "\U0001f504 Прогресс сброшен! Твой следующий день — День 1 \U0001f4aa",
        reply_markup=get_main_keyboard()
    )


# ============================================================
# Callback handlers
# ============================================================

@dp.callback_query(DayCallback.filter(F.action == "main"))
async def callback_main(callback: CallbackQuery) -> None:
    """Handle "get workout" button."""
    user_id = callback.from_user.id
    current_day = get_user_day(user_id)
    day_data = WORKOUTS[current_day]

    if not day_data["is_rest"]:
        await callback.message.answer(WARMUP)

    await callback.message.answer(
        day_data["workout"],
        reply_markup=workout_keyboard(current_day)
    )

    advance_user_day(user_id)
    await callback.answer()


@dp.callback_query(DayCallback.filter(F.action == "explain"))
async def show_explanations(callback: CallbackQuery, callback_data: DayCallback) -> None:
    """Show exercise explanations."""
    day = callback_data.day
    day_data = WORKOUTS[day]

    if day_data["explanations"] is None:
        await callback.answer("Нет объяснений для этого дня")
        return

    await callback.message.edit_text(
        day_data["explanations"],
        reply_markup=back_keyboard(day)
    )
    await callback.answer()


@dp.callback_query(DayCallback.filter(F.action == "train"))
async def back_to_workout(callback: CallbackQuery, callback_data: DayCallback) -> None:
    """Return from explanations to workout card."""
    day = callback_data.day
    day_data = WORKOUTS[day]

    await callback.message.edit_text(
        day_data["workout"],
        reply_markup=workout_keyboard(day)
    )
    await callback.answer()


@dp.callback_query(DayCallback.filter(F.action == "done"))
async def callback_done(callback: CallbackQuery, callback_data: DayCallback) -> None:
    """Handle "done" button."""
    from storage import record_completion
    user_id = callback.from_user.id
    record_completion(user_id, callback_data.day)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(DONE_TEXT, reply_markup=get_main_keyboard())
    await callback.answer()


# ============================================================
# WebApp data handler (Mini App)
# ============================================================

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message) -> None:
    """Handle data sent from Telegram Mini App."""
    data = message.web_app_data.data
    await message.answer(
        f"Данные из Mini App получены: {data}",
        reply_markup=get_main_keyboard()
    )


# ============================================================
# Main
# ============================================================

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
