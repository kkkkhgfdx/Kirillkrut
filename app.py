import telebot, random, json, os, time, threading
from telebot import types
from telebot.types import BotCommand
from flask import Flask

TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0"
OWNER_ID = 6170286634
FRIEND_ID = 7527864291
CHAT_ID = -1004215885788

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp, pending_messages = {}, 10000, {}
duel_club = {"pot": 0, "players": {}}
clans = {}

BUSINESSES = {
    "farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600},
    "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800},
    "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}
}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "businesses": {}, "bank_deposit": 0, "bank_time": 0, "achieves": [], "last_loan": 0, "last_rob": 0, "last_steal": 0, "last_duel": 0, "last_boss_hit": 0, "last_mine": 0, "last_smuggle": 0, "has_chest": False, "last_daily": 0, "clan": None, "clan_rank": None, "safe": 0}
    if name: users[uid_str]["name"] = name
    for k, v in {"businesses": {}, "achieves": [], "last_steal": 0, "last_duel": 0, "bank_deposit": 0, "has_chest": False, "clan": None, "clan_rank": None, "debt": 0, "safe": 0}.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

def save_db():
    try:
        data = {"users": users, "clans": clans}
        with open("users.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="💾 База Синдиката 74.0")
            try: bot.pin_chat_message(CHAT_ID, sent.message_id, disable_notification=True)
            except: pass
    except: pass

def load_db():
    global users, clans
    try:
        chat = bot.get_chat(CHAT_ID)
        if chat.pinned_message and chat.pinned_message.document:
            downloaded = bot.download_file(bot.get_file(chat.pinned_message.document.file_id).file_path)
            data = json.loads(downloaded.decode('utf-8'))
            if "users" in data and "clans" in data: users, clans = data["users"], data["clans"]
            else: users = data
            return
    except: pass
    users, clans = {}, {}
load_db()

@app.route('/')
def health(): return "OK", 200

def give_achieve(uid, name, reward):
    u = get_u(uid)
    if name not in u["achieves"]:
        u["achieves"].append(name); u["coins"] += reward
        try: bot.send_message(CHAT_ID, f"🏆 **АЧИВКА!** {u['name']} получил **{name}**!")
        except: pass

def get_target(msg):
    if msg.reply_to_message: return str(msg.reply_to_message.from_user.id), get_u(msg.reply_to_message.from_user.id)
    parts = msg.text.split()
    if len(parts) > 1 and parts[1].startswith("@"):
        un = parts[1].replace("@", "").lower()
        for uid, data in users.items():
            if data.get("username", "").lower() == un: return uid, data
    return None, None

def main_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"), types.InlineKeyboardButton("🛒 Магазин", callback_data="menu_shop"))
    kb.add(types.InlineKeyboardButton("🏢 Бизнесы", callback_data="menu_biz"), types.InlineKeyboardButton("🏦 Банк", callback_data="menu_bank"))
    kb.add(types.InlineKeyboardButton("🐉 Босс", callback_data="menu_boss"), types.InlineKeyboardButton("🎰 Казино", callback_data="menu_casino"))
    kb.add(types.InlineKeyboardButton("⛏ Шахта", callback_data="menu_mine"), types.InlineKeyboardButton("🕵️ Контрабанда", callback_data="menu_smuggle"))
    kb.add(types.InlineKeyboardButton("🛡 Кланы", callback_data="menu_clans"), types.InlineKeyboardButton("🏆 Топ", callback_data="menu_top"))
    kb.add(types.InlineKeyboardButton("🎁 Ежедневка", callback_data="menu_daily"))
    return kb

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.message.reply_to_message and call.message.reply_to_message.from_user.id != call.from_user.id:
        return bot.answer_callback_query(call.id, "❌ Меню не твое!", show_alert=True)
    global boss_hp
    u = get_u(call.from_user.id, call.from_user.first_name)
    uid = str(call.from_user.id)
    
    if call.data.startswith("buy_") or call.data == "open_chest":
        if call.data == "open_chest":
            if not u.get("has_chest"): return bot.answer_callback_query(call.id, "❌ Нет кейса.")
            u["has_chest"] = False
            if random.random() > 0.5: u["coins"] += 2000; bot.answer_callback_query(call.id, "✅ +2000!")
            else: u["dmg"] += 5; bot.answer_callback_query(call.id, "✅ +5 урона!")
            save_db(); return
        i = call.data.split("_")[1]
        if i == "antidote":
            if u["coins"] < 500: return bot.answer_callback_query(call.id, "❌")
            u["coins"] -= 500; save_db(); return bot.answer_callback_query(call.id, "💊 ОК!")
        p = BUSINESSES[i]["price"]
        if u["coins"] < p: return bot.answer_callback_query(call.id, "❌ Мало!")
        u["coins"] -= p
        if "businesses" not in u: u["businesses"] = {}
        u["businesses"][i] = time.time() - BUSINESSES[i]["cooldown"]
        save_db(); bot.answer_callback_query(call.id, f"✅ {BUSINESSES[i]['name']} куплен!"); return

    if call.data == "menu_main": 
        bot.edit_message_text("🚜 Синдикат 74.0", call.message.chat.id, call.message.message_id, reply_markup=main_kb(call.from_user.id))
    elif call.data == "menu_profile":
    clan_name = clans[u["clan"]]["name"] if u.get("clan") and u["clan"] in clans else "Нет"
    text = f"👤 {u['name']}\n💰 Монеты: {u['coins']}\n🏦 Долг: {u.get('debt', 0)}\n🔒 Сейф: {u.get('safe', 0)}\n📈 Уровень: {u['lvl']}\n🏢 Бизнесов: {len(u['businesses'])}\n🛡 Клан: {clan_name}"
    kb = types.InlineKeyboardMarkup()
    if u.get("debt", 0) > 0: kb.add(types.InlineKeyboardButton("💸 Вернуть долг", callback_data="pay_debt"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
elif call.data == "pay_debt":
    if u.get("debt", 0) <= 0: return bot.answer_callback_query(call.id, "✅ Нет долгов!")
    if u["coins"] < u["debt"]: return bot.answer_callback_query(call.id, f"❌ Мало! Долг: {u['debt']}")
    u["coins"] -= u["debt"]; u["debt"] = 0; save_db()
    bot.answer_callback_query(call.id, "✅ Долг погашен!")
elif call.data == "menu_shop":
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🌾 Ферма", callback_data="buy_farm"))
    kb.add(types.InlineKeyboardButton("🌳 Сад", callback_data="buy_garden"))
    kb.add(types.InlineKeyboardButton("🏭 Завод", callback_data="buy_factory"))
    kb.add(types.InlineKeyboardButton("💊 Антидот", callback_data="buy_antidote"))
    kb.add(types.InlineKeyboardButton("🎁 Кейс", callback_data="open_chest"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
    bot.edit_message_text("🛒 Магазин", call.message.chat.id, call.message.message_id, reply_markup=kb)
elif call.data == "menu_clans":
    if u.get("clan"):
        text = "Ты в клане"
        kb = types.InlineKeyboardMarkup()
        if str(clans[str(u['clan'])]['leader']) == uid: 
            kb.add(types.InlineKeyboardButton("⚔️ Рейд", callback_data="clan_raid_menu"))
            kb.add(types.InlineKeyboardButton("🔗 Инвайт", callback_data=f"clan_invite_{u['clan']}"))
        kb.add(types.InlineKeyboardButton("💸 Вложить", callback_data="clan_deposit"))
        kb.add(types.InlineKeyboardButton("🛡 Апгрейд", callback_data="clan_upgrade"))
        kb.add(types.InlineKeyboardButton("👥 Люди", callback_data="clan_members"))
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Создать", callback_data="clan_create"))
        kb.add(types.InlineKeyboardButton("📋 Список", callback_data="clan_list"))
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text("🛡 Кланы", call.message.chat.id, call.message.message_id, reply_markup=kb)
elif call.data == "clan_create":
    if u["coins"] < 5000: return bot.answer_callback_query(call.id, "❌ Нужно 5000!")
    u["coins"] -= 5000
    c_id = str(random.randint(10000, 99999))
    while c_id in clans: c_id = str(random.randint(10000, 99999))
    clans[c_id] = {"name": f"Клан_{u['name'][:5]}", "leader": uid, "bank": 0, "rep": 0, "lvl": 1, "def": 0, "members": [uid]}
    u["clan"] = c_id
    u["clan_rank"] = "Лидер"
    save_db()
    bot.answer_callback_query(call.id, "✅ Клан создан!")
elif call.data == "clan_list":
    bot.answer_callback_query(call.id, "Список кланов")
elif call.data == "clan_deposit":
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 1000; clans[u["clan"]]["bank"] += 1000; save_db(); bot.answer_callback_query(call.id, "✅ +1000")
elif call.data == "clan_upgrade":
    if u.get("clan_rank") != "Лидер": return bot.answer_callback_query(call.id, "❌ Только Лидер!")
    c = clans[u["clan"]]; cost = c.get("lvl", 1) * 5000
    if c.get("bank", 0) < cost: return bot.answer_callback_query(call.id, f"❌ Нужно {cost}")
    c["bank"] -= cost; c["lvl"] += 1; c["def"] += 50; save_db(); bot.answer_callback_query(call.id, "✅ Апгрейд!")
elif call.data == "clan_members":
    bot.answer_callback_query(call.id, "Люди")
elif call.data == "clan_raid_menu":
    bot.answer_callback_query(call.id, "Выбери врага")
elif call.data.startswith("clan_invite_"):
    c_id = call.data.split("_")[2]
    bot.send_message(call.message.chat.id, "Вступить в клан:", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Вступить", callback_data=f"clan_join_{c_id}")))
elif call.data.startswith("clan_join_"):
    c_id = call.data.split("_")[2]
    if c_id not in clans or u.get("clan"): return bot.answer_callback_query(call.id, "❌ Ошибка")
    u["clan"] = c_id; u["clan_rank"] = "Боец"; clans[c_id]["members"].append(uid); save_db(); bot.answer_callback_query(call.id, "✅ Вступил!")
elif call.data == "menu_bank":
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000"))
    kb.add(types.InlineKeyboardButton("🔒 В сейф 1000", callback_data="safe_1000"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
    bot.edit_message_text("🏦 Банк / Сейф", call.message.chat.id, call.message.message_id, reply_markup=kb)
elif call.data == "bank_1000":
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 1000; u["bank_deposit"] = u.get("bank_deposit", 0) + 1000; save_db(); bot.answer_callback_query(call.id, "✅ Вложено!")
elif call.data == "safe_1000":
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 1000; u["safe"] = u.get("safe", 0) + 1000; save_db(); bot.answer_callback_query(call.id, "🔒 В сейфе!")
elif call.data == "menu_biz":
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
    bot.edit_message_text("🏢 Бизнесы", call.message.chat.id, call.message.message_id, reply_markup=kb)
elif call.data == "biz_collect":
    total = 0
    for b, l in list(u["businesses"].items()):
        if time.time() - l >= BUSINESSES[b]["cooldown"]: total += BUSINESSES[b]["income"]; u["businesses"][b] = time.time()
    if total > 0: u["coins"] += total; save_db(); bot.answer_callback_query(call.id, f"✅ Собрано: {total}!")
    else: bot.answer_callback_query(call.id, "⏳ Пусто")
elif call.data == "menu_boss":
    text = f"🐉 Босс: {boss_hp}/10000 HP"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⚔️ Ударить", callback_data="hit_boss"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
elif call.data == "hit_boss":
    if boss_hp <= 0: boss_hp = 10000
    dmg = u["dmg"]; boss_hp -= dmg; u["coins"] += dmg * 2; save_db()
    bot.answer_callback_query(call.id, f"⚔️ -{dmg} HP. Осталось {boss_hp}")
elif call.data == "menu_casino":
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎰 Слоты 100", callback_data="casino_slots"))
    kb.add(types.InlineKeyboardButton("🎡 Рулетка 1000", callback_data="casino_roulette"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
    bot.edit_message_text("🎰 Казино", call.message.chat.id, call.message.message_id, reply_markup=kb)
elif call.data == "casino_slots":
    if u["coins"] < 100: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 100
    if random.random() > 0.5: u["coins"] += 200; bot.answer_callback_query(call.id, "✅ +200!")
    else: bot.answer_callback_query(call.id, "💀 -100!")
    save_db()
elif call.data == "casino_roulette":
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 1000
    if random.random() > 0.5: u["coins"] += 3000; bot.answer_callback_query(call.id, "🔥 +3000!")
    else: bot.answer_callback_query(call.id, "💀 -1000!")
    save_db()
elif call.data == "menu_mine":
    bot.answer_callback_query(call.id, "⛏ Шахта")
elif call.data == "menu_smuggle":
    bot.answer_callback_query(call.id, "🕵️ Контрабанда")
elif call.data == "menu_top":
    s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
    t = "🏆 Топ:\n"
    for i, (uid, d) in enumerate(s[:10], 1): t += f"{i}. {d.get('name', 'Игрок')} — {d.get('coins', 0)}\n"
    bot.edit_message_text(t, call.message.chat.id, call.message.message_id)
elif call.data == "menu_daily":
    if time.time() - u.get("last_daily", 0) < 86400: return bot.answer_callback_query(call.id, "❌ Раз в сутки!")
    u["last_daily"] = time.time(); u["has_chest"] = True; save_db(); bot.answer_callback_query(call.id, "🎁 Кейс получен")
@bot.message_handler(commands=['start', 'menu'])
def start(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if msg.from_user.username: u["username"] = msg.from_user.username
    if msg.text == "/start": give_achieve(msg.from_user.id, "Первые шаги", 100)
    bot.send_message(msg.chat.id, f"🔥 Синдикат 74.0\nПривет, {msg.from_user.first_name}!", reply_markup=main_kb(msg.from_user.id))

@bot.message_handler(commands=['massa'])
def massa_cmd(msg):
    photo_id = "AgACAgIAAxkBAAEkcFJq82R-iFmb58gRRvHJHCBj4IAJzwACfiNrG0LGmUutKyBc9t_cdwEAAwIAA3kAAz0E"
    try:
        bot.send_photo(msg.chat.id, photo_id, caption="✈️ **Полетели, масса!**", parse_mode="Markdown")
    except:
        bot.reply_to(msg, "✈️ Полетели, масса!")

@bot.message_handler(commands=['myclan'])
def myclan_cmd(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if not u.get("clan"): return bot.reply_to(msg, "🛡 Нет клана.")
    bot.reply_to(msg, "Твой клан")

@bot.message_handler(commands=['clantop'])
def clantop_cmd(msg):
    bot.reply_to(msg, "Топ кланов")

@bot.message_handler(commands=['paydebt'])
def paydebt_cmd(msg):
    u = get_u(msg.from_user.id)
    if u.get("debt", 0) <= 0: return bot.reply_to(msg, "✅ Нет долгов!")
    if u["coins"] < u["debt"]: return bot.reply_to(msg, f"❌ Мало! Долг: {u['debt']}")
    u["coins"] -= u["debt"]; u["debt"] = 0; save_db(); bot.reply_to(msg, "✅ Долг погашен!")

@bot.message_handler(commands=['mine'])
def mine(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_mine", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    u["last_mine"] = time.time(); res = random.random()
    if res > 0.8: w = 1000; u["coins"] += w; bot.reply_to(msg, f"💎 +{w}!")
    else: w = min(200, u["coins"]); u["coins"] -= w; bot.reply_to(msg, f"💥 -{w}.")
    save_db()

@bot.message_handler(commands=['smuggle'])
def smuggle(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_smuggle", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    if u["coins"] < 1000: return bot.reply_to(msg, "❌ Нужно 1000.")
    u["last_smuggle"] = time.time()
    if random.random() > 0.5: u["coins"] += 3000; bot.reply_to(msg, "🕵️ +3000!")
    else: u["coins"] -= 1000; bot.reply_to(msg, "🚔 -1000!")
    save_db()

@bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_loan", 0) < 10: return bot.reply_to(msg, "❌ Жди 10с.")
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Верни долг!")
    u["last_loan"] = time.time(); u["coins"] += 1000; u["debt"] += 1500; bot.reply_to(msg, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_rob", 0) < 10: return bot.reply_to(msg, "❌ Жди 10с.")
    u["last_rob"] = time.time()
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "🔫 +300!")
    else: p = min(200, u["coins"]); u["coins"] -= p; bot.reply_to(msg, f"🚔 -{p}")

@bot.message_handler(commands=['casino'])
def casino(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "❌ /casino 100")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "❌ Мало.")
    if random.random() > 0.5: u["coins"] += bet; bot.reply_to(msg, f"🎰 +{bet}")
    else: u["coins"] -= bet; bot.reply_to(msg, f"🎰 -{bet}")
    save_db()

@bot.message_handler(commands=['boss'])
def boss(msg):
    global boss_hp
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_boss_hit", 0) < 2: return bot.reply_to(msg, "❌ Жди 2 сек.")
    u["last_boss_hit"] = time.time()
    if boss_hp <= 0: boss_hp = 10000
    dmg = u["dmg"]; boss_hp -= dmg; u["coins"] += dmg * 2; save_db()
    bot.reply_to(msg, f"🐉 -{dmg} HP. Осталось {boss_hp}.")

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    bot.reply_to(msg, f"👤 {u['name']}\n💰 {u['coins']}\n🏦 Долг: {u.get('debt', 0)}")

@bot.message_handler(commands=['top'])
def top(msg):
    s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
    t = "🏆 Топ:\n"
    for i, (uid, d) in enumerate(s[:10], 1): t += f"{i}. {d.get('name', 'Игрок')} — {d.get('coins', 0)}\n"
    bot.reply_to(msg, t)

@bot.message_handler(commands=['save'])
def save_cmd(msg):
    if msg.from_user.id == OWNER_ID: save_db(); bot.reply_to(msg, "💾 ОК!")

def run_bot():
    cmds = [
        BotCommand("menu", "Меню"), BotCommand("start", "Старт"), BotCommand("help", "Справка"),
        BotCommand("profile", "Профиль"), BotCommand("top", "Топ"), BotCommand("shop", "Магазин"),
        BotCommand("business", "Бизнесы"), BotCommand("bank", "Банк"), BotCommand("loan", "Кредит"),
        BotCommand("paydebt", "Вернуть долг"), BotCommand("rob", "Ограбить"), BotCommand("boss", "Босс"),
        BotCommand("casino", "Казино"), BotCommand("mine", "Шахта"), BotCommand("smuggle", "Контрабанда"),
        BotCommand("steal", "Украсть"), BotCommand("duel", "Дуэль"), BotCommand("myclan", "Мой Клан"),
        BotCommand("clantop", "Топ Кланов"), BotCommand("daily", "Бонус"), BotCommand("massa", "Полетели, масса!")
    ]
    bot.set_my_commands(cmds)
    print("🚀 СИНДИКАТ 74.0 ЗАПУЩЕН!")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
