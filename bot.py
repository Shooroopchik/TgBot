# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import os

# Загружаем токен
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# 🔧 РЕЖИМ ОТЛАДКИ: пока True — заказы идут тебе
DEBUG_MODE = True

# 🧑‍💻 Твой ID или username (для тестов)
DEV_CHAT = "@Shooroopchik"  # замени на свой username

# 👔 Администратор (на будущее)
ADMIN_CHAT = "@nadezda_bolshaya_elnya"  # username админа (потом раскомментируешь)

# Каталог товаров
PRODUCTS = {
    "apple": {"name": "Яблоки", "price": 120},
    "milk": {"name": "Молоко", "price": 80},
    "bread": {"name": "Хлеб", "price": 40},
}

# Клавиатура с товарами
def create_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} — {p['price']} руб", callback_data=key)]
        for key, p in PRODUCTS.items()
    ]
    return InlineKeyboardMarkup(keyboard)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋\n"
        "Я — бот для заказов.\n"
        "Напиши /order, чтобы сделать заказ."
    )

# /order — начало заказа
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = create_menu_keyboard()
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🛒\n"
        "Выбери товар:",
        reply_markup=keyboard
    )

# Обработка выбора товара
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_key = query.data
    if product_key in PRODUCTS:
        context.user_data['product'] = product_key
        product = PRODUCTS[product_key]
        await query.edit_message_text(
            f"Вы выбрали: *{product['name']}*\n"
            "Теперь укажите количество:",
            parse_mode="Markdown"
        )
        context.user_data['step'] = 'quantity'

# Обработка текста (количество → имя → телефон)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    step = context.user_data.get('step')

    if step == 'quantity':
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("Введите число больше 0.")
            return
        context.user_data['quantity'] = int(text)
        await update.message.reply_text("Теперь укажите ваше имя:")
        context.user_data['step'] = 'name'

    elif step == 'name':
        context.user_data['name'] = text
        await update.message.reply_text("Укажите ваш телефон:")
        context.user_data['step'] = 'phone'

    elif step == 'phone':
        context.user_data['phone'] = text
        user = update.effective_user
        product_key = context.user_data['product']
        product = PRODUCTS[product_key]
        quantity = context.user_data['quantity']
        name = context.user_data['name']
        phone = context.user_data['phone']
        total = product['price'] * quantity

        # Формируем сообщение
        order_message = (
            f"🛒 *НОВЫЙ ЗАКАЗ*\n"
            f"Пользователь: @{user.username} (ID: {user.id})\n"
            f"Товар: {product['name']} — {product['price']} руб\n"
            f"Количество: {quantity}\n"
            f"Сумма: {total} руб\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Время: {update.message.date.strftime('%H:%M %d.%m.%Y')}"
        )

        # 🎯 ОТПРАВКА ЗАКАЗА: зависит от режима
        if DEBUG_MODE:
            # 🔧 Режим отладки — заказ идёт тебе
            await context.bot.send_message(
                chat_id=DEV_CHAT,
                text=order_message,
                parse_mode="Markdown"
            )
        else:
            # ✅ Продакшен — заказ идёт админу
            await context.bot.send_message(
                chat_id=ADMIN_CHAT,
                text=order_message,
                parse_mode="Markdown"
            )

        # Подтверждение клиенту
        await update.message.reply_text(
            f"✅ Заказ принят!\n"
            f"Товар: {product['name']}\n"
            f"Количество: {quantity}\n"
            f"Сумма: {total} руб\n"
            f"С вами свяжутся по телефону: {phone}\n\n"
            f"Спасибо за заказ, {name}! 🎉"
        )

        # Сброс
        context.user_data.clear()

# Основная функция
def main():
    print("Запускаем бота...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", order))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()

if __name__ == "__main__":
    main()