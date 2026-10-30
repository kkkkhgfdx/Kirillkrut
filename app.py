import telebot, random, json, os, time, threading
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
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "xp": 0, "dmg": 10, "name": name or "Игрок", "businesses": {}, "clan": None, "username": "", "bank_deposit": 0, "last_loan": 0, "last_rob": 0, "last_daily": 0, "last_boss_hit": 0, "has_chest": False}
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

def add_xp(uid, amt):
    u = get_u(uid); u["xp"] += amt
    while u["xp"] >= 100 * u["lvl"]: u["xp"] -= 100 * u["lvl"]; u["lvl"] += 1; u["coins"] += 200; u["dmg"] += 2

def get_target(msg):
    if msg.reply_to_message: return str(msg.reply_to_message.from_user.id), get_u(msg.reply_to_message.from_user.id)
    parts = msg.text.split()
    if len(parts) > 1 and parts[1].startswith("@"):
        un = parts[1].replace("@", "").lower()
        for uid, data in users.items():
            if data.get("username", "").lower() == un: return uid, data
    return None, None

def run_bot():
    print("🚀 Запущен!")
    import commands
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
