from app import bot, users, get_u, save_db, add_xp, get_target, BUSINESSES, boss_hp
from telebot import types
import random, time

@bot.message_handler(commands=['start'])
def start(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.from_user.id, "Бот запущен! Пиши /help.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['help'])
def help_cmd(msg): bot.reply_to(msg, "📋 /profile /loan /rob /bank /boss /top /daily /save /reset")

@bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_loan", 0) < 10: return bot.reply_to(msg, "❌ Жди 10 сек!")
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Верни долг!")
    u["last_loan"] = time.time(); u["coins"] += 1000; u["debt"] += 1500; bot.reply_to(msg, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_rob", 0) < 10: return bot.reply_to(msg, "❌ Жди 10 сек!")
    u["last_rob"] = time.time()
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "🔫 +300!")
    else: p = min(200, u["coins"]); u["coins"] -= p; bot.reply_to(msg, f"🚔 -{p}")

@bot.message_handler(commands=['bank'])
def bank(msg):
    u = get_u(msg.from_user.id)
    if u.get("bank_deposit", 0) > 0: return bot.reply_to(msg, "🏦 Вклад уже открыт.")
    m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000")); bot.reply_to(msg, "🏦 Банк (20%)", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "bank_1000")
def bank_dep(call):
    u = get_u(call.from_user.id)
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!")
    u["coins"] -= 1000; u["bank_deposit"] = 1000; u["bank_time"] = time.time(); bot.answer_callback_query(call.id, "✅ Вложено!")

@bot.message_handler(commands=['daily'])
def daily(msg):
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_daily", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки!")
    u["last_daily"] = time.time(); u["coins"] += 500; add_xp(msg.from_user.id, 100); bot.reply_to(msg, "🎁 +500!")

@bot.message_handler(commands=['boss'])
def boss(msg):
    import app
    u = get_u(msg.from_user.id)
    if time.time() - u.get("last_boss_hit", 0) < 2: return bot.reply_to(msg, "❌ Жди 2 сек.")
    u["last_boss_hit"] = time.time()
    if app.boss_hp <= 0: app.boss_hp = 10000; return bot.reply_to(msg, "🐉 Новый босс!")
    dmg = u["dmg"]; app.boss_hp -= dmg; u["coins"] += dmg * 2
    bot.reply_to(msg, f"🐉 -{dmg} HP. Осталось {app.boss_hp}.")

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id); c = u.get("clan") or "Нет"
    bot.reply_to(msg, f"👤 {u['name']}\n🏅 Ур: {u['lvl']}\n💰 {u['coins']}\n⚔️ Урон: {u['dmg']}\n🛡 Клан: {c}")

@bot.message_handler(commands=['top'])
def top(msg):
    s = sorted(users.items(), key=lambda x: x[1]["coins"], reverse=True); t = "🏆 Топ:\n\n"
    for i, (uid, d) in enumerate(s, 1): t += f"{i}. {d.get('name', 'Игрок')} — {d['coins']}\n"
    for x in range(0, len(t), 4000): bot.send_message(msg.chat.id, t[x:x+4000])

@bot.message_handler(commands=['save'])
def save_cmd(msg):
    from app import OWNER_ID, save_db
    if msg.from_user.id == OWNER_ID: save_db(); bot.reply_to(msg, "💾 ОК!")

@bot.message_handler(commands=['reset'])
def reset_cmd(msg):
    from app import OWNER_ID
    if msg.from_user.id != OWNER_ID: return
    parts = msg.text.split()
    if len(parts) < 2: return bot.reply_to(msg, "❌ /reset @юзер")
    un = parts[1].replace("@", "").lower()
    for uid, d in users.items():
        if d.get("username", "").lower() == un: d["coins"] = 0; save_db(); bot.reply_to(msg, f"🧹 {un} обнулен!"); return

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_msg(msg):
    from app import OWNER_ID, FRIEND_ID, pending_messages
    if msg.chat.type != 'private': return
    u = get_u(msg.from_user.id)
    if msg.from_user.id == OWNER_ID:
        if msg.reply_to_message:
            t = pending_messages.get(msg.reply_to_message.message_id)
            if t:
                try: bot.copy_message(t, msg.chat.id, msg.message_id); bot.reply_to(msg, "✅!")
                except: pass
        else:
            try: bot.forward_message(FRIEND_ID, msg.chat.id, msg.message_id); bot.forward_message(OWNER_ID, msg.chat.id, msg.message_id)
            except: pass
