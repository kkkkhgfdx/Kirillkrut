import telebot, random, json, os, time, threading
from telebot import types
from telebot.types import BotCommand
from flask import Flask

TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0"
OWNER_ID = 6170286634
CHAT_ID = -1004215885788

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp = {}, 10000

BUSINESSES = {
    "farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600},
    "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800},
    "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}
}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "businesses": {}, "achieves": [], "last_loan": 0, "last_rob": 0, "last_steal": 0, "last_mine": 0, "last_smuggle": 0, "has_chest": False, "last_daily": 0, "antidote": 0, "last_hack": 0}
    if name: users[uid_str]["name"] = name
    return users[uid_str]

def save_db():
    try:
        with open("users.json", "w", encoding="utf-8") as f: json.dump(users, f, ensure_ascii=False)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="База")
            try: bot.pin_chat_message(CHAT_ID, sent.message_id, disable_notification=True)
            except: pass
    except: pass

def load_db():
    global users
    try:
        chat = bot.get_chat(CHAT_ID)
        if chat.pinned_message and chat.pinned_message.document:
            data = json.loads(bot.download_file(bot.get_file(chat.pinned_message.document.file_id).file_path).decode('utf-8'))
            users = data.get("users", {}) if isinstance(data, dict) and "users" in data else data
            return
    except: pass
    users = {}
load_db()

@app.route('/')
def health(): return "OK", 200

def main_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"), types.InlineKeyboardButton("🛒 Магазин", callback_data="menu_shop"))
    kb.add(types.InlineKeyboardButton("🏢 Бизнесы", callback_data="menu_biz"), types.InlineKeyboardButton("🐉 Босс", callback_data="menu_boss"))
    kb.add(types.InlineKeyboardButton("🏆 Топ", callback_data="menu_top"))
    return kb

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global boss_hp
    u = get_u(call.from_user.id, call.from_user.first_name)
    uid = str(call.from_user.id)
    if call.data.startswith("buy_") or call.data == "open_chest":
        if call.data == "buy_antidote":
            if u["coins"] < 500: return bot.answer_callback_query(call.id, "❌ Мало!")
            u["coins"] -= 500; u["antidote"] = u.get("antidote", 0) + 1; save_db()
            return bot.answer_callback_query(call.id, "✅ Куплен антидот!")
        if call.data == "buy_chest":
            if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!")
            u["coins"] -= 1000; u["has_chest"] = True; save_db()
            return bot.answer_callback_query(call.id, "✅ Кейс куплен! Открой его.")
        if call.data == "open_chest":
            if not u.get("has_chest"): return bot.answer_callback_query(call.id, "❌ Нет кейса.")
            u["has_chest"] = False
            if random.random() > 0.5: u["coins"] += 2000; bot.answer_callback_query(call.id, "✅ +2000!")
            else: u["dmg"] += 5; bot.answer_callback_query(call.id, "✅ +5 урона!")
            save_db(); return
        i = call.data.split("_")[1]
        p = BUSINESSES[i]["price"]
        if u["coins"] < p: return bot.answer_callback_query(call.id, "❌ Мало!")
        u["coins"] -= p; u["businesses"][i] = time.time() - BUSINESSES[i]["cooldown"]; save_db()
        return bot.answer_callback_query(call.id, f"✅ {BUSINESSES[i]['name']} куплен!")
    if call.data == "menu_main": bot.edit_message_text("🚜 Меню", call.message.chat.id, call.message.message_id, reply_markup=main_kb(uid))
    elif call.data == "menu_profile": bot.edit_message_text(f"👤 {u['name']}\n💰 {u['coins']}\n💳 Долг: {u['debt']}\n💊 Антидот: {u.get('antidote', 0)}\n🏢 Бизнесов: {len(u['businesses'])}", call.message.chat.id, call.message.message_id)
    elif call.data == "menu_shop":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🌾 Ферма", callback_data="buy_farm"), types.InlineKeyboardButton("🌳 Сад", callback_data="buy_garden"), types.InlineKeyboardButton("🏭 Завод", callback_data="buy_factory"))
        kb.add(types.InlineKeyboardButton("💊 Антидот (500)", callback_data="buy_antidote"), types.InlineKeyboardButton("🎁 Кейс (1000)", callback_data="buy_chest"))
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text("🛒 Магазин:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "menu_biz":
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect")).add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text("🏢 Бизнесы", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "biz_collect":
        total = sum(BUSINESSES[b]["income"] for b, l in u["businesses"].items() if time.time() - l >= BUSINESSES[b]["cooldown"])
        for b in u["businesses"]:
            if time.time() - u["businesses"][b] >= BUSINESSES[b]["cooldown"]: u["businesses"][b] = time.time()
        u["coins"] += total; save_db(); bot.answer_callback_query(call.id, f"✅ Собрано {total}!")
    elif call.data == "menu_boss":
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⚔️ Ударить", callback_data="hit_boss")).add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text(f"🐉 Босс: {boss_hp} HP", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "hit_boss":
        dmg = u["dmg"]; boss_hp -= dmg; u["coins"] += dmg * 2; save_db(); bot.answer_callback_query(call.id, f"⚔️ -{dmg} HP. +{dmg*2}!")
    elif call.data == "menu_top":
        s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
        bot.edit_message_text("🏆 Топ:\n" + "\n".join([f"{i}. {d.get('name')} - {d.get('coins')}" for i, (uid, d) in enumerate(s[:10], 1)]), call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['start', 'menu'])
def start(msg): bot.send_message(msg.chat.id, "🔥 Бот запущен!", reply_markup=main_kb(msg.from_user.id))

@bot.message_handler(commands=['massa'])
def massa(msg): bot.reply_to(msg, "✈️ Полетели, масса!")

@bot.message_handler(commands=['business'])
def business(msg):
    u = get_u(msg.from_user.id)
    if not u.get("businesses"): return bot.reply_to(msg, "❌ Нет бизнесов!")
    bot.reply_to(msg, "🏢 Бизнесы:\n" + "\n".join([f"{BUSINESSES[b]['name']} — {'✅' if time.time() - l >= BUSINESSES[b]['cooldown'] else '⏳'}" for b, l in u["businesses"].items()]) + "\n\nСобрать: /collect")

@bot.message_handler(commands=['collect'])
def collect(msg):
    u = get_u(msg.from_user.id); total = sum(BUSINESSES[b]["income"] for b, l in u["businesses"].items() if time.time() - l >= BUSINESSES[b]["cooldown"])
    for b in u["businesses"]:
        if time.time() - u["businesses"][b] >= BUSINESSES[b]["cooldown"]: u["businesses"][b] = time.time()
    u["coins"] += total; save_db(); bot.reply_to(msg, f"✅ Собрано {total}!")

@bot.message_handler(commands=['smuggle'])
def smuggle(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_smuggle", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту!")
    u["last_smuggle"] = time.time()
    if random.random() > 0.5: u["coins"] += 3000; bot.reply_to(msg, "🕵️ +3000!")
    else: u["coins"] -= 1000; bot.reply_to(msg, "🚔 -1000!")
    save_db()

@bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id)
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Верни долг!")
    u["coins"] += 1000; u["debt"] += 1500; save_db(); bot.reply_to(msg, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['paydebt'])
def paydebt(msg):
    u = get_u(msg.from_user.id)
    if u["debt"] <= 0: return bot.reply_to(msg, "✅ Нет долгов!")
    if u["coins"] < u["debt"]: return bot.reply_to(msg, f"❌ Нужно {u['debt']}!")
    u["coins"] -= u["debt"]; u["debt"] = 0; save_db(); bot.reply_to(msg, "✅ Долг погашен!")

@bot.message_handler(commands=['mine'])
def mine(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_mine", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту!")
    u["last_mine"] = time.time(); u["coins"] += 500; save_db(); bot.reply_to(msg, "⛏ +500!")

@bot.message_handler(commands=['daily'])
def daily(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_daily", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки!")
    u["last_daily"] = time.time(); u["coins"] += 500; save_db(); bot.reply_to(msg, "🎁 +500!")

@bot.message_handler(commands=['casino'])
def casino(msg):
    u = get_u(msg.from_user.id); parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "❌ /casino 100")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "❌ Мало!")
    if random.random() > 0.5: u["coins"] += bet; bot.reply_to(msg, f"🎰 +{bet}!")
    else: u["coins"] -= bet; bot.reply_to(msg, f"💀 -{bet}!")
    save_db()

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id); bot.reply_to(msg, f"👤 {u['name']}\n💰 {u['coins']}\n💳 Долг: {u['debt']}\n💊 Антидот: {u.get('antidote', 0)}")

@bot.message_handler(commands=['top'])
def top(msg):
    s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
    bot.reply_to(msg, "🏆 Топ:\n" + "\n".join([f"{i}. {d.get('name')} - {d.get('coins')}" for i, (uid, d) in enumerate(s[:10], 1)]))

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_rob", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту!")
    u["last_rob"] = time.time()
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "🔫 +300!")
    else: u["coins"] -= 200; bot.reply_to(msg, "🚔 -200!")
    save_db()

@bot.message_handler(commands=['steal'])
def steal(msg):
    if not msg.reply_to_message: return bot.reply_to(msg, "❌ Ответь на жертву!")
    u = get_u(msg.from_user.id); target = get_u(msg.reply_to_message.from_user.id)
    if target.get("antidote", 0) > 0: return bot.reply_to(msg, "🛡 У жертвы антидот!")
    if time.time() - u.get("last_steal", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту!")
    u["last_steal"] = time.time()
    if random.random() > 0.4: s = min(500, target["coins"]); target["coins"] -= s; u["coins"] += s; bot.reply_to(msg, f"🥷 Украл {s}!")
    else: u["coins"] -= 300; bot.reply_to(msg, "🚔 -300!")
    save_db()

@bot.message_handler(commands=['infect'])
def infect(msg):
    if not msg.reply_to_message: return bot.reply_to(msg, "❌ Ответь на жертву!")
    u = get_u(msg.from_user.id); target = get_u(msg.reply_to_message.from_user.id)
    if u["coins"] < 300: return bot.reply_to(msg, "❌ Нужно 300!")
    u["coins"] -= 300; target["dmg"] = max(1, target["dmg"] - 2); save_db(); bot.reply_to(msg, f"🦠 Заразил {target['name']}!")

@bot.message_handler(commands=['hack'])
def hack(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_hack", 0) < 3600: return bot.reply_to(msg, "❌ Раз в час!")
    if u["coins"] < 500 or u["dmg"] < 15: return bot.reply_to(msg, "❌ Нужно 500 монет и 15 урона!")
    u["last_hack"] = time.time(); u["coins"] -= 500
    if random.random() > 0.3:
        targets = [k for k in users if k != str(msg.from_user.id) and users[k]["coins"] > 1000]
        if targets:
            victim = random.choice(targets); loot = int(users[victim]["coins"] * 0.1)
            users[victim]["coins"] -= loot; u["coins"] += loot
            bot.reply_to(msg, f"💻 Взлом! Украл {loot} у {users[victim]['name']}!")
        else: u["coins"] += 500; bot.reply_to(msg, "💻 Взлом! Но все пустые, вернул 500.")
    else: bot.reply_to(msg, "🚨 Взлом провален! -500.")
    save_db()

def run_bot():
    cmds = [BotCommand("start", "Старт"), BotCommand("menu", "Меню"), BotCommand("shop", "Магазин"), BotCommand("massa", "Полетели"), BotCommand("profile", "Профиль"), BotCommand("top", "Топ"), BotCommand("business", "Бизнесы"), BotCommand("collect", "Собрать"), BotCommand("mine", "Шахта"), BotCommand("smuggle", "Контрабанда"), BotCommand("casino", "Казино"), BotCommand("loan", "Кредит"), BotCommand("paydebt", "Долг"), BotCommand("rob", "Ограбить"), BotCommand("steal", "Украсть"), BotCommand("infect", "Заразить"), BotCommand("hack", "Взлом"), BotCommand("daily", "Бонус")]
    bot.set_my_commands(cmds); bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
