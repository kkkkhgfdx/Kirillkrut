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

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "last_loan": 0, "last_rob": 0, "bank_deposit": 0, "bank_time": 0, "achieves": [], "last_boss_hit": 0, "last_steal": 0, "last_duel": 0}
    if name: users[uid_str]["name"] = name
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
        try: bot.send_message(CHAT_ID, f"🏆 **АЧИВКА!** {u['name']} получил **{name}** (+{reward} монет)!")
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
    get_u(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.from_user.id, "Бот запущен! Пиши /help.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['help'])
def help_cmd(msg): bot.reply_to(msg, "📋 /profile /top /bank /loan /rob /boss /casino /achieves /steal /infect /duel /save /give /broadcast /sendchat /reset")

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
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "🔫 +300!")
    else: p = min(200, u["coins"]); u["coins"] -= p; bot.reply_to(msg, f"🚔 -{p}")

@bot.message_handler(commands=['bank'])
def bank(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u.get("bank_deposit", 0) > 0:
        if time.time() - u.get("bank_time", 0) >= 86400:
            profit = int(u["bank_deposit"] * 1.2); u["coins"] += profit; u["bank_deposit"] = 0; bot.reply_to(msg, f"🏦 Вклад закрыт! +{profit}")
        else: bot.reply_to(msg, "🏦 Жди 24 часа.")
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

@bot.message_handler(commands=['sendchat'])
def sendchat(msg):
    if msg.from_user.id != OWNER_ID: return
    text = msg.text.replace("/sendchat", "").strip()
    if not text: return bot.reply_to(msg, "❌ Пусто.")
    try: bot.send_message(CHAT_ID, text); bot.reply_to(msg, "✅ Отправлено в чат!")
    except Exception as e: bot.reply_to(msg, f"❌ {e}")

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
    cmds = [BotCommand("start", "Старт"), BotCommand("help", "Справка"), BotCommand("profile", "Профиль"), BotCommand("top", "Топ"), BotCommand("bank", "Банк"), BotCommand("loan", "Кредит"), BotCommand("rob", "Ограбить"), BotCommand("boss", "Босс"), BotCommand("casino", "Казино"), BotCommand("steal", "Украсть"), BotCommand("infect", "Заразить"), BotCommand("duel", "Дуэль"), BotCommand("achieves", "Ачивки"), BotCommand("save", "Сохранить"), BotCommand("reset", "Обнулить")]
    bot.set_my_commands(cmds)
    print("🚀 ЗАПУЩЕН!")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
@bot.message_handler(commands=['wipe_group'])
def wipe_group(msg):
    if msg.from_user.id != OWNER_ID: return
    to_delete = []
    for uid, data in users.items():
        name = str(data.get("name", "")).lower()
        if "group" in name or "группа" in name:
            to_delete.append(uid)
    
    if not to_delete:
        return bot.reply_to(msg, "❌ Не нашел никого с именем 'Group' или 'Группа'.")
        
    for uid in to_delete:
        del users[uid]
    save_db()
    bot.reply_to(msg, f"🧹 Удалено из базы: {len(to_delete)} шт. (ID: {', '.join(to_delete)})")
