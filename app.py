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
market_item = {"name": None, "price": 0, "time": 0}
crypto_price = 1000

BUSINESSES = {
    "farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600},
    "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800},
    "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}
}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "businesses": {}, "bank_deposit": 0, "bank_time": 0, "achieves": [], "last_loan": 0, "last_rob": 0, "last_steal": 0, "last_duel": 0, "last_boss_hit": 0}
    if name: users[uid_str]["name"] = name
    for k, v in {"businesses": {}, "achieves": [], "last_steal": 0, "last_duel": 0, "bank_deposit": 0}.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

def save_db():
    try:
        with open("users.json", "w", encoding="utf-8") as f: json.dump(users, f, ensure_ascii=False, indent=4)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="💾 База")
            try: bot.pin_chat_message(CHAT_ID, sent.message_id, disable_notification=True)
            except: pass
    except: pass

def load_db():
    global users
    try:
        chat = bot.get_chat(CHAT_ID)
        if chat.pinned_message and chat.pinned_message.document:
            downloaded = bot.download_file(bot.get_file(chat.pinned_message.document.file_id).file_path)
            users = json.loads(downloaded.decode('utf-8'))
            return
    except: pass
    users = {}
load_db()

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

@bot.message_handler(commands=['start'])
def start(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if msg.from_user.username: u["username"] = msg.from_user.username
    give_achieve(msg.from_user.id, "Первые шаги", 100)
    bot.send_message(msg.from_user.id, "Бот запущен!", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['help'])
def help_cmd(msg): bot.reply_to(msg, "📋 /profile /business /shop /top /bank /loan /rob /casino /boss /steal /infect /duel /achieves /save /ban")

@bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_loan", 0) < 10: return bot.reply_to(msg, "❌ Жди 10 сек!")
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Верни долг!")
    u["last_loan"] = time.time(); u["coins"] += 1000; u["debt"] += 1500; bot.reply_to(msg, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_rob", 0) < 10: return bot.reply_to(msg, "❌ Жди 10 сек!")
    u["last_rob"] = time.time()
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "🔫 +300!")
    else: p = min(200, u["coins"]); u["coins"] -= p; bot.reply_to(msg, f"🚔 -{p}")

@bot.message_handler(commands=['bank'])
def bank(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u.get("bank_deposit", 0) > 0:
        if time.time() - u.get("bank_time", 0) >= 86400:
            profit = int(u["bank_deposit"] * 1.2); u["coins"] += profit; u["bank_deposit"] = 0; bot.reply_to(msg, f"🏦 +{profit}")
        else: bot.reply_to(msg, "🏦 Жди 24ч.")
        return
    m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000")); bot.reply_to(msg, "🏦 Банк (20%)", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "bank_1000")
def bank_dep(call):
    u = get_u(call.from_user.id)
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 1000; u["bank_deposit"] = 1000; u["bank_time"] = time.time(); bot.answer_callback_query(call.id, "✅ Вложено!")

@bot.message_handler(commands=['steal'])
def steal(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_steal", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    u["last_steal"] = time.time()
    if random.random() > 0.4: s = min(500, target["coins"]); target["coins"] -= s; u["coins"] += s; bot.reply_to(msg, f"🥷 Украл {s}!")
    else: u["coins"] -= min(300, u["coins"]); bot.reply_to(msg, "🚔 Поймали!")

@bot.message_handler(commands=['infect'])
def infect(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    if tid == str(msg.from_user.id): return bot.reply_to(msg, "❌ Себя нельзя.")
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u["coins"] < 300: return bot.reply_to(msg, "❌ Нужно 300.")
    u["coins"] -= 300; target["virus_until"] = time.time() + 3600; bot.reply_to(msg, f"🦠 Заразил {target['name']}!")

@bot.message_handler(commands=['duel'])
def duel(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_duel", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    if tid == str(msg.from_user.id): return bot.reply_to(msg, "❌ Себя нельзя.")
    bet = int(msg.text.split()[-1]) if msg.text.split()[-1].isdigit() else 100
    if u["coins"] < bet: return bot.reply_to(msg, "❌ Мало.")
    u["last_duel"] = time.time()
    if random.random() > 0.5: u["coins"] += bet; target["coins"] -= bet; bot.reply_to(msg, f"🤺 Победил {target['name']}!")
    else: u["coins"] -= bet; target["coins"] += bet; bot.reply_to(msg, f"🤺 {target['name']} победил.")

@bot.message_handler(commands=['casino'])
def casino(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "❌ /casino 100")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "❌ Мало.")
    bot.send_dice(msg.chat.id, emoji="🎰"); time.sleep(3); res = random.randint(1, 64)
    if res == 64: u["coins"] += bet * 5; bot.reply_to(msg, f"🎰 ДЖЕКПОТ! +{bet*5}")
    elif res >= 32: u["coins"] += bet; bot.reply_to(msg, f"🎰 +{bet}")
    else: u["coins"] -= bet; bot.reply_to(msg, f"🎰 -{bet}")

@bot.message_handler(commands=['boss'])
def boss(msg):
    global boss_hp
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_boss_hit", 0) < 2: return bot.reply_to(msg, "❌ Жди 2 сек.")
    u["last_boss_hit"] = time.time()
    if boss_hp <= 0: boss_hp = 10000; return bot.reply_to(msg, "🐉 Новый босс!")
    dmg = u["dmg"]; boss_hp -= dmg; u["coins"] += dmg * 2
    bot.reply_to(msg, f"🐉 -{dmg} HP. Осталось {boss_hp}.")

@bot.message_handler(commands=['shop'])
def shop(msg):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"), types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"), types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"))
    bot.reply_to(msg, "🛒 **Магазин**", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_cb(call):
    u = get_u(call.from_user.id); i = call.data.split("_")[1]
    p = BUSINESSES[i]["price"]
    if u["coins"] < p: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= p
    if "businesses" not in u: u["businesses"] = {}
    u["businesses"][i] = 0
    save_db()
    bot.answer_callback_query(call.id, f"✅ {BUSINESSES[i]['name']} куплен!")

@bot.message_handler(commands=['business'])
def business_menu(msg):
    u = get_u(msg.from_user.id)
    if not u.get("businesses"): return bot.reply_to(msg, "🏢 Купи в /shop.")
    text = "🏢 **БИЗНЕС**\n\n"
    for b, l in u["businesses"].items(): text += f"{BUSINESSES[b]['name']} — {'✅' if time.time() - l >= BUSINESSES[b]['cooldown'] else '⏳'}\n"
    m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect")); bot.reply_to(msg, text, reply_markup=m, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "biz_collect")
def biz_collect(call):
    u = get_u(call.from_user.id); total = 0
    for b, l in list(u["businesses"].items()):
        if time.time() - l >= BUSINESSES[b]["cooldown"]: total += BUSINESSES[b]["income"]; u["businesses"][b] = time.time()
    if total > 0: u["coins"] += total; save_db(); bot.answer_callback_query(call.id, f"✅ {total}!")
    else: bot.answer_callback_query(call.id, "⏳ Пусто.")

@bot.message_handler(commands=['top'])
def top(msg):
    s = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True); t = "🏆 **Топ:**\n\n"
    for i, (uid, d) in enumerate(s, 1): t += f"{i}. {d.get('name', 'Игрок')} — {d['coins']}\n"
    bot.reply_to(msg, t[:4000])

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    bot.reply_to(msg, f"👤 {u['name']}\n💰 {u['coins']}\n🏆 Ачивок: {len(u['achieves'])}")

@bot.message_handler(commands=['achieves'])
def show_achieves(msg):
    u = get_u(msg.from_user.id)
    if not u["achieves"]: return bot.reply_to(msg, "Нет ачивок.")
    bot.reply_to(msg, "🏆 Ачивки:\n" + "\n".join(u["achieves"]))

@bot.message_handler(commands=['give'])
def give(msg):
    if msg.from_user.id != OWNER_ID: return
    parts = msg.text.split()
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        if parts[1] in users: users[parts[1]]["coins"] += int(parts[2]); save_db(); bot.reply_to(msg, "💸 Выдано!")
        else: bot.reply_to(msg, "❌ Не найден.")
    else: bot.reply_to(msg, "❌ /give [ID] [Сумма]")

@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if msg.from_user.id != OWNER_ID: return
    text = msg.text.replace("/broadcast", "").strip()
    if not text: return bot.reply_to(msg, "❌ Пусто.")
    c = 0
    for uid in users.keys():
        try: bot.send_message(int(uid), f"📢 {text}"); c += 1
        except: pass
    bot.reply_to(msg, f"✅ {c} игрокам.")

@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.id != OWNER_ID: return
    if msg.reply_to_message:
        target_id = str(msg.reply_to_message.from_user.id)
        if target_id in users: del users[target_id]; save_db(); bot.reply_to(msg, f"🚫 {target_id} удален!")
        else: bot.reply_to(msg, "❌ Нет в базе.")
        return
    parts = msg.text.split()
    if len(parts) < 2: return bot.reply_to(msg, "❌ /ban [ID] или Reply")
    if parts[1] in users: del users[parts[1]]; save_db(); bot.reply_to(msg, f"🚫 {parts[1]} удален!")
    else: bot.reply_to(msg, "❌ Не найден.")

@bot.message_handler(commands=['save'])
def save_cmd(msg):
    if msg.from_user.id == OWNER_ID: save_db(); bot.reply_to(msg, "💾 ОК!")

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_msg(msg):
    if msg.chat.type != 'private': return
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if msg.from_user.username: u["username"] = msg.from_user.username
    if msg.from_user.id == OWNER_ID:
        if msg.reply_to_message:
            t = pending_messages.get(msg.reply_to_message.message_id)
            if t:
                try: bot.copy_message(t, msg.chat.id, msg.message_id); bot.reply_to(msg, "✅!")
                except: pass
        else:
            try: bot.forward_message(FRIEND_ID, msg.chat.id, msg.message_id); bot.forward_message(OWNER_ID, msg.chat.id, msg.message_id)
            except: pass

def run_bot():
    cmds = [BotCommand("start", "Старт"), BotCommand("help", "Справка"), BotCommand("profile", "Профиль"), BotCommand("top", "Топ"), BotCommand("shop", "Магазин"), BotCommand("business", "Бизнесы"), BotCommand("bank", "Банк"), BotCommand("loan", "Кредит"), BotCommand("rob", "Ограбить"), BotCommand("boss", "Босс"), BotCommand("casino", "Казино"), BotCommand("steal", "Украсть"), BotCommand("infect", "Заразить"), BotCommand("duel", "Дуэль"), BotCommand("achieves", "Ачивки"), BotCommand("save", "Сохранить")]
    bot.set_my_commands(cmds)
    print("🚀 ЗАПУЩЕН!")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ========== ПАТЧ: ВОЗВРАЩАЕМ АНТИДОТ, ГИФТ, РАССЫЛКИ ==========

# 1. Возвращаем Антидот в магазин
@bot.message_handler(commands=['shop'])
def shop_patch(msg):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"))
    m.add(types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"))
    m.add(types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"))
    m.add(types.InlineKeyboardButton("💊 Антидот (500)", callback_data="buy_antidote"))
    bot.reply_to(msg, "🛒 **Магазин**", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "buy_antidote")
def buy_antidote_patch(call):
    u = get_u(call.from_user.id)
    if u["coins"] < 500: return bot.answer_callback_query(call.id, "❌ Мало монет!")
    u["coins"] -= 500
    if "virus_until" in u: u["virus_until"] = 0
    save_db()
    bot.answer_callback_query(call.id, "💊 Ты вылечился!")

# 2. Возвращаем /gift (подарить монеты)
@bot.message_handler(commands=['gift'])
def gift_patch(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        a = int(parts[-1])
        if u["coins"] < a: return bot.reply_to(msg, "❌ Мало.")
        u["coins"] -= a; target["coins"] += a; save_db()
        bot.reply_to(msg, f"🎁 Подарил {a} игроку {target['name']}!")
    else: bot.reply_to(msg, "❌ /gift [ID] [Сумма]")

# 3. Возвращаем /broadcast (рассылка в ЛС)
@bot.message_handler(commands=['broadcast'])
def broadcast_patch(msg):
    if msg.from_user.id != OWNER_ID: return
    text = msg.text.replace("/broadcast", "").strip()
    if not text: return bot.reply_to(msg, "❌ Пусто.")
    c = 0
    for uid in users.keys():
        try: bot.send_message(int(uid), f"📢 {text}"); c += 1
        except: pass
    bot.reply_to(msg, f"✅ {c} игрокам.")

# 4. Возвращаем /sendchat (рассылка в чат)
@bot.message_handler(commands=['sendchat'])
def sendchat_patch(msg):
    if msg.from_user.id != OWNER_ID: return
    text = msg.text.replace("/sendchat", "").strip()
    if not text: return bot.reply_to(msg, "❌ Пусто.")
    try: bot.send_message(CHAT_ID, text); bot.reply_to(msg, "✅ Отправлено в чат!")
    except Exception as e: bot.reply_to(msg, f"❌ {e}")
