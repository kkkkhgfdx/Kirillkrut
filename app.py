import telebot, random, json, os, time, threading
from telebot import types
from telebot.types import BotCommand
from flask import Flask

TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0"
OWNER_ID = 6170286634
CHAT_ID = -1004215885788

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp, clans = {}, 10000, {}

BUSINESSES = {
    "farm": {"name": "Ферма", "price": 1000, "income": 200, "cooldown": 3600},
    "garden": {"name": "Сад", "price": 3000, "income": 500, "cooldown": 1800},
    "factory": {"name": "Завод", "price": 10000, "income": 2000, "cooldown": 7200}
}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "businesses": {}, "bank_deposit": 0, "achieves": [], "last_loan": 0, "last_rob": 0, "last_mine": 0, "last_smuggle": 0, "has_chest": False, "last_daily": 0, "clan": None, "clan_rank": None, "safe": 0}
    if name: users[uid_str]["name"] = name
    return users[uid_str]

def save_db():
    try:
        with open("users.json", "w", encoding="utf-8") as f: json.dump({"users": users, "clans": clans}, f, ensure_ascii=False)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="База")
            try: bot.pin_chat_message(CHAT_ID, sent.message_id, disable_notification=True)
            except: pass
    except: pass

def load_db():
    global users, clans
    try:
        chat = bot.get_chat(CHAT_ID)
        if chat.pinned_message and chat.pinned_message.document:
            data = json.loads(bot.download_file(bot.get_file(chat.pinned_message.document.file_id).file_path).decode('utf-8'))
            users = data.get("users", {})
            clans = data.get("clans", {})
            return
    except: pass
    users, clans = {}, {}

load_db()

@app.route('/')
def health(): return "OK", 200

def main_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"))
    kb.add(types.InlineKeyboardButton("🛒 Магазин", callback_data="menu_shop"))
    kb.add(types.InlineKeyboardButton("🏢 Бизнесы", callback_data="menu_biz"))
    kb.add(types.InlineKeyboardButton("🏦 Банк", callback_data="menu_bank"))
    kb.add(types.InlineKeyboardButton("🐉 Босс", callback_data="menu_boss"))
    kb.add(types.InlineKeyboardButton("🎰 Казино", callback_data="menu_casino"))
    kb.add(types.InlineKeyboardButton("🛡 Кланы", callback_data="menu_clans"))
    kb.add(types.InlineKeyboardButton("🏆 Топ", callback_data="menu_top"))
    return kb

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global boss_hp
    u = get_u(call.from_user.id, call.from_user.first_name)
    uid = str(call.from_user.id)
    
    if call.data.startswith("buy_") or call.data == "open_chest":
        if call.data == "open_chest":
            u["has_chest"] = False
            if random.random() > 0.5: u["coins"] += 2000
            else: u["dmg"] += 5
            save_db()
            return bot.answer_callback_query(call.id, "Открыто")
        i = call.data.split("_")[1]
        p = BUSINESSES[i]["price"]
        if u["coins"] < p: return bot.answer_callback_query(call.id, "Мало")
        u["coins"] -= p
        u["businesses"][i] = time.time() - BUSINESSES[i]["cooldown"]
        save_db()
        return bot.answer_callback_query(call.id, "Куплено")

    if call.data == "menu_main": 
        bot.edit_message_text("Меню", call.message.chat.id, call.message.message_id, reply_markup=main_kb(uid))
    elif call.data == "menu_profile":
        bot.edit_message_text(f"Баланс: {u['coins']}", call.message.chat.id, call.message.message_id)
    elif call.data == "menu_shop":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Ферма", callback_data="buy_farm"))
        kb.add(types.InlineKeyboardButton("Сад", callback_data="buy_garden"))
        kb.add(types.InlineKeyboardButton("Завод", callback_data="buy_factory"))
        kb.add(types.InlineKeyboardButton("Назад", callback_data="menu_main"))
        bot.edit_message_text("Магазин", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "menu_clans":
        if u.get("clan"):
            bot.edit_message_text("Ты в клане", call.message.chat.id, call.message.message_id)
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Создать", callback_data="clan_create"))
            kb.add(types.InlineKeyboardButton("Назад", callback_data="menu_main"))
            bot.edit_message_text("Кланы", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "clan_create":
        if u["coins"] < 5000: return bot.answer_callback_query(call.id, "Нужно 5000")
        u["coins"] -= 5000
        c_id = str(random.randint(10000, 99999))
        clans[c_id] = {"name": "Клан", "leader": uid, "bank": 0, "members": [uid]}
        u["clan"] = c_id
        u["clan_rank"] = "Лидер"
        save_db()
        bot.answer_callback_query(call.id, "Создан")
    elif call.data == "menu_biz":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Собрать", callback_data="biz_collect"))
        kb.add(types.InlineKeyboardButton("Назад", callback_data="menu_main"))
        bot.edit_message_text("Бизнесы", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "biz_collect":
        total = 0
        for b, l in list(u["businesses"].items()):
            if time.time() - l >= BUSINESSES[b]["cooldown"]: total += BUSINESSES[b]["income"]; u["businesses"][b] = time.time()
        u["coins"] += total
        save_db()
        bot.answer_callback_query(call.id, f"Собрано: {total}")
    elif call.data == "menu_bank":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000"))
        kb.add(types.InlineKeyboardButton("Назад", callback_data="menu_main"))
        bot.edit_message_text("Банк", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "bank_1000":
        if u["coins"] < 1000: return bot.answer_callback_query(call.id, "Мало")
        u["coins"] -= 1000
        u["bank_deposit"] = u.get("bank_deposit", 0) + 1000
        save_db()
        bot.answer_callback_query(call.id, "Вложено")
    elif call.data == "menu_boss":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Ударить", callback_data="hit_boss"))
        kb.add(types.InlineKeyboardButton("Назад", callback_data="menu_main"))
        bot.edit_message_text(f"Босс: {boss_hp} HP", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "hit_boss":
        dmg = u["dmg"]
        boss_hp -= dmg
        u["coins"] += dmg * 2
        save_db()
        bot.answer_callback_query(call.id, f"Удар -{dmg}")
    elif call.data == "menu_casino":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Слоты 100", callback_data="casino_slots"))
        kb.add(types.InlineKeyboardButton("Назад", callback_data="menu_main"))
        bot.edit_message_text("Казино", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "casino_slots":
        if u["coins"] < 100: return bot.answer_callback_query(call.id, "Мало")
        u["coins"] -= 100
        if random.random() > 0.5: u["coins"] += 200
        save_db()
        bot.answer_callback_query(call.id, "Сыграно")
    elif call.data == "menu_top":
        bot.edit_message_text("Топ", call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['start', 'menu'])
def start(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.chat.id, "Бот запущен", reply_markup=main_kb(msg.from_user.id))

@bot.message_handler(commands=['massa'])
def massa_cmd(msg):
    bot.reply_to(msg, "Полетели, масса")

@bot.message_handler(commands=['mine'])
def mine(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_mine", 0) < 60: return bot.reply_to(msg, "Жди минуту")
    u["last_mine"] = time.time()
    u["coins"] += 500
    save_db()
    bot.reply_to(msg, "Намайнил 500")

@bot.message_handler(commands=['boss'])
def boss(msg):
    global boss_hp
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    dmg = u["dmg"]
    boss_hp -= dmg
    u["coins"] += dmg * 2
    save_db()
    bot.reply_to(msg, f"Удар -{dmg}. Осталось {boss_hp}")

@bot.message_handler(commands=['casino'])
def casino(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "Введи ставку")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "Мало")
    if random.random() > 0.5: u["coins"] += bet; bot.reply_to(msg, "Победа")
    else: u["coins"] -= bet; bot.reply_to(msg, "Проигрыш")
    save_db()

@bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u["debt"] > 0: return bot.reply_to(msg, "Верни долг")
    u["coins"] += 1000
    u["debt"] += 1500
    save_db()
    bot.reply_to(msg, "Кредит выдан")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "Успех")
    else: u["coins"] -= 200; bot.reply_to(msg, "Поймали")
    save_db()

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    bot.reply_to(msg, f"Баланс: {u['coins']}")

@bot.message_handler(commands=['top'])
def top(msg):
    s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
    t = "Топ:\n" + "\n".join([f"{i}. {d.get('name')} - {d.get('coins')}" for i, (uid, d) in enumerate(s[:10], 1)])
    bot.reply_to(msg, t)

@bot.message_handler(commands=['save'])
def save_cmd(msg):
    if msg.from_user.id == OWNER_ID: save_db(); bot.reply_to(msg, "Сохранено")

def run_bot():
    cmds = [BotCommand("menu", "Меню"), BotCommand("massa", "Полетели"), BotCommand("profile", "Профиль"), BotCommand("top", "Топ"), BotCommand("mine", "Шахта"), BotCommand("casino", "Казино"), BotCommand("boss", "Босс"), BotCommand("loan", "Кредит"), BotCommand("rob", "Ограбить")]
    bot.set_my_commands(cmds)
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
