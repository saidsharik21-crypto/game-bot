import logging
import os
import random
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ADMIN_ID = 8512105562

logging.basicConfig(level=logging.INFO)
client = Groq(api_key=GROQ_API_KEY)

players = {}
clans = {}

def get_player(user_id, username="Игрок"):
    if user_id not in players:
        players[user_id] = {
            "id": user_id,
            "username": username,
            "balance": 1000,
            "bank": 0,
            "job": None,
            "car": None,
            "house": None,
            "spouse_id": None,
            "clan": None,
            "rating": 0
        }
    return players[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_player(user.id, user.first_name)
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"🆔 Твой ID: {user.id}\n\n"
        "🎮 Добро пожаловать в игру!\n\n"
        "Команды (просто напиши):\n"
        "профиль — твой профиль\n"
        "работа — работать\n"
        "казино — казино\n"
        "банк — банк\n"
        "магазин — магазин\n"
        "топ — рейтинг игроков\n"
        "клан — меню кланов\n"
        "жениться [ID] — свадьба\n"
        "развод — развестись"
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    p = get_player(user.id, user.first_name)
    spouse = players.get(p["spouse_id"])
    spouse_name = spouse["username"] if spouse else "Нет"
    clan_name = p["clan"] if p["clan"] else "Нет"
    await update.message.reply_text(
        f"👤 Профиль {user.first_name}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💰 Баланс: {p['balance']}$\n"
        f"🏦 В банке: {p['bank']}$\n"
        f"⭐ Рейтинг: {p['rating']}\n"
        f"💼 Работа: {p['job'] or 'Нет'}\n"
        f"🚗 Машина: {p['car'] or 'Нет'}\n"
        f"🏠 Дом: {p['house'] or 'Нет'}\n"
        f"💍 Супруг: {spouse_name}\n"
        f"⚔️ Клан: {clan_name}"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not players:
        await update.message.reply_text("Пока нет игроков!")
        return
    sorted_players = sorted(players.values(), key=lambda x: x["rating"], reverse=True)[:10]
    text = "🏆 Топ игроков:\n\n"
    for i, p in enumerate(sorted_players, 1):
        text += f"{i}. {p['username']} — ⭐{p['rating']} | 💰{p['balance']}$\n"
    await update.message.reply_text(text)

async def work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👨‍💻 Программист (+500$)", callback_data="work_programmer")],
        [InlineKeyboardButton("🚕 Таксист (+200$)", callback_data="work_driver")],
        [InlineKeyboardButton("🍕 Курьер (+150$)", callback_data="work_courier")],
    ]
    await update.message.reply_text("💼 Выбери работу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎰 Слоты (50$)", callback_data="casino_slots")],
        [InlineKeyboardButton("🎲 Рулетка (100$)", callback_data="casino_roulette")],
        [InlineKeyboardButton("🃏 Блэкджек (200$)", callback_data="casino_blackjack")],
    ]
    await update.message.reply_text("🎰 Казино:", reply_markup=InlineKeyboardMarkup(keyboard))

async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💵 Положить 100$", callback_data="bank_deposit_100")],
        [InlineKeyboardButton("💵 Положить 500$", callback_data="bank_deposit_500")],
        [InlineKeyboardButton("💸 Снять всё", callback_data="bank_withdraw")],
    ]
    await update.message.reply_text("🏦 Банк:", reply_markup=InlineKeyboardMarkup(keyboard))

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚗 Жигули (1000$)", callback_data="buy_car_lada")],
        [InlineKeyboardButton("🚗 BMW (5000$)", callback_data="buy_car_bmw")],
        [InlineKeyboardButton("🚗 Lamborghini (20000$)", callback_data="buy_car_lambo")],
        [InlineKeyboardButton("🏠 Квартира (3000$)", callback_data="buy_house_apartment")],
        [InlineKeyboardButton("🏠 Дом (10000$)", callback_data="buy_house_mansion")],
        [InlineKeyboardButton("🏰 Вилла (50000$)", callback_data="buy_house_villa")],
    ]
    await update.message.reply_text("🛒 Магазин:", reply_markup=InlineKeyboardMarkup(keyboard))

async def clan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚔️ Создать клан", callback_data="clan_create")],
        [InlineKeyboardButton("🔍 Вступить в клан", callback_data="clan_join")],
        [InlineKeyboardButton("🏆 Топ кланов", callback_data="clan_top")],
        [InlineKeyboardButton("📊 Мой клан", callback_data="clan_info")],
    ]
    await update.message.reply_text("⚔️ Меню кланов:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.lower().strip()
    p = get_player(user.id, user.first_name)

    # Команды администратора
    if user.id == ADMIN_ID and text.startswith("выдать"):
        parts = text.split()
        if len(parts) == 3:
            try:
                target_id = int(parts[1])
                amount = int(parts[2])
                target = players.get(target_id)
                if target:
                    target["balance"] += amount
                    await update.message.reply_text(f"✅ Выдал {amount}$ игроку {target['username']}!")
                else:
                    await update.message.reply_text("❌ Игрок не найден!")
            except:
                await update.message.reply_text("❌ Формат: выдать [ID] [сумма]")
        return

    if text == "профиль":
        await profile(update, context)
    elif text == "работа":
        await work(update, context)
    elif text == "казино":
        await casino(update, context)
    elif text == "банк":
        await bank(update, context)
    elif text == "магазин":
        await shop(update, context)
    elif text == "топ":
        await top(update, context)
    elif text == "клан":
        await clan_menu(update, context)
    elif text == "развод":
        if not p["spouse_id"]:
            await update.message.reply_text("❌ Ты не в браке!")
            return
        spouse = players.get(p["spouse_id"])
        if spouse:
            spouse["spouse_id"] = None
        p["spouse_id"] = None
        await update.message.reply_text("💔 Ты развёлся!")
    elif text.startswith("жениться"):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Формат: жениться [ID]")
            return
        if p["spouse_id"]:
            await update.message.reply_text("❌ Ты уже в браке! Напиши: развод")
            return
        try:
            target_id = int(parts[1])
        except:
            await update.message.reply_text("❌ Неверный ID!")
            return
        if target_id == user.id:
            await update.message.reply_text("❌ Нельзя жениться на себе!")
            return
        target = players.get(target_id)
        if not target:
            await update.message.reply_text("❌ Игрок не найден!")
            return
        if target["spouse_id"]:
            await update.message.reply_text("❌ Этот игрок уже в браке!")
            return
        p["spouse_id"] = target_id
        target["spouse_id"] = user.id
        await update.message.reply_text(f"💍 Поздравляем! Ты теперь в браке с {target['username']}!")
    elif text.startswith("создатьклан"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("❌ Формат: создатьклан [название]")
            return
        if p["clan"]:
            await update.message.reply_text("❌ Ты уже в клане!")
            return
        name = parts[1]
        clan_id = str(len(clans) + 1)
        clans[clan_id] = {
            "id": clan_id,
            "name": name,
            "leader": user.id,
            "members": [user.id],
            "treasury": 0,
            "rating": 0
        }
        p["clan"] = clan_id
        await update.message.reply_text(f"⚔️ Клан '{name}' создан!\n🆔 ID клана: {clan_id}")
    elif text.startswith("вступитьклан"):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Формат: вступитьклан [ID]")
            return
        if p["clan"]:
            await update.message.reply_text("❌ Ты уже в клане!")
            return
        clan_id = parts[1]
        if clan_id not in clans:
            await update.message.reply_text("❌ Клан не найден!")
            return
        clans[clan_id]["members"].append(user.id)
        p["clan"] = clan_id
        await update.message.reply_text(f"✅ Вступил в клан '{clans[clan_id]['name']}'!")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.first_name
    p = get_player(user_id, username)
    data = query.data

    if data == "work_programmer":
        p["balance"] += 500
        p["rating"] += 5
        p["job"] = "Программист"
        await query.edit_message_text("👨‍💻 Заработал 500$! +5 рейтинга")
    elif data == "work_driver":
        p["balance"] += 200
        p["rating"] += 2
        p["job"] = "Таксист"
        await query.edit_message_text("🚕 Заработал 200$! +2 рейтинга")
    elif data == "work_courier":
        p["balance"] += 150
        p["rating"] += 1
        p["job"] = "Курьер"
        await query.edit_message_text("🍕 Заработал 150$! +1 рейтинга")
    elif data == "casino_slots":
        bet = 50
        if p["balance"] < bet:
            await query.edit_message_text("❌ Недостаточно денег!")
            return
        symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣"]
        s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
        if s1 == s2 == s3:
            win = bet * 5
            p["balance"] += win
            p["rating"] += 10
            await query.edit_message_text(f"🎰 {s1}{s2}{s3}\n🎉 ДЖЕКПОТ! Выиграл {win}$!")
        elif s1 == s2 or s2 == s3:
            win = bet
            p["balance"] += win
            await query.edit_message_text(f"🎰 {s1}{s2}{s3}\n✅ Выиграл {win}$!")
        else:
            p["balance"] -= bet
            await query.edit_message_text(f"🎰 {s1}{s2}{s3}\n❌ Проиграл {bet}$!")
    elif data == "casino_roulette":
        bet = 100
        if p["balance"] < bet:
            await query.edit_message_text("❌ Недостаточно денег!")
            return
        number = random.randint(0, 36)
        color = "🔴" if number % 2 == 0 else "⚫"
        if random.random() > 0.5:
            p["balance"] += bet
            p["rating"] += 3
            await query.edit_message_text(f"🎲 Рулетка: {color} {number}\n✅ Выиграл {bet}$!")
        else:
            p["balance"] -= bet
            await query.edit_message_text(f"🎲 Рулетка: {color} {number}\n❌ Проиграл {bet}$!")
    elif data == "casino_blackjack":
        bet = 200
        if p["balance"] < bet:
            await query.edit_message_text("❌ Недостаточно денег!")
            return
        player_score = random.randint(15, 21)
        dealer_score = random.randint(15, 21)
        if player_score > dealer_score or dealer_score > 21:
            p["balance"] += bet
            p["rating"] += 5
            await query.edit_message_text(f"🃏 Блэкджек!\nТы: {player_score} | Дилер: {dealer_score}\n✅ Выиграл {bet}$!")
        else:
            p["balance"] -= bet
            await query.edit_message_text(f"🃏 Блэкджек!\nТы: {player_score} | Дилер: {dealer_score}\n❌ Проиграл {bet}$!")
    elif data == "bank_deposit_100":
        if p["balance"] >= 100:
            p["balance"] -= 100
            p["bank"] += 100
            await query.edit_message_text("🏦 Положил 100$ в банк!")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "bank_deposit_500":
        if p["balance"] >= 500:
            p["balance"] -= 500
            p["bank"] += 500
            await query.edit_message_text("🏦 Положил 500$ в банк!")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "bank_withdraw":
        amount = p["bank"]
        p["balance"] += amount
        p["bank"] = 0
        await query.edit_message_text(f"💸 Снял {amount}$ из банка!")
    elif data == "buy_car_lada":
        if p["balance"] >= 1000:
            p["balance"] -= 1000
            p["car"] = "Жигули"
            p["rating"] += 5
            await query.edit_message_text("🚗 Купил Жигули! +5 рейтинга")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "buy_car_bmw":
        if p["balance"] >= 5000:
            p["balance"] -= 5000
            p["car"] = "BMW"
            p["rating"] += 20
            await query.edit_message_text("🚗 Купил BMW! +20 рейтинга")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "buy_car_lambo":
        if p["balance"] >= 20000:
            p["balance"] -= 20000
            p["car"] = "Lamborghini"
            p["rating"] += 50
            await query.edit_message_text("🚗 Купил Lamborghini! +50 рейтинга")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "buy_house_apartment":
        if p["balance"] >= 3000:
            p["balance"] -= 3000
            p["house"] = "Квартира"
            p["rating"] += 10
            await query.edit_message_text("🏠 Купил квартиру! +10 рейтинга")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "buy_house_mansion":
        if p["balance"] >= 10000:
            p["balance"] -= 10000
            p["house"] = "Дом"
            p["rating"] += 30
            await query.edit_message_text("🏠 Купил дом! +30 рейтинга")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "buy_house_villa":
        if p["balance"] >= 50000:
            p["balance"] -= 50000
            p["house"] = "Вилла"
            p["rating"] += 100
            await query.edit_message_text("🏰 Купил виллу! +100 рейтинга")
        else:
            await query.edit_message_text("❌ Недостаточно денег!")
    elif data == "clan_create":
        await query.edit_message_text("Напиши: создатьклан [название]")
    elif data == "clan_join":
        await query.edit_message_text("Напиши: вступитьклан [ID клана]")
    elif data == "clan_top":
        if not clans:
            await query.edit_message_text("Кланов пока нет!")
            return
        sorted_clans = sorted(clans.values(), key=lambda x: x["rating"], reverse=True)[:10]
        text = "🏆 Топ кланов:\n\n"
        for i, c in enumerate(sorted_clans, 1):
            text += f"{i}. [{c['id']}] {c['name']} — ⭐{c['rating']} | 💰{c['treasury']}$\n"
        await query.edit_message_text(text)
    elif data == "clan_info":
        clan_id = p["clan"]
        if not clan_id or clan_id not in clans:
            await query.edit_message_text("Ты не в клане!")
            return
        c = clans[clan_id]
        await query.edit_message_text(
            f"⚔️ Клан: {c['name']}\n"
            f"🆔 ID: {c['id']}\n"
            f"⭐ Рейтинг: {c['rating']}\n"
            f"💰 Казна: {c['treasury']}$\n"
            f"👥 Участников: {len(c['members'])}"
        )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Игровой бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
