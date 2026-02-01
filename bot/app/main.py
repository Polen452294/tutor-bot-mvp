import asyncio
from datetime import datetime
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import User, Lead, Homework
from app import texts
from app.keyboards import (
    main_menu, back_to_menu, support_menu,
    lead_class_kb, lead_goal_kb, lead_time_kb, lead_finish_kb,
    hw_class_kb, hw_topic_kb,
    admin_lead_actions, admin_hw_actions,
)
from app.utils import classify_message


# ---------------- FSM ----------------

class SupportStates(StatesGroup):
    waiting_question = State()


class LeadStates(StatesGroup):
    student_class = State()
    goal = State()
    time_pref = State()
    contact = State()
    confirm = State()


class HomeworkStates(StatesGroup):
    student_class = State()
    topic = State()
    waiting_payload = State()


class AdminStates(StatesGroup):
    waiting_hw_comment = State()  # stores hw_id


# ---------------- helpers ----------------

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


async def db_session() -> AsyncSession:
    return SessionLocal()


async def upsert_user(session: AsyncSession, message: Message):
    tg_id = message.from_user.id
    user = await session.get(User, tg_id)
    if not user:
        user = User(
            tg_id=tg_id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        session.add(user)
        await session.commit()


async def notify_admins(bot: Bot, text: str, reply_markup=None):
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # не ломаем поток из-за недоступного админа
            pass


# ---------------- bot ----------------

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with SessionLocal() as s:
        await upsert_user(s, message)
    await message.answer(texts.WELCOME, reply_markup=main_menu())


# ---- MENU callbacks ----

@dp.callback_query(F.data == "menu:home")
async def cb_home(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text(texts.WELCOME, reply_markup=main_menu())
    await query.answer()


@dp.callback_query(F.data == "menu:about")
async def cb_about(query: CallbackQuery):
    await query.message.edit_text(texts.ABOUT, reply_markup=back_to_menu(), parse_mode=ParseMode.MARKDOWN)
    await query.answer()


@dp.callback_query(F.data == "menu:reviews")
async def cb_reviews(query: CallbackQuery):
    await query.message.edit_text(texts.REVIEWS, reply_markup=back_to_menu(), parse_mode=ParseMode.MARKDOWN)
    await query.answer()


@dp.callback_query(F.data == "menu:faq")
async def cb_faq(query: CallbackQuery):
    await query.message.edit_text(texts.FAQ_TEXT, reply_markup=support_menu(), parse_mode=ParseMode.MARKDOWN)
    await query.answer()


# ---- mini-diagnostic (MVP: быстрый “продающий” вариант) ----
@dp.callback_query(F.data == "menu:diag")
async def cb_diag(query: CallbackQuery):
    txt = (
        "🧪 *Мини-диагностика (1 минута)*\n\n"
        "Ответьте честно — я подскажу, какая группа подойдёт.\n\n"
        "1) Какая цель?\n"
        "— подтянуть оценки\n"
        "— ОГЭ\n"
        "— ЕГЭ\n\n"
        "Нажмите *Записаться* — и в заявке укажите цель и класс 🙂"
    )
    await query.message.edit_text(txt, reply_markup=support_menu(), parse_mode=ParseMode.MARKDOWN)
    await query.answer()


# ---------------- SUPPORT: ask a question ----------------

@dp.callback_query(F.data == "support:ask")
async def cb_support_ask(query: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_question)
    await query.message.edit_text(texts.ASK_QUESTION_HINT, reply_markup=back_to_menu())
    await query.answer()


@dp.message(SupportStates.waiting_question)
async def support_question(message: Message, state: FSMContext, bot: Bot):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Напишите вопрос текстом одним сообщением 🙂")
        return

    await state.clear()
    user = message.from_user
    admin_text = (
        "💬 *Вопрос от ученика*\n\n"
        f"От: {user.full_name} (@{user.username or '—'})\n"
        f"ID: `{user.id}`\n\n"
        f"Текст:\n{text}"
    )
    await notify_admins(bot, admin_text)
    await message.answer("✅ Принято! Я отвечу вам в ближайшее время.", reply_markup=main_menu())


# ---------------- LEAD: enrollment ----------------

@dp.callback_query(F.data == "lead:start")
async def lead_start(query: CallbackQuery, state: FSMContext):
    await state.set_state(LeadStates.student_class)
    await query.message.edit_text(
        "🗓 *Запись в группу*\n\nВыберите класс ученика:",
        reply_markup=lead_class_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await query.answer()


@dp.callback_query(LeadStates.student_class, F.data.startswith("lead:class:"))
async def lead_class(query: CallbackQuery, state: FSMContext):
    student_class = query.data.split(":")[-1]
    await state.update_data(student_class=student_class)
    await state.set_state(LeadStates.goal)
    await query.message.edit_text(
        "🎯 Какая цель занятий?",
        reply_markup=lead_goal_kb(),
    )
    await query.answer()


@dp.callback_query(LeadStates.goal, F.data.startswith("lead:goal:"))
async def lead_goal(query: CallbackQuery, state: FSMContext):
    goal_code = query.data.split(":")[-1]
    goal_map = {"improve": "подтянуть успеваемость", "oge": "ОГЭ", "ege": "ЕГЭ"}
    await state.update_data(goal=goal_map.get(goal_code, goal_code))
    await state.set_state(LeadStates.time_pref)
    await query.message.edit_text(
        "🕒 Когда удобнее заниматься?",
        reply_markup=lead_time_kb(),
    )
    await query.answer()


@dp.callback_query(LeadStates.time_pref, F.data.startswith("lead:time:"))
async def lead_time(query: CallbackQuery, state: FSMContext):
    time_code = query.data.split(":")[-1]
    time_map = {"morning": "утро", "day": "день", "evening": "вечер"}
    await state.update_data(time_pref=time_map.get(time_code, time_code))
    await state.set_state(LeadStates.contact)
    await query.message.edit_text(
        "📱 Оставьте контакт для связи (например, номер или @ник).\n"
        "Можно просто отправить @username, если так удобнее.",
        reply_markup=back_to_menu(),
    )
    await query.answer()


@dp.message(LeadStates.contact)
async def lead_contact(message: Message, state: FSMContext):
    contact = (message.text or "").strip()
    if not contact:
        await message.answer("Напишите контакт текстом 🙂")
        return
    await state.update_data(contact=contact)
    data = await state.get_data()
    await state.set_state(LeadStates.confirm)

    summary = (
        "✅ *Проверьте заявку*\n\n"
        f"Класс: *{data['student_class']}*\n"
        f"Цель: *{data['goal']}*\n"
        f"Время: *{data['time_pref']}*\n"
        f"Контакт: `{data['contact']}`\n\n"
        "Если всё верно — отправляйте."
    )
    await message.answer(summary, reply_markup=lead_finish_kb(), parse_mode=ParseMode.MARKDOWN)


@dp.callback_query(LeadStates.confirm, F.data == "lead:submit")
async def lead_submit(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    async with SessionLocal() as s:
        lead = Lead(
            tg_id=query.from_user.id,
            student_class=data["student_class"],
            goal=data["goal"],
            time_pref=data["time_pref"],
            contact=data.get("contact"),
            status="new",
        )
        s.add(lead)
        await s.commit()
        await s.refresh(lead)

    admin_text = (
        "📥 *Новая заявка*\n\n"
        f"От: {query.from_user.full_name} (@{query.from_user.username or '—'})\n"
        f"ID: `{query.from_user.id}`\n\n"
        f"Класс: *{data['student_class']}*\n"
        f"Цель: *{data['goal']}*\n"
        f"Время: *{data['time_pref']}*\n"
        f"Контакт: `{data.get('contact')}`\n"
        f"Заявка: `#{lead.id}`"
    )
    await notify_admins(bot, admin_text, reply_markup=admin_lead_actions(lead.id))
    await query.message.edit_text(texts.LEAD_DONE, reply_markup=main_menu())
    await query.answer()


# ---------------- HOMEWORK: submit + admin actions ----------------

@dp.callback_query(F.data == "hw:start")
async def hw_start(query: CallbackQuery, state: FSMContext):
    await state.set_state(HomeworkStates.student_class)
    await query.message.edit_text(texts.HW_START, reply_markup=hw_class_kb(), parse_mode=ParseMode.MARKDOWN)
    await query.answer()


@dp.callback_query(HomeworkStates.student_class, F.data.startswith("hw:class:"))
async def hw_class(query: CallbackQuery, state: FSMContext):
    student_class = query.data.split(":")[-1]
    await state.update_data(student_class=student_class)
    await state.set_state(HomeworkStates.topic)
    await query.message.edit_text("📌 Выберите тему:", reply_markup=hw_topic_kb())
    await query.answer()


@dp.callback_query(HomeworkStates.topic, F.data.startswith("hw:topic:"))
async def hw_topic(query: CallbackQuery, state: FSMContext):
    topic_code = query.data.split(":")[-1]
    topic_map = {
        "algebra": "алгебра",
        "geometry": "геометрия",
        "word": "текстовые задачи",
        "exam": "ОГЭ/ЕГЭ",
    }
    await state.update_data(topic=topic_map.get(topic_code, topic_code))
    await state.set_state(HomeworkStates.waiting_payload)
    await query.message.edit_text(
        "Отправьте ДЗ одним сообщением:\n"
        "— текст\n"
        "— или фото\n"
        "— или файл (pdf/word/картинка)\n\n"
        "Можно добавить подпись: где застряли / что не понятно.",
        reply_markup=back_to_menu(),
    )
    await query.answer()


@dp.message(HomeworkStates.waiting_payload)
async def hw_payload(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    payload_type = "text"
    payload_text = None
    file_id = None
    caption = None

    if message.photo:
        payload_type = "photo"
        file_id = message.photo[-1].file_id
        caption = message.caption
    elif message.document:
        payload_type = "document"
        file_id = message.document.file_id
        caption = message.caption
    else:
        payload_text = message.text

    async with SessionLocal() as s:
        hw = Homework(
            tg_id=message.from_user.id,
            student_class=data["student_class"],
            topic=data["topic"],
            payload_type=payload_type,
            payload_text=payload_text,
            file_id=file_id,
            caption=caption,
            status="new",
            admin_comment=None,
            updated_at=datetime.utcnow(),
        )
        s.add(hw)
        await s.commit()
        await s.refresh(hw)

    # notify admins with forwarded-like content
    header = (
        "📝 *Новое ДЗ*\n\n"
        f"От: {message.from_user.full_name} (@{message.from_user.username or '—'})\n"
        f"ID: `{message.from_user.id}`\n"
        f"Класс: *{data['student_class']}*\n"
        f"Тема: *{data['topic']}*\n"
        f"ДЗ: `#{hw.id}`\n"
    )

    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, header, parse_mode=ParseMode.MARKDOWN)
            if payload_type == "photo":
                await bot.send_photo(admin_id, file_id, caption=caption or "—")
            elif payload_type == "document":
                await bot.send_document(admin_id, file_id, caption=caption or "—")
            else:
                await bot.send_message(admin_id, payload_text or "—")
            await bot.send_message(admin_id, "Действия:", reply_markup=admin_hw_actions(hw.id))
        except Exception:
            pass

    await state.clear()
    await message.answer(texts.HW_DONE, reply_markup=main_menu())


# ---------------- ADMIN actions ----------------

@dp.callback_query(F.data.startswith("admin:lead:"), F.from_user.func(lambda u: u.id in settings.admin_ids))
async def admin_lead_action(query: CallbackQuery):
    _, _, action, lead_id = query.data.split(":")
    lead_id = int(lead_id)

    async with SessionLocal() as s:
        lead = await s.get(Lead, lead_id)
        if not lead:
            await query.answer("Заявка не найдена", show_alert=True)
            return

        new_status = "approved" if action == "ok" else "rejected"
        lead.status = new_status
        await s.commit()

    # notify user
    try:
        if action == "ok":
            await query.bot.send_message(
                lead.tg_id,
                "✅ Заявка подтверждена!\n\nЯ напишу вам детали по группе и времени занятий.",
                reply_markup=main_menu(),
            )
        else:
            await query.bot.send_message(
                lead.tg_id,
                "Спасибо за заявку! Сейчас подходящих мест нет 😔\n"
                "Я могу предложить другое время/формат — напишите, пожалуйста, в ответ.",
                reply_markup=main_menu(),
            )
    except Exception:
        pass

    await query.answer("Готово ✅")


@dp.callback_query(F.data.startswith("admin:hw:"), F.from_user.func(lambda u: u.id in settings.admin_ids))
async def admin_hw_action(query: CallbackQuery, state: FSMContext):
    _, _, action, hw_id = query.data.split(":")
    hw_id = int(hw_id)

    if action == "comment":
        await state.set_state(AdminStates.waiting_hw_comment)
        await state.update_data(hw_id=hw_id)
        await query.message.answer(f"💬 Напишите комментарий для ДЗ #{hw_id} одним сообщением.")
        await query.answer()
        return

    async with SessionLocal() as s:
        hw = await s.get(Homework, hw_id)
        if not hw:
            await query.answer("ДЗ не найдено", show_alert=True)
            return

        if action == "accept":
            hw.status = "accepted"
            text_user = "✅ ДЗ проверено: *Принято*.\n\nЕсли хотите — отправьте следующее 🙂"
        else:
            hw.status = "rework"
            text_user = "🔁 ДЗ проверено: *Нужно доработать*.\n\nЕсли хотите — отправьте исправленную версию."
        hw.updated_at = datetime.utcnow()
        await s.commit()

    try:
        await query.bot.send_message(hw.tg_id, text_user, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())
    except Exception:
        pass

    await query.answer("Статус отправлен ✅")


@dp.message(AdminStates.waiting_hw_comment, F.from_user.func(lambda u: u.id in settings.admin_ids))
async def admin_hw_comment(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Комментарий должен быть текстом 🙂")
        return

    data = await state.get_data()
    hw_id = int(data["hw_id"])

    async with SessionLocal() as s:
        hw = await s.get(Homework, hw_id)
        if not hw:
            await message.answer("ДЗ не найдено.")
            await state.clear()
            return

        hw.admin_comment = text
        hw.updated_at = datetime.utcnow()
        await s.commit()

    try:
        await message.bot.send_message(
            hw.tg_id,
            f"💬 *Комментарий по ДЗ #{hw_id}*\n\n{text}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu(),
        )
    except Exception:
        pass

    await state.clear()
    await message.answer("Комментарий отправлен ✅")


# ---------------- fallback: auto-answers ----------------

@dp.message(F.text)
async def any_text(message: Message, state: FSMContext):
    # если пользователь в FSM — не мешаем
    if await state.get_state() is not None:
        return

    action = classify_message(message.text or "")
    if action == "menu:faq":
        await message.answer(texts.FAQ_TEXT, reply_markup=support_menu(), parse_mode=ParseMode.MARKDOWN)
        return
    if action == "menu:about":
        await message.answer(texts.ABOUT, reply_markup=back_to_menu(), parse_mode=ParseMode.MARKDOWN)
        return
    if action == "menu:reviews":
        await message.answer(texts.REVIEWS, reply_markup=back_to_menu(), parse_mode=ParseMode.MARKDOWN)
        return
    if action == "lead:start":
        await message.answer("Ок, давайте запишемся 👇", reply_markup=main_menu())
        return
    if action == "hw:start":
        await message.answer("Ок, отправим ДЗ на проверку 👇", reply_markup=main_menu())
        return

    await message.answer(texts.UNKNOWN_TEXT, reply_markup=support_menu())


async def main():
    await init_db()
    bot = Bot(
    settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())