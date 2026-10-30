import telebot, random, json, os, time, threading
from telebot import types
from flask import Flask

# ========== НАСТРОЙКИ ==========
TOKEN = "9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0"
OWNER_ID = 6170286634
FRIEND_ID = 7527864291
CHAT_ID = -1004215885788

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users, boss_hp, pending_messages, crypto_price = {}, 10000, {}, 1000
market_item = {"name": None, "price": 0, "time": 0}

def get_u(uid, name=None):
    uid_str = str(uid)
    if uid_str not in users:
        users[uid_str] = {"coins": 1000, "debt": 0, "lvl": 1, "xp": 0, "dmg": 10, "name": name or "Игрок", "businesses": {}, "clan": None, "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_roulette": 0, "last_casino": 0, "last_daily": 0, "achieves": [], "last_arena": 0, "multi": 1, "last_steal": 0, "casino_plays": 0, "last_loan": 0, "last_rob": 0, "last_craft": 0, "last_duel": 0}
    if name: users[uid_str]["name"] = name
    defaults = {"businesses": {}, "clan": None, "debt": 0, "dmg": 10, "name": "Игрок", "username": "", "crypto": 0, "bank_deposit": 0, "has_chest": False, "clan_dmg_bonus": 0, "last_quest": 0, "last_boss_hit": 0, "last_roulette": 0, "last_casino": 0, "last_daily": 0, "achieves": [], "last_arena": 0, "multi": 1, "last_steal": 0, "casino_plays": 0, "last_loan": 0, "last_rob": 0, "last_craft": 0, "last_duel": 0}
    for k, v in defaults.items():
        if k not in users[uid_str]: users[uid_str][k] = v
    return users[uid_str]

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
