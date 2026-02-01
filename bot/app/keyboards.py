from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📘 О занятиях", callback_data="menu:about")],
        [InlineKeyboardButton(text="🧪 Мини-диагностика", callback_data="menu:diag")],
        [InlineKeyboardButton(text="🗓 Записаться в группу", callback_data="lead:start")],
        [InlineKeyboardButton(text="📝 Проверка ДЗ", callback_data="hw:start")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="menu:reviews")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="menu:faq")],
        [InlineKeyboardButton(text="💬 Задать вопрос", callback_data="support:ask")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:home")]
    ])


def support_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗓 Записаться", callback_data="lead:start")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:home")]
    ])


def lead_class_kb() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="1–4", callback_data="lead:class:1-4"),
        InlineKeyboardButton(text="5–8", callback_data="lead:class:5-8"),
        InlineKeyboardButton(text="9", callback_data="lead:class:9"),
        InlineKeyboardButton(text="10", callback_data="lead:class:10"),
        InlineKeyboardButton(text="11", callback_data="lead:class:11"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])


def lead_goal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Подтянуть успеваемость", callback_data="lead:goal:improve")],
        [InlineKeyboardButton(text="🧩 Подготовка к ОГЭ", callback_data="lead:goal:oge")],
        [InlineKeyboardButton(text="🎯 Подготовка к ЕГЭ", callback_data="lead:goal:ege")],
    ])


def lead_time_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌤 Утро", callback_data="lead:time:morning")],
        [InlineKeyboardButton(text="☀️ День", callback_data="lead:time:day")],
        [InlineKeyboardButton(text="🌙 Вечер", callback_data="lead:time:evening")],
    ])


def lead_finish_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить заявку", callback_data="lead:submit")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:home")],
    ])


def hw_class_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1–4", callback_data="hw:class:1-4"),
         InlineKeyboardButton(text="5–8", callback_data="hw:class:5-8")],
        [InlineKeyboardButton(text="9", callback_data="hw:class:9"),
         InlineKeyboardButton(text="10", callback_data="hw:class:10"),
         InlineKeyboardButton(text="11", callback_data="hw:class:11")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:home")],
    ])


def hw_topic_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Алгебра", callback_data="hw:topic:algebra")],
        [InlineKeyboardButton(text="📐 Геометрия", callback_data="hw:topic:geometry")],
        [InlineKeyboardButton(text="📊 Текстовые задачи", callback_data="hw:topic:word")],
        [InlineKeyboardButton(text="🎓 Экзамен (ОГЭ/ЕГЭ)", callback_data="hw:topic:exam")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:home")],
    ])


def admin_lead_actions(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin:lead:ok:{lead_id}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"admin:lead:no:{lead_id}"),
        ]
    ])


def admin_hw_actions(hw_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принято", callback_data=f"admin:hw:accept:{hw_id}"),
            InlineKeyboardButton(text="🔁 На доработку", callback_data=f"admin:hw:rework:{hw_id}"),
        ],
        [
            InlineKeyboardButton(text="💬 Комментарий", callback_data=f"admin:hw:comment:{hw_id}")
        ],
    ])
