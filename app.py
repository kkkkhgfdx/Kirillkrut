import telebot
from telebot import types
from telebot.types import BotCommand
from flask import Flask
import random, json, os, time, threading

# ========== НАСТРОЙКИ ==========
TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0"  # <--- ВСТАВЬ ТОКЕН ОТ BOTFATHER
OWNER_ID = 6170286634
FRIEND_ID = 7527864291
CHAT_ID = -1004215885788  # Твоя группа (бот должен быть админом с правом закрепа)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp, pending_messages, crypto_price = {}, 10000, {}, 1000

def save_db():
    try:
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="💾 База сохранена")
            try:
                bot.pin_chat_message(CHAT_ID, sent.message_id, disable_notification=True)
            except Exception as pin_err:
                print(f"Не удалось закрепить: {pin_err}")
    except Exception as e: print(f"Ошибка сохранения: {e}")

def load_db():
    global users
    try:
        chat = bot.get_chat(CHAT_ID)
        if chat.pinned_message and chat.pinned_message.document:
            file_info = bot.get_file(chat.pinned_message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            users = json.loads(downloaded.decode('utf-8'))
            print("✅ База загружена из закрепа в группе!")
            return
    except Exception as e: print(f"Ошибка загрузки: {e}")
    users = {}
    print("⚠️ Создана новая база.")

load_db()

def get_u(uid):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "xp": 0, "dmg": 10, "name": "Игрок", "businesses": {}, "clan": None, "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_biz_collect": 0, "last_roulette": 0}
    for k, v in {"businesses": {}, "clan": None, "debt": 0, "dmg": 10, "name": "Игрок", "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_biz_collect": 0, "last_roulette": 0}.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

def add_xp(uid, amt):
    u = get_u(uid); u["xp"] += amt
    while u["xp"] >= 100 * u["lvl"]:
        u["xp"] -= 100 * u["lvl"]; u["lvl"] += 1; u["coins"] += 200; u["dmg"] += 2
        try: bot.send_message(uid, f"🎉 Уровень {u['lvl']}! +200 монет.")
        except: pass

BUSINESSES = {"farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600}, "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800}, "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}}

def set_cmds():
    cmds = [BotCommand("start", "🚀 Запустить"), BotCommand("profile", "👤 Профиль"), BotCommand("top", "🏆 Топ"), BotCommand("business", "🏢 Бизнесы"), BotCommand("shop", "🛒 Магазин"), BotCommand("bank", "🏦 Банк"), BotCommand("crypto", "📈 Биржа"), BotCommand("casino", "🎰 Казино"), BotCommand("roulette", "🎡 Рулетка"), BotCommand("treasure", "🗝 Сокровищница"), BotCommand("quest", "📜 Квест"), BotCommand("clan", "🛡 Кланы"), BotCommand("clan_upgrade", "🛡 Прокачать клан"), BotCommand("clan_top", "⚔️ Топ кланов"), BotCommand("boss", "🐉 Босс"), BotCommand("infect", "🦠 Заразить"), BotCommand("steal", "🥷 Украсть"), BotCommand("gift", "🎁 Подарить"), BotCommand("daily", "🎁 Бонус"), BotCommand("duel", "🤺 Дуэль"), BotCommand("help", "📋 Справка"), BotCommand("save", "💾 Сохранить базу")]
    bot.set_my_commands(cmds)

@bot.message_handler(commands=['save'])
def save_cmd(msg):
    if msg.from_user.id == OWNER_ID:
        save_db(); bot.reply_to(msg, "💾 База сохранена и закреплена в группе!")

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
    u = get_u(msg.from_user.id); u["name"] = msg.from_user.first_name or "Игрок"
    if msg.from_user.username: u["username"] = msg.from_user.username
    if msg.from_user.id == OWNER_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True); markup.add("👤 Профиль", "🏢 Бизнесы", "🛡 Кланы", "🎁 Бонус")
        bot.send_message(msg.from_user.id, "👑 Босс, Синдикат 19.0. База в группе с закрепом!", reply_markup=markup)
    else: bot.reply_to(msg, "Привет! Пиши /help.")

@bot.message_handler(commands=['quest'])
def quest(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_quest", 0) < 3600: return bot.reply_to(msg, "❌ Через час.")
    u["last_quest"] = time.time(); r = random.randint(500, 2000); u["coins"] += r; add_xp(msg.from_user.id, 20); bot.reply_to(msg, f"📜 +{r} монет!")

@bot.message_handler(commands=['roulette'])
def roulette(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_roulette", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки.")
    u["last_roulette"] = time.time()
    if random.random() > 0.7: w = random.randint(1000, 5000); u["coins"] += w; bot.reply_to(msg, f"🎡 +{w}!")
    else: l = u["coins"] // 2; u["coins"] -= l; bot.reply_to(msg, f"🎡 -{l}!")

@bot.message_handler(commands=['crypto'])
def crypto(msg):
    u = get_u(msg.from_user.id); markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton("Купить", callback_data="crypto_buy"), types.InlineKeyboardButton("Продать", callback_data="crypto_sell"))
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

@bot.message_handler(commands=['duel'])
def duel(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    if tid == str(msg.from_user.id): return bot.reply_to(msg, "❌ Себя нельзя.")
    u = get_u(msg.from_user.id); bet = int(msg.text.split()[-1]) if msg.text.split()[-1].isdigit() else 100
    if u["coins"] < bet: return bot.reply_to(msg, "❌ Мало.")
    if random.random() > 0.5: u["coins"] += bet; target["coins"] -= bet; bot.reply_to(msg, f"🤺 Ты победил {target['name']}!")
    else: u["coins"] -= bet; target["coins"] += bet; bot.reply_to(msg, f"🤺 {target['name']} победил.")

@bot.message_handler(commands=['business'])
def business_menu(msg):
    u = get_u(msg.from_user.id)
    if not u["businesses"]: return bot.reply_to(msg, "🏢 Нет бизнесов. Купи в /shop.")
    text = "🏢 **БИЗНЕС-ЦЕНТР**\n\n"
    for bus_id, last in u["businesses"].items(): text += f"{BUSINESSES[bus_id]['name']} — {'✅' if time.time() - last >= BUSINESSES[bus_id]['cooldown'] else '⏳'}\n"
    markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect")); bot.reply_to(msg, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "biz_collect")
def biz_collect(call):
    u = get_u(call.from_user.id); total = 0
    for bus_id, last in list(u["businesses"].items()):
        if time.time() - last >= BUSINESSES[bus_id]["cooldown"]: total += BUSINESSES[bus_id]["income"]; u["businesses"][bus_id] = time.time()
    if total > 0: u["coins"] += total; bot.answer_callback_query(call.id, f"✅ {total}!")
    else: bot.answer_callback_query(call.id, "⏳ Пусто.")

@bot.message_handler(commands=['boss'])
def boss(msg):
    global boss_hp
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_boss_hit", 0) < 2: return bot.reply_to(msg, "❌ Жди 2 сек.")
    u["last_boss_hit"] = time.time()
    if boss_hp <= 0: boss_hp = 10000; return bot.reply_to(msg, "🐉 Новый босс!")
    dmg = u["dmg"] + int(u["dmg"] * (u.get("clan_dmg_bonus", 0) / 100)) if u.get("clan") else u["dmg"]
    boss_hp -= dmg; r = 10 + u["lvl"]; u["coins"] += r
    if boss_hp <= 0: u["coins"] += 2000; bot.send_message(msg.chat.id, f"💀 БОСС УБИТ! {u['name']} +2000!")
    else: bot.reply_to(msg, f"🐉 -{dmg} HP. Осталось {boss_hp}. +{r}")

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id); clan = u.get("clan") or "Нет"; b = f" (+{u['clan_dmg_bonus']}%)" if u.get('clan') else ""; d = f"\n🔴 Долг: {u['debt']}" if u.get('debt', 0) > 0 else ""
    bot.reply_to(msg, f"👤 **{u['name']}**\n🏅 Ур: {u['lvl']}\n💰 {u['coins']}\n⚔️ Урон: {u['dmg']}{b}\n🛡 Клан: {clan}{d}", parse_mode="Markdown")

@bot.message_handler(commands=['top'])
def top(msg):
    sorted_users = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True)[:5]; text = "🏆 **Топ:**\n\n"
    for i, (uid, d) in enumerate(sorted_users, 1): text += f"{i}. {d.get('name', 'Игрок')} — {d['coins']}\n"
    bot.reply_to(msg, text, parse_mode="Markdown")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id)
    if random.random() > 0.5: u["coins"] += 300; add_xp(msg.from_user.id, 10); bot.reply_to(msg, "🔫 +300!")
    else: p = min(200, u["coins"]); u["coins"] -= p; bot.reply_to(msg, f"🚔 -{p}")

@bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id)
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Верни долг!")
    u["coins"] += 1000; u["debt"] += 1500; bot.reply_to(msg, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['give'])
def give(msg):
    if msg.from_user.id != OWNER_ID: return
    parts = msg.text.split()
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        if parts[1] in users: users[parts[1]]["coins"] += int(parts[2]); bot.reply_to(msg, "💸 Выдано!")
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

@bot.message_handler(commands=['gift'])
def gift(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    u = get_u(msg.from_user.id); parts = msg.text.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        a = int(parts[-1])
        if u["coins"] < a: return bot.reply_to(msg, "❌ Мало.")
        u["coins"] -= a; target["coins"] += a; bot.reply_to(msg, f"🎁 Подарил {a} игроку {target['name']}!")
    else: bot.reply_to(msg, "❌ /gift [ID] [Сумма]")

@bot.message_handler(commands=['clan'])
def clan_menu(msg):
    u = get_u(msg.from_user.id)
    if u.get("clan"): return bot.reply_to(msg, f"🛡 Клан: **{u['clan']}**\nБонус: +{u['clan_dmg_bonus']}%", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup(); markup.add(types.InlineKeyboardButton("Создать (5000)", callback_data="clan_create")); bot.reply_to(msg, "🛡 **Кланы**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "clan_create")
def clan_create(call):
    u = get_u(call.from_user.id)
    if u["coins"] < 5000: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 5000; u["clan"] = f"Клан_{u['name']}"; bot.answer_callback_query(call.id, "✅ Создан!")

@bot.message_handler(commands=['clan_upgrade'])
def clan_upgrade(msg):
    u = get_u(msg.from_user.id)
    if not u.get("clan"): return bot.reply_to(msg, "❌ Не в клане.")
    if u["coins"] < 10000: return bot.reply_to(msg, "❌ Нужно 10000.")
    u["coins"] -= 10000; u["clan_dmg_bonus"] += 10; bot.reply_to(msg, f"🛡 Бонус: +{u['clan_dmg_bonus']}%")

@bot.message_handler(commands=['clan_top'])
def clan_top(msg):
    clans = {}
    for uid, data in users.items():
        if data.get("clan"): clans[data["clan"]] = clans.get(data["clan"], 0) + data.get("clan_dmg_bonus", 0) + data["lvl"]
    sorted_clans = sorted(clans.items(), key=lambda x: x[1], reverse=True)[:5]; text = "⚔️ **Топ кланов:**\n\n"
    for i, (name, score) in enumerate(sorted_clans, 1): text += f"{i}. {name} — {score}\n"
    bot.reply_to(msg, text, parse_mode="Markdown")

@bot.message_handler(commands=['treasure'])
def treasure(msg):
    u = get_u(msg.from_user.id)
    if not u.get("has_chest"): return bot.reply_to(msg, "❌ Завтра.")
    u["has_chest"] = False; r = random.random()
    if r > 0.8: u["coins"] += 5000; bot.reply_to(msg, "🗝 +5000!")
    elif r > 0.5: u["dmg"] += 10; bot.reply_to(msg, "🗝 +10 урона!")
    else: bot.reply_to(msg, "🗝 Пусто.")

@bot.message_handler(commands=['infect'])
def infect(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    if tid == str(msg.from_user.id): return bot.reply_to(msg, "❌ Себя нельзя.")
    u = get_u(msg.from_user.id)
    if u["coins"] < 300: return bot.reply_to(msg, "❌ Нужно 300.")
    u["coins"] -= 300; target["virus_until"] = time.time() + 3600; bot.reply_to(msg, f"🦠 Заразил **{target['name']}**!", parse_mode="Markdown")

@bot.message_handler(commands=['steal'])
def steal(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    u = get_u(msg.from_user.id)
    if random.random() > 0.4: s = min(500, target["coins"]); target["coins"] -= s; u["coins"] += s; bot.reply_to(msg, f"🥷 Украл {s} у **{target['name']}**!", parse_mode="Markdown")
    else: u["coins"] -= min(300, u["coins"]); bot.reply_to(msg, "🚔 Поймали!")

@bot.message_handler(commands=['casino'])
def casino(msg):
    u = get_u(msg.from_user.id); parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit(): return bot.reply_to(msg, "❌ /casino 100")
    bet = int(parts[1])
    if bet > u["coins"]: return bot.reply_to(msg, "❌ Мало.")
    bot.send_dice(msg.chat.id, emoji="🎰"); time.sleep(3); res = random.randint(1, 64)
    if res == 64: u["coins"] += bet * 5; bot.reply_to(msg, f"🎰 ДЖЕКПОТ! +{bet*5}")
    elif res >= 32: u["coins"] += bet; bot.reply_to(msg, f"🎰 +{bet}")
    else: u["coins"] -= bet; bot.reply_to(msg, f"🎰 -{bet}")

@bot.message_handler(commands=['shop'])
def shop(msg):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"), types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"), types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"), types.InlineKeyboardButton("💊 Антидот (500)", callback_data="buy_antidote"), types.InlineKeyboardButton("🎁 Кейс", callback_data="open_chest"))
    bot.reply_to(msg, "🛒 **Магазин**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "open_chest")
def open_chest(call):
    u = get_u(call.from_user.id)
    if not u.get("has_chest"): return bot.answer_callback_query(call.id, "❌ Нет кейса.")
    u["has_chest"] = False
    if random.random() > 0.5: u["coins"] += 2000; bot.answer_callback_query(call.id, "✅ +2000!")
    else: u["dmg"] += 5; bot.answer_callback_query(call.id, "✅ +5 урона!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_callback(call):
    u = get_u(call.from_user.id); item = call.data.split("_")[1]
    if item == "antidote":
        if u["coins"] < 500: return bot.answer_callback_query(call.id, "❌")
        u["coins"] -= 500; u["virus_until"] = 0; bot.answer_callback_query(call.id, "💊 Вылечился!"); return
    p = BUSINESSES[item]["price"]
    if u["coins"] < p: return bot.answer_callback_query(call.id, "❌")
    u["coins"] -= p; u["businesses"][item] = 0; bot.answer_callback_query(call.id, "✅ Куплено!")

@bot.message_handler(commands=['daily'])
def daily(msg):
    u = get_u(msg.from_user.id); u["coins"] += 500; add_xp(msg.from_user.id, 100); u["has_chest"] = True; bot.reply_to(msg, "🎁 +500 монет и Кейс!")

@bot.message_handler(commands=['help'])
def help_cmd(msg): bot.reply_to(msg, "📋 /profile /business /clan /clan_upgrade /clan_top /treasure /quest /roulette /crypto /duel /boss /gift /infect /steal /shop /casino /rob /loan /daily /top /save")

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_msg(msg):
    if msg.chat.type != 'private': return
    u = get_u(msg.from_user.id)
    if msg.from_user.username: u["username"] = msg.from_user.username
    if msg.from_user.id == OWNER_ID:
        if msg.text == "👤 Профиль": profile(msg); return
        if msg.text == "🏢 Бизнесы": business_menu(msg); return
        if msg.text == "🛡 Кланы": clan_menu(msg); return
        if msg.text == "🎁 Бонус": daily(msg); return
        if msg.reply_to_message:
            t = pending_messages.get(msg.reply_to_message.message_id)
            if t:
                try: bot.copy_message(t, msg.chat.id, msg.message_id); bot.reply_to(msg, "✅ Отправлено!")
                except: bot.reply_to(msg, "❌")
            else: bot.reply_to(msg, "❌ Reply.")
        else:
            try: bot.forward_message(FRIEND_ID, msg.chat.id, msg.message_id); bot.forward_message(OWNER_ID, msg.chat.id, msg.message_id); bot.reply_to(msg, "✅ Отправлено другу и тебе!")
            except: bot.reply_to(msg, "❌")
    else:
        try:
            sent = bot.forward_message(FRIEND_ID, msg.chat.id, msg.message_id); pending_messages[sent.message_id] = msg.from_user.id
            bot.send_message(FRIEND_ID, f"✉️ От {msg.from_user.first_name}. Ответь.", reply_markup=types.ForceReply(selective=True))
            bot.forward_message(OWNER_ID, msg.chat.id, msg.message_id); bot.reply_to(msg, "✅ Отправлено!")
        except: bot.reply_to(msg, "❌")

def run_bot():
    set_cmds(); print("🚀 СИНДИКАТ 19.0 ЗАПУЩЕН."); bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
