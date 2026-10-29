import telebot
from telebot import types
from telebot.types import BotCommand
from flask import Flask
import random
import json
import os
import time
import threading

# ========== НАСТРОЙКИ ==========
TOKEN = "9291373316:AAGlBUAKEvAmsbVTn542imkEBCYrMG0Rry0" 
OWNER_ID = 6170286634       # ТЫ
FRIEND_ID = 7527864291      # Друг
CHAT_ID = -1002021366605    # Канал для сплетен

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__) # Для Render

# ========== БАЗА ==========
DB_FILE = "users.json"
users = {}
boss_hp = 10000
pending_messages = {}

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except: users = {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def get_user(uid):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {
            "coins": 1000, "debt": 0, "lvl": 1, "xp": 0, 
            "dmg": 10, "name": "Игрок", "last_rob": 0, "last_loan": 0,
            "businesses": {}, "last_steal": 0, "cursed_until": 0,
            "clan": None, "last_daily": 0, "virus_until": 0
        }
        save_db()
    # Проверка на новые поля
    for key in ["businesses", "clan", "virus_until"]:
        if key not in users[uid_str]: 
            users[uid_str][key] = {} if key == "businesses" else (None if key == "clan" else 0)
    return users[uid_str]

def add_xp(uid, amount):
    user = get_user(uid)
    user["xp"] += amount
    while user["xp"] >= 100 * user["lvl"]:
        user["xp"] -= 100 * user["lvl"]
        user["lvl"] += 1
        user["coins"] += 200
        user["dmg"] += 2
        try: bot.send_message(uid, f"🎉 Уровень {user['lvl']}! +200 монет, +2 урона.")
        except: pass
    save_db()

# ========== КОНФИГ ==========
BUSINESSES = {
    "farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600},
    "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800},
    "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}
}

# ========== МЕНЮ ==========
def set_commands():
    commands = [
        BotCommand("start", "🚀 Запустить"),
        BotCommand("profile", "👤 Профиль"),
        BotCommand("business", "🏢 Бизнесы"),
        BotCommand("shop", "🛒 Магазин"),
        BotCommand("clan", "🛡 Кланы"),
        BotCommand("infect", "🦠 Заразить игрока"),
        BotCommand("steal", "🥷 Украсть"),
        BotCommand("daily", "🎁 Бонус"),
        BotCommand("loan", "🏦 Кредит"),
        BotCommand("boss", "🐉 Босс"),
        BotCommand("top", "🏆 Топ"),
        BotCommand("give", "💸 Выдать монеты (Админ)"),
        BotCommand("broadcast", "📢 Рассылка (Админ)"),
        BotCommand("help", "📋 Справка")
    ]
    bot.set_my_commands(commands)

# ========== ВИРУС И ИВЕНТЫ ==========
def virus_loop():
    """Каждый час снимает монеты у зараженных"""
    while True:
        time.sleep(3600)
        for uid, user in users.items():
            if user.get("virus_until", 0) > time.time():
                loss = int(user["coins"] * 0.1) # -10%
                user["coins"] -= loss
                try: bot.send_message(int(uid), f"🦠 Вирус съел {loss} монет! Купи антидот в /shop.")
                except: pass
        save_db()

@bot.message_handler(commands=['infect'])
def infect(message):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(message, "❌ /infect [ID]")
    target_id = parts[1]
    if target_id == str(message.from_user.id): return bot.reply_to(message, "❌ Себя нельзя.")
    
    target = users.get(target_id)
    if not target: return bot.reply_to(message, "❌ Игрок не найден.")
    
    user = get_user(message.from_user.id)
    if user["coins"] < 300: return bot.reply_to(message, "❌ Нужно 300 монет для вируса.")
    
    user["coins"] -= 300
    target["virus_until"] = time.time() + 3600 # Заражен на час
    save_db()
    bot.reply_to(message, f"🦠 Ты заразил игрока {target_id}!")
    try: bot.send_message(int(target_id), "🦠 Ты заражен вирусом! Срочно купи антидот в /shop!")
    except: pass

@bot.message_handler(commands=['grab'])
def grab_event(message):
    global global_event
    if not global_event["active"]: return bot.reply_to(message, "❌ Ивент прошел.")
    global_event["active"] = False
    uid = message.from_user.id
    user = get_user(uid)
    user["coins"] += global_event["reward"]
    add_xp(uid, 50); save_db()
    bot.send_message(message.chat.id, f"🎉 {user['name']} заграбастал {global_event['reward']} монет!")

# ========== СТАРТ И АДМИНКА ==========
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    user = get_user(uid)
    user["name"] = message.from_user.first_name or "Игрок"
    save_db()
    
    if uid == OWNER_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👤 Профиль", "🏢 Бизнесы", "🛡 Кланы", "🎁 Бонус")
        bot.send_message(uid, "👑 Босс, Синдикат 6.0. Добавлен ВИРУС и починены команды!", reply_markup=markup)
    else:
        bot.reply_to(message, "Привет! Теперь можно заражать людей. Пиши /help.")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != OWNER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return bot.reply_to(message, "❌ /broadcast [текст]")
    final_text = f"📢 **ОБЪЯВЛЕНИЕ ОТ АДМИНИСТРАЦИИ:**\n\n{text}"
    count = 0
    for uid_str in users.keys():
        try: bot.send_message(int(uid_str), final_text, parse_mode="Markdown"); count += 1; time.sleep(0.05)
        except: pass
    bot.reply_to(message, f"✅ Отправлено {count} игрокам.")

@bot.message_handler(commands=['give'])
def give(message):
    if message.from_user.id != OWNER_ID: return
    parts = message.text.split()
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        target_id, amount = parts[1], int(parts[2])
        if target_id in users:
            users[target_id]["coins"] += amount; save_db()
            bot.reply_to(message, f"💸 Выдано {amount} игроку {target_id}!")
        else: bot.reply_to(message, "❌ Не найден.")
    else: bot.reply_to(message, "❌ /give [ID] [Сумма]")

# ========== БАЗОВЫЕ КОМАНДЫ ==========
@bot.message_handler(commands=['profile'])
def profile(message):
    user = get_user(message.from_user.id)
    virus = "🦠 Ты заражен!" if user.get("virus_until", 0) > time.time() else ""
    bot.reply_to(message, f"👤 **{user['name']}**\n💰 {user['coins']}\n🛡 Клан: {user['clan'] or 'Нет'}\n{virus}", parse_mode="Markdown")

@bot.message_handler(commands=['clan'])
def clan_menu(message):
    user = get_user(message.from_user.id)
    if user["clan"]: return bot.reply_to(message, f"🛡 Ты в клане: **{user['clan']}**", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Создать клан (5000)", callback_data="clan_create"))
    bot.reply_to(message, "🛡 **Кланы**\nСоздай свой клан за 5000 монет!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "clan_create")
def clan_create(call):
    user = get_user(call.from_user.id)
    if user["coins"] < 5000: return bot.answer_callback_query(call.id, "❌ Мало монет!")
    user["coins"] -= 5000
    user["clan"] = f"Клан_{user['name']}"
    save_db(); bot.answer_callback_query(call.id, "✅ Клан создан!")

@bot.message_handler(commands=['business'])
def business_menu(message):
    user = get_user(message.from_user.id)
    if not user["businesses"]: return bot.reply_to(message, "🏢 Нет бизнесов. Купи в /shop.")
    text = "🏢 **БИЗНЕС-ЦЕНТР**\n\n"
    now = int(time.time())
    for bus_id, last_time in user["businesses"].items():
        bus = BUSINESSES[bus_id]
        if now - last_time >= bus["cooldown"]: text += f"{bus['name']} — ✅ Готово (+{bus['income']})\n"
        else: text += f"{bus['name']} — ⏳ Работает\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect"))
    bot.reply_to(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "biz_collect")
def biz_collect(call):
    user = get_user(call.from_user.id)
    total = 0; now = int(time.time())
    for bus_id, last_time in list(user["businesses"].items()):
        bus = BUSINESSES[bus_id]
        if now - last_time >= bus["cooldown"]:
            total += bus["income"]; user["businesses"][bus_id] = now
    if total > 0: user["coins"] += total; save_db(); bot.answer_callback_query(call.id, f"✅ Собрано {total}!")
    else: bot.answer_callback_query(call.id, "⏳ Ничего нет.")

@bot.message_handler(commands=['shop'])
def shop(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"))
    markup.add(types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"))
    markup.add(types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"))
    markup.add(types.InlineKeyboardButton("💊 Антидот от вируса (500)", callback_data="buy_antidote"))
    bot.reply_to(message, "🛒 **Магазин:** Выбирай!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_callback(call):
    user = get_user(call.from_user.id)
    item = call.data.split("_")[1]
    
    if item == "antidote":
        if user["coins"] < 500: return bot.answer_callback_query(call.id, "❌ Мало монет!")
        if user.get("virus_until", 0) < time.time(): return bot.answer_callback_query(call.id, "✅ Ты не болен.")
        user["coins"] -= 500; user["virus_until"] = 0; save_db()
        bot.answer_callback_query(call.id, "💊 Ты вылечился!")
        return

    price = BUSINESSES[item]["price"]
    if user["coins"] < price: return bot.answer_callback_query(call.id, "❌ Мало монет!")
    user["coins"] -= price; user["businesses"][item] = 0; save_db()
    bot.answer_callback_query(call.id, f"✅ {BUSINESSES[item]['name']} куплен!")

@bot.message_handler(commands=['steal'])
def steal(message):
    user = get_user(message.from_user.id)
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "❌ /steal [ID]")
    target_id = parts[1]
    if time.time() - user.get("last_steal", 0) < 60: return bot.reply_to(message, "❌ Жди минуту.")
    user["last_steal"] = time.time(); target = users.get(target_id)
    if not target: return bot.reply_to(message, "❌ Не найден.")
    if random.random() > 0.4:
        stolen = min(500, target["coins"]); target["coins"] -= stolen; user["coins"] += stolen; save_db()
        bot.reply_to(message, f"🥷 Украл {stolen} монет!")
    else: user["coins"] -= min(300, user["coins"]); save_db(); bot.reply_to(message, "🚔 Поймали! Штраф.")

@bot.message_handler(commands=['daily'])
def daily(message):
    user = get_user(message.from_user.id)
    if time.time() - user.get("last_daily", 0) < 86400: return bot.reply_to(message, "❌ Завтра!")
    user["last_daily"] = time.time(); user["coins"] += 500; add_xp(message.from_user.id, 100); save_db()
    bot.reply_to(message, "🎁 +500 монет!")

@bot.message_handler(commands=['loan'])
def loan(message):
    user = get_user(message.from_user.id)
    if time.time() - user.get("last_loan", 0) < 10: return bot.reply_to(message, "❌ Жди 10 сек.")
    if user["debt"] > 0: return bot.reply_to(message, "❌ Верни долг.")
    user["coins"] += 1000; user["debt"] += 1500; user["last_loan"] = time.time(); save_db()
    bot.reply_to(message, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['boss'])
def boss(message):
    global boss_hp
    user = get_user(message.from_user.id)
    if boss_hp <= 0: boss_hp = 10000; return bot.reply_to(message, "🐉 Новый босс!")
    dmg = random.randint(user["dmg"] - 5, user["dmg"] + 10)
    boss_hp -= dmg; user["coins"] += dmg * 3; save_db()
    if boss_hp <= 0:
        user["coins"] += 2000; save_db(); bot.send_message(message.chat.id, f"💀 БОСС УБИТ! {user['name']} +2000!")
    else: bot.reply_to(message, f"🐉 -{dmg} HP. Осталось {boss_hp}.")

@bot.message_handler(commands=['top'])
def top(message):
    top_users = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True)[:5]
    text = "🏆 **Топ:**\n\n"
    for i, (uid, d) in enumerate(top_users, 1): text += f"{i}. {d['name']} — {d['coins']} монет\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "📋 /profile /business /clan /infect /shop /steal /daily /loan /boss /top")

# ========== ЛОГИКА ПЕРЕСЫЛКИ (ТЕПЕРЬ И ТЕБЕ, И ДРУГУ) ==========
@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_message(message):
    if message.chat.type != 'private': return
    uid = message.from_user.id
    name = message.from_user.first_name or "Кто-то"
    
    # Если пишет Босс
    if uid == OWNER_ID:
        if message.text == "👤 Профиль": profile(message); return
        if message.text == "🏢 Бизнесы": business_menu(message); return
        if message.text == "🛡 Кланы": clan_menu(message); return
        if message.text == "🎁 Бонус": daily(message); return

        # Ответ (Reply) на сообщение
        if message.reply_to_message:
            target_uid = pending_messages.get(message.reply_to_message.message_id)
            if target_uid:
                try:
                    bot.copy_message(target_uid, message.chat.id, message.message_id)
                    bot.reply_to(message, "✅ Отправлено пользователю!")
                except: bot.reply_to(message, "❌ Ошибка.")
            else: bot.reply_to(message, "❌ Сделай Reply.")
        
        # Если Босс пишет просто текст -> ЛЕТИТ И БОССУ, И ДРУГУ
        else:
            try:
                bot.forward_message(FRIEND_ID, message.chat.id, message.message_id)
                bot.forward_message(OWNER_ID, message.chat.id, message.message_id) # Дублируем тебе
                bot.reply_to(message, "✅ Отправлено другу (и тебе)!")
            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка: {e}")
    
    # Если пишет кто-то другой -> ЛЕТИТ И БОССУ, И ДРУГУ
    else:
        try:
            # Отправляем другу
            sent_msg = bot.forward_message(FRIEND_ID, message.chat.id, message.message_id)
            pending_messages[sent_msg.message_id] = uid
            bot.send_message(FRIEND_ID, f"✉️ От {name}. Ответь.", reply_markup=types.ForceReply(selective=True))
            
            # Отправляем боссу (тебе)
            bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
            
            bot.reply_to(message, "✅ Отправлено Боссу и другу!")
        except Exception as e: bot.reply_to(message, "❌ Ошибка.")

# ========== ЗАПУСК ДЛЯ RENDER ==========
def run_bot():
    set_commands()
    print("🚀 СИНДИКАТ 6.0 С ВИРУСОМ ЗАПУЩЕН.")
    # Запускаем фоновый поток для вируса
    threading.Thread(target=virus_loop, daemon=True).start()
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
