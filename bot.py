import logging
import os
import random
import time
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = 8512105562
DATA_FILE = "data.json"

logging.basicConfig(level=logging.INFO)

# Глобальные данные
players = {}
market = []
promocodes = {}
vip_limits = {"bronze": 50000, "silver": 200000, "gold": 500000}

# ========== СОХРАНЕНИЕ ==========
def save():
    with open(DATA_FILE, "w") as f:
        json.dump({"players": players, "market": market, "promocodes": promocodes}, f)

def load():
    global players, market, promocodes
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
            players.update(data.get("players", {}))
            market.extend(data.get("market", []))
            promocodes.update(data.get("promocodes", {}))

# ========== ИГРОКИ ==========
def get_p(uid):
    uid = str(uid)
    if uid not in players:
        players[uid] = {
            "gid": uid,
            "name": "Игрок",
            "bal": 1000,
            "bank": 0,
            "cases": 0,
            "rare": 0,
            "epic": 0,
            "business": 0,
            "vip": None,
            "banned": False,
            "muted_until": 0,
            "last_bonus": 0,
            "last_duel": 0,
            "lover": None,
            "proposal": None,
            "love": 0,
            "rating": 0,
            "clan": None,
            "vip_given": 0,
            "vip_reset": 0,
            "deposit": 0,
            "deposit_amount": 0,
            "deposit_time": 0,
        }
    return players[uid]

def find_gid(gid):
    return players.get(str(gid))

# ========== МЕНЮ ==========
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Баланс", callback_data="bal"),
         InlineKeyboardButton("🎁 Кейсы", callback_data="cases")],
        [InlineKeyboardButton("🏦 Банк", callback_data="bank_menu"),
         InlineKeyboardButton("💼 Работа", callback_data="work_menu")],
        [InlineKeyboardButton("🛒 Магазин", callback_data="shop_menu"),
         InlineKeyboardButton("🎰 Казино", callback_data="casino_menu")],
        [InlineKeyboardButton("⚔️ Клан", callback_data="clan_menu"),
         InlineKeyboardButton("🏆 Топ", callback_data="top_menu")],
    ])

# ========== СТАРТ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    p = get_p(user.id)
    p["name"] = user.first_name
    save()
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"🆔 Твой ID: {user.id}\n\n"
        "🎮 Добро пожаловать!\n\n"
        "Команды:\n"
        "баланс — баланс\n"
        "бонус — ежедневный бонус\n"
        "казино [сумма] — казино\n"
        "дуэль — дуэль (ответь на сообщение)\n"
        "предложение — предложить отношения\n"
        "принять — принять предложение\n"
        "купитькейс — купить кейс\n"
        "открытькейс — открыть кейс\n"
        "открытьrare — открыть rare\n"
        "открытьepic — открыть epic\n"
        "купитьбизнес — купить бизнес\n"
        "бизнес — получить доход\n"
        "депозит [сумма] — вложить деньги\n"
        "снятьдепозит — снять депозит\n"
        "продать [цена] — выставить лот\n"
        "купить [номер] — купить лот\n"
        "рынок — посмотреть рынок\n"
        "промо [код] — активировать промокод\n"
        "топ — рейтинг игроков\n",
        reply_markup=menu()
    )

# ========== ДЕПОЗИТ ==========
def deposit_system(p, t):
    if t.startswith("депозит"):
        parts = t.split()
        if len(parts) < 2:
            return "Формат: депозит [сумма]"
        try:
            amount = int(parts[1])
        except:
            return "❌ Неверная сумма"
        if p["deposit"] > 0:
            return "❌ У тебя уже есть депозит. Сначала сними его."
        fee = int(amount * 0.015)
        total = amount - fee
        if p["bal"] < amount:
            return "❌ Недостаточно денег"
        p["bal"] -= amount
        p["deposit"] = total
        p["deposit_amount"] = total
        p["deposit_time"] = time.time()
        save()
        return f"🏦 Депозит открыт!\nВложено: {amount}$\nКомиссия: {fee}$\nНа депозите: {total}$\n+10% в день"

    if t == "снятьдепозит":
        if p["deposit"] <= 0:
            return "❌ Нет депозита"
        days = (time.time() - p["deposit_time"]) / 86400
        earned = int(p["deposit_amount"] * 0.10 * days)
        total = p["deposit"] + earned
        fee = int(total * 0.025)
        payout = total - fee
        p["bal"] += payout
        p["deposit"] = 0
        p["deposit_amount"] = 0
        p["deposit_time"] = 0
        save()
        return f"💸 Депозит снят!\nНакоплено: +{earned}$\nКомиссия: {fee}$\nВыплачено: {payout}$"

    if t == "депозит":
        if p["deposit"] <= 0:
            return "❌ Нет активного депозита"
        days = (time.time() - p["deposit_time"]) / 86400
        earned = int(p["deposit_amount"] * 0.10 * days)
        return f"🏦 Депозит: {p['deposit']}$\nНакоплено: +{earned}$"

# ========== КЕЙСЫ ==========
def case_system(p, t):
    if t == "купитькейс":
        if p["bal"] >= 1000:
            p["bal"] -= 1000
            p["cases"] += 1
            save()
            return "🎁 Кейс куплен!"
        return "❌ Нужно 1000$"

    if t == "открытькейс":
        if p["cases"] <= 0:
            return "❌ Нет кейсов"
        p["cases"] -= 1
        r = random.random()
        if r < 0.5:
            win = random.randint(500, 2000)
            p["bal"] += win
            save()
            return f"💰 +{win}$"
        elif r < 0.8:
            win = random.randint(2000, 5000)
            p["bal"] += win
            save()
            return f"💎 +{win}$"
        elif r < 0.95:
            p["rare"] += 1
            save()
            return "🔵 Rare кейс!"
        else:
            p["epic"] += 1
            save()
            return "🟣 EPIC кейс!"

    if t == "открытьrare":
        if p["rare"] <= 0:
            return "❌ Нет rare кейсов"
        p["rare"] -= 1
        win = random.randint(5000, 15000)
        p["bal"] += win
        save()
        return f"🔵 +{win}$"

    if t == "открытьepic":
        if p["epic"] <= 0:
            return "❌ Нет epic кейсов"
        p["epic"] -= 1
        win = random.randint(20000, 50000)
        p["bal"] += win
        save()
        return f"🟣 +{win}$"

# ========== ЭКОНОМИКА ==========
def economy(p, t):
    if t == "бонус":
        if time.time() - p["last_bonus"] > 86400:
            bonus = random.randint(1000, 10000)
            p["bal"] += bonus
            p["last_bonus"] = time.time()
            save()
            return f"🎁 Бонус: +{bonus}$"
        left = 86400 - (time.time() - p["last_bonus"])
        h = int(left // 3600)
        m = int((left % 3600) // 60)
        return f"⏰ Бонус через {h}ч {m}м"

    if t.startswith("казино"):
        parts = t.split()
        if len(parts) < 2:
            return "Формат: казино [сумма]"
        try:
            bet = int(parts[1])
        except:
            return "❌ Неверная сумма"
        if p["bal"] < bet:
            return "❌ Недостаточно денег"
        if random.random() < 0.5:
            p["bal"] += bet
            p["rating"] += 3
            save()
            return f"🎰 Выиграл +{bet}$!"
        else:
            p["bal"] -= bet
            save()
            return f"🎰 Проиграл -{bet}$"

    if t == "купитьбизнес":
        if p["bal"] >= 10000000:
            p["bal"] -= 10000000
            p["business"] += 1
            p["rating"] += 100
            save()
            return f"🏢 Бизнес куплен! Всего: {p['business']}"
        return f"❌ Нужно 10,000,000$. У тебя {p['bal']}$"

    if t == "бизнес":
        if p["business"] <= 0:
            return "❌ Нет бизнеса"
        income = p["business"] * 2000
        p["bal"] += income
        save()
        return f"🏢 Доход: +{income}$"

# ========== ПРОМОКОДЫ ==========
def promo_system(p, t):
    args = t.split()
    if not args:
        return None

    if args[0] == "создатьпромо":
        if p["gid"] != str(ADMIN_ID):
            return "❌ Нет прав"
        if len(args) < 3:
            return "Формат: создатьпромо название сумма"
        name = args[1]
        try:
            amount = int(args[2])
        except:
            return "❌ Неверная сумма"
        promocodes[name] = {"amount": amount, "used": []}
        save()
        return f"✅ Промокод {name} создан на {amount}$"

    if args[0] == "промо":
        if len(args) < 2:
            return "Формат: промо [код]"
        name = args[1]
        if name not in promocodes:
            return "❌ Нет такого промокода"
        if p["gid"] in promocodes[name]["used"]:
            return "❌ Уже использовал"
        promocodes[name]["used"].append(p["gid"])
        p["bal"] += promocodes[name]["amount"]
        save()
        return f"🎁 +{promocodes[name]['amount']}$"

# ========== РЫНОК ==========
def market_system(p, t):
    if t.startswith("продать"):
        parts = t.split()
        if len(parts) < 2:
            return "Формат: продать [цена]"
        try:
            price = int(parts[1])
        except:
            return "❌ Неверная цена"
        market.append({"seller": p["gid"], "price": price, "name": p["name"]})
        save()
        return f"✅ Лот выставлен за {price}$"

    if t == "рынок":
        if not market:
            return "🛒 Рынок пуст"
        text = "🛒 Рынок:\n\n"
        for i, lot in enumerate(market):
            text += f"{i}. {lot['name']} — {lot['price']}$\n"
        return text

    if t.startswith("купить"):
        parts = t.split()
        if len(parts) < 2:
            return "Формат: купить [номер]"
        try:
            i = int(parts[1])
        except:
            return "❌ Неверный номер"
        if i >= len(market):
            return "❌ Лот не найден"
        lot = market[i]
        if p["bal"] < lot["price"]:
            return "❌ Недостаточно денег"
        seller = find_gid(lot["seller"])
        p["bal"] -= lot["price"]
        if seller:
            seller["bal"] += lot["price"]
        market.pop(i)
        save()
        return f"✅ Куплено за {lot['price']}$"

# ========== ДУЭЛЬ ==========
async def duel(p, update):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответь на сообщение соперника!")
        return
    if time.time() - p["last_duel"] < 60:
        left = int(60 - (time.time() - p["last_duel"]))
        await update.message.reply_text(f"⏰ Дуэль доступна через {left} сек")
        return
    target = get_p(update.message.reply_to_message.from_user.id)
    if random.random() < 0.5:
        p["bal"] += 1000
        p["rating"] += 5
        target["bal"] -= 1000
        await update.message.reply_text(f"⚔️ Ты победил! +1000$")
    else:
        p["bal"] -= 1000
        target["bal"] += 1000
        target["rating"] += 5
        await update.message.reply_text(f"⚔️ Ты проиграл! -1000$")
    p["last_duel"] = time.time()
    save()

# ========== РП ==========
rp_list = ["обнял", "поцеловал", "ударил", "пнул", "лизнул", "укусил", "погладил"]

async def rp_system(p, t, update):
    for cmd in rp_list:
        if t.startswith(cmd):
            if not update.message.reply_to_message:
                await update.message.reply_text("❌ Ответь на сообщение!")
                return
            target = get_p(update.message.reply_to_message.from_user.id)
            if p["lover"] == target["gid"]:
                p["love"] += 1
            save()
            await update.message.reply_text(f"💫 {p['name']} {cmd} {target['name']}")
            return

# ========== ОТНОШЕНИЯ ==========
async def relations(p, t, update):
    if t == "предложение":
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Ответь на сообщение!")
            return
        target = get_p(update.message.reply_to_message.from_user.id)
        target["proposal"] = p["gid"]
        save()
        await update.message.reply_text(f"💍 Предложение отправлено {target['name']}!")

    if t == "принять":
        if not p["proposal"]:
            await update.message.reply_text("❌ Нет предложений!")
            return
        other = find_gid(p["proposal"])
        if other:
            p["lover"] = other["gid"]
            other["lover"] = p["gid"]
        p["proposal"] = None
        save()
        await update.message.reply_text(f"💑 Вы теперь вместе с {other['name']}!")

    if t == "развод":
        if not p["lover"]:
            await update.message.reply_text("❌ Нет партнёра!")
            return
        other = find_gid(p["lover"])
        if other:
            other["lover"] = None
        p["lover"] = None
        save()
        await update.message.reply_text("💔 Развод оформлен!")

# ========== ВЫДАЧА ДЕНЕГ ==========
async def give_money(update):
    args = update.message.text.split()
    sender = get_p(update.effective_user.id)

    if len(args) < 3:
        await update.message.reply_text("Формат: выдать [ID] [сумма]")
        return

    try:
        gid = int(args[1])
        amount = int(args[2])
    except:
        await update.message.reply_text("❌ Неверный формат")
        return

    target = find_gid(gid)
    if not target:
        await update.message.reply_text("❌ Игрок не найден")
        return

    if update.effective_user.id == ADMIN_ID:
        target["bal"] += amount
        save()
        await update.message.reply_text(f"✅ Выдал {amount}$ игроку {target['name']}!")
        return

    vip = sender.get("vip")
    if vip not in vip_limits:
        await update.message.reply_text("❌ Нет прав!")
        return

    if time.time() - sender.get("vip_reset", 0) > 86400:
        sender["vip_given"] = 0
        sender["vip_reset"] = time.time()

    if sender.get("vip_given", 0) + amount > vip_limits[vip]:
        await update.message.reply_text("❌ Превышен дневной лимит!")
        return

    sender["vip_given"] = sender.get("vip_given", 0) + amount
    target["bal"] += amount
    save()
    await update.message.reply_text(f"✅ Переведено {amount}$ игроку {target['name']}!")

# ========== ВЫДАЧА КЕЙСОВ (АДМИН) ==========
async def give_cases(update, t):
    parts = t.split()
    if len(parts) < 3:
        await update.message.reply_text("Формат: выдатькейс [ID] [количество]")
        return
    try:
        gid = int(parts[1])
        count = int(parts[2])
    except:
        await update.message.reply_text("❌ Неверный формат")
        return
    target = find_gid(gid)
    if target:
        target["cases"] += count
        save()
        await update.message.reply_text(f"✅ Выдал {count} кейсов игроку {target['name']}!")
    else:
        await update.message.reply_text("❌ Игрок не найден")

# ========== ОБРАБОТЧИК КНОПОК ==========
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    p = get_p(q.from_user.id)
    p["name"] = q.from_user.first_name

    if q.data == "bal":
        partner = find_gid(p["lover"])
        partner_name = partner["name"] if partner else "Нет"
        await q.edit_message_text(
            f"💰 Баланс: {p['bal']}$\n"
            f"🏦 Банк: {p['bank']}$\n"
            f"🎁 Кейсы: {p['cases']} | 🔵 Rare: {p['rare']} | 🟣 Epic: {p['epic']}\n"
            f"🏢 Бизнесов: {p['business']}\n"
            f"💑 Партнёр: {partner_name}\n"
            f"⭐ Рейтинг: {p['rating']}",
            reply_markup=menu()
        )

    elif q.data == "cases":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Купить кейс (1000$)", callback_data="buy_case")],
            [InlineKeyboardButton("🎁 Открыть кейс", callback_data="open_case")],
            [InlineKeyboardButton("🔵 Открыть Rare", callback_data="open_rare")],
            [InlineKeyboardButton("🟣 Открыть Epic", callback_data="open_epic")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")],
        ])
        await q.edit_message_text(
            f"🎁 Кейсы: {p['cases']} | 🔵 Rare: {p['rare']} | 🟣 Epic: {p['epic']}",
            reply_markup=kb
        )

    elif q.data == "buy_case":
        if p["bal"] >= 1000:
            p["bal"] -= 1000
            p["cases"] += 1
            save()
            await q.edit_message_text(f"✅ Кейс куплен! У тебя: {p['cases']} кейсов")
        else:
            await q.edit_message_text("❌ Нужно 1000$")

    elif q.data == "open_case":
        if p["cases"] <= 0:
            await q.edit_message_text("❌ Нет кейсов!")
            return
        p["cases"] -= 1
        r = random.random()
        if r < 0.5:
            win = random.randint(500, 2000)
            p["bal"] += win
            text = f"💰 +{win}$"
        elif r < 0.8:
            win = random.randint(2000, 5000)
            p["bal"] += win
            text = f"💎 +{win}$"
        elif r < 0.95:
            p["rare"] += 1
            text = "🔵 Rare кейс!"
        else:
            p["epic"] += 1
            text = "🟣 EPIC кейс!"
        save()
        await q.edit_message_text(text)

    elif q.data == "open_rare":
        if p["rare"] <= 0:
            await q.edit_message_text("❌ Нет Rare кейсов!")
            return
        p["rare"] -= 1
        win = random.randint(5000, 15000)
        p["bal"] += win
        save()
        await q.edit_message_text(f"🔵 +{win}$!")

    elif q.data == "open_epic":
        if p["epic"] <= 0:
            await q.edit_message_text("❌ Нет Epic кейсов!")
            return
        p["epic"] -= 1
        win = random.randint(20000, 50000)
        p["bal"] += win
        save()
        await q.edit_message_text(f"🟣 +{win}$!")

    elif q.data == "bank_menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 Положить 1000$", callback_data="bank_dep_1000")],
            [InlineKeyboardButton("💵 Положить 5000$", callback_data="bank_dep_5000")],
            [InlineKeyboardButton("💸 Снять всё", callback_data="bank_withdraw")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")],
        ])
        await q.edit_message_text(f"🏦 Банк: {p['bank']}$", reply_markup=kb)

    elif q.data == "bank_dep_1000":
        if p["bal"] >= 1000:
            p["bal"] -= 1000
            p["bank"] += 1000
            save()
            await q.edit_message_text(f"✅ Положил 1000$ в банк! В банке: {p['bank']}$")
        else:
            await q.edit_message_text("❌ Недостаточно денег!")

    elif q.data == "bank_dep_5000":
        if p["bal"] >= 5000:
            p["bal"] -= 5000
            p["bank"] += 5000
            save()
            await q.edit_message_text(f"✅ Положил 5000$ в банк! В банке: {p['bank']}$")
        else:
            await q.edit_message_text("❌ Недостаточно денег!")

    elif q.data == "bank_withdraw":
        amount = p["bank"]
        p["bal"] += amount
        p["bank"] = 0
        save()
        await q.edit_message_text(f"💸 Снял {amount}$ из банка!")

    elif q.data == "work_menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("👨‍💻 Программист (+500$)", callback_data="work_prog")],
            [InlineKeyboardButton("🚕 Таксист (+200$)", callback_data="work_taxi")],
            [InlineKeyboardButton("🍕 Курьер (+150$)", callback_data="work_courier")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")],
        ])
        await q.edit_message_text("💼 Выбери работу:", reply_markup=kb)

    elif q.data == "work_prog":
        p["bal"] += 500
        p["rating"] += 5
        save()
        await q.edit_message_text("👨‍💻 +500$! +5 рейтинга")

    elif q.data == "work_taxi":
        p["bal"] += 200
        p["rating"] += 2
        save()
        await q.edit_message_text("🚕 +200$! +2 рейтинга")

    elif q.data == "work_courier":
        p["bal"] += 150
        p["rating"] += 1
        save()
        await q.edit_message_text("🍕 +150$! +1 рейтинга")

    elif q.data == "shop_menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚗 Жигули (1000$)", callback_data="buy_lada")],
            [InlineKeyboardButton("🚗 BMW (5000$)", callback_data="buy_bmw")],
            [InlineKeyboardButton("🚗 Lamborghini (20000$)", callback_data="buy_lambo")],
            [InlineKeyboardButton("🏠 Квартира (3000$)", callback_data="buy_apt")],
            [InlineKeyboardButton("🏠 Дом (10000$)", callback_data="buy_house")],
            [InlineKeyboardButton("🏰 Вилла (50000$)", callback_data="buy_villa")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")],
        ])
        await q.edit_message_text("🛒 Магазин:", reply_markup=kb)

    elif q.data == "buy_lada":
        if p["bal"] >= 1000:
            p["bal"] -= 1000
            p["rating"] += 5
            save()
            await q.edit_message_text("🚗 Купил Жигули! +5 рейтинга")
        else:
            await q.edit_message_text("❌ Нужно 1000$")

    elif q.data == "buy_bmw":
        if p["bal"] >= 5000:
            p["bal"] -= 5000
            p["rating"] += 20
            save()
            await q.edit_message_text("🚗 Купил BMW! +20 рейтинга")
        else:
            await q.edit_message_text("❌ Нужно 5000$")

    elif q.data == "buy_lambo":
        if p["bal"] >= 20000:
            p["bal"] -= 20000
            p["rating"] += 50
            save()
            await q.edit_message_text("🚗 Купил Lamborghini! +50 рейтинга")
        else:
            await q.edit_message_text("❌ Нужно 20000$")

    elif q.data == "buy_apt":
        if p["bal"] >= 3000:
            p["bal"] -= 3000
            p["rating"] += 10
            save()
            await q.edit_message_text("🏠 Купил квартиру! +10 рейтинга")
        else:
            await q.edit_message_text("❌ Нужно 3000$")

    elif q.data == "buy_house":
        if p["bal"] >= 10000:
            p["bal"] -= 10000
            p["rating"] += 30
            save()
            await q.edit_message_text("🏠 Купил дом! +30 рейтинга")
        else:
            await q.edit_message_text("❌ Нужно 10000$")

    elif q.data == "buy_villa":
        if p["bal"] >= 50000:
            p["bal"] -= 50000
            p["rating"] += 100
            save()
            await q.edit_message_text("🏰 Купил виллу! +100 рейтинга")
        else:
            await q.edit_message_text("❌ Нужно 50000$")

    elif q.data == "casino_menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎰 Слоты (50$)", callback_data="slots")],
            [InlineKeyboardButton("🎲 Рулетка (100$)", callback_data="roulette")],
            [InlineKeyboardButton("🃏 Блэкджек (200$)", callback_data="blackjack")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")],
        ])
        await q.edit_message_text("🎰 Казино:", reply_markup=kb)

    elif q.data == "slots":
        bet = 50
        if p["bal"] < bet:
            await q.edit_message_text("❌ Нужно 50$")
            return
        symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣"]
        s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
        if s1 == s2 == s3:
            win = bet * 5
            p["bal"] += win
            p["rating"] += 10
            text = f"🎰 {s1}{s2}{s3}\n🎉 ДЖЕКПОТ! +{win}$"
        elif s1 == s2 or s2 == s3:
            p["bal"] += bet
            text = f"🎰 {s1}{s2}{s3}\n✅ +{bet}$"
        else:
            p["bal"] -= bet
            text = f"🎰 {s1}{s2}{s3}\n❌ -{bet}$"
        save()
        await q.edit_message_text(text)

    elif q.data == "roulette":
        bet = 100
        if p["bal"] < bet:
            await q.edit_message_text("❌ Нужно 100$")
            return
        number = random.randint(0, 36)
        color = "🔴" if number % 2 == 0 else "⚫"
        if random.random() > 0.5:
            p["bal"] += bet
            p["rating"] += 3
            text = f"🎲 {color} {number} — +{bet}$"
        else:
            p["bal"] -= bet
            text = f"🎲 {color} {number} — -{bet}$"
        save()
        await q.edit_message_text(text)

    elif q.data == "blackjack":
        bet = 200
        if p["bal"] < bet:
            await q.edit_message_text("❌ Нужно 200$")
            return
        ps = random.randint(15, 21)
        ds = random.randint(15, 21)
        if ps > ds or ds > 21:
            p["bal"] += bet
            p["rating"] += 5
            text = f"🃏 Ты: {ps} | Дилер: {ds}\n✅ +{bet}$"
        else:
            p["bal"] -= bet
            text = f"🃏 Ты: {ps} | Дилер: {ds}\n❌ -{bet}$"
        save()
        await q.edit_message_text(text)

    elif q.data == "clan_menu":
        await q.edit_message_text(
            "⚔️ Клан — команды:\n\n"
            "создатьклан [название]\n"
            "вступитьклан [ID]\n"
            "топкланов — рейтинг кланов"
        )

    elif q.data == "top_menu":
        if not players:
            await q.edit_message_text("Нет игроков!")
            return
        sorted_p = sorted(players.values(), key=lambda x: x["rating"], reverse=True)[:10]
        text = "🏆 Топ игроков:\n\n"
        for i, pl in enumerate(sorted_p, 1):
            text += f"{i}. {pl['name']} — ⭐{pl['rating']} | 💰{pl['bal']}$\n"
        await q.edit_message_text(text)

    elif q.data == "back_menu":
        await q.edit_message_text("🎮 Главное меню:", reply_markup=menu())

# ========== ГЛАВНЫЙ ОБРАБОТЧИК ==========
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.lower().strip()
    uid = update.effective_user.id
    p = get_p(uid)
    p["name"] = update.effective_user.first_name

    if p["banned"] or time.time() < p["muted_until"]:
        return

    # Админ команды
    if uid == ADMIN_ID and t.startswith("выдатькейс"):
        await give_cases(update, t)
        return

    if t.startswith("выдать"):
        await give_money(update)
        return

    # Промокоды
    msg = promo_system(p, t)
    if msg:
        await update.message.reply_text(msg)
        return

    # Кейсы
    msg = case_system(p, t)
    if msg:
        await update.message.reply_text(msg)
        return

    # Депозит
    if t.startswith("депозит") or t == "снятьдепозит":
        msg = deposit_system(p, t)
        if msg:
            await update.message.reply_text(msg)
        return

    # Экономика
    msg = economy(p, t)
    if msg:
        await update.message.reply_text(msg)
        return

    # Рынок
    msg = market_system(p, t)
    if msg:
        await update.message.reply_text(msg)
        return

    # Дуэль
    if t.startswith("дуэль"):
        await duel(p, update)
        return

    # РП
    await rp_system(p, t, update)

    # Отношения
    await relations(p, t, update)

    # Баланс
    if t in ["баланс", "б"]:
        await update.message.reply_text(
            f"💰 Баланс: {p['bal']}$\n"
            f"🏦 Банк: {p['bank']}$\n"
            f"⭐ Рейтинг: {p['rating']}"
        )

    # Топ
    if t == "топ":
        sorted_p = sorted(players.values(), key=lambda x: x["rating"], reverse=True)[:10]
        text = "🏆 Топ игроков:\n\n"
        for i, pl in enumerate(sorted_p, 1):
            text += f"{i}. {pl['name']} — ⭐{pl['rating']} | 💰{pl['bal']}$\n"
        await update.message.reply_text(text)

    # Кланы
    if t.startswith("создатьклан"):
        parts = t.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("Формат: создатьклан [название]")
            return
        if p["clan"]:
            await update.message.reply_text("❌ Ты уже в клане!")
            return
        name = parts[1]
        clan_id = str(len(players))
        p["clan"] = {"id": clan_id, "name": name, "members": [uid], "treasury": 0, "rating": 0}
        save()
        await update.message.reply_text(f"⚔️ Клан '{name}' создан! ID: {clan_id}")

    save()

# ========== MAIN ==========
def main():
    load()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
