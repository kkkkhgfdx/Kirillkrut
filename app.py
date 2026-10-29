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
TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0" 
OWNER_ID = 6170286634       
FRIEND_ID = 7527864291      
CHAT_ID = -1002021366605    

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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
            "clan": None, "last_daily": 0, "virus_until": 0, "username": "",
            "bank_deposit": 0, "bank_time": 0
        }
        save_db()
    for key in ["businesses", "clan", "virus_until", "bank_deposit", "bank_time"]:
        if key not in users[uid_str]: 
            if key == "businesses": users[uid_str][key] = {}
            elif key == "clan": users[uid_str][key] = None
            else: users[uid_str][key] = 0
    return users[uid_str]

def find_user_by_username(username):
    username = username.replace("@", "").lower()
    for uid, data in users.items():
        if data.get("username", "").lower() == username:
            return uid, data
    return None, None

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
        BotCommand("bank", "🏦 Банк"),
        BotCommand("casino", "🎰 Казино"),
        BotCommand("clan", "🛡 Кланы"),
        BotCommand("infect", "🦠 Заразить"),
        BotCommand("steal", "🥷 Украсть"),
        BotCommand("daily", "🎁 Бонус"),
        BotCommand("boss", "🐉 Босс"),
        BotCommand("top", "🏆 Топ"),
        BotCommand("help", "📋 Справка")
    ]
    bot.set_my_commands(commands)

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    user = get_user(uid)
    user["name"] = message.from_user.first_name or "Игрок"
    if message.from_user.username: user["username"] = message.from_user.username
    save_db()
    
    if uid == OWNER_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👤 Профиль", "🏢 Бизнесы", "🛡 Кланы", "🎁 Бонус")
        bot.send_message(uid, "👑 Босс, Синдикат Ultimate запущен. Всё стабильно!", reply_markup=markup)
    else:
        bot.reply_to(message, "Привет! Пиши /help.")

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['profile'])
def profile(message):
    user = get_user(message.from_user.id)
    virus = "🦠 Заражен!" if user.get("virus_until", 0) > time.time() else ""
    clan = user.get("clan") or "Нет"
    bank = f"\n🏦 Вклад: {user['bank_deposit']}" if user.get("bank_deposit", 0) > 0 else ""
    bot.reply_to(message, f"👤 **{user['name']}**\n💰 {user['coins']}\n🛡 Клан: {clan}{bank}\n{virus}", parse_mode="Markdown")

@bot.message_handler(commands=['clan'])
def clan_menu(message):
    user = get_user(message.from_user.id)
    if user.get("clan"): 
        return bot.reply_to(message, f"🛡 Ты в клане: **{user['clan']}**", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Создать клан (5000)", callback_data="clan_create"))
    bot.reply_to(message, "🛡 **Кланы**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "clan_create")
def clan_create(call):
    user = get_user(call.from_user.id)
    if user["coins"] < 5000: return bot.answer_callback_query(call.id, "❌ Мало монет!")
    user["coins"] -= 5000; user["clan"] = f"Клан_{user['name']}"; save_db()
    bot.answer_callback_query(call.id, "✅ Клан создан!")

@bot.message_handler(commands=['bank'])
def bank(message):
    user = get_user(message.from_user.id)
    if user["bank_deposit"] > 0:
        passed = int(time.time()) - user["bank_time"]
        if passed >= 86400:
            profit = int(user["bank_deposit"] * 1.2)
            user["coins"] += profit; user["bank_deposit"] = 0; save_db()
            return bot.reply_to(message, f"🏦 Получено {profit} монет (с процентами).")
        return bot.reply_to(message, f"🏦 Жди еще {(86400 - passed) // 3600} ч.")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000"))
    bot.reply_to(message, "🏦 **Банк (20% в сутки)**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "bank_1000")
def bank_dep(call):
    user = get_user(call.from_user.id)
    if user["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало монет!")
    user["coins"] -= 1000; user["bank_deposit"] += 1000; user["bank_time"] = int(time.time()); save_db()
    bot.answer_callback_query(call.id, "✅ Вложено 1000!")

@bot.message_handler(commands=['casino'])
def casino(message):
    user = get_user(message.from_user.id)
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(message, "❌ /casino 100")
    bet = int(parts[1])
    if bet > user["coins"]: return bot.reply_to(message, "❌ Мало монет.")
    bot.send_dice(message.chat.id, emoji="🎰"); time.sleep(3)
    res = random.randint(1, 64)
    if res == 64: user["coins"] += bet * 5; bot.reply_to(message, f"🎰 ДЖЕКПОТ! +{bet*5}")
    elif res >= 32: user["coins"] += bet; bot.reply_to(message, f"🎰 +{bet}")
    else: user["coins"] -= bet; bot.reply_to(message, f"🎰 -{bet}")
    save_db()

def get_target(message):
    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
        return str(target_uid), get_user(target_uid)
    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("@"):
        return find_user_by_username(parts[1])
    return None, None

@bot.message_handler(commands=['infect'])
def infect(message):
    tid, target = get_target(message)
    if not target: return bot.reply_to(message, "❌ @юзер или Reply.")
    if tid == str(message.from_user.id): return bot.reply_to(message, "❌ Себя нельзя.")
    user = get_user(message.from_user.id)
    if user["coins"] < 300: return bot.reply_to(message, "❌ Нужно 300.")
    user["coins"] -= 300; target["virus_until"] = time.time() + 3600; save_db()
    bot.reply_to(message, f"🦠 Заразил **{target['name']}**!", parse_mode="Markdown")
    try: bot.send_message(int(tid), "🦠 Ты заражен!")
    except: pass

@bot.message_handler(commands=['steal'])
def steal(message):
    tid, target = get_target(message)
    if not target: return bot.reply_to(message, "❌ @юзер или Reply.")
    user = get_user(message.from_user.id)
    if time.time() - user.get("last_steal", 0) < 60: return bot.reply_to(message, "❌ Жди минуту.")
    user["last_steal"] = time.time()
    if random.random() > 0.4:
        stolen = min(500, target["coins"]); target["coins"] -= stolen; user["coins"] += stolen; save_db()
        bot.reply_to(message, f"🥷 Украл {stolen} у **{target['name']}**!", parse_mode="Markdown")
    else:
        user["coins"] -= min(300, user["coins"]); save_db(); bot.reply_to(message, "🚔 Поймали!")

@bot.message_handler(commands=['business'])
def business_menu(message):
    user = get_user(message.from_user.id)
    if not user["businesses"]: return bot.reply_to(message, "🏢 Нет бизнесов. Купи в /shop.")
    text = "🏢 **БИЗНЕС-ЦЕНТР**\n\n"
    for bus_id, last in user["businesses"].items():
        bus = BUSINESSES[bus_id]
        text += f"{bus['name']} — {'✅ Готово' if time.time() - last >= bus['cooldown'] else '⏳'}\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect"))
    bot.reply_to(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "biz_collect")
def biz_collect(call):
    user = get_user(call.from_user.id); total = 0
    for bus_id, last in list(user["businesses"].items()):
        bus = BUSINESSES[bus_id]
        if time.time() - last >= bus["cooldown"]:
            total += bus["income"]; user["businesses"][bus_id] = time.time()
    if total > 0: user["coins"] += total; save_db(); bot.answer_callback_query(call.id, f"✅ {total}!")
    else: bot.answer_callback_query(call.id, "⏳")

@bot.message_handler(commands=['shop'])
def shop(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"))
    markup.add(types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"))
    markup.add(types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"))
    markup.add(types.InlineKeyboardButton("💊 Антидот (500)", callback_data="buy_antidote"))
    bot.reply_to(message, "🛒 **Магазин**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_callback(call):
    user = get_user(call.from_user.id); item = call.data.split("_")[1]
    if item == "antidote":
        if user["coins"] < 500: return bot.answer_callback_query(call.id, "❌")
        user["coins"] -= 500; user["virus_until"] = 0; save_db()
        bot.answer_callback_query(call.id, "💊 Вылечился!")
        return
    price = BUSINESSES[item]["price"]
    if user["coins"] < price: return bot.answer_callback_query(call.id, "❌")
    user["coins"] -= price; user["businesses"][item] = 0; save_db()
    bot.answer_callback_query(call.id, "✅ Куплено!")

@bot.message_handler(commands=['daily'])
def daily(message):
    user = get_user(message.from_user.id)
    if time.time() - user.get("last_daily", 0) < 86400: return bot.reply_to(message, "❌ Завтра!")
    user["last_daily"] = time.time(); user["coins"] += 500; add_xp(message.from_user.id, 100); save_db()
    bot.reply_to(message, "🎁 +500 монет!")

@bot.message_handler(commands=['boss'])
def boss(message):
    global boss_hp
    user = get_user(message.from_user.id)
    if boss_hp <= 0: boss_hp = 10000; return bot.reply_to(message, "🐉 Новый босс!")
    dmg = random.randint(user["dmg"] - 5, user["dmg"] + 10)
    boss_hp -= dmg; user["coins"] += dmg * 3; save_db()
    if boss_hp <= 0: user["coins"] += 2000; save_db(); bot.send_message(message.chat.id, f"💀 БОСС УБИТ! {user['name']} +2000!")
    else: bot.reply_to(message, f"🐉 -{dmg} HP. Осталось {boss_hp}.")

@bot.message_handler(commands=['top'])
def top(message):
    top_users = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True)[:5]
    text = "🏆 **Топ:**\n\n"
    for i, (uid, d) in enumerate(top_users, 1): text += f"{i}. {d['name']} — {d['coins']}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "📋 /profile /business /clan /bank /casino /infect /shop /steal /daily /boss /top")

# ========== ПЕРЕСЫЛКА ==========
@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_message(message):
    if message.chat.type != 'private': return
    uid = message.from_user.id; name = message.from_user.first_name or "Кто-то"
    user = get_user(uid)
    if message.from_user.username: user["username"] = message.from_user.username; save_db()

    if uid == OWNER_ID:
        if message.text == "👤 Профиль": profile(message); return
        if message.text == "🏢 Бизнесы": business_menu(message); return
        if message.text == "🛡 Кланы": clan_menu(message); return
        if message.text == "🎁 Бонус": daily(message); return
        if message.reply_to_message:
            target = pending_messages.get(message.reply_to_message.message_id)
            if target:
                try: bot.copy_message(target, message.chat.id, message.message_id); bot.reply_to(message, "✅ Отправлено!")
                except: bot.reply_to(message, "❌")
            else: bot.reply_to(message, "❌ Сделай Reply.")
        else:
            try:
                bot.forward_message(FRIEND_ID, message.chat.id, message.message_id)
                bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
                bot.reply_to(message, "✅ Отправлено другу и тебе!")
            except: bot.reply_to(message, "❌")
    else:
        try:
            sent = bot.forward_message(FRIEND_ID, message.chat.id, message.message_id)
            pending_messages[sent.message_id] = uid
            bot.send_message(FRIEND_ID, f"✉️ От {name}. Ответь.", reply_markup=types.ForceReply(selective=True))
            bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "✅ Отправлено Боссу и другу!")
        except: bot.reply_to(message, "❌")
  @bot.message_handler(commands=['profile'])
def show_profile_fix(message):
    user = get_user(message.from_user.id)
    virus = " 🦠" if user.get("virus_until", 0) > time.time() else ""
    clan = user.get("clan") or "Нет"
    bot.send_message(message.chat.id, f"👤 **{user['name']}**\n💰 {user['coins']}{virus}\n🛡 Клан: {clan}", parse_mode="Markdown")

@bot.message_handler(commands=['clan'])
def show_clan_fix(message):
    user = get_user(message.from_user.id)
    if user.get("clan"): 
        return bot.send_message(message.chat.id, f"🛡 Ты в клане: **{user['clan']}**", parse_mode="Markdown")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Создать клан (5000)", callback_data="clan_create"))
    bot.send_message(message.chat.id, "🛡 **Кланы**\nСоздай клан за 5000 монет!", reply_markup=markup)          
# ========== ЗАПУСК ==========
def run_bot():
    set_commands()
    print("🚀 СИНДИКАТ ULTIMATE ЗАПУЩЕН.")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
