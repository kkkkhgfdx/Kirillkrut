import telebot, random, json, os, time, threading
from telebot import types
from telebot.types import BotCommand
from flask import Flask
from datetime import datetime

# ========== НАСТРОЙКИ ==========
TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0" # СМЕНИ ТОКЕН В BOTFATHER!
OWNER_ID = 6170286634
CHAT_ID = -1004215885788

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp = {}, 10000

# ========== БАЗА ДАННЫХ ==========
DB_FILE = "users.json"

def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f: 
            json.dump(users, f, ensure_ascii=False, indent=4)
        with open(DB_FILE, "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="💾 База Синдиката")
            try: bot.pin_chat_message(CHAT_ID, sent.message_id, disable_notification=True)
            except: pass
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def load_db():
    global users
    try:
        chat = bot.get_chat(CHAT_ID)
        if chat.pinned_message and chat.pinned_message.document:
            downloaded = bot.download_file(bot.get_file(chat.pinned_message.document.file_id).file_path)
            users = json.loads(downloaded.decode('utf-8'))
            print("✅ База загружена из канала!")
            return
    except: pass
    
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            print("✅ Локальная база загружена!")
            return
        except: pass
        
    users = {}
    print("⚠️ Создана новая база.")
load_db()

@app.route('/')
def health(): return "OK", 200

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "businesses": {}, "achieves": [], "last_loan": 0, "last_rob": 0, "last_mine": 0, "last_smuggle": 0, "last_daily": 0, "last_boss_hit": 0, "last_hack": 0}
    if name: users[uid_str]["name"] = name
    return users[uid_str]

def give_achieve(uid, name, reward):
    u = get_u(uid)
    if name not in u["achieves"]:
        u["achieves"].append(name)
        u["coins"] += reward
        try: bot.send_message(CHAT_ID, f"🏆 **АЧИВКА!** {u['name']} получил **{name}**!")
        except: pass

# ========== ГЛАВНОЕ МЕНЮ ==========
def main_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"),
           types.InlineKeyboardButton("🛒 Магазин", callback_data="menu_shop"))
    kb.add(types.InlineKeyboardButton("🏢 Бизнесы", callback_data="menu_biz"),
           types.InlineKeyboardButton("🎰 Казино", callback_data="menu_casino"))
    kb.add(types.InlineKeyboardButton("🐉 Босс", callback_data="menu_boss"),
           types.InlineKeyboardButton("🏆 Топ", callback_data="menu_top"))
    kb.add(types.InlineKeyboardButton("🎁 Ежедневка", callback_data="menu_daily"))
    return kb

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start', 'menu'])
def start(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if msg.from_user.username: u["username"] = msg.from_user.username
    if msg.text == "/start": give_achieve(msg.from_user.id, "Первые шаги", 100)
    save_db()
    
    menu_text = "🔥 **Синдикат v1.0 (Release)**\nЖми кнопки или пиши /help."
    
    # === ИВЕНТ ПЯТНИЦА 13 ===
    if datetime.now().day == 13:
        menu_text = "🔪 **СЕГОДНЯ ПЯТНИЦА 13-Я!** В СИНДИКАТЕ НЕСПОКОЙНО. КАЗИНО РАБОТАЕТ ПО-КРОВАВОМУ!\n\n" + menu_text
        
    bot.send_message(msg.chat.id, menu_text, reply_markup=main_kb(msg.from_user.id), parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_cmd(msg): 
    bot.reply_to(msg, "📋 **Команды:**\n/profile /top /shop /business /loan /paydebt /rob /hack /boss /casino /mine /smuggle /daily /achieves /gift /save")

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    bot.reply_to(msg, f"👤 {u['name']}\n💰 {u['coins']}\n🏦 Долг: {u.get('debt', 0)}\n📈 Ур: {u['lvl']} (DMG: {u['dmg']})\n🏢 Бизнесов: {len(u['businesses'])}\n🏆 Ачивок: {len(u['achieves'])}")

@bot.message_handler(commands=['top'])
def top(msg):
    s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
    t = "🏆 **Топ:**\n\n"
    for i, (uid, d) in enumerate(s[:10], 1): t += f"{i}. {d.get('name', 'Игрок')} — {d.get('coins', 0)} 💰\n"
    bot.reply_to(msg, t, parse_mode="Markdown")

@bot.message_handler(commands=['shop'])
def shop(msg):
    m = types.InlineKeyboardMarkup(row_width=1)
    
    # === ИВЕНТ ПЯТНИЦА 13 (Скидка 13%) ===
    is_friday_13 = (datetime.now().day == 13)
    discount = 0.87 if is_friday_13 else 1.0
    
    farm_price = int(1000 * discount)
    garden_price = int(3000 * discount)
    factory_price = int(10000 * discount)
    
    m.add(types.InlineKeyboardButton(f"🌾 Ферма ({farm_price})", callback_data="buy_farm"))
    m.add(types.InlineKeyboardButton(f"🌳 Сад ({garden_price})", callback_data="buy_garden"))
    m.add(types.InlineKeyboardButton(f"🏭 Завод ({factory_price})", callback_data="buy_factory"))
    
    shop_text = "🛒 **Магазин**"
    if is_friday_13:
        shop_text += "\n\n🔥 **СКИДКА 13% НА ВСЕ ТОВАРЫ!**"
        
    bot.reply_to(msg, shop_text, reply_markup=m, parse_mode="Markdown")

@bot.message_handler(commands=['business'])
def business_menu(msg):
    u = get_u(msg.from_user.id)
    if not u.get("businesses"): return bot.reply_to(msg, "🏢 Купи в /shop.")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("💰 Собрать доход", callback_data="biz_collect"))
    bot.reply_to(msg, "🏢 **Твои бизнесы**\nЖми кнопку, чтобы собрать бабки.", reply_markup=m, parse_mode="Markdown")

@bot.message_handler(commands=['mine'])
def mine(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_mine", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    u["last_mine"] = time.time(); res = random.random()
    if res > 0.8: w = 1000; u["coins"] += w; bot.reply_to(msg, f"💎 АЛМАЗ! +{w}!")
    elif res > 0.4: w = 300; u["coins"] += w; bot.reply_to(msg, f"🪙 Золото! +{w}!")
    else: w = min(50, u["coins"]); u["coins"] -= w; bot.reply_to(msg, f"💥 Обвал! -{w}.")
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
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Верни долг (/paydebt)!")
    u["last_loan"] = time.time(); u["coins"] += 1000; u["debt"] += 1500; save_db()
    bot.reply_to(msg, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['paydebt'])
def paydebt(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u.get("debt", 0) <= 0: return bot.reply_to(msg, "✅ Нет долгов!")
    if u["coins"] < u["debt"]: return bot.reply_to(msg, f"❌ Мало! Долг: {u['debt']}.")
    u["coins"] -= u["debt"]; u["debt"] = 0; save_db()
    bot.reply_to(msg, "✅ Долг погашен!")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_rob", 0) < 10: return bot.reply_to(msg, "❌ Жди 10с.")
    u["last_rob"] = time.time()
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "🔫 +300!")
    else: p = min(200, u["coins"]); u["coins"] -= p; bot.reply_to(msg, f"🚔 -{p}")
    save_db()

@bot.message_handler(commands=['hack'])
def hack(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_hack", 0) < 3600: return bot.reply_to(msg, "❌ Взлом раз в час!")
    if u["coins"] < 500 or u["dmg"] < 15: return bot.reply_to(msg, "❌ Нужно 500 монет и 15 DMG!")
    u["last_hack"] = time.time(); u["coins"] -= 500
    
    if random.random() > 0.3:
        targets = [k for k in users if k != str(msg.from_user.id) and users[k]["coins"] > 1000]
        if targets:
            victim = random.choice(targets); loot = int(users[victim]["coins"] * 0.1)
            users[victim]["coins"] -= loot; u["coins"] += loot
            bot.reply_to(msg, f"💻 Взлом успешен! Ты украл {loot} у {users[victim]['name']}!")
        else: u["coins"] += 500; bot.reply_to(msg, "💻 Взлом успешен, но все нищие. Вернул 500.")
    else: bot.reply_to(msg, "🚨 Взлом провален! -500.")
    save_db()

@bot.message_handler(commands=['boss'])
def boss(msg):
    global boss_hp
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_boss_hit", 0) < 2: return bot.reply_to(msg, "❌ Жди 2 сек.")
    u["last_boss_hit"] = time.time()
    if boss_hp <= 0: boss_hp = 10000; return bot.reply_to(msg, "🐉 Новый босс!")
    dmg = u["dmg"]; boss_hp -= dmg; u["coins"] += dmg * 2; save_db()
    bot.reply_to(msg, f"🐉 -{dmg} HP. Осталось {boss_hp}.")

@bot.message_handler(commands=['casino'])
def casino(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "❌ /casino 100")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "❌ Мало монет.")
    
    # === ИВЕНТ ПЯТНИЦА 13 (Сделка с Дьяволом) ===
    is_friday_13 = (datetime.now().day == 13)
    
    if random.random() > 0.5: 
        win_amount = bet * 2 if is_friday_13 else bet
        u["coins"] += win_amount
        bot.reply_to(msg, f"🎰 Победа! +{win_amount}!" + (" (x2 Пятница 13!)" if is_friday_13 else ""))
    else: 
        if is_friday_13:
            tax = int(bet * 0.13)
            u["coins"] -= (bet + tax)
            bot.reply_to(msg, f"💀 Проигрыш! -{bet} + налог на страх 13% (-{tax}).")
        else:
            u["coins"] -= bet
            bot.reply_to(msg, f"💀 Проигрыш! -{bet}.")
    save_db()

@bot.message_handler(commands=['daily'])
def daily(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_daily", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки!")
    u["last_daily"] = time.time(); u["coins"] += 500; save_db()
    bot.reply_to(msg, "🎁 +500 монет!")

@bot.message_handler(commands=['achieves'])
def show_achieves(msg):
    u = get_u(msg.from_user.id)
    if not u["achieves"]: return bot.reply_to(msg, "Нет ачивок.")
    bot.reply_to(msg, "🏆 Ачивки:\n" + "\n".join(u["achieves"]))

@bot.message_handler(commands=['gift'])
def gift(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if msg.reply_to_message:
        target = get_u(msg.reply_to_message.from_user.id)
        if len(parts) >= 2 and parts[-1].isdigit():
            a = int(parts[-1])
            if u["coins"] < a: return bot.reply_to(msg, "❌ Мало.")
            u["coins"] -= a; target["coins"] += a; save_db()
            bot.reply_to(msg, f"🎁 Подарил {a} игроку {target['name']}!")
        else: bot.reply_to(msg, "❌ /gift 100 в ответ на сообщение")

@bot.message_handler(commands=['save'])
def save_cmd(msg):
    if msg.from_user.id == OWNER_ID: save_db(); bot.reply_to(msg, "💾 Сохранено!")

# ========== ИНЛАЙН-КНОПКИ ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global boss_hp
    u = get_u(call.from_user.id, call.from_user.first_name)
    
    if call.data == "menu_main": 
        bot.edit_message_text("🔥 **Синдикат v1.0 (Release)**", call.message.chat.id, call.message.message_id, reply_markup=main_kb(call.from_user.id), parse_mode="Markdown")
    elif call.data == "menu_profile":
        bot.edit_message_text(f"👤 {u['name']}\n💰 {u['coins']}\n🏦 Долг: {u.get('debt', 0)}", call.message.chat.id, call.message.message_id)
    elif call.data == "menu_shop":
        bot.answer_callback_query(call.id, "Напиши /shop для покупок")
    elif call.data == "menu_biz":
        bot.answer_callback_query(call.id, "Напиши /business")
    elif call.data == "menu_casino":
        bot.answer_callback_query(call.id, "Напиши /casino 100")
    elif call.data == "menu_boss":
        bot.answer_callback_query(call.id, f"Босс: {boss_hp} HP. Пиши /boss")
    elif call.data == "menu_top":
        s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
        t = "🏆 **Топ:**\n\n"
        for i, (uid, d) in enumerate(s[:10], 1): t += f"{i}. {d.get('name')} — {d.get('coins', 0)}\n"
        bot.edit_message_text(t, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    elif call.data == "menu_daily":
        bot.answer_callback_query(call.id, "Пиши /daily")
        
    elif call.data.startswith("buy_"):
        i = call.data.split("_")[1]
        prices = {"farm": 1000, "garden": 3000, "factory": 10000}
        p = prices.get(i, 99999)
        
        # Скидка в магазине
        if datetime.now().day == 13:
            p = int(p * 0.87)
            
        if u["coins"] < p: return bot.answer_callback_query(call.id, "❌ Мало денег!")
        u["coins"] -= p
        if "businesses" not in u: u["businesses"] = {}
        u["businesses"][i] = time.time()
        save_db()
        bot.answer_callback_query(call.id, f"✅ Бизнес куплен за {p}!")

    elif call.data == "biz_collect":
        total = 0
        for b, l in list(u["businesses"].items()):
            if time.time() - l >= 3600: total += 1000; u["businesses"][b] = time.time()
        if total > 0: u["coins"] += total; save_db(); bot.answer_callback_query(call.id, f"✅ Собрано: {total}!")
        else: bot.answer_callback_query(call.id, "⏳ Пока пусто.")

# ========== ЗАПУСК ==========
def run_bot():
    cmds = [
        BotCommand("menu", "Меню"), BotCommand("start", "Старт"), BotCommand("help", "Справка"),
        BotCommand("profile", "Профиль"), BotCommand("top", "Топ"), BotCommand("shop", "Магазин"),
        BotCommand("business", "Бизнесы"), BotCommand("loan", "Кредит"), BotCommand("paydebt", "Вернуть долг"),
        BotCommand("rob", "Ограбить"), BotCommand("hack", "Взлом"), BotCommand("boss", "Босс"),
        BotCommand("casino", "Казино"), BotCommand("mine", "Шахта"), BotCommand("smuggle", "Контрабанда"),
        BotCommand("daily", "Бонус"), BotCommand("achieves", "Ачивки")
    ]
    bot.set_my_commands(cmds)
    print("🚀 СИНДИКАТ v1.0 (ПЯТНИЦА 13) ЗАПУЩЕН!")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
