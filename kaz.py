import discord
from discord.ext import commands
import sqlite3
import random
import time
from dotenv import load_dotenv

# Создаем intents, которые разрешают боту работать с событиями пользователей
intents = discord.Intents.default()
intents.message_content = True  # Разрешаем доступ к содержимому сообщений

# Инициализируем бота с intents
bot = commands.Bot(command_prefix='!', intents=intents)

YOUR_ADMIN_ID = 979011152795283456

# Создание подключения к базе данных и инициализация таблиц
def create_db():
    conn = sqlite3.connect("kazino.db")
    cursor = conn.cursor()

    # Создание таблицы пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)

    # Создание таблицы бонусов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bonuses (
            user_id INTEGER,
            bonus_type TEXT,
            last_claim INTEGER,
            PRIMARY KEY (user_id, bonus_type)
        )
    """)

    conn.commit()
    conn.close()

# Вызови создание базы перед запуском бота
create_db()
print("[INFO] База данных инициализирована.")



# Функция получения баланса пользователя
def get_balance(user_id):
    conn = sqlite3.connect("kazino.db")
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()
    if balance:
        return balance[0]
    else:
        # Если пользователь не найден, создаем его с начальным балансом
        cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        return 0
    conn.close()

# Функция для обновления баланса пользователя
def update_balance(user_id, amount):
    conn = sqlite3.connect("kazino.db")
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

@bot.command(name='cf')
async def coinflip(ctx, bet: int, choice: str):
    user_id = ctx.author.id
    balance = get_balance(user_id)
    if bet > balance:
        await ctx.send(f"У вас недостаточно средств для этой ставки! Ваш баланс: {balance} монет.")
        return
    result = random.choice(["орел", "решка"])
    if result == choice:
        update_balance(user_id, bet)
        await ctx.send(f"Вы выиграли! На монетке выпал {result}. Ваш новый баланс: {get_balance(user_id)} монет.")
    else:
        update_balance(user_id, -bet)
        await ctx.send(f"Вы проиграли. На монетке выпал {result}. Ваш новый баланс: {get_balance(user_id)} монет.")

@bot.command(name='slots')
async def slots(ctx, bet: int):
    user_id = ctx.author.id
    balance = get_balance(user_id)
    if bet > balance:
        await ctx.send(f"У вас недостаточно средств для этой ставки! Ваш баланс: {balance} монет.")
        return
    symbols = ['🍒', '🍊', '🍉', '🍇', '🍍']
    result = [random.choice(symbols) for _ in range(3)]
    if result[0] == result[1] == result[2]:
        winnings = bet * 10
        update_balance(user_id, winnings)
        await ctx.send(f"Вы выиграли {winnings} монет! Результат: {result[0]} {result[1]} {result[2]}. Ваш новый баланс: {get_balance(user_id)} монет.")
    else:
        update_balance(user_id, -bet)
        await ctx.send(f"Вы проиграли. Результат: {result[0]} {result[1]} {result[2]}. Ваш новый баланс: {get_balance(user_id)} монет.")

@bot.command(name='dice')
async def dice(ctx, bet: int, guess: int):
    user_id = ctx.author.id
    balance = get_balance(user_id)
    if bet > balance:
        await ctx.send(f"У вас недостаточно средств для этой ставки! Ваш баланс: {balance} монет.")
        return
    if not 1 <= guess <= 6:
        await ctx.send("Пожалуйста, введите число от 1 до 6 для ставки на кубик.")
        return
    roll = random.randint(1, 6)
    if roll == guess:
        winnings = bet * 6
        update_balance(user_id, winnings)
        await ctx.send(f"Вы выиграли! Выпал {roll}. Ваш новый баланс: {get_balance(user_id)} монет.")
    else:
        update_balance(user_id, -bet)
        await ctx.send(f"Вы проиграли. Выпал {roll}. Ваш новый баланс: {get_balance(user_id)} монет.")

# Функция для игры HighLow
@bot.command(name='highlow')
async def highlow(ctx, bet: int, choice: str):
    user_id = ctx.author.id
    balance = get_balance(user_id)

    if bet > balance:
        await ctx.send(f"У вас недостаточно средств для этой ставки! Ваш баланс: {balance} монет.")
        return

    if choice not in ['High', 'Low']:
        await ctx.send("Выберите правильный вариант: 'High' или 'Low'.")
        return

    # Генерация случайного числа от 1 до 100
    number = random.randint(1, 100)
    result = 'High' if number >= 50 else 'Low'

    if choice == result:
        winnings = bet * 2
        update_balance(user_id, winnings)
        await ctx.send(f"Вы выиграли {winnings} монет! Число: {number} ({result}). Ваш новый баланс: {get_balance(user_id)} монет.")
    else:
        update_balance(user_id, -bet)
        await ctx.send(f"Вы проиграли. Число: {number} ({result}). Ваш новый баланс: {get_balance(user_id)} монет.")



# Команда для проверки баланса пользователя
@bot.command(name='bal')
async def bal(ctx):
    user_id = ctx.author.id
    balance = get_balance(user_id)
    await ctx.send(f"Ваш баланс: {balance} монет.")


# Функция для получения последнего времени получения бонуса
def get_last_claim_time(user_id, bonus_type):
    conn = sqlite3.connect('kazino.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_claim FROM bonuses WHERE user_id = ? AND bonus_type = ?', (user_id, bonus_type))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Функция для обновления времени получения бонуса
def update_last_claim_time(user_id, bonus_type):
    conn = sqlite3.connect('kazino.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO bonuses (user_id, bonus_type, last_claim) VALUES (?, ?, ?) ON CONFLICT(user_id, bonus_type) DO UPDATE SET last_claim = ?',
                   (user_id, bonus_type, int(time.time()), int(time.time())))
    conn.commit()
    conn.close()

# Команда для ежедневного получения монет (раз в 24 часа)
@bot.command(name='daily')
async def daily(ctx):
    user_id = ctx.author.id
    last_claim = get_last_claim_time(user_id, "daily")
    current_time = int(time.time())

    if last_claim and current_time - last_claim < 86400:  # 86400 секунд = 24 часа
        remaining_time = 86400 - (current_time - last_claim)
        hours, minutes = divmod(remaining_time // 60, 60)
        await ctx.send(f"Вы уже получали бонус сегодня! Попробуйте снова через {hours} часов {minutes} минут.")
        return

    reward = random.randint(1000, 9000)
    update_balance(user_id, reward)
    update_last_claim_time(user_id, "daily")
    await ctx.send(f"Вы получили {reward} монет за ежедневный бонус! Ваш новый баланс: {get_balance(user_id)} монет.")

# Команда для получения монет каждый час
@bot.command(name='hourly')
async def hourly(ctx):
    user_id = ctx.author.id
    last_claim = get_last_claim_time(user_id, "hourly")
    current_time = int(time.time())

    if last_claim and current_time - last_claim < 3600:  # 3600 секунд = 1 час
        remaining_time = 3600 - (current_time - last_claim)
        minutes, seconds = divmod(remaining_time, 60)
        await ctx.send(f"Вы уже получали бонус в последний час! Попробуйте снова через {minutes} минут {seconds} секунд.")
        return

    reward = random.randint(1000, 3000)
    update_balance(user_id, reward)
    update_last_claim_time(user_id, "hourly")
    await ctx.send(f"Вы получили {reward} монет за бонус каждый час! Ваш новый баланс: {get_balance(user_id)} монет.")


# Админ команда для выдачи монет
@bot.command(name='givemoney')
async def givemoney(ctx, amount: int, user_id: int):
    if ctx.author.id != YOUR_ADMIN_ID:  # Замените на ID вашего администратора
        await ctx.send("У вас нет прав на эту команду.")
        return
    update_balance(user_id, amount)
    await ctx.send(f"Вы выдали {amount} монет пользователю с ID {user_id}. Новый баланс: {get_balance(user_id)} монет.")

# Админ команда для удаления монет
@bot.command(name='takemoney')
async def takemoney(ctx, amount: int, user_id: int):
    if ctx.author.id != YOUR_ADMIN_ID:  # Замените на ID вашего администратора
        await ctx.send("У вас нет прав на эту команду.")
        return
    update_balance(user_id, -amount)
    await ctx.send(f"Вы забрали {amount} монет у пользователя с ID {user_id}. Новый баланс: {get_balance(user_id)} монет.")

# Команда для кражи монет
@bot.command(name='rob')
async def rob(ctx, amount: int, user_id: int):
    user_id_robber = ctx.author.id
    balance = get_balance(user_id_robber)
    if amount > balance:
        await ctx.send("У вас недостаточно средств для этой кражи!")
        return
    chance = random.randint(1, 100)
    if chance <= 45:
        update_balance(user_id_robber, amount)
        update_balance(user_id, -amount)
        await ctx.send(f"Вы украли {amount} монет у пользователя с ID {user_id}. Ваш новый баланс: {get_balance(user_id_robber)} монет.")
    else:
        update_balance(user_id_robber, -amount)
        await ctx.send(f"Вы были пойманы за кражей и потеряли {amount} монет. Ваш новый баланс: {get_balance(user_id_robber)} монет.")

# Команда для помощи
@bot.command(name='helpkaz')
async def helpkaz(ctx):
    help_text = """
    Доступные команды:
    - !bal - Проверить ваш баланс
    - !daily - Получить ежедневный бонус (от 1к до 9к монет)
    - !hourly - Получить бонус каждый час (от 1к до 3к монет)
    - !top - Топ 10 богатых игроков
    - !cf <ставка> <орел/решка> - Подбрасывание монетки
    - !slots <ставка> - Игровой автомат
    - !dice <ставка> <число от 1 до 6> - Игровой кубик
    - !highlow <ставка> <high/low> - Ставка на большее или меньшее [!FIXING!]
    - !givemoney <сумма> <ID пользователя> - Выдать деньги пользователю (админ)
    - !takemoney <сумма> <ID пользователя> - Забрать деньги у пользователя (админ)
    - !rob <сумма> <ID пользователя> - Украсть деньги у пользователя
    """
    await ctx.send(help_text)

@bot.command(name='top')
async def top(ctx):
    conn = sqlite3.connect("kazino.db")
    cursor = conn.cursor()

    # Получаем топ-10 пользователей по балансу
    cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()

    if not top_users:
        await ctx.send("В топе пока нет игроков!")
        return

    # Формируем список лидеров
    leaderboard = "**🏆 Топ 10 богачей сервера 🏆**\n\n"
    for i, (user_id, balance) in enumerate(top_users, start=1):
        user = await bot.fetch_user(user_id)  # Получаем имя пользователя по ID
        username = user.name if user else f"Неизвестный ({user_id})"
        leaderboard += f"**{i}.** {username} — {balance} монет\n"

    await ctx.send(leaderboard)


# Запуск бота
load_dotenv()

# Получаем токен
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    create_db()  # Инициализация базы данных
    bot.run(DISCORD_TOKEN)


