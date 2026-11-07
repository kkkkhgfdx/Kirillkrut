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
BUSINESSES = {"farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600}, "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800}, "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users: users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "businesses": {}, "bank_deposit": 0, "bank_time": 0, "achieves": [], "last_loan": 0, "last_rob": 0, "last_steal": 0, "last_duel": 0, "last_boss_hit": 0, "last_mine": 0, "last_smuggle": 0, "has_chest": False, "last_daily": 0, "clan": None, "clan_rank": None}
    if name: users[uid_str]["name"] = name
    for k, v in {"businesses": {}, "achieves": [], "last_steal": 0, "last_duel": 0, "bank_deposit": 0, "has_chest": False, "clan": None, "clan_rank": None, "debt": 0}.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

def save_db():
    try:
        data = {"users": users, "clans": clans}
        with open("users.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="💾 База Синдиката")
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
    global boss_hp
    u = get_u(call.from_user.id, call.from_user.first_name)
    uid = str(call.from_user.id)
    
    if call.data == "menu_main": bot.edit_message_text("🚜 **Синдикат 71.0**\nВыбирай:", call.message.chat.id, call.message.message_id, reply_markup=main_kb(call.from_user.id), parse_mode="Markdown")
    elif call.data == "menu_profile":
        clan_name = clans[u["clan"]]["name"] if u.get("clan") and u["clan"] in clans else "Нет"
        text = f"👤 **{u['name']}**\n💰 {u['coins']}\n🏦 Долг: {u.get('debt', 0)}\n📈 Ур: {u['lvl']} (DMG: {u['dmg']})\n🏢 Биз: {len(u['businesses'])}\n🛡 Клан: **{clan_name}**\n🏆 Ачив: {len(u['achieves'])}"
        kb = types.InlineKeyboardMarkup()
        if u.get("debt", 0) > 0: kb.add(types.InlineKeyboardButton("💸 Вернуть долг", callback_data="pay_debt"))
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "pay_debt":
        if u.get("debt", 0) <= 0: return bot.answer_callback_query(call.id, "✅ Нет долгов!", show_alert=True)
        if u["coins"] < u["debt"]: return bot.answer_callback_query(call.id, f"❌ Мало! Долг: {u['debt']}", show_alert=True)
        u["coins"] -= u["debt"]; u["debt"] = 0; save_db()
        bot.answer_callback_query(call.id, "✅ Долг погашен!", show_alert=True)
        bot.edit_message_text("✅ Долг погашен!", call.message.chat.id, call.message.message_id, reply_markup=main_kb(call.from_user.id), parse_mode="Markdown")
    elif call.data == "menu_shop":
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"), types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"), types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"), types.InlineKeyboardButton("💊 Антидот (500)", callback_data="buy_antidote"), types.InlineKeyboardButton("🎁 Кейс", callback_data="open_chest"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text("🛒 **Магазин**", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "menu_clans":
        if u.get("clan"):
            c_id = str(u["clan"]); c = clans.get(c_id)
            if not c: u["clan"] = None; return bot.answer_callback_query(call.id, "❌ Клан удален.", show_alert=True)
            leader_id = str(c.get("leader", "")); leader_name = users.get(leader_id, {}).get('name', 'Неизвестен')
            text = f"🛡 **Клан: {c.get('name')}**\n👑 Лидер: {leader_name}\n💰 Банк: {c.get('bank', 0)}\n📈 Репа: {c.get('rep', 0)}\n👥 Людей: {len(c.get('members', []))}\n"
            kb = types.InlineKeyboardMarkup(row_width=2)
            if leader_id == uid: kb.add(types.InlineKeyboardButton("⚔️ Рейд", callback_data="clan_raid_menu"), types.InlineKeyboardButton("🗑 Удалить", callback_data="clan_disband"))
            kb.add(types.InlineKeyboardButton("💸 Вложить 1000", callback_data="clan_deposit"), types.InlineKeyboardButton("👥 Люди", callback_data="clan_members"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        else:
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton("➕ Создать (5000 💰)", callback_data="clan_create"), types.InlineKeyboardButton("📋 Список", callback_data="clan_list"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
            bot.edit_message_text("🛡 **Кланы**\nСоздай банду или вступи!", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "clan_create":
        if u["coins"] < 5000: return bot.answer_callback_query(call.id, "❌ Нужно 5000!", show_alert=True)
        u["coins"] -= 5000; c_id = str(random.randint(10000, 99999))
        while c_id in clans: c_id = str(random.randint(10000, 99999))
        clans[c_id] = {"name": f"Клан_{u['name'][:5]}", "leader": uid, "bank": 0, "rep": 0, "members": [uid]}
        u["clan"] = c_id; u["clan_rank"] = "Лидер"; save_db()
        bot.answer_callback_query(call.id, "✅ Клан создан!", show_alert=True)
        bot.edit_message_text("🛡 **Клан создан!**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    elif call.data == "clan_list":
        if not clans: return bot.answer_callback_query(call.id, "❌ Кланов нет.", show_alert=True)
        kb = types.InlineKeyboardMarkup(row_width=1)
        for c_id, c in clans.items(): kb.add(types.InlineKeyboardButton(f"Вступить в {c.get('name')}", callback_data=f"clan_join_{c_id}"))
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_clans"))
        bot.edit_message_text("📋 **Список кланов:**", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data.startswith("clan_join_"):
        c_id = call.data.split("_")[2]
        if c_id not in clans or u.get("clan"): return bot.answer_callback_query(call.id, "❌ Ошибка.", show_alert=True)
        if len(clans[c_id].get("members", [])) >= 20: return bot.answer_callback_query(call.id, "❌ Полон!", show_alert=True)
        u["clan"] = c_id; u["clan_rank"] = "Боец"; clans[c_id].setdefault("members", []).append(uid); save_db()
        bot.answer_callback_query(call.id, f"✅ Вступил!", show_alert=True)
    elif call.data == "clan_deposit":
        if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!", show_alert=True)
        u["coins"] -= 1000; clans[u["clan"]]["bank"] = clans[u["clan"]].get("bank", 0) + 1000; save_db()
        bot.answer_callback_query(call.id, "✅ +1000 в банк!", show_alert=True)
    elif call.data == "clan_members":
        c = clans.get(str(u["clan"]), {}); text = f"👥 **Участники:**\n\n"
        for m_id in c.get("members", []): text += f"- {users.get(str(m_id), {}).get('name', 'Игрок')}\n"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_clans"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "clan_raid_menu":
        kb = types.InlineKeyboardMarkup(row_width=1); found = False
        for c_id, c in clans.items():
            if str(c_id) != str(u["clan"]): kb.add(types.InlineKeyboardButton(f"Атаковать {c.get('name')} (Банк: {c.get('bank', 0)})", callback_data=f"clan_attack_{c_id}")); found = True
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_clans"))
        bot.edit_message_text("⚔️ **Выбери врага:**" if found else "❌ Нет врагов.", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data.startswith("clan_attack_"):
        target_id = call.data.split("_")[2]
        if u.get("clan_rank") != "Лидер" or target_id not in clans: return bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
        my_clan = clans[u["clan"]]; enemy = clans[target_id]
        my_power = my_clan.get("rep", 0) + len(my_clan.get("members", [])) * 10 + random.randint(1, 100)
        enemy_power = enemy.get("rep", 0) + len(enemy.get("members", [])) * 10 + random.randint(1, 100)
        if my_power > enemy_power:
            steal = max(100, int(enemy.get("bank", 0) * 0.2)); enemy["bank"] = max(0, enemy.get("bank", 0) - steal); my_clan["bank"] = my_clan.get("bank", 0) + steal; my_clan["rep"] = my_clan.get("rep", 0) + 50
            bot.answer_callback_query(call.id, f"🔥 ПОБЕДА! Забрали {steal} монет!", show_alert=True)
        else:
            my_clan["rep"] = max(0, my_clan.get("rep", 0) - 20); my_clan["bank"] = max(0, my_clan.get("bank", 0) - 200)
            bot.answer_callback_query(call.id, "💀 ПОРАЖЕНИЕ! -200 монет и репа.", show_alert=True)
        save_db()
    elif call.data == "clan_disband":
        if u.get("clan_rank") != "Лидер": return bot.answer_callback_query(call.id, "❌ Только Лидер!", show_alert=True)
        c_id = u["clan"]
        if c_id in clans:
            for m_id in clans[c_id].get("members", []):
                if str(m_id) in users: users[str(m_id)]["clan"], users[str(m_id)]["clan_rank"] = None, None
            del clans[c_id]; save_db()
        bot.answer_callback_query(call.id, "🗑 Клан удален!", show_alert=True)
        bot.edit_message_text("Клан удален.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    elif call.data == "menu_biz":
        if not u.get("businesses"): return bot.answer_callback_query(call.id, "❌ Нет бизнесов!", show_alert=True)
        text = "🏢 **Бизнесы**\n\n"
        for b, l in u["businesses"].items(): text += f"{BUSINESSES[b]['name']} — {'✅' if time.time() - l >= BUSINESSES[b]['cooldown'] else '⏳'}\n"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "biz_collect":
        total = 0
        for b, l in list(u["businesses"].items()):
            if time.time() - l >= BUSINESSES[b]["cooldown"]: total += BUSINESSES[b]["income"]; u["businesses"][b] = time.time()
        if total > 0: u["coins"] += total; save_db(); bot.answer_callback_query(call.id, f"✅ Собрано: {total}!", show_alert=True)
        else: bot.answer_callback_query(call.id, "⏳ Пусто.", show_alert=True)
    elif call.data == "menu_bank":
        if u.get("bank_deposit", 0) > 0:
            if time.time() - u.get("bank_time", 0) >= 86400: profit = int(u["bank_deposit"] * 1.2); u["coins"] += profit; u["bank_deposit"] = 0; save_db(); bot.answer_callback_query(call.id, f"🏦 +{profit}!", show_alert=True)
            else: bot.answer_callback_query(call.id, "🏦 Жди 24ч.", show_alert=True)
        else:
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
            bot.edit_message_text("🏦 **Банк (20%/сутки)**", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "bank_1000":
        if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!", show_alert=True)
        u["coins"] -= 1000; u["bank_deposit"] = 1000; u["bank_time"] = time.time(); save_db(); bot.answer_callback_query(call.id, "✅ Вложено!")
    elif call.data == "menu_boss":
        text = f"🐉 **БОСС**\n❤️ HP: {boss_hp}/10000\n\nБей и получай деньги!"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⚔️ Ударить", callback_data="hit_boss"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "hit_boss":
        if time.time() - u.get("last_boss_hit", 0) < 2: return bot.answer_callback_query(call.id, "❌ Жди 2с.", show_alert=True)
        u["last_boss_hit"] = time.time()
        if boss_hp <= 0: boss_hp = 10000; return bot.answer_callback_query(call.id, "🐉 Новый босс!", show_alert=True)
        dmg = u["dmg"]; boss_hp -= dmg; u["coins"] += dmg * 2; save_db()
        bot.answer_callback_query(call.id, f"⚔️ -{dmg} HP. Осталось {boss_hp}.", show_alert=True)
    elif call.data == "menu_casino":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("🎰 Слоты (100)", callback_data="casino_slots"), types.InlineKeyboardButton("🎡 Рулетка (1000)", callback_data="casino_roulette"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text("🎰 **Казино**", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    elif call.data == "casino_slots":
        bet = 100
        if u["coins"] < bet: return bot.answer_callback_query(call.id, "❌ Мало!", show_alert=True)
        u["coins"] -= bet; save_db(); bot.send_dice(call.message.chat.id, emoji="🎰"); time.sleep(2)
        if random.random() > 0.8: u["coins"] += bet * 5; bot.send_message(call.message.chat.id, f"🎰 ДЖЕКПОТ! +{bet*5}")
        elif random.random() > 0.5: u["coins"] += bet; bot.send_message(call.message.chat.id, f"🎰 +{bet}")
        else: bot.send_message(call.message.chat.id, f"🎰 -{bet}")
    elif call.data == "casino_roulette":
        bet = 1000
        if u["coins"] < bet: return bot.answer_callback_query(call.id, "❌ Мало!", show_alert=True)
        u["coins"] -= bet; save_db()
        if random.random() > 0.5: u["coins"] += bet * 3; bot.answer_callback_query(call.id, f"🔥 +{bet*3}!", show_alert=True)
        else: bot.answer_callback_query(call.id, f"💀 -{bet}!", show_alert=True)
    elif call.data == "menu_mine":
        if time.time() - u.get("last_mine", 0) < 60: return bot.answer_callback_query(call.id, "❌ Жди минуту.", show_alert=True)
        u["last_mine"] = time.time(); res = random.random()
        if res > 0.8: w = 1000; u["coins"] += w; bot.answer_callback_query(call.id, f"💎 +{w}!", show_alert=True)
        elif res > 0.4: w = 300; u["coins"] += w; bot.answer_callback_query(call.id, f"🪙 +{w}!", show_alert=True)
        elif res > 0.1: w = 50; u["coins"] += w; bot.answer_callback_query(call.id, f"⛏ +{w}.", show_alert=True)
        else: w = min(200, u["coins"]); u["coins"] -= w; bot.answer_callback_query(call.id, f"💥 -{w}.", show_alert=True)
        save_db()
    elif call.data == "menu_smuggle":
        if time.time() - u.get("last_smuggle", 0) < 60: return bot.answer_callback_query(call.id, "❌ Жди минуту.", show_alert=True)
        if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Нужно 1000.", show_alert=True)
        u["last_smuggle"] = time.time(); save_db()
        if random.random() > 0.5: u["coins"] += 3000; bot.answer_callback_query(call.id, "🕵️ +3000.", show_alert=True)
        else: u["coins"] -= 1000; bot.answer_callback_query(call.id, "🚔 -1000.", show_alert=True)
    elif call.data == "menu_daily":
        if time.time() - u.get("last_daily", 0) < 86400: return bot.answer_callback_query(call.id, "❌ Раз в сутки!", show_alert=True)
        u["last_daily"] = time.time(); u["has_chest"] = True; save_db(); bot.answer_callback_query(call.id, "🎁 Кейс получен!", show_alert=True)
    elif call.data == "menu_top":
        s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True); t = "🏆 **Топ:**\n\n"
        for i, (user_id, d) in enumerate(s[:10], 1): t += f"{i}. {d.get('name', 'Игрок')} — {d.get('coins', 0)} 💰\n"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text(t, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
@bot.message_handler(commands=['start', 'menu'])
def start(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if msg.from_user.username: u["username"] = msg.from_user.username
    if msg.text == "/start": give_achieve(msg.from_user.id, "Первые шаги", 100)
    bot.send_message(msg.from_user.id, "🔥 **Синдикат 71.0**\nЖми кнопки или пиши /help.", reply_markup=main_kb(msg.from_user.id), parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_cmd(msg): bot.reply_to(msg, "📋 /menu /profile /top /shop /business /bank /loan /paydebt /rob /boss /casino /mine /smuggle /steal /infect /duel /duelclub /myclan /clantop /achieves /daily /gift /save /reset /ban")

@bot.message_handler(commands=['myclan'])
def myclan_cmd(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if not u.get("clan") or str(u["clan"]) not in clans: return bot.reply_to(msg, "🛡 Нет клана.")
    c = clans[str(u["clan"])]; leader_id = str(c.get("leader", ""))
    text = f"🛡 **{c.get('name')}**\n👑 Лидер: {users.get(leader_id, {}).get('name', '?')}\n💰 Банк: {c.get('bank', 0)}\n📈 Репа: {c.get('rep', 0)}\n👥 Людей: {len(c.get('members', []))}\n"
    kb = types.InlineKeyboardMarkup()
    if leader_id == str(msg.from_user.id): kb.add(types.InlineKeyboardButton("⚔️ Рейд", callback_data="clan_raid_menu"))
    kb.add(types.InlineKeyboardButton("👥 Люди", callback_data="clan_members"))
    bot.reply_to(msg, text, reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(commands=['clantop'])
def clantop_cmd(msg):
    if not clans: return bot.reply_to(msg, "❌ Кланов нет.")
    s = sorted(clans.items(), key=lambda x: (x[1].get("rep", 0), x[1].get("bank", 0)), reverse=True)
    t = "🏆 **Топ кланов:**\n\n"
    for i, (cid, c) in enumerate(s[:10], 1): t += f"{i}. 🛡 **{c.get('name')}** | Репа: {c.get('rep', 0)} | 💰 {c.get('bank', 0)}\n"
    bot.reply_to(msg, t, parse_mode="Markdown")

@bot.message_handler(commands=['paydebt'])
def paydebt_cmd(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u.get("debt", 0) <= 0: return bot.reply_to(msg, "✅ Нет долгов!")
    if u["coins"] < u["debt"]: return bot.reply_to(msg, f"❌ Мало! Долг: {u['debt']}.")
    u["coins"] -= u["debt"]; u["debt"] = 0; save_db(); bot.reply_to(msg, "✅ Долг погашен!")

@bot.message_handler(commands=['mine'])
def mine(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_mine", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    u["last_mine"] = time.time(); res = random.random()
    if res > 0.8: w = 1000; u["coins"] += w; bot.reply_to(msg, f"💎 +{w}!")
    elif res > 0.4: w = 300; u["coins"] += w; bot.reply_to(msg, f"🪙 +{w}!")
    elif res > 0.1: w = 50; u["coins"] += w; bot.reply_to(msg, f"⛏ +{w}.")
    else: w = min(200, u["coins"]); u["coins"] -= w; bot.reply_to(msg, f"💥 -{w}.")

@bot.message_handler(commands=['smuggle'])
def smuggle(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_smuggle", 0) < 60: return bot.reply_to(msg, "❌ Жди минуту.")
    if u["coins"] < 1000: return bot.reply_to(msg, "❌ Нужно 1000.")
    u["last_smuggle"] = time.time()
    if random.random() > 0.5: u["coins"] += 3000; bot.reply_to(msg, "🕵️ +3000.")
    else: u["coins"] -= 1000; bot.reply_to(msg, "🚔 -1000.")

@bot.message_handler(commands=['duelclub'])
def duelclub(msg):
    global duel_club
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u["coins"] < 500: return bot.reply_to(msg, "❌ Ставка 500.")
    if str(msg.from_user.id) in duel_club["players"]: return bot.reply_to(msg, "❌ Ты уже в клубе.")
    u["coins"] -= 500; duel_club["pot"] += 500; duel_club["players"][str(msg.from_user.id)] = u["name"]
    bot.reply_to(msg, f"⚔️ Банк: {duel_club['pot']}. Ждем...")
    if len(duel_club["players"]) >= 3:
        winner_id = random.choice(list(duel_club["players"].keys())); winner_name = duel_club["players"][winner_id]
        get_u(winner_id)["coins"] += duel_club["pot"]; bot.send_message(CHAT_ID, f"🏆 **КЛУБ:** {winner_name} забирает {duel_club['pot']}!"); duel_club = {"pot": 0, "players": {}}

@bot.message_handler(commands=['loan'])
def loan(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_loan", 0) < 10: return bot.reply_to(msg, "❌ Жди 10с.")
    if u["debt"] > 0: return bot.reply_to(msg, "❌ Верни долг (/paydebt)!")
    u["last_loan"] = time.time(); u["coins"] += 1000; u["debt"] += 1500; bot.reply_to(msg, "🏦 +1000. Долг: 1500.")

@bot.message_handler(commands=['rob'])
def rob(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_rob", 0) < 10: return bot.reply_to(msg, "❌ Жди 10с.")
    u["last_rob"] = time.time()
    if random.random() > 0.5: u["coins"] += 300; bot.reply_to(msg, "🔫 +300!")
    else: 
        p = min(200, u["coins"])
        u["coins"] -= p
        bot.reply_to(msg, f"🚔 -{p}")

@bot.message_handler(commands=['bank'])
def bank(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if u.get("bank_deposit", 0) > 0:
        if time.time() - u.get("bank_time", 0) >= 86400: 
                u["coins"] += int(u["bank_deposit"] * 1.2)
                u["bank_deposit"] = 0
                bot.reply_to(msg, f"🏦 Банк начислил проценты!")
        else: 
            bot.reply_to(msg, "🏦 Жди 24ч.")
        return
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000"))
    bot.reply_to(msg, "🏦 Банк (20%)", reply_markup=m)

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
    m.add(types.InlineKeyboardButton("🌾 Ферма (1000)", callback_data="buy_farm"), types.InlineKeyboardButton("🌳 Сад (3000)", callback_data="buy_garden"), types.InlineKeyboardButton("🏭 Завод (10000)", callback_data="buy_factory"), types.InlineKeyboardButton("💊 Антидот (500)", callback_data="buy_antidote"), types.InlineKeyboardButton("🎁 Открыть Кейс", callback_data="open_chest"))
    bot.reply_to(msg, "🛒 **Магазин**", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_") or call.data == "open_chest")
def buy_cb(call):
    u = get_u(call.from_user.id)
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
    if u["coins"] < p: return bot.answer_callback_query(call.id, "❌")
    u["coins"] -= p
    if "businesses" not in u: u["businesses"] = {}
    u["businesses"][i] = 0; save_db()
    bot.answer_callback_query(call.id, f"✅ {BUSINESSES[i]['name']} куплен!")

@bot.message_handler(commands=['business'])
def business_menu(msg):
    u = get_u(msg.from_user.id)
    if not u.get("businesses"): return bot.reply_to(msg, "🏢 Купи в /shop.")
    text = "🏢 **БИЗНЕС**\n\n"
    for b, l in u["businesses"].items(): text += f"{BUSINESSES[b]['name']} — {'✅' if time.time() - l >= BUSINESSES[b]['cooldown'] else '⏳'}\n"
    m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("💰 Собрать", callback_data="biz_collect")); bot.reply_to(msg, text, reply_markup=m, parse_mode="Markdown")

@bot.message_handler(commands=['daily'])
def daily(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    if time.time() - u.get("last_daily", 0) < 86400: return bot.reply_to(msg, "❌ Раз в сутки!")
    u["last_daily"] = time.time(); u["has_chest"] = True
    bot.reply_to(msg, "🎁 Ты получил Ежедневный Кейс! Открой его в /shop.")

@bot.message_handler(commands=['top'])
def top(msg):
    s = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True); t = "🏆 **Топ:**\n\n"
    for i, (uid, d) in enumerate(s, 1): t += f"{i}. {d.get('name', 'Игрок')} — {d.get('coins', 0)}\n"
    bot.reply_to(msg, t[:4000])

@bot.message_handler(commands=['profile'])
def profile(msg):
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    clan_name = clans[u["clan"]]["name"] if u.get("clan") and u["clan"] in clans else "Нет"
    bot.reply_to(msg, f"👤 {u['name']}\n💰 {u['coins']}\n🏦 Долг: {u.get('debt', 0)}\n📈 Уровень: {u['lvl']} (DMG: {u['dmg']})\n🛡 Клан: {clan_name}\n🏆 Ачивок: {len(u['achieves'])}")

@bot.message_handler(commands=['achieves'])
def show_achieves(msg):
    u = get_u(msg.from_user.id)
    if not u["achieves"]: return bot.reply_to(msg, "Нет ачивок.")
    bot.reply_to(msg, "🏆 Ачивки:\n" + "\n".join(u["achieves"]))

@bot.message_handler(commands=['reset'])
def reset_cmd(msg):
    if msg.from_user.id != OWNER_ID: return
    if msg.reply_to_message:
        target_id = str(msg.reply_to_message.from_user.id)
        if target_id in users: users[target_id]["coins"] = 0; save_db(); bot.reply_to(msg, f"🧹 {users[target_id].get('name')} обнулен!")
        else: bot.reply_to(msg, "❌ Нет в базе.")
        return
    parts = msg.text.split()
    if len(parts) < 2: return bot.reply_to(msg, "❌ /reset @юзер или Reply")
    un = parts[1].replace("@", "").lower()
    for uid, data in users.items():
        if data.get("username", "").lower() == un: data["coins"] = 0; save_db(); return bot.reply_to(msg, f"🧹 @{un} обнулен!")
    bot.reply_to(msg, "❌ Не найден.")

@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.id != OWNER_ID: return
    if msg.reply_to_message:
        target_id = str(msg.reply_to_message.from_user.id)
        if target_id in users: del users[target_id]; save_db(); bot.reply_to(msg, f"🚫 {target_id} забанен!")
        else: bot.reply_to(msg, "❌ Нет в базе.")
        return
    parts = msg.text.split()
    if len(parts) < 2: return bot.reply_to(msg, "❌ /ban [ID] или Reply")
    if parts[1] in users: del users[parts[1]]; save_db(); bot.reply_to(msg, f"🚫 {parts[1]} забанен!")
    else: bot.reply_to(msg, "❌ Не найден.")

@bot.message_handler(commands=['gift'])
def gift(msg):
    tid, target = get_target(msg)
    if not target: return bot.reply_to(msg, "❌ @юзер или Reply.")
    u = get_u(msg.from_user.id, msg.from_user.first_name)
    parts = msg.text.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        a = int(parts[-1])
        if u["coins"] < a: return bot.reply_to(msg, "❌ Мало.")
        u["coins"] -= a; target["coins"] += a; save_db()
        bot.reply_to(msg, f"🎁 Подарил {a} игроку {target['name']}!")
    else: bot.reply_to(msg, "❌ /gift [Сумма]")

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
    cmds = [BotCommand("menu", "Меню"), BotCommand("start", "Старт"), BotCommand("help", "Справка"), BotCommand("profile", "Профиль"), BotCommand("top", "Топ"), BotCommand("shop", "Магазин"), BotCommand("business", "Бизнесы"), BotCommand("bank", "Банк"), BotCommand("loan", "Кредит"), BotCommand("paydebt", "Вернуть долг"), BotCommand("rob", "Ограбить"), BotCommand("boss", "Босс"), BotCommand("casino", "Казино"), BotCommand("mine", "Шахта"), BotCommand("smuggle", "Контрабанда"), BotCommand("duelclub", "Дуэльный Клуб"), BotCommand("steal", "Украсть"), BotCommand("infect", "Заразить"), BotCommand("duel", "Дуэль"), BotCommand("myclan", "Мой Клан"), BotCommand("clantop", "Топ Кланов"), BotCommand("achieves", "Ачивки"), BotCommand("daily", "Бонус"), BotCommand("gift", "Подарить"), BotCommand("save", "Сохранить"), BotCommand("reset", "Обнулить")]
    bot.set_my_commands(cmds)
    print("🚀 СИНДИКАТ 71.0 ЗАПУЩЕН!")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
