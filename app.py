import telebot
import json
import os
import random
import time
from datetime import datetime
from flask import Flask
import threading

# ================= НАСТРОЙКИ =================
TOKEN = '9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0'
CHANNEL_ID = '-100...'  # ВСТАВЬ СЮДА ID КАНАЛА (например, -1001234567890)
bot = telebot.TeleBot(TOKEN)
DB_FILE = 'users.json'

# --- FLASK (для Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот Синдикат работает!"

# ================= АВТОСОХРАНЕНИЕ В КАНАЛ =================
def download_db_from_channel():
    """Скачивает файл users.json из закрепленного сообщения в канале при запуске"""
    try:
        chat_info = bot.get_chat(CHANNEL_ID)
        pinned_message = chat_info.pinned_message
        
        if pinned_message and pinned_message.document:
            file_id = pinned_message.document.file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            with open(DB_FILE, 'wb') as new_file:
                new_file.write(downloaded_file)
            print("✅ База данных успешно скачана из канала.")
            return True
        else:
            print("⚠️ В канале нет закрепленного файла. Создаю новую базу.")
            return False
    except Exception as e:
        print(f"❌ Ошибка скачивания базы: {e}")
        return False

def upload_db_to_channel():
    """Отправляет обновленный users.json в канал и закрепляет его"""
    if not os.path.exists(DB_FILE):
        return
        
    try:
        chat_info = bot.get_chat(CHANNEL_ID)
        if chat_info.pinned_message:
            bot.unpin_chat_message(CHANNEL_ID, chat_info.pinned_message.message_id)
            
        with open(DB_FILE, 'rb') as f:
            msg = bot.send_document(CHANNEL_ID, f, caption="🗄 Актуальная база данных")
            
        bot.pin_chat_message(CHANNEL_ID, msg.message_id)
        print("✅ База данных обновлена в канале.")
    except Exception as e:
        print(f"❌ Ошибка загрузки базы в канал: {e}")

# ================= БАЗА ДАННЫХ =================
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    upload_db_to_channel()

# ================= МАГАЗИН =================
BUSINESS_SHOP = {
    "farm": {"name": "🥕 Ферма", "price": 1000, "income": 150},
    "garden": {"name": "🍎 Сад", "price": 5000, "income": 800},
    "factory": {"name": "🏭 Завод", "price": 20000, "income": 3500}
}

# ================= КОМАНДЫ =================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    db = load_db()
    if user_id not in db:
        db[user_id] = {
            "name": message.from_user.first_name,
            "balance": 1000, "level": 1, "xp": 0, "dmg": 15, "debt": 0,
            "businesses": [], "last_daily": 0, "last_collect": 0, "last_case": 0
        }
        save_db(db)
    bot.send_message(message.chat.id, "👋 Добро пожаловать в **Синдикат**!\nПиши /menu для управления.")

@bot.message_handler(commands=['menu'])
def menu(message):
    text = (
        "📱 **Главное меню:**\n\n"
        "👤 /profile — твой профиль\n"
        "🛒 /shop — магазин бизнесов\n"
        "💼 /business — собрать доход\n"
        "🎰 /casino [ставка] — казино\n"
        "⛏ /mine — шахта\n"
        "💻 /hack — взлом (15 DMG)\n"
        "🐉 /boss — босс\n"
        "🥷 /rob — ограбить\n"
        "🚢 /smuggle — контрабанда\n"
        "💳 /loan — кредит\n"
        "💸 /paydebt — вернуть долг\n"
        "🎁 /daily — бонус\n"
        "🎲 **/case — Ежедневный кейс**\n"
        "🏆 /top — топ богачей"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['profile'])
def profile(message):
    user = load_db().get(str(message.from_user.id))
    if not user: return bot.reply_to(message, "Сначала /start")
    text = (f"👤 **Профиль**\n💰 Баланс: {user['balance']}\n"
            f"⭐ Ур: {user['level']} | ⚔️ DMG: {user['dmg']}\n"
            f"💳 Долг: {user.get('debt', 0)}")
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['shop'])
def shop(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🥕 Ферма (1000м)", callback_data="buy_biz_farm"))
    markup.add(telebot.types.InlineKeyboardButton("🍎 Сад (5000м)", callback_data="buy_biz_garden"))
    markup.add(telebot.types.InlineKeyboardButton("🏭 Завод (20000м)", callback_data="buy_biz_factory"))
    bot.send_message(message.chat.id, "🛒 **Магазин бизнесов:**", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_biz_'))
def buy_biz(call):
    biz_id = call.data.replace('buy_biz_', '')
    biz = BUSINESS_SHOP.get(biz_id)
    db = load_db()
    user = db.get(str(call.from_user.id))
    
    if biz_id in user['businesses']: return bot.answer_callback_query(call.id, "У тебя уже есть этот бизнес!")
    if user['balance'] < biz['price']: return bot.answer_callback_query(call.id, "❌ Мало денег!")
    
    user['balance'] -= biz['price']
    user['businesses'].append(biz_id)
    save_db(db)
    bot.answer_callback_query(call.id, f"✅ Куплено: {biz['name']}!")
    bot.send_message(call.message.chat.id, f"Ты купил {biz['name']}! Собирай доход через /business.")

@bot.message_handler(commands=['business'])
def collect_biz(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user.get('businesses'): return bot.reply_to(message, "У тебя нет бизнесов. Купи в /shop!")
    
    current_time = int(time.time())
    if current_time - user.get('last_collect', 0) < 3600:
        return bot.reply_to(message, "⏳ Бизнесы еще не принесли доход. Приходи через час.")
        
    total_income = sum(BUSINESS_SHOP[b]['income'] for b in user['businesses'])
    user['balance'] += total_income
    user['last_collect'] = current_time
    save_db(db)
    bot.reply_to(message, f"💸 Ты собрал доход: **+{total_income} монет!**", parse_mode='Markdown')

@bot.message_handler(commands=['mine'])
def mine(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    
    reward = random.randint(50, 250)
    user['balance'] += reward
    save_db(db)
    bot.reply_to(message, f"⛏ Ты нашел {reward} монет в шахте!")

@bot.message_handler(commands=['boss'])
def boss(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")

    reward = random.randint(100, 500)
    xp = random.randint(10, 30)
    user['balance'] += reward
    user['xp'] += xp
    
    if user['xp'] >= user['level'] * 100:
        user['level'] += 1
        user['xp'] = 0
        user['dmg'] += 5
        
    save_db(db)
    bot.reply_to(message, f"🐉 Босс повержен!\n+{reward} монет, +{xp} XP.")

@bot.message_handler(commands=['casino'])
def casino(message):
    try:
        amount = int(message.text.split()[1])
        user_id = str(message.from_user.id)
        db = load_db()
        user = db.get(user_id)
        if amount <= 0: return bot.reply_to(message, "❌ Ставка > 0.")
        if user['balance'] < amount: return bot.reply_to(message, "❌ Мало денег.")
        
        if random.choice([True, False]):
            user['balance'] += amount
            bot.reply_to(message, f"🎰 Победа! Выиграл {amount}.")
        else:
            user['balance'] -= amount
            bot.reply_to(message, f"🎰 Проигрыш! Потерял {amount}.")
        save_db(db)
    except: bot.reply_to(message, "❌ Пример: /casino 100")

@bot.message_handler(commands=['hack'])
def hack(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    if user['dmg'] < 15: return bot.reply_to(message, "❌ Нужно 15 DMG.")
    
    if random.choice([True, False]):
        user['balance'] += 500
        bot.reply_to(message, "💻 Взлом удался! +500 монет.")
    else: 
        bot.reply_to(message, "💻 Взлом провален.")
    save_db(db)

@bot.message_handler(commands=['loan'])
def loan(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if user.get('debt', 0) > 0: return bot.reply_to(message, "❌ Уже есть долг.")
    user['balance'] += 1000
    user['debt'] = 1500
    save_db(db)
    bot.reply_to(message, "💳 Взял 1000. Долг: 1500 (/paydebt).")

@bot.message_handler(commands=['paydebt'])
def paydebt(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if user.get('debt', 0) == 0: return bot.reply_to(message, "✅ Долгов нет.")
    if user['balance'] < user['debt']: return bot.reply_to(message, "❌ Мало денег.")
    user['balance'] -= user['debt']
    user['debt'] = 0
    save_db(db)
    bot.reply_to(message, "✅ Долг погашен!")

@bot.message_handler(commands=['daily'])
def daily(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if int(time.time()) - user.get('last_daily', 0) < 86400: return bot.reply_to(message, "⏳ Приходи завтра.")
    user['balance'] += 500
    user['last_daily'] = int(time.time())
    save_db(db)
    bot.reply_to(message, "🎁 Бонус +500!")

@bot.message_handler(commands=['smuggle'])
def smuggle(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    if user['balance'] < 1000: return bot.reply_to(message, "❌ Нужно 1000 монет для контрабанды.")
    
    if random.choice([True, False]):
        user['balance'] += 2000
        bot.reply_to(message, "🚢 Контрабанда удалась! +2000 монет.")
    else:
        user['balance'] -= 1000
        bot.reply_to(message, "🚔 Контрабанда провалилась! Ты потерял 1000 монет.")
    save_db(db)

@bot.message_handler(commands=['rob'])
def rob(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    
    if random.choice([True, False]):
        reward = random.randint(200, 600)
        user['balance'] += reward
        bot.reply_to(message, f"🥷 Ты успешно ограбил прохожего! +{reward} монет.")
    else:
        fine = random.randint(100, 300)
        user['balance'] -= fine
        bot.reply_to(message, f"🚓 Тебя поймали! Штраф: -{fine} монет.")
    save_db(db)

@bot.message_handler(commands=['top'])
def top(message):
    db = load_db()
    if not db: return bot.reply_to(message, "База пуста.")
    sorted_users = sorted(db.items(), key=lambda x: x[1].get('balance', 0), reverse=True)
    text = "🏆 **Топ-10 богатейших:**\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10], 1):
        name = data.get('name', f"Агент_{uid}")
        balance = data.get('balance', 0)
        text += f"{i}. {name} — {balance} 💰\n"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['case'])
def daily_case(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    
    current_time = int(time.time())
    last_case = user.get('last_case', 0)
    
    if current_time - last_case < 86400:
        time_left = 86400 - (current_time - last_case)
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        return bot.reply_to(message, f"⏳ Кейс еще не восстановился. Приходи через {hours} ч. {minutes} мин.")
    
    roll = random.randint(1, 100)
    
    if roll <= 50:
        reward = random.randint(200, 500)
        user['balance'] += reward
        text = f"📦 Ты открыл кейс и нашел **{reward} монет**!"
    elif roll <= 80:
        reward = random.randint(1000, 2000)
        user['balance'] += reward
        text = f"🎁 Ого! В кейсе был **крупный куш: {reward} монет**!"
    elif roll <= 95:
        user['dmg'] += 2
        text = "⚔️ Невероятная удача! Ты нашел в кейсе **+2 DMG**!"
    else:
        reward = 10000
        user['balance'] += reward
        text = f"🔥 **ДЖЕКПОТ!!!** Ты сорвал банк: **{reward} монет**! 🔥"
    
    user['last_case'] = current_time
    save_db(db)
    bot.reply_to(message, text, parse_mode='Markdown')

# ================= ЗАПУСК =================
def run_bot():
    download_db_from_channel() # Скачиваем базу при старте
    bot.polling(non_stop=True)

if __name__ == '__main__':
    # 1. Запускаем бота в фоне
    t = threading.Thread(target=run_bot)
    t.start()
    
    # 2. Запускаем Flask, чтобы Render видел открытый порт
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
