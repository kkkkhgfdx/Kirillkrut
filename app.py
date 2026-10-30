import telebot, random, json, os, time, threading
from telebot import types
from flask import Flask

# ========== НАСТРОЙКИ ==========
TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0"
OWNER_ID = 6170286634
FRIEND_ID = 7527864291
CHAT_ID = -1004215885788

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp, pending_messages, crypto_price = {}, 10000, {}, 1000
market_item = {"name": None, "price": 0, "time": 0}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "xp": 0, "dmg": 10, "name": name or "Игрок", "businesses": {}, "clan": None, "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_roulette": 0, "last_casino": 0, "last_daily": 0, "achieves": [], "last_arena": 0, "multi": 1, "last_steal": 0, "casino_plays": 0, "last_loan": 0, "last_rob": 0, "last_craft": 0, "last_duel": 0}
    if name: users[uid_str]["name"] = name
    defaults = {"businesses": {}, "clan": None, "debt": 0, "dmg": 10, "name": "Игрок", "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_roulette": 0, "last_casino": 0, "last_daily": 0, "achieves": [], "last_arena": 0, "multi": 1, "last_steal": 0, "casino_plays": 0, "last_loan": 0, "last_rob": 0, "last_craft": 0, "last_duel": 0}
    for k, v in defaults.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

def save_db():
    try:
        with open("users.json", "w", encoding="utf-8") as f: json.dump(users, f, ensure_ascii=False, indent=4)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="💾 База")
            try: bot.pin_chat_message(CHAT_ID, sent.message_id, disable_notification=True)
            except: pass
    except Exception as e: print(f"Err: {e}")

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
        try: bot.send_message(CHAT_ID, f"🏆 **НОВАЯ АЧИВКА!**\n👤 Игрок: **{u['name']}**\n🎖 Достижение: **{name}**\n💰 Награда: {reward} монет!", parse_mode="Markdown")
        except: pass

def add_xp(uid, amt):
    u = get_u(uid); u["xp"] += amt
    while u["xp"] >= 100 * u["lvl"]:
        u["xp"] -= 100 * u["lvl"]; u["lvl"] += 1; u["coins"] += 200; u["dmg"] += 2
        if u["lvl"] >= 10: give_achieve(uid, "Коллекционер", 1500)
        if u["coins"] >= 10000: give_achieve(uid, "Богач", 2000)

BUSINESSES = {"farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600}, "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800}, "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}}

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
    markup = types.ReplyKeyboardRemove(selective=False)
    if msg.from_user.id == OWNER_ID: bot.send_message(msg.from_user.id, "👑 Босс, Синдикат запущен!", reply_markup=markup)
    else: bot.reply_to(msg, "Привет! Пиши /help.", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.reply_to(msg, "📋 /profile /business /clan /slots /market /arena /craft /casino /roulette /bank /loan /rob /boss /steal /infect /duel /daily /shop /top /achieves /save /reset")
    
    @bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_loan", 0) < 10: return bot.reply_to(msg, "❌ Жди 10 секунд!")
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Сначала верни прошлый долг!")
    u["last_loan"] = time.time(); u["coins"] += 1000; u["debt"] += 1500; bot.reply_to(msg, "🏦 Ты взял 1000. Долг: 1500.")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_rob", 0) < 10: return bot.reply_to(msg, "❌ Жди 10 секунд!")
    u["last_rob"] = time.time()
    if random.random() > 0.5: u["coins"] += 300; add_xp(msg.from_user.id, 10); bot.reply_to(msg, "🔫 Ты ограбил казну и получил +300!")
    else: p = min(200, u["coins"]); u["coins"] -= p; bot.reply_to(msg, f"🚔 Тебя поймали! Штраф: -{p}")

@bot.message_handler(commands=['bank'])
def bank(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u.get("bank_deposit", 0) > 0:
        if time.time() - u.get("bank_time", 0) >= 86400:
            profit = int(u["bank_deposit"] * 1.2); u["coins"] += profit; u["bank_deposit"] = 0; bot.reply_to(msg, f"🏦 Вклад закрыт! Ты получил {profit} монет.")
        else: bot.reply_to(msg, "🏦 Твой вклад еще работает. Жди 24 часа.")
        return
    markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000"))
    bot.reply_to(msg, "🏦 **Банк**\nВложи 1000 под 20% в сутки.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "bank_1000")
def bank_dep(call):
    u = get_u(call.from_user.id)
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало монет!")
    u["coins"] -= 1000; u["bank_deposit"] = 1000; u["bank_time"] = time.time(); bot.answer_callback_query(call.id, "✅ Вложено 1000!")

@bot.message_handler(commands=['daily'])
def daily(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_daily", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки!")
    u["last_daily"] = time.time(); u["coins"] += 500; add_xp(msg.from_user.id, 100); u["has_chest"] = True; bot.reply_to(msg, "🎁 +500 и Кейс!")

@bot.message_handler(commands=['casino'])
def casino(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_casino", 0) < 10: return bot.reply_to(msg, "❌ Жди 10 сек.")
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "❌ /casino 100")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "❌ Мало.")
    u["last_casino"] = time.time(); u["casino_plays"] = u.get("casino_plays", 0) + 1
    if u["casino_plays"] >= 10: give_achieve(msg.from_user.id, "Игроман", 1000)
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
    dmg = u["dmg"] + int(u["dmg"] * (u.get("clan_dmg_bonus", 0) / 100)) if u.get("clan") else u["dmg"]
    boss_hp -= dmg; r = 10 + u["lvl"]; u["coins"] += r
    if boss_hp <= 0: u["coins"] += 2000; give_achieve(msg.from_user.id, "Босс-убийца", 5000); bot.send_message(msg.chat.id, f"💀 БОСС УБИТ! {u['name']} +2000!")
    else: bot.reply_to(msg, f"🐉 -{dmg} HP. Осталось {boss_hp}. +{r}")

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name); c = u.get("clan") or "Нет"
    bot.reply_to(msg, f"👤 **{u['name']}**\n🏅 Ур: {u['lvl']}\n💰 {u['coins']}\n⚔️ Урон: {u['dmg']}\n🛡 Клан: {c}\n🌟 Множитель: x{u.get('multi', 1)}\n🏆 Ачивок: {len(u.get('achieves', []))}", parse_mode="Markdown")

@bot.message_handler(commands=['top'])
def top(msg):
    sorted_users = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True)
    if not sorted_users: return bot.reply_to(msg, "Пока никто не играл.")
    text = "🏆 **Полный топ игроков:**\n\n"
    for i, (uid, d) in enumerate(sorted_users, 1):
        text += f"{i}. {d.get('name', 'Игрок')} — {d['coins']} монет\n"
    for x in range(0, len(text), 4000):
        bot.send_message(msg.chat.id, text[x:x+4000], parse_mode="Markdown")

@bot.message_handler(commands=['save'])
def save_cmd(msg):
    if msg.from_user.id == OWNER_ID: save_db(); bot.reply_to(msg, "💾 ОК!")

@bot.message_handler(commands=['reset'])
def reset_cmd(msg):
    if msg.from_user.id != OWNER_ID: return
    parts = msg.text.split()
    if len(parts) < 2: return bot.reply_to(msg, "❌ /reset @юзер")
    un = parts[1].replace("@", "").lower()
    for uid, d in users.items():
        if d.get("username", "").lower() == un: d["coins"] = 0; save_db(); bot.reply_to(msg, f"🧹 {un} обнулен!"); return

def run_bot():
    print("🚀 СИНДИКАТ ЗАПУЩЕН.")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
