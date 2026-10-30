import telebot
from telebot import types
from telebot.types import BotCommand
from flask import Flask
import random, json, os, time, threading

TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0"
OWNER_ID = 6170286634
FRIEND_ID = 7527864291
CHAT_ID = -1004215885788

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp, pending_messages, crypto_price = {}, 10000, {}, 1000
market_item = {"name": None, "price": 0, "time": 0}

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

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "xp": 0, "dmg": 10, "name": name or "Игрок", "businesses": {}, "clan": None, "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_roulette": 0, "last_casino": 0, "last_daily": 0, "achieves": [], "last_arena": 0, "multi": 1, "last_steal": 0, "casino_plays": 0, "last_loan": 0, "last_rob": 0, "last_craft": 0, "last_duel": 0}
    if name: users[uid_str]["name"] = name
    for k, v in {"businesses": {}, "clan": None, "debt": 0, "dmg": 10, "name": "Игрок", "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_roulette": 0, "last_casino": 0, "last_daily": 0, "achieves": [], "last_arena": 0, "multi": 1, "last_steal": 0, "casino_plays": 0, "last_loan": 0, "last_rob": 0, "last_craft": 0, "last_duel": 0}.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

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

def set_cmds():
    cmds = [BotCommand("start", "🚀 Старт"), BotCommand("profile", "👤 Профиль"), BotCommand("top", "🏆 Топ"), BotCommand("business", "🏢 Бизнесы"), BotCommand("shop", "🛒 Магазин"), BotCommand("bank", "🏦 Банк"), BotCommand("crypto", "📈 Биржа"), BotCommand("casino", "🎰 Казино"), BotCommand("roulette", "🎡 Рулетка"), BotCommand("slots", "🎰 Слоты"), BotCommand("market", "🕵️ Рынок"), BotCommand("arena", "⚔️ Арена"), BotCommand("craft", "📦 Крафт"), BotCommand("quest", "📜 Квест"), BotCommand("clan", "🛡 Кланы"), BotCommand("boss", "🐉 Босс"), BotCommand("infect", "🦠 Заразить"), BotCommand("steal", "🥷 Украсть"), BotCommand("gift", "🎁 Подарить"), BotCommand("duel", "🤺 Дуэль"), BotCommand("daily", "🎁 Бонус"), BotCommand("rob", "🔫 Ограбить"), BotCommand("loan", "🏦 Кредит"), BotCommand("help", "📋 Справка"), BotCommand("save", "💾 Сохранить"), BotCommand("reset", "🧹 Обнулить"), BotCommand("achieves", "🏆 Ачивки")]
    bot.set_my_commands(cmds)

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
    if msg.from_user.id == OWNER_ID: bot.send_message(msg.from_user.id, "👑 Босс, Синдикат 30.0. Всё готово!", reply_markup=markup)
    else: bot.reply_to(msg, "Привет! Пиши /help.", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_cmd(msg): 
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.reply_to(msg, "📋 /profile /business /clan /slots /market /arena /craft /casino /roulette /bank /loan /rob /boss /steal /infect /duel /daily /shop /top /achieves /save /reset", reply_markup=markup)

@bot.message_handler(commands=['achieves'])
def show_achieves(msg):
    u = get_u(msg.from_user.id)
    if not u["achieves"]: return bot.reply_to(msg, "У тебя пока нет ачивок.")
    bot.reply_to(msg, f"🏆 **Твои ачивки:**\n" + "\n".join([f"• {a}" for a in u["achieves"]]), parse_mode="Markdown")

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

@bot.message_handler(commands=['steal'])
def steal(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_steal", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    u["last_steal"] = time.time()
    if random.random() > 0.4: s = min(500, target["coins"]); target["coins"] -= s; u["coins"] += s; bot.reply_to(msg, f"🥷 Украл {s} у **{target['name']}**!", parse_mode="Markdown")
    else: u["coins"] -= min(300, u["coins"]); bot.reply_to(msg, "🚔 Поймали!")

@bot.message_handler(commands=['infect'])
def infect(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    if tid == str(msg.from_user.id): return bot.reply_to(msg, "❌ Себя нельзя.")
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u["coins"] < 300: return bot.reply_to(msg, "❌ Нужно 300.")
    u["coins"] -= 300; target["virus_until"] = time.time() + 3600; bot.reply_to(msg, f"🦠 Заразил **{target['name']}**!", parse_mode="Markdown")

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
    if random.random() > 0.5: u["coins"] += bet; target["coins"] -= bet; bot.reply_to(msg, f"🤺 Ты победил {target['name']}!")
    else: u["coins"] -= bet; target["coins"] += bet; bot.reply_to(msg, f"🤺 {target['name']} победил.")

@bot.message_handler(commands=['slots'])
def slots(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "❌ /slots 100")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "❌ Мало.")
    bot.send_dice(msg.chat.id, emoji="🎰"); time.sleep(3)
    res = random.randint(1, 64)
    if res == 64: u["coins"] += bet * 10; bot.reply_to(msg, f"🎰 ДЖЕКПОТ x10! +{bet*10}")
    elif res >= 50: u["coins"] += bet * 2; bot.reply_to(msg, f"🎰 x2! +{bet*2}")
    elif res >= 32: bot.reply_to(msg, "🎰 Возврат.")
    else: u["coins"] -= bet; bot.reply_to(msg, f"🎰 -{bet}")

@bot.message_handler(commands=['market'])
def market(msg):
    global market_item
    if time.time() - market_item["time"] > 3600:
        items = [{"n": "💎 Алмаз", "p": 5000}, {"n": "🍀 Клевер", "p": 2000}, {"n": "🔮 Шар", "p": 10000}]
        i = random.choice(items); market_item = {"name": i["n"], "price": i["p"], "time": time.time()}
    markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton(f"Купить за {market_item['price']}", callback_data="buy_market"))
    bot.reply_to(msg, f"🕵️ **Рынок**\nТовар: {market_item['name']}\nЦена: {market_item['price']}", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "buy_market")
def buy_market(call):
    global market_item
    u = get_u(call.from_user.id)
    if not market_item["name"]: return bot.answer_callback_query(call.id, "❌ Уже купили!")
    if u["coins"] < market_item["price"]: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= market_item["price"]; u["multi"] += 0.5; market_item["name"] = None; save_db()
    bot.edit_message_text("🕵️ Куплено!", call.message.chat.id, call.message.message_id); bot.answer_callback_query(call.id, "✅ +0.5 к множителю")

@bot.message_handler(commands=['arena'])
def arena(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_arena", 0) < 300: return bot.reply_to(msg, "❌ Жди 5 минут.")
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    if tid == str(msg.from_user.id): return bot.reply_to(msg, "❌ Себя нельзя.")
    u["last_arena"] = time.time()
    if random.random() > 0.5: w = int(target["coins"] * 0.1); u["coins"] += w; target["coins"] -= w; bot.reply_to(msg, f"⚔️ Победил {target['name']} и забрал {w}!")
    else: l = int(u["coins"] * 0.1); u["coins"] -= l; target["coins"] += l; bot.reply_to(msg, f"⚔️ {target['name']} победил, забрал {l}.")

@bot.message_handler(commands=['craft'])
def craft(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_craft", 0) < 3600: return bot.reply_to(msg, "❌ Крафт раз в час!")
    if u["coins"] < 1000: return bot.reply_to(msg, "❌ Нужно 1000.")
    u["last_craft"] = time.time(); u["coins"] -= 1000
    if random.random() > 0.5: u["coins"] += 3000; bot.reply_to(msg, "📦 Золотой кейс! +3000")
    else: u["dmg"] += 5; bot.reply_to(msg, "📦 +5 урона!")

@bot.message_handler(commands=['quest'])
def quest(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_quest", 0) < 3600: return bot.reply_to(msg, "❌ Через час.")
    u["last_quest"] = time.time(); r = random.randint(500, 2000); u["coins"] += r; add_xp(msg.from_user.id, 20); bot.reply_to(msg, f"📜 +{r}!")

@bot.message_handler(commands=['roulette'])
def roulette(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_roulette", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки.")
    u["last_roulette"] = time.time()
    if random.random() > 0.7: w = random.randint(1000, 5000); u["coins"] += w; bot.reply_to(msg, f"🎡 +{w}!")
    else: l = u["coins"] // 2; u["coins"] -= l; bot.reply_to(msg, f"🎡 -{l}!")

@bot.message_handler(commands=['crypto'])
def crypto(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name); markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton("Купить", callback_data="crypto_buy"), types.InlineKeyboardButton("Продать", callback_data="crypto_sell"))
    bot.reply_to(msg, f"📈 Курс: {crypto_price}. У тебя: {u['crypto']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("crypto_"))
def crypto_trade(call):
    u = get_u(call.from_user.id)
    if call.data == "crypto_buy":
        if u["coins"] < crypto_price: return bot.answer_callback_query(call.id, "❌ Мало!")
        u["coins"] -= crypto_price; u["crypto"] += 1; bot.answer_callback_query(call.id, "✅ Куплен!")
    else:
        if u["crypto"] < 1: return bot.answer_callback_query(call.id, "❌ Нет!")
        u["crypto"] -= 1; u["coins"] += crypto_price; bot.answer_callback_query(call.id, "✅ Продан!")

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

@bot.message_handler(commands=['business'])
def business_menu(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if not u["businesses"]: return bot.reply_to(msg, "🏢 Купи в /shop.")
    text = "🏢 **БИЗНЕС**\n\n"
    for b, l in u["businesses"].items(): text += f"{BUSINESSES[b]['name']} — {'✅' if time.time() - l >= BUSINESSES[b]['cooldown'] else '⏳'}\n"
    markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect")); bot.reply_to(msg, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "biz_collect")
def biz_collect(call):
    u = get_u(call.from_user.id); total = 0
    for b, l in list(u["businesses"].items()):
        if time.time() - l >= BUSINESSES[b]["cooldown"]: total += int(BUSINESSES[b]["income"] * u.get("multi", 1)); u["businesses"][b] = time.time()
    if total > 0: u["coins"] += total; bot.answer_callback_query(call.id, f"✅ {total}!")
    else: bot.answer_callback_query(call.id, "⏳ Пусто.")

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

@bot.message_handler(commands=['shop'])
def shop(msg):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"), types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"), types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"), types.InlineKeyboardButton("💊 Антидот (500)", callback_data="buy_antidote"))
    bot.reply_to(msg, "🛒 **Магазин**", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_cb(call):
    u = get_u(call.from_user.id); i = call.data.split("_")[1]
    if i == "antidote":
        if u["coins"] < 500: return bot.answer_callback_query(call.id, "❌")
        u["coins"] -= 500; u["virus_until"] = 0; bot.answer_callback_query(call.id, "💊 ОК!"); return
    p = BUSINESSES[i]["price"]
    if u["coins"] < p: return bot.answer_callback_query(call.id, "❌")
    u["coins"] -= p; u["businesses"][i] = 0; give_achieve(call.from_user.id, "Бизнесмен", 500); bot.answer_callback_query(call.id, "✅ Куплено!")

@bot.message_handler(commands=['daily'])
def daily(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_daily", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки!")
    u["last_daily"] = time.time(); u["coins"] += 500; add_xp(msg.from_user.id, 100); u["has_chest"] = True; bot.reply_to(msg, "🎁 +500 и Кейс!")

@bot.message_handler(commands=['clan'])
def clan_menu(msg):
        u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u.get("clan"): return bot.reply_to(msg, f"🛡 Клан: **{u['clan']}**", parse_mode="Markdown")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("Создать (5000)", callback_data="clan_create"))
    bot.reply_to(msg, "🛡 **Кланы**", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "clan_create")
def clan_create(call):
    u = get_u(call.from_user.id)
    if u["coins"] < 5000: return bot.answer_callback_query(call.id, "❌")
    u["coins"] -= 5000; u["clan"] = f"К_{u['name']}"; give_achieve(call.from_user.id, "Клановод", 1000); bot.answer_callback_query(call.id, "✅!")

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
    set_cmds(); print("🚀 СИНДИКАТ 30.0 ЗАПУЩЕН."); bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    u = get_u(msg.from_user.id, msg.from_user.first_na
