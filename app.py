import telebot
import json
import os
import random
import time
from datetime import datetime

# ================= НАСТРОЙКИ =================
TOKEN = '9002014471:AAE_AOkZk6e8P8GRw1EhwsX3tfYIskE5m-I'
bot = telebot.TeleBot(TOKEN)
DB_FILE = 'users.json'

# ================= БАЗА ДАННЫХ =================
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ База данных повреждена, создаю новую...")
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= УВЕДОМЛЕНИЯ =================
def check_notify(chat_id, user):
    """Проверяет, доступна ли награда, и шлет уведомление"""
    # Если XP больше 1000, но награда еще не забрана (уровень не поднялся)
    if user.get('contract_xp', 0) >= 1000:
        text = (
            "🔔 **Внимание, Агент!**\n\n"
            "Ты накопил достаточно опыта. У тебя доступна награда в **Контракте Синдиката**!\n"
            "Скорее забери её: /contract"
        )
        bot.send_message(chat_id, text, parse_mode='Markdown')

# ================= МАГАЗИН =================
FOOD_SHOP = {
    "bread": {"name": "🍞 Хлеб", "price": 200, "energy": 20},
    "cake": {"name": "🧁 Пирожное", "price": 500, "energy": 50},
    "tort": {"name": "🎂 Торт", "price": 1000, "energy": 100}
}

BUSINESS_SHOP = {
    "farm": {"name": "🥕 Ферма", "price": 1000, "income": 150},
    "garden": {"name": "🍎 Сад", "price": 5000, "income": 800},
    "factory": {"name": "🏭 Завод", "price": 20000, "income": 3500}
}

# ================= КОНТРАКТ =================
PREMIUM_PRICE = 5000

CONTRACT_REWARDS = {
    1: {"free": 500, "premium": 1000}, 2: {"free": 1000, "premium": 2000},
    3: {"free": 1500, "premium": 3000}, 4: {"free": 2000, "premium": 5000},
    5: {"free": 3000, "premium": 8000}, 6: {"free": 4000, "premium": 10000},
    7: {"free": 5000, "premium": 15000}, 8: {"free": 7000, "premium": 20000},
    9: {"free": 10000, "premium": 30000}, 10: {"free": 15000, "premium": 50000}
}

def add_contract_xp(user, amount):
    user['contract_xp'] = user.get('contract_xp', 0) + amount
    # Мы НЕ повышаем уровень автоматически, а даем XP. Уровень повышается только при нажатии "Забрать награду"

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
    bot.send_message(message.chat.id, "👋 Добро пожаловать в **Синдикат**!\nПиши /profile для просмотра stats.")

@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = str(message.from_user.id)
    db = load_db()
    user = db.get(user_id)
    if not user: return bot.reply_to(message, "Сначала /start")
    
    # Проверка наград
    check_notify(message.chat.id, user)
    
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
    add_contract_xp(user, 50) # Добавляем XP
    save_db(db)
    
    bot.reply_to(message, f"⛏ Найдено {reward} монет!\n+50 XP Контракта.\n⚡ Энергия: {user['energy']}")
    
    # Проверка наград
    check_notify(message.chat.id, user)

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
        
    add_contract_xp(user, 100) # Добавляем XP
    save_db(db)
    
    bot.reply_to(message, f"🐉 Босс повержен!\n+{reward} монет, +{xp} XP, +100 XP Контракта.")
    
    # Проверка наград
    check_notify(message.chat.id, user)

@bot.message_handler(commands=['shop'])
def shop(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🍞 Хлеб (200м)", callback_data="buy_food_bread"))
    markup.add(telebot.types.InlineKeyboardButton("🧁 Пирожное (500м)", callback_data="buy_food_cake"))
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
    if not user.get('businesses'): return bot.reply_to(message, "У тебя нет бизнесов. Купи в /shop!")
    
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
    add_contract_xp(user, 50)
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
    
    # Прогресс-бар (максимум 1000 XP)
    bar_progress = min(10, int((xp / 1000) * 10))
    bar = "█" * bar_progress + "░" * (10 - bar_progress)
    
    text = f"🎟 **Контракт:** {'💎 ПРЕМИУМ' if is_prem else '🆓 БЕСПЛАТНЫЙ'}\n"
    text += f"Уровень: {level}/10\nПрогресс: `{bar}` {xp}/1000\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    if not is_prem: 
        markup.add(telebot.types.InlineKeyboardButton(f"💎 Купить Премиум ({PREMIUM_PRICE} монет)", callback_data="buy_premium_coins"))
    markup.add(telebot.types.InlineKeyboardButton("🎁 Забрать награду", callback_data="claim_reward"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "buy_premium_coins")
def buy_premium_coins(call):
    db = load_db()
    user = db.get(str(call.from_user.id))
    
    if user.get('is_premium'):
        return bot.answer_callback_query(call.id, "У тебя уже есть Премиум!")
        
    if user['balance'] < PREMIUM_PRICE:
        return bot.answer_callback_query(call.id, f"❌ Не хватает монет! Нужно {PREMIUM_PRICE}.", show_alert=True)
        
    user['balance'] -= PREMIUM_PRICE
    user['is_premium'] = True
    save_db(db)
    
    bot.answer_callback_query(call.id, "💎 Премиум куплен!")
    bot.send_message(call.message.chat.id, f"💎 **Поздравляю!** Ты купил Премиум Контракт за {PREMIUM_PRICE} монет.\nТеперь твои награды удвоены!")

@bot.callback_query_handler(func=lambda call: call.data == "claim_reward")
def claim_reward(call):
    db = load_db()
    user = db.get(str(call.from_user.id))
    level = user.get('contract_level', 1)
    xp = user.get('contract_xp', 0)
    
    if level > 10: 
        return bot.answer_callback_query(call.id, "Максимальный уровень!")
    if xp < 1000:
        return bot.answer_callback_query(call.id, "❌ Ты еще не накопил 1000 XP!", show_alert=True)
    
    reward = CONTRACT_REWARDS[level]['premium'] if user.get('is_premium') else CONTRACT_REWARDS[level]['free']
    user['balance'] += reward
    user['contract_level'] += 1
    user['contract_xp'] = 0 # Сбрасываем XP
    save_db(db)
    
    bot.answer_callback_query(call.id, f"✅ Получено {reward}!")
    bot.send_message(call.message.chat.id, f"🎁 Награда: {reward} монет!\nНовый уровень: {user['contract_level']}")

print("Бот запущен...")
bot.polling(non_stop=True)
