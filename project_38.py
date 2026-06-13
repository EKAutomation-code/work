import requests
import asyncio
import threading
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ApplicationBuilder

TELEGRAM_BOT_TOKEN ="8899332559:AAGSK7vq7qEoDzNk1LVJEPlLdJu0FkigCIg"
target_prices={} # {chat_id: target_price}
active_monitors={} # {chat_id: True/False}
PROXY_URL = None
def get_bitcoin_price():
    try:
        url="https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response=requests.get(url, timeout=10)
        data=response.json()
        return float(data['price'])
    except Exception as e:
        print(f"Ошибка получения цены: {e}")
        return None
def monitor_user_price(chat_id,target_price,application):
    def monitor():
        while chat_id in target_prices and target_prices[chat_id]==target_price:
            try:
                current_price=get_bitcoin_price()
                if current_price is not None and current_price>=target_price:
                    message=f"""Достигнута целевая цена!🎉
BTC: ${current_price:,.2f}
Ваша цель: ${target_price:,.2f}
Поздравляю! Цена достигла вашего порога!"""
                    application.bot.send_message(chat_id=chat_id,text=message)
                    if chat_id in target_prices:
                        del target_prices[chat_id]
                    break
            except Exception as e:
                print(f"Ошибка мониторинга для {chat_id}: {e}")
            time.sleep(15)
    thread=threading.Thread(target=monitor,daemon=True)
    thread.start()
    active_monitors[chat_id]=thread
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - приветствие и инструкция"""
    user_name=update.effective_user.first_name
    welcome_message=f"""Привет, {user_name}!
Я бот для отслеживания цены Биткоина.
**Как пользоваться:**
1. Просто отправь мне **число** - желаемую цену в долларах
2. Я буду следить за ценой BTC 24/7
3. Когда цена достигнет цели - я сам тебе напишу!

**Пример**
Отправь `70000` и я сообщу, когда BTC будет >= $70,000

**Команды**
/price - узнать текущую цену BTC
/mytarget - посмотреть свою активную цель
/stop - остановить отслеживание
/help - показать это сообщение

Вперед!"""

    await update.message.reply_text(welcome_message)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - справка"""
    help_text="""**Справка по командам:**
**Отправь число** - установите цель.
Пример:`50000`

`/price` - текущая цена BTC

`/mytarget` - твоя текущая цель

`/stop` - остановить отслеживание

`/start` - приветствие

`/help` - это сообщение

**Совет:** Бот работает 24/7. Отправь цель и занимаймся своими делами!"""

    await update.message.reply_text(help_text)

async def show_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price - показывает текущую цену"""
    price =get_bitcoin_price()
    if price is None:
        await update.message.reply_text("Не удалось получить цену. Проверь интернет и попробуй позже")
        return
    await update.message.reply_text(f"Текущая цена BTC: **${price:,.2f}**")
async def show_my_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mytarget - показывает текущая цель пользователя"""
    user_id=update.effective_chat.id
    if user_id in target_prices:
        target=target_prices[user_id]
        current_price=get_bitcoin_price()
        if current_price:
            diff = target - current_price
            if diff>0:
                status=f"До цели осталось: ${diff:,.2f}"
            else:
                status=f"Цель достигнута! (но уведомление уже отправлено)"
        else:
            status=f"Не удалось получить текущую цену"
        await update.message.reply_text(
            f"**Твоя цель:** ${target:,.2f}\n"
            f"{status}\n\n"
            f"Я напишу тебе, когда BTC достигнет этой цены!"
        )
    else:
        await update.message.reply_text(
            "У тебя нет активной цели.\n\n"
            "Отправь мне число, чтобы установить цель. Например: `65000`"
        )
async def stop_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Комнада /stop - останавливает отслеживание"""
    user_id=update.effective_chat.id
    if user_id in target_prices:
        del target_prices[user_id]
        await update.message.reply_text(
            "Отслеживание остановлено. \n\n"
            "Чтобы установить новую цель, просто отправь мне число"
        )
    else:
        await update.message.reply_text(
            "У тебя нет активной цели для остановки. \n\n"
            "Отправь мне число, чтобы начать отслеживание."
        )
async def handle_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения(числа) от пользователя"""
    user_id=update.effective_chat.id
    text=update.message.text.strip()
    try:
        target_price=float(text)
        if target_price<=0:
            await update.message.reply_text("Цена должна быть больше 0! Попробуй еще раз.")
            return
        if target_price>200000:
            await update.message.reply_text("Цена слишком высокая. Введи реалистичную цену")
            return
        current_price=get_bitcoin_price()
        if current_price is None:
            await update.message.reply_text("Не удалось получить текущую цену. Попробуйте позже")
        if current_price>=target_price:
            await update.message.reply_text(
                f"Ура! Цена BTC уже **${current_price:,.2f}**\n\n"
                f"А ты хотел отслеживать ${target_price:,.2f}\n"
                f"Цель достигнута!"
            )
            return
        if user_id in target_prices:
            old_target=target_prices[user_id]
            await update.message.reply_text(
                f"У тебя уже есть активная цель: **${old_target:,.2f}**\n\n"
                f"Хочешь заменить её на  **${target_price:,.2f}**?\n\n"
                f"Просто отправь это число еще раз для подтверждения."
            )
            context.user_data['pending_target']=target_price
            return
        target_prices[user_id]=target_price
        monitor_user_price(user_id, target_price,context.application)
        await update.message.reply_text(
            f"**Отслеживание начато!**\n\n"
            f"Цель: **${target_price:,.2f}**\n"
            f"Текущий BTC: **${current_price:,.2f}**\n"
            f"До цели: **${target_price-current_price:,.2f}**\n\n"
            f"Я напишу тебе, когда цена достигнет ${target_price:,.2f}!\n\n"
            f"Используй /mytarget чтобы проверить статус"
        )
    except ValueError:
        pass
async def confirm_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение замены цели"""
    user_id=update.effective_chat.id
    if 'pending_target' in context.user_data:
        target_price=context.user_data['pending_target']
        current_price=get_bitcoin_price()
        if current_price and current_price>=target_price:
            await update.message.reply_text(
                f"Цена уже достигла ${current_price:,.2f}!\n"
                f"Цель ${target_price:,.2f} уже пройдена!"
            )
            del context.user_data['pending_target']
            return
        if user_id in target_prices:
            del target_prices[user_id]
        target_prices[user_id]=target_price
        monitor_user_price(user_id,target_price,context.application)
        del context.user_data['pending_target']
        await update.message.reply_text(
            f"**Цель обновлена!**\n\n"
            f"Новая цель: **${target_price:,.2f}**\n"
            f"Текущий курс BTC: **${current_price:,.2f}**\n\n"
            f"Я буду следить!"
        )
def main():
    """Запуск бота"""
    if PROXY_URL:
        print(f"Использую SOCKS5 прокси: {PROXY_URL}")
        # Современный способ через ApplicationBuilder
        app = (ApplicationBuilder()
               .token(TELEGRAM_BOT_TOKEN)
               .proxy(PROXY_URL)  # для методов бота (send_message и т.д.)
               .get_updates_proxy(PROXY_URL)  # для получения обновлений от Telegram
               .build())
    else:
        print("Без прокси (прямое подключение)")
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", show_price))
    app.add_handler(CommandHandler("mytarget", show_my_target))
    app.add_handler(CommandHandler("stop", stop_tracking))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price_input))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_target))
    print("Бот запущен")
    print("Бот работает и готов принимать пользователей...")
    print("Нажми Ctrl+C для остановки.")
    app.run_polling()
if __name__=="__main__":
    main()