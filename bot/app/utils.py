import re

FAQ_PATTERNS = [
    (re.compile(r"\b(цена|сколько\s+стоит|стоимость|оплата)\b", re.I), "menu:faq"),
    (re.compile(r"\b(расписани|когда\s+занятия|время|дни)\b", re.I), "menu:about"),
    (re.compile(r"\b(отзыв|результат|кейсы)\b", re.I), "menu:reviews"),
    (re.compile(r"\b(запис|хочу\s+заниматься|как\s+попасть)\b", re.I), "lead:start"),
    (re.compile(r"\b(дз|домашк|провер(ить|ка))\b", re.I), "hw:start"),
]


def classify_message(text: str) -> str | None:
    t = (text or "").strip()
    if not t:
        return None
    for pattern, action in FAQ_PATTERNS:
        if pattern.search(t):
            return action
    return None
