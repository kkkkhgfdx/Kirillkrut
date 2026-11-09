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

BUSINESSES = {
    "farm": {"name": "🌾 Ферма", "price": 1000, "income": 200, "cooldown": 3600},
    "garden": {"name": "🌳 Сад", "price": 3000, "income": 500, "cooldown": 1800},
    "factory": {"name": "🏭 Завод", "price": 10000, "income": 2000, "cooldown": 7200}
}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "dmg": 10, "name": name or "Игрок", "businesses": {}, "bank_deposit": 0, "bank_time": 0, "achieves": [], "last_loan": 0, "last_rob": 0, "last_steal": 0, "last_duel": 0, "last_boss_hit": 0, "last_mine": 0, "last_smuggle": 0, "has_chest": False, "last_daily": 0, "clan": None, "clan_rank": None, "safe": 0}
    if name: users[uid_str]["name"] = name
    for k, v in {"businesses": {}, "achieves": [], "last_steal": 0, "last_duel": 0, "bank_deposit": 0, "has_chest": False, "clan": None, "clan_rank": None, "debt": 0, "safe": 0}.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

def save_db():
    try:
        data = {"users": users, "clans": clans}
        with open("users.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
        with open("users.json", "rb") as f:
            sent = bot.send_document(CHAT_ID, f, caption="💾 База Синдиката 74.0 (Прайм)")
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
    # ПРОВЕРКА: Если меню вызвал один, а нажал другой
    if call.message.reply_to_message and call.message.reply_to_message.from_user.id != call.from_user.id:
        return bot.answer_callback_query(call.id, "❌ Это меню не твое! Вызови /menu сам.", show_alert=True)
        
    global boss_hp
    u = get_u(call.from_user.id, call.from_user.first_name)
    uid = str(call.from_user.id)
    
    # ================= МАГАЗИН (ПОЧИНЕН) =================
    if call.data.startswith("buy_") or call.data == "open_chest":
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
        if u["coins"] < p: return bot.answer_callback_query(call.id, "❌ Мало денег!")
        u["coins"] -= p
        if "businesses" not in u: u["businesses"] = {}
        u["businesses"][i] = time.time() - BUSINESSES[i]["cooldown"]
        save_db()
        bot.answer_callback_query(call.id, f"✅ {BUSINESSES[i]['name']} куплен!")
        return

    # ================= МЕНЮ =================
    if call.data == "menu_main": 
        bot.edit_message_text("🚜 **Синдикат 74.0**\nВыбирай:", call.message.chat.id, call.message.message_id, reply_markup=main_kb(call.from_user.id), parse_mode="Markdown")
    elif call.data == "menu_profile":
        clan_name = "Нет"
        if u.get("clan") and str(u["clan"]) in clans: clan_name = clans[str(u["clan"])].get("name", "Нет")
        text = f"👤 **{u['name']}**\n💰 Монеты: {u['coins']}\n🏦 Долг: {u.get('debt', 0)}\n🔒 Сейф: {u.get('safe', 0)}\n📈 Уровень: {u['lvl']} (DMG: {u['dmg']})\n🏢 Бизнесов: {len(u['businesses'])}\n🛡 Клан: **{clan_name}**\n🏆 Ачивок: {len(u['achieves'])}"
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
        bot.edit_message_text("🛒 Магазин", call.message.chat.id, call.message.message_id, reply_markup=kb)
        elif call.data == "menu_clans":
    c_id = str(u.get("clan", ""))
    if c_id and c_id in clans:
        c = clans[c_id]; leader_id = str(c.get("leader", ""))
        text = f"🛡 **{c.get('name')}**\n👑 Лидер: {users.get(leader_id, {}).get('name', '?')}\n💰 Банк: {c.get('bank', 0)}\n📈 Репа: {c.get('rep', 0)} (Ур. {c.get('lvl', 1)})\n🛡 Защита: {c.get('def', 0)}\n👥 Людей: {len(c.get('members', []))}"
        kb = types.InlineKeyboardMarkup(row_width=2)
        if leader_id == uid: 
            kb.add(types.InlineKeyboardButton("⚔️ Рейд", callback_data="clan_raid_menu"), types.InlineKeyboardButton("🗑 Удалить", callback_data="clan_disband"))
            kb.add(types.InlineKeyboardButton("🔗 Инвайт", callback_data=f"clan_invite_{c_id}"))
        kb.add(types.InlineKeyboardButton("💸 Вложить 1000", callback_data="clan_deposit"), types.InlineKeyboardButton("🛡 Апгрейд", callback_data="clan_upgrade"), types.InlineKeyboardButton("👥 Люди", callback_data="clan_members"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("➕ Создать (5000 💰)", callback_data="clan_create"), types.InlineKeyboardButton("📋 Список", callback_data="clan_list"), types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
        bot.edit_message_text("🛡 **Кланы**\nСоздай банду или вступи!", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
elif call.data == "clan_create":
    if u["coins"] < 5000: return bot.answer_callback_query(call.id, "❌ Нужно 5000!", show_alert=True)
    u["coins"] -= 5000; c_id = str(random.randint(10000, 99999))
    while c_id in clans: c_id = str(random.randint(10000, 99999))
    clans[c_id] = {"name": f"Клан_{u['name'][:5]}", "leader": uid, "bank": 0, "rep": 0, "lvl": 1, "def": 0, "members": [uid]}
    u["clan"] = c_id; u["clan_rank"] = "Лидер"; save_db()
    bot.answer_callback_query(call.id, "✅ Клан создан!", show_alert=True)
    bot.edit_message_text("🛡 **Клан создан!** Иди в /myclan.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
elif call.data == "clan_list":
    if not clans: return bot.answer_callback_query(call.id, "❌ Кланов нет.", show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for c_id, c in clans.items(): kb.add(types.InlineKeyboardButton(f"Вступить в {c.get('name')} (Ур.{c.get('lvl',1)})", callback_data=f"clan_join_{c_id}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_clans"))
    bot.edit_message_text("📋 **Список кланов:**", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
elif call.data.startswith("clan_join_"):
    c_id = call.data.split("_")[2]
    if c_id not in clans or u.get("clan"): return bot.answer_callback_query(call.id, "❌ Ошибка.", show_alert=True)
    if len(clans[c_id].get("members", [])) >= 20: return bot.answer_callback_query(call.id, "❌ Полон!", show_alert=True)
    u["clan"] = c_id; u["clan_rank"] = "Боец"; clans[c_id].setdefault("members", []).append(uid); save_db()
    bot.answer_callback_query(call.id, f"✅ Вступил!", show_alert=True)
elif call.data.startswith("clan_invite_"):
    c_id = call.data.split("_")[2]
    bot.answer_callback_query(call.id, "Ссылка скопирована (отправь другу)!", show_alert=True)
    bot.send_message(call.message.chat.id, f"👋 Приглашаю в мой клан! Нажми кнопку ниже:", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Вступить в клан", callback_data=f"clan_join_{c_id}")))
elif call.data == "clan_deposit":
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!", show_alert=True)
    u["coins"] -= 1000; clans[u["clan"]]["bank"] = clans[u["clan"]].get("bank", 0) + 1000; save_db()
    bot.answer_callback_query(call.id, "✅ +1000 в банк!", show_alert=True)
elif call.data == "clan_upgrade":
    if u.get("clan_rank") != "Лидер": return bot.answer_callback_query(call.id, "❌ Только Лидер!", show_alert=True)
    c = clans[u["clan"]]; cost = c.get("lvl", 1) * 5000
    if c.get("bank", 0) < cost: return bot.answer_callback_query(call.id, f"❌ Нужно {cost} в банке!", show_alert=True)
    c["bank"] -= cost; c["lvl"] = c.get("lvl", 1) + 1; c["def"] = c.get("def", 0) + 50; save_db()
    bot.answer_callback_query(call.id, f"✅ Клан прокачан до Ур.{c['lvl']}! +50 Защиты.", show_alert=True)
elif call.data == "clan_members":
    c = clans.get(str(u["clan"]), {}); text = f"👥 **Участники:**\n\n"
    for m_id in c.get("members", []): text += f"- {users.get(str(m_id), {}).get('name', 'Игрок')} ({users.get(str(m_id), {}).get('clan_rank', 'Боец')})\n"
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_clans"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
elif call.data == "clan_raid_menu":
    kb = types.InlineKeyboardMarkup(row_width=1); found = False
    for c_id, c in clans.items():
        if str(c_id) != str(u["clan"]): kb.add(types.InlineKeyboardButton(f"Атаковать {c.get('name')} (Банк: {c.get('bank', 0)} | Защ: {c.get('def',0)})", callback_data=f"clan_attack_{c_id}")); found = True
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_clans"))
    bot.edit_message_text("⚔️ **Выбери врага:**\n(Забираешь 30% банка)" if found else "❌ Нет врагов.", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
elif call.data.startswith("clan_attack_"):
    target_id = call.data.split("_")[2]
    if u.get("clan_rank") != "Лидер": return bot.answer_callback_query(call.id, "❌ Только Лидер!", show_alert=True)
    if target_id not in clans: return bot.answer_callback_query(call.id, "❌ Клан исчез.", show_alert=True)
    my_clan = clans[u["clan"]]; enemy = clans[target_id]
    my_power = my_clan.get("rep", 0) + len(my_clan.get("members", [])) * 10 + random.randint(1, 100)
    enemy_power = enemy.get("rep", 0) + len(enemy.get("members", [])) * 10 + enemy.get("def", 0) + random.randint(1, 100)
    if my_power > enemy_power:
        steal = max(1000, int(enemy.get("bank", 0) * 0.3)); enemy["bank"] = max(0, enemy.get("bank", 0) - steal); my_clan["bank"] = my_clan.get("bank", 0) + steal; my_clan["rep"] = my_clan.get("rep", 0) + 100
        bot.answer_callback_query(call.id, f"🔥 ПОБЕДА! Забрали {steal} монет и +100 репы!", show_alert=True)
    else:
        my_clan["rep"] = max(0, my_clan.get("rep", 0) - 50); loss = min(my_clan.get("bank", 0), 1000); my_clan["bank"] -= loss
        bot.answer_callback_query(call.id, f"💀 ПОРАЖЕНИЕ! Потеряли {loss} монет и 50 репы.", show_alert=True)
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
elif call.data == "menu_bank":
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("Вложить 1000", callback_data="bank_1000"), types.InlineKeyboardButton("🔒 В сейф 1000", callback_data="safe_1000"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"))
    bot.edit_message_text("🏦 **Банк / Сейф**\nВ банке 20% в сутки (но можно ограбить). В сейфе монеты в безопасности!", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
elif call.data == "bank_1000":
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!", show_alert=True)
    u["coins"] -= 1000; u["bank_deposit"] = u.get("bank_deposit", 0) + 1000; save_db(); bot.answer_callback_query(call.id, "✅ Вложено в банк!")
elif call.data == "safe_1000":
    if u["coins"] < 1000: return bot.answer_callback_query(call.id, "❌ Мало!", show_alert=True)
    u["coins"] -= 1000; u["safe"] = u.get("safe", 0) + 1000; save_db(); bot.answer_callback_query(call.id, "🔒 В сейфе! Ограбить не смогут.")
