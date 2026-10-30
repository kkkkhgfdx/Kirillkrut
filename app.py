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
TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0" # <--- ВСТАВЬ СЮДА СВОЙ ТОКЕН
OWNER_ID = 6170286634       
FRIEND_ID = 7527864291      
CHAT_ID = -1002021366605    

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== БАЗА ==========
DB_FILE = "users.json"
users = {}
boss_hp = 50000
pending_messages = {}
crypto_price = 1000 

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
            "dmg": 10, "name": "Игрок", "businesses": {}, 
            "clan": None, "username": "", "crypto": 0, "bank_deposit": 0
        }
        save_db()
    defaults = {"businesses": {}, "clan": None, "debt": 0, "dmg": 10, "name": "Игрок", "username": "", "crypto": 0, "bank_deposit": 0}
    for k, v in defaults.items():
        if k not in users[uid_str]: users[uid_str][k] = v
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
        BotCommand("start", "🚀 Запустить"), BotCommand("profile", "👤 Профиль"),
        BotCommand("top", "🏆 Топ"), BotCommand("business", "🏢 Бизнесы"),
        BotCommand("shop", "🛒 Магазин"), BotCommand("bank", "🏦 Банк"),
        BotCommand("crypto", "📈 Биржа"), BotCommand("casino", "🎰 Казино"),
        BotCommand("roulette", "🎡 Рулетка"), BotCommand("upgrade", "⚔️ Прокачка"),
        BotCommand("clan", "🛡 Кланы"), BotCommand("duel", "🤺 Дуэль"),
        BotCommand("boss", "🐉 Босс"), BotCommand("infect", "🦠 Заразить"),
        BotCommand("steal", "🥷 Украсть"), BotCommand("gift", "🎁 Подарить"),
        BotCommand("daily", "🎁 Бонус"), BotCommand("rob", "🔫 Ограбить"),
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
        bot.send_message(uid, "👑 Босс, версия без кулдаунов запущена. Спамь на здоровье!", reply_markup=markup)
    else:
        bot.reply_to(message, "Привет! Пиши /help.")

# ========== НОВЫЕ ФИШКИ ==========
@bot.message_handler(commands=['roulette'])
def roulette(message):
    user = get_user(message.from_user.id)
    if random.random() > 0.7:
        win = random.randint(1000, 5000); user["coins"] += win
        bot.reply_to(message, f"🎡 ТЕБЕ ПОВЕЗЛО! +{win} монет!")
    else:
        loss = user["coins"] // 2; user["coins"] -= loss
        bot.reply_to(message, f"🎡 НЕ ПОВЕЗЛО! Потеряно {loss} монет.")
    save_db()

@bot.message_handler(commands=['crypto'])
def crypto(message):
    global crypto_price
    user = get_user(message.from_user.id)
    text = f"📈 **Биржа**\nКурс: {crypto_price}\nУ тебя: {user['crypto']} битков\n\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Купить 1", callback_data="crypto_buy"))
    markup.add(types.InlineKeyboardButton("Продать 1", callback_data="crypto_sell"))
    bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("crypto_"))
def crypto_trade(call):
    global crypto_price
    user = get_user(call.from_user.id)
    if call.data == "crypto_buy":
        if user["coins"] < crypto_price: return bot.answer_callback_query(call.id, "❌ Мало!")
        user["coins"] -= crypto_price; user["crypto"] += 1; save_db()
        bot.answer_callback_query(call.id, "✅ Куплен!")
    else:
        if user["crypto"] < 1: return bot.answer_callback_query(call.id, "❌ Нет!")
        user["crypto"] -= 1; user["coins"] += crypto_price; save_db()
        bot.answer_callback_query(call.id, "✅ Продан!")

@bot.message_handler(commands=['duel'])
def duel(message):
    target_id, target = get_target(message)
    if not target: return bot.reply_to(message, "❌ @юзер или Reply.")
    if target_id == str(message.from_user.id): return bot.reply_to(message, "❌ Себя нельзя.")
    user = get_user(message.from_user.id)
    parts = message.text.split()
    bet = int(parts[-1]) if parts[-1].isdigit() else 100
    if user["coins"] < bet: return bot.reply_to(message, "❌ Мало монет.")
    
    if random.random() > 0.5:
        user["coins"] += bet; target["coins"] -= bet
        bot.reply_to(message, f"🤺 Ты победил {target['name']} и забрал {bet}!")
    else:
        user["coins"] -= bet; target["coins"] += bet
        bot.reply_to(message, f"🤺 {target['name']} победил тебя и забрал {bet}.")
    save_db()

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['profile'])
def profile(message):
    user = get_user(message.from_user.id)
    clan = user.get("clan") or "Нет"
    debt = f"\n🔴 Долг: {user['debt']}" if user.get('debt', 0) > 0 else ""
    crypto = f"\n📈 Битков: {user['crypto']}" if user.get('crypto', 0) > 0 else ""
    bot.reply_to(message, f"👤 **{user['name']}**\n🏅 Уровень: {user['lvl']}\n💰 {user['coins']}\n⚔️ Урон: {user['dmg']}\n🛡 Клан: {clan}{debt}{crypto}", parse_mode="Markdown")

@bot.message_handler(commands=['top'])
def top(message):
    sorted_users = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True)[:5]
    text = "🏆 **Топ богачей:**\n\n"
    for i, (uid, d) in enumerate(sorted_users, 1):
        name = d.get('name', 'Игрок')
        if name == "Игрок": 
            try: name = bot.get_chat(int(uid)).first_name
            except: pass
        text += f"{i}. {name} — {d['coins']}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['rob'])
def rob(message):
    user = get_user(message.from_user.id)
    if random.random() > 0.5: 
        user["coins"] += 300; add_xp(message.from_user.id, 10); save_db(); bot.reply_to(message, "🔫 +300!")
    else: penalty = min(200, user["coins"]); user["coins"] -= penalty; save_db(); bot.reply_to(message, f"🚔 -{penalty}.")

@bot.message_handler(commands=['loan'])
def loan(message):
    user = get_user(message.from_user.id)
    if user["debt"] > 0: return bot.reply_to(message, "❌ Верни долг!")
    user["coins"] += 1000; user["debt"] += 1500; save_db()
    bot.reply_to(message, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['give'])
def give(message):
    if message.from_user.id != OWNER_ID: return
    parts = message.text.split()
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        target_id, amount = parts[1], int(parts[2])
        if target_id in users:
            users[target_id]["coins"] += amount; save_db()
            bot.reply_to(message, f"💸 +{amount} игроку {target_id}!")
    else: bot.reply_to(message, "❌ /give [ID] [Сумма]")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != OWNER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return bot.reply_to(message, "❌ /broadcast [текст]")
    count = 0
    for uid_str in users.keys():
        try: bot.send_message(int(uid_str), f"📢 **ОБЪЯВЛЕНИЕ:**\n{text}", parse_mode="Markdown"); count += 1
        except: pass
    bot.reply_to(message, f"✅ {count} игрокам.")

@bot.message_handler(commands=['upgrade'])
def upgrade(message):
    user = get_user(message.from_user.id)
    if user["coins"] < 500: return bot.reply_to(message, "❌ Нужно 500.")
    user["coins"] -= 500; user["dmg"] += 5; save_db()
    bot.reply_to(message, f"⚔️ Урон: {user['dmg']}!")

def get_target(message):
    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
        return str(target_uid), get_user(target_uid)
    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("@"):
        return find_user_by_username(parts[1])
    return None, None

@bot.message_handler(commands=['gift'])
def gift(message):
    target_id, target = get_target(message)
    if not target: return bot.reply_to(message, "❌ @юзер или Reply.")
    user = get_user(message.from_user.id)
    parts = message.text.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        amount = int(parts[-1])
        if user["coins"] < amount: return bot.reply_to(message, "❌ Мало.")
        user["coins"] -= amount; target["coins"] += amount; save_db()
        bot.reply_to(message, f"🎁 Подарил {amount} игроку {target['name']}!")
    else: bot.reply_to(message, "❌ /gift [ID/Reply] [Сумма]")

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
    if user["coins"] < 5000: return bot.answer_callback_query(call.id, "❌ Мало!")
    user["coins"] -= 5000; user["clan"] = f"Клан_{user['name']}"; save_db()
    bot.answer_callback_query(call.id, "✅ Клан создан!")

@bot.message_handler(commands=['boss'])
def boss(message):
    global boss_hp
    user = get_user(message.from_user.id)
    if boss_hp <= 0: boss_hp = 50000; return bot.reply_to(message, "🐉 Новый босс (50к HP)!")
    
    dmg = user["dmg"]
    if user.get("clan"): dmg *= 2 
    boss_hp -= dmg
    
    # ФИКС: Маленькая фиксированная награда, чтобы нельзя было нафармить
    reward = 10 + user["lvl"]
    user["coins"] += reward; save_db()
    
    if boss_hp <= 0:
        user["coins"] += 2000; save_db(); bot.send_message(message.chat.id, f"💀 БОСС УБИТ! {user['name']} +2000!")
    else: bot.reply_to(message, f"🐉 -{dmg} HP. Осталось {boss_hp}. +{reward} монет.")

@bot.message_handler(commands=['infect'])
def infect(message):
    tid, target = get_target(message)
    if not target: return bot.reply_to(message, "❌ @юзер или Reply.")
    if tid == str(message.from_user.id): return bot.reply_to(message, "❌ Себя нельзя.")
    user = get_user(message.from_user.id)
    if user["coins"] < 300: return bot.reply_to(message, "❌ Нужно 300.")
    user["coins"] -= 300; target["virus_until"] = time.time() + 3600; save_db()
    bot.reply_to(message, f"🦠 Заразил **{target['name']}**!", parse_mode="Markdown")

@bot.message_handler(commands=['steal'])
def steal(message):
    tid, target = get_target(message)
    if not target: return bot.reply_to(message, "❌ @юзер или Reply.")
    user = get_user(message.from_user.id)
    if random.random() > 0.4:
        stolen = min(500, target["coins"]); target["coins"] -= stolen; user["coins"] += stolen; save_db()
        bot.reply_to(message, f"🥷 Украл {stolen} у **{target['name']}**!", parse_mode="Markdown")
    else: user["coins"] -= min(300, user["coins"]); save_db(); bot.reply_to(message, "🚔 Поймали!")

@bot.message_handler(commands=['casino'])
def casino(message):
    user = get_user(message.from_user.id)
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(message, "❌ /casino 100")
    bet = int(parts[1])
    if bet > user["coins"]: return bot.reply_to(message, "❌ Мало.")
    bot.send_dice(message.chat.id, emoji="🎰"); time.sleep(3)
    res = random.randint(1, 64)
    if res == 64: user["coins"] += bet * 5; bot.reply_to(message, f"🎰 ДЖЕКПОТ! +{bet*5}")
    elif res >= 32: user["coins"] += bet; bot.reply_to(message, f"🎰 +{bet}")
    else: user["coins"] -= bet; bot.reply_to(message, f"🎰 -{bet}")
    save_db()

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
    else: bot.answer_callback_query(call.id, "⏳ Ничего нет.")

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
    user["coins"] += 500; add_xp(message.from_user.id, 100); save_db()
    bot.reply_to(message, "🎁 +500 монет!")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "📋 /profile /business /clan /boss /upgrade /gift /infect /steal /shop /bank /casino /roulette /crypto /duel /rob /loan /daily /top")

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

# ========== ЗАПУСК ==========
def run_bot():
    set_commands()
    print("🚀 СИНДИКАТ БЕЗ КУЛДАУНОВ ЗАПУЩЕН.")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
