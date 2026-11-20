import telebot
import json
import os
import random
import time
from datetime import datetime

# ================= НАСТРОЙКИ =================
TOKEN = '9291373316:AAEjyaBDwtP15QihndBnkeCXjUwR6b77DA0'  # ВСТАВЬ СВОЙ ТОКЕН
bot = telebot.TeleBot(TOKEN)
DB_FILE = 'users.json'

# ================= БАЗА ДАННЫХ =================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)

# ================= МАГАЗИН =================
FOOD_SHOP = {
    "bread": {"name": "🍞 Хлеб", "price": 200, "energy": 20},
    "cake": {"name": "🧁 Пирожное", "price": 500, "energy": 50},
    "tort": {"name": "🎂 Торт", "price": 1000, "energy": 100}
}

# Бизнесы (вернул их сюда)
BUSINESS_SHOP = {
    "farm": {"name": "🥕 Ферма", "price": 1000, "income": 150},
    "garden": {"name": "🍎 Сад", "price": 5000, "income": 800},
    "factory": {"name": "🏭 Завод", "price": 20000, "income": 3500}
}

# ================= КОНТРАКТ =================
CONTRACT_REWARDS = {
    1: {"free": 500, "premium": 1000}, 2: {"free": 1000, "premium": 2000},
    3: {"free": 1500, "premium": 3000}, 4: {"free": 2000, "premium": 5000},
    5: {"free": 3000, "premium": 8000}, 6: {"free": 4000, "premium": 10000},
    7: {"free": 5000, "premium": 15000}, 8: {"free": 7000, "premium": 20000},
    9: {"free": 10000, "premium": 30000}, 10: {"free": 15000, "premium": 50000}
}

def add_contract_xp(user, amount):
    user['contract_xp'] = user.get('contract_xp', 0) + amount
    if user['contract_xp'] >= 1000:
        user['contract_xp'] -= 1000
        user['contract_level'] = user.get('contract_level', 1) + 1
        if user['contract_level'] > 10:
            user['contract_level'] = 10
            user['contract_xp'] = 0

# ================= КОМАНДЫ =================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    db = load_db()
    if user_id not in db:
        db[user_id] = {
            "balance": 1000, "energy": 100, "max_energy": 100,
            "level": 1, "xp": 0, "dmg": 15, "debt": 0,
            "businesses": [], "last_daily": 0, "last_collect": 0,
            "contract_level": 1, "contract_xp": 0, "is_premium": False
        }
        save_db(db)
    bot.send_message(message.chat.id, "👋 Добро пожаловать в **Синдикат**!\nПиши /menu для управления или /profile для просмотра stats.")

@bot.message_handler(commands=['profile'])
def profile(message):
    user = load_db().get(str(message.from_user.id))
    if not user: return bot.reply_to(message, "Сначала /start")
    prem = "💎" if user.get('is_premium') else "🆓"
    text = (f"👤 **Профиль**\n💰 Баланс: {user['balance']}\n"
            f"⚡ Энергия: {user.get('energy', 100)}/{user.get('max_energy', 100)}\n"
            f"⭐ Ур: {user['level']} | ⚔️ DMG: {user['dmg']}\n"
            f"💳 Долг: {user.get('debt', 0)}\n"
            f"🎟 Контракт: {prem} Ур. {user.get('contract_level', 1)}")
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['mine'])
def mine(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    if user.get('energy', 0) < 10: return bot.reply_to(message, "⚡ Энергия кончилась! Купи еду в /shop.")
    
    user['energy'] -= 10
    reward = random.randint(50, 250)
    user['balance'] += reward
    add_contract_xp(user, 50)
    save_db(db)
    bot.reply_to(message, f"⛏ Найдено {reward} монет!\n+50 XP Контракта.\n⚡ Энергия: {user['energy']}")

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
        
    add_contract_xp(user, 100)
    save_db(db)
    bot.reply_to(message, f"🐉 Босс повержен!\n+{reward} монет, +{xp} XP, +100 XP Контракта.")

@bot.message_handler(commands=['shop'])
def shop(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Еда
    markup.add(telebot.types.InlineKeyboardButton("🍞 Хлеб (200м)", callback_data="buy_food_bread"))
    markup.add(telebot.types.InlineKeyboardButton("🧁 Пирожное (500м)", callback_data="buy_food_cake"))
    # Бизнесы
    markup.add(telebot.types.InlineKeyboardButton("🥕 Ферма (1000м)", callback_data="buy_biz_farm"))
    markup.add(telebot.types.InlineKeyboardButton("🍎 Сад (5000м)", callback_data="buy_biz_garden"))
    markup.add(telebot.types.InlineKeyboardButton("🏭 Завод (20000м)", callback_data="buy_biz_factory"))
    
    bot.send_message(message.chat.id, "🛒 **Магазин (Еда и Бизнесы):**", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_food_'))
def buy_food(call):
    item_id = call.data.replace('buy_food_', '')
    item = FOOD_SHOP.get(item_id)
    db = load_db()
    user = db.get(str(call.from_user.id))
    
    if user['balance'] < item['price']: return bot.answer_callback_query(call.id, "❌ Мало денег!")
    user['balance'] -= item['price']
    user['energy'] = min(user['max_energy'], user['energy'] + item['energy'])
    save_db(db)
    bot.answer_callback_query(call.id, f"✅ Съедено: {item['name']}!")
    bot.send_message(call.message.chat.id, f"Энергия: {user['energy']}/{user['max_energy']}")

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
    if not user['businesses']: return bot.reply_to(message, "У тебя нет бизнесов. Купи в /shop!")
    
    current_time = int(time.time())
    if current_time - user.get('last_collect', 0) < 3600:
        return bot.reply_to(message, "⏳ Бизнесы еще не принесли доход. Приходи через час.")
        
    total_income = sum(BUSINESS_SHOP[b]['income'] for b in user['businesses'])
    user['balance'] += total_income
    user['last_collect'] = current_time
    save_db(db)
    bot.reply_to(message, f"💸 Ты собрал доход: **+{total_income} монет!**", parse_mode='Markdown')

@bot.message_handler(commands=['casino'])
def casino(message):
    try:
        amount = int(message.text.split()[1])
        user_id = str(message.from_user.id)
        db = load_db()
        user = db.get(user_id)
        if user['balance'] < amount: return bot.reply_to(message, "❌ Мало денег.")
        
        if random.choice([True, False]):
            user['balance'] += amount
            bot.reply_to(message, f"🎰 Победа! Выиграл {amount}.")
        else:
            user['balance'] -= amount
            bot.reply_to(message, f"🎰 Проигрыш! Потерял {amount}.")
        add_contract_xp(user, 30)
        save_db(db)
    except: bot.reply_to(message, "❌ Пример: /casino 100")

@bot.message_handler(commands=['hack'])
def hack(message):
    user = load_db().get(str(message.from_user.id))
    if user['dmg'] < 15: return bot.reply_to(message, "❌ Нужно 15 DMG.")
    if random.choice([True, False]):
        user['balance'] += 500
        bot.reply_to(message, "💻 Взлом удался! +500 монет.")
    else: bot.reply_to(message, "💻 Взлом провален.")
    save_db(load_db())

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

# --- КОНТРАКТ ---
@bot.message_handler(commands=['contract'])
def show_contract(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    
    level = user.get('contract_level', 1)
    xp = user.get('contract_xp', 0)
    is_prem = user.get('is_premium', False)
    bar = "█" * int((xp / 1000) * 10) + "░" * (10 - int((xp / 1000) * 10))
    
    text = f"🎟 **Контракт:** {'💎 ПРЕМИУМ' if is_prem else '🆓 БЕСПЛАТНЫЙ'}\n"
    text += f"Уровень: {level}/10\nПрогресс: `{bar}` {xp}/1000\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    if not is_prem: markup.add(telebot.types.InlineKeyboardButton("💎 Купить Премиум", callback_data="buy_premium"))
    markup.add(telebot.types.InlineKeyboardButton("🎁 Забрать награду", callback_data="claim_reward"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def buy_premium(call):
    db = load_db()
    user = db.get(str(call.from_user.id))
    user['is_premium'] = True
    save_db(db)
    bot.answer_callback_query(call.id, "💎 Премиум активирован!")
    bot.send_message(call.message.chat.id, "Ты купил Премиум Контракт! Награды удвоены.")

@bot.callback_query_handler(func=lambda call: call.data == "claim_reward")
def claim_reward(call):
    db = load_db()
    user = db.get(str(call.from_user.id))
    level = user.get('contract_level', 1)
    if level > 10: return bot.answer_callback_query(call.id, "Максимальный уровень!")
    
    reward = CONTRACT_REWARDS[level]['premium'] if user.get('is_premium') else CONTRACT_REWARDS[level]['free']
    user['balance'] += reward
    user['contract_level'] += 1
    user['contract_xp'] = 0
    save_db(db)
    bot.answer_callback_query(call.id, f"✅ Получено {reward}!")
    bot.send_message(call.message.chat.id, f"🎁 Награда: {reward} монет!\nНовый уровень: {user['contract_level']}")

print("Бот запущен...")
bot.polling(non_stop=True)