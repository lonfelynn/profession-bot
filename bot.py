import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import DB_Manager
from config import token, database

bot = telebot.TeleBot(token)
db = DB_Manager(database)


user_states = {}



def pretty_interaction(level: int) -> str:
    """Человекочитаемое описание уровня общения (0-2)."""
    if level == 0:
        return "🟦 Низкая необходимость общения — работа преимущественно самостоятельная"
    if level == 1:
        return "🟩 Умеренный уровень общения — сочетание индивидуальной работы и командного взаимодействия"
    if level == 2:
        return "🟥 Высокий уровень общения — постоянная работа с людьми/клиентами"
    return "—"

def pretty_education(level: int) -> str:
    """Человекочитаемое описание уровня образования (0-3)."""
    mapping = {
        0: "0 — Образование не требуется (самообучение, практика)",
        1: "1 — Курсы / колледж / профессиональное обучение",
        2: "2 — Университет (бакалавриат / магистратура)",
        3: "3 — PhD / докторантура"
    }
    return mapping.get(level, "—")



def make_reply_keyboard(button_texts, row_width=2, resize=True, one_time=True):
    kb = types.ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=resize, one_time_keyboard=one_time)
    buttons = [types.KeyboardButton(text=t) for t in button_texts]
    kb.add(*buttons)
    return kb

def start_menu_keyboard():
    return make_reply_keyboard(["📘 Пройти тест", "🔁 Сменить профессию", "ℹ️ Про профессию"], row_width=1)



def _send_professions_list(chat_id, results):
    if not results:
        bot.send_message(chat_id, "Ничего не найдено по вашим критериям.")
        return

    lines = []
    ikb = InlineKeyboardMarkup()
    for pid, name, desc in results:
        lines.append(f"🔹 *{name}*\n_{desc}_")
        
        btn_view = InlineKeyboardButton(text="Подробнее", callback_data=f"viewprof:{pid}")
        btn_rate = InlineKeyboardButton(text="Оценить", callback_data=f"rate:{pid}")
        ikb.add(btn_view, btn_rate)

    text = "Найденные профессии:\n\n" + "\n\n".join(lines)
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=ikb)


@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    user_states[user_id] = {"stage": "awaiting_name", "data": {}}

    bot.send_message(
        message.chat.id,
        "👋 <b>Привет!</b>\n\n"
        "Я — <b>ПрофГайд Бот</b> 🤖✨\n"
        "Помогу подобрать профессию, сменить карьеру или узнать о специальности.\n\n"
        "<i>Давай познакомимся! Как тебя зовут?</i>",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "📘 <b>Справка</b>\n\n"
        "Вот что я умею:\n\n"
        "🔹 <b>Пройти тест</b> — подберу профессии по интересам и стилю работы.\n"
        "🔹 <b>Сменить профессию</b> — подскажу варианты при смене сферы и с учётом готовности учиться.\n"
        "🔹 <b>Узнать про профессию</b> — покажу подробности (требования, образование, путь).\n"
        "🔹 <b>Оставить отзыв</b> — скажи, подошла ли профессия.\n\n"
        "Используй кнопки — так удобнее 😊",
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    state = user_states.get(user_id)

    if not state:
        user_states[user_id] = {"stage": "awaiting_name", "data": {}}
        bot.send_message(message.chat.id, "Привет! Как тебя зовут?")
        return

    stage = state["stage"]

    if stage == "awaiting_name":
        if not text:
            bot.send_message(message.chat.id, "Напиши, пожалуйста, своё имя (текстом).")
            return
        state["data"]["name"] = text
        state["stage"] = "awaiting_age"
        bot.send_message(message.chat.id, f"Приятно познакомиться, {text}! Сколько тебе лет?")
        return

    if stage == "awaiting_age":
        try:
            age = int(text)
        except Exception:
            bot.send_message(message.chat.id, "Пожалуйста, введи возраст числом (например: 16).")
            return
        state["data"]["age"] = age


        try:
            if hasattr(db, "add_user"):
                db.add_user(user_id, state["data"]["name"], age)
        except Exception as e:
            print("warning: add_user failed:", e)

        state["stage"] = "menu"
        bot.send_message(message.chat.id, "Отлично! Чем хочешь заняться?", reply_markup=start_menu_keyboard())
        return

    if stage == "menu":
        if text == "📘 Пройти тест":
            kb = make_reply_keyboard(["Нравится", "Нейтрально", "Не люблю"], row_width=1)
            bot.send_message(message.chat.id, "Как ты относишься к общению с людьми?", reply_markup=kb)
            state["stage"] = "test_interaction"
            return

        if text == "🔁 Сменить профессию":
            categories = []
            try:
                categories = db.get_all_categories()
            except Exception as e:
                print("warning: get_all_categories failed:", e)

            if not categories:
                bot.send_message(message.chat.id, "В базе пока нет категорий.")
                return
            kb = make_reply_keyboard(categories, row_width=1)
            bot.send_message(message.chat.id, "В какой сфере ты сейчас работаешь? (выбери категорию)", reply_markup=kb)
            state["stage"] = "change_current_field"
            return

        if text == "ℹ️ Про профессию":
            categories = []
            try:
                categories = db.get_all_categories()
            except Exception as e:
                print("warning: get_all_categories failed:", e)

            if not categories:
                bot.send_message(message.chat.id, "В базе пока нет категорий.")
                return
            kb = make_reply_keyboard(categories, row_width=1)
            bot.send_message(message.chat.id, "Выбери категорию, чтобы посмотреть профессии:", reply_markup=kb)
            state["stage"] = "info_choose_category"
            return

        bot.send_message(message.chat.id, "Выбери опцию из меню:", reply_markup=start_menu_keyboard())
        return

    
    if stage == "test_interaction":
        mapping = {"не люблю": 0, "нейтрально": 1, "нравится": 2}
        key = text.lower()
        if key not in mapping:
            bot.send_message(message.chat.id, "Пожалуйста, выбери один из вариантов кнопками.")
            return
        state["data"]["interaction_level"] = mapping[key]

        try:
            categories = db.get_all_categories()
        except Exception as e:
            print("warning: get_all_categories failed:", e)
            categories = []

        if not categories:
            bot.send_message(message.chat.id, "В базе пока нет категорий.")
            state["stage"] = "menu"
            return

        kb = make_reply_keyboard(categories, row_width=1)
        bot.send_message(message.chat.id, "Выбери категорию, которая тебе нравится:", reply_markup=kb)
        state["stage"] = "test_category"
        return

    if stage == "test_category":
        try:
            categories = db.get_all_categories()
        except Exception:
            categories = []

        if text not in categories:
            bot.send_message(message.chat.id, "Пожалуйста, выбери категорию кнопкой.")
            return
        state["data"]["category"] = text

        try:
            reqs = db.get_all_requirements(category=text)
        except Exception as e:
            print("warning: get_all_requirements failed:", e)
            reqs = []

        if not reqs:
            results = db.find_professions(interaction_level=state["data"]["interaction_level"], category=text)
            _send_professions_list(message.chat.id, results)
            state["stage"] = "menu"
            bot.send_message(message.chat.id, "Готово — вернулись в меню.", reply_markup=start_menu_keyboard())
            return

        kb = make_reply_keyboard(reqs, row_width=1)
        bot.send_message(message.chat.id, "Выбери навык/требование, которое тебе ближе:", reply_markup=kb)
        state["stage"] = "test_requirement"
        return

    if stage == "test_requirement":
        try:
            reqs = db.get_all_requirements(category=state["data"]["category"])
        except Exception:
            reqs = []

        if text not in reqs:
            bot.send_message(message.chat.id, "Пожалуйста, выбери требование кнопкой.")
            return

        results = db.find_professions(
            interaction_level=state["data"]["interaction_level"],
            category=state["data"]["category"],
            requirement=text
        )
        _send_professions_list(message.chat.id, results)

        state["stage"] = "menu"
        bot.send_message(message.chat.id, "Хотите что-то ещё?", reply_markup=start_menu_keyboard())
        return

    
    if stage == "change_current_field":
        try:
            categories = db.get_all_categories()
        except Exception:
            categories = []

        if text not in categories:
            bot.send_message(message.chat.id, "Пожалуйста, выбери категорию кнопкой.")
            return

        state["data"]["current_field"] = text
        kb = make_reply_keyboard(["Да", "Нет"])
        bot.send_message(message.chat.id, f"Хочешь остаться в сфере '{text}'?", reply_markup=kb)
        state["stage"] = "change_wants_to_stay"
        return

    if stage == "change_wants_to_stay":
        if text not in ["Да", "Нет"]:
            bot.send_message(message.chat.id, "Выбери кнопкой.")
            return
        state["data"]["wants_to_stay"] = (text == "Да")
        kb = make_reply_keyboard(["Да", "Нет"])
        bot.send_message(message.chat.id, "Готов(а) получать новое образование (например, курсы/колледж/университет)?", reply_markup=kb)
        state["stage"] = "change_ready_to_study"
        return

    if stage == "change_ready_to_study":
        if text not in ["Да", "Нет"]:
            bot.send_message(message.chat.id, "Выбери кнопкой.")
            return
        state["data"]["ready"] = (text == "Да")

        if not state["data"]["wants_to_stay"]:
            try:
                categories = db.get_all_categories()
            except Exception:
                categories = []
            if not categories:
                bot.send_message(message.chat.id, "В базе нет категорий.")
                state["stage"] = "menu"
                return
            kb = make_reply_keyboard(categories, row_width=1)
            bot.send_message(message.chat.id, "В какую сферу хочешь перейти? (выбери категорию)", reply_markup=kb)
            state["stage"] = "change_target_category"
            return

        category = state["data"]["current_field"]
        try:
            reqs = db.get_all_requirements(category)
        except Exception:
            reqs = []

        edu_max = 1 if not state["data"]["ready"] else None

        if not reqs:
            results = db.find_professions(category=category, education_max=edu_max)
            _send_professions_list(message.chat.id, results)
            state["stage"] = "menu"
            bot.send_message(message.chat.id, "Готово — вернулись в меню.", reply_markup=start_menu_keyboard())
            return

        kb = make_reply_keyboard(reqs)
        bot.send_message(message.chat.id, "Выбери требование/навык:", reply_markup=kb)
        state["stage"] = "change_choose_requirement"
        return

    if stage == "change_target_category":
        try:
            categories = db.get_all_categories()
        except Exception:
            categories = []
        if text not in categories:
            bot.send_message(message.chat.id, "Выбери категорию кнопкой.")
            return

        state["data"]["target_field"] = text
        try:
            reqs = db.get_all_requirements(text)
        except Exception:
            reqs = []

        edu_max = 1 if not state["data"]["ready"] else None

        if not reqs:
            results = db.find_professions(category=text, education_max=edu_max)
            _send_professions_list(message.chat.id, results)
            state["stage"] = "menu"
            bot.send_message(message.chat.id, "Готово — возвращаемся в меню.", reply_markup=start_menu_keyboard())
            return

        kb = make_reply_keyboard(reqs)
        bot.send_message(message.chat.id, "Выбери требование:", reply_markup=kb)
        state["stage"] = "change_choose_requirement"
        return

    if stage == "change_choose_requirement":
        category = state["data"]["current_field"] if state["data"]["wants_to_stay"] else state["data"].get("target_field")
        try:
            reqs = db.get_all_requirements(category)
        except Exception:
            reqs = []

        if text not in reqs:
            bot.send_message(message.chat.id, "Выбери требование кнопкой.")
            return

        edu_max = 1 if not state["data"]["ready"] else None
        results = db.find_professions(category=category, requirement=text, education_max=edu_max)
        _send_professions_list(message.chat.id, results)

        state["stage"] = "menu"
        bot.send_message(message.chat.id, "Готово! Вернулись в меню.", reply_markup=start_menu_keyboard())
        return

   
    if stage == "info_choose_category":
        try:
            categories = db.get_all_categories()
        except Exception:
            categories = []

        if text not in categories:
            bot.send_message(message.chat.id, "Пожалуйста, выбери категорию кнопкой.")
            return

        proflist = db.get_professions_in_category(text)
        if not proflist:
            bot.send_message(message.chat.id, "В этой категории пока нет профессий.")
            state["stage"] = "menu"
            bot.send_message(message.chat.id, "Вернуться в меню?", reply_markup=start_menu_keyboard())
            return

        ikb = InlineKeyboardMarkup()
        for pid, pname in proflist:
            ikb.add(InlineKeyboardButton(text=pname, callback_data=f"viewprof:{pid}"))

        bot.send_message(message.chat.id, "Выбери профессию, чтобы увидеть детали:", reply_markup=ikb)
        state["stage"] = "menu"
        return

    bot.send_message(message.chat.id, "Не понял. Выбери действие:", reply_markup=start_menu_keyboard())
    state["stage"] = "menu"



@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("viewprof:"))
def callback_view_prof(call):
    try:
        pid = int(call.data.split(":", 1)[1])
    except Exception:
        bot.answer_callback_query(call.id, "Ошибка идентификатора.")
        return

    prof = db.get_profession_details(pid)
    if not prof:
        bot.answer_callback_query(call.id, "Профессия не найдена.")
        return

    
    inter_text = pretty_interaction(prof.get("interaction_level"))
    edu_text = pretty_education(prof.get("education_level"))

    text = (f"🎯 *{prof['name']}*\n\n"
            f"{prof['description']}\n\n"
            f"📂 *Категории:* {', '.join(prof.get('categories', []))}\n"
            f"📌 *Требования:* {', '.join(prof.get('requirements', []))}\n\n"
            f"🗣 *Уровень общения:* {inter_text}\n"
            f"🎓 *Образование:* {edu_text}\n\n"
            "Хотите оставить отзыв по этой профессии?")
    
    ikb = InlineKeyboardMarkup()
    ikb.add(InlineKeyboardButton("👍 Подходит", callback_data=f"fb_yes:{pid}"),
            InlineKeyboardButton("👎 Не подходит", callback_data=f"fb_no:{pid}"))

    
    try:
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=ikb)
    except Exception:
        bot.send_message(call.message.chat.id, text.replace("*", ""), reply_markup=ikb)

    bot.answer_callback_query(call.id)



@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("rate:"))
def callback_rate_from_list(call):
    try:
        pid = int(call.data.split(":", 1)[1])
    except Exception:
        bot.answer_callback_query(call.id, "Ошибка.")
        return

    ikb = InlineKeyboardMarkup()
    ikb.add(InlineKeyboardButton("👍 Подходит", callback_data=f"fb_yes:{pid}"),
            InlineKeyboardButton("👎 Не подходит", callback_data=f"fb_no:{pid}"))

    bot.send_message(call.message.chat.id, "Пожалуйста, оцени эту профессию:", reply_markup=ikb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data and (call.data.startswith("fb_yes:") or call.data.startswith("fb_no:")))
def callback_feedback(call):
    parts = call.data.split(":")
    if len(parts) != 2:
        bot.answer_callback_query(call.id, "Неправильные данные.")
        return

    kind, pid_s = parts[0], parts[1]
    try:
        pid = int(pid_s)
    except Exception:
        bot.answer_callback_query(call.id, "Неправильный ID профессии.")
        return

    is_satisfied = 1 if kind == "fb_yes" else 0
    user_id = call.from_user.id

    try:
        if hasattr(db, "save_user_feedback"):
            db.save_user_feedback(user_id, pid, is_satisfied)
    except Exception as e:
        print("warning: save_user_feedback failed:", e)

    
    if is_satisfied:
        bot.send_message(user_id, "🥰 Спасибо! Рад, что подсказал подходящую профессию.")
    else:
        bot.send_message(user_id, "Спасибо за отклик — попробуем подобрать другой вариант.")

    
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    except Exception:
        pass

    bot.answer_callback_query(call.id)



if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)