import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# مراحل گفتگو
SELECT_MODE, RECEIVE_MEDIA, WAIT_CAPTION, RECEIVE_CAPTION, CHOOSE_BUTTON_SEND, RECEIVE_BUTTON, RECEIVE_TARGET = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    آغاز مکالمه و نمایش منوی ابتدایی برای انتخاب حالت ارسال رسانه یا متن ساده.
    """
    keyboard = [
        [InlineKeyboardButton("🖼 ارسال عکس/ویدیو", callback_data="choose_media")],
        [InlineKeyboardButton("📝 ارسال تنها متن", callback_data="choose_text")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام! لطفاً یکی از گزینه‌ها را انتخاب کن:", reply_markup=reply_markup)
    return SELECT_MODE

async def mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    واکنش به انتخاب کاربر برای ارسال رسانه یا متن ساده.
    """
    query = update.callback_query
    await query.answer()
    mode = query.data

    # یک‌سری داده‌ها را در context.user_data ذخیره می‌کنیم
    context.user_data.clear()
    context.user_data["buttons"] = []

    if mode == "choose_media":
        await query.edit_message_text("🥳 حالا لطفاً عکس یا ویدیو را ارسال کن.")
        return RECEIVE_MEDIA
    else:  # choose_text
        # در حالت متنی، media_type را None می‌گذاریم
        context.user_data["media_type"] = None
        await query.edit_message_text("📝 لطفاً متن را وارد کن (این متن به عنوان کپشن ذخیره می‌شود).")
        return RECEIVE_CAPTION

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دریافت عکس یا ویدئو و ذخیره‌ی file_id، سپس نمایش دکمه برای رفتن به مرحله بعد (ارسال کپشن).
    """
    message = update.message
    if message.photo:
        context.user_data["media_type"] = "photo"
        context.user_data["file_id"] = message.photo[-1].file_id
    elif message.video:
        context.user_data["media_type"] = "video"
        context.user_data["file_id"] = message.video.file_id
    else:
        await update.message.reply_text("❌ لطفاً دقیقاً یک عکس یا یک ویدیو ارسال کن.")
        return RECEIVE_MEDIA

    # بعد از دریافت رسانه، دکمه می‌فرستیم که کاربر برای ارسال کپشن کلیک کند
    keyboard = [
        [InlineKeyboardButton("📝 ارسال کپشن", callback_data="to_caption")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ رسانه دریافت شد. برای ادامه و ارسال کپشن دکمه را بزن.", reply_markup=reply_markup)
    return WAIT_CAPTION

async def to_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    پس از کلیک روی دکمه 'ارسال کپشن'، درخواست کپشن از کاربر.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📋 لطفاً کپشن (یا متن پیام) را وارد کن:")
    return RECEIVE_CAPTION

async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دریافت متن کپشن یا پیام و ذخیره‌ی آن. سپس پیشنهاد ساخت دکمه یا ارسال پیام به کاربر.
    """
    context.user_data["caption"] = update.message.text
    # منو برای افزودن دکمه یا ارسال پیام نهایی
    keyboard = [
        [InlineKeyboardButton("➕ افزودن دکمه", callback_data="add_button")],
        [InlineKeyboardButton("📤 ارسال پیام", callback_data="send_now")],
    ]
    await update.message.reply_text("✅ کپشن دریافت شد. حالا انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_BUTTON_SEND

async def handle_after_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    واکنش به انتخاب کاربر بعد از کپشن: افزودن دکمه یا ارسال پیام نهایی.
    """
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "add_button":
        await query.edit_message_text(
            "📥 برای افزودن هر دکمه، ابتدا متن دکمه را در یک خط و سپس لینک را در خط بعد وارد کن.\n"
            "مثال:\n"
            "اینستاگرام\n"
            "https://instagram0.com"
        )
        return RECEIVE_BUTTON
    else:  # send_now
        await query.edit_message_text("📥 لطفاً آیدی کانال یا گروه را وارد کن (مثلاً: @mychannel یا -1001234567890):")
        return RECEIVE_TARGET

async def receive_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دریافت متن و لینک یک دکمه و ذخیره‌ی آن. سپس پیشنهاد ساخت مجدد دکمه یا ارسال پیام.
    """
    text = update.message.text.split("\n")
    if len(text) != 2:
        await update.message.reply_text(
            "❌ فرمت اشتباه است. لطفاً ابتدا متن دکمه را بنویس و خط بعدی لینک را بفرست.\n"
            "مثال:\n"
            "ورود\n"
            "example.com"
        )
        return RECEIVE_BUTTON

    btn_text, btn_url = text[0].strip(), text[1].strip()
    context.user_data["buttons"].append((btn_text, btn_url))

    # بعد از ذخیره دکمه، نمایش منو برای افزودن دکمه دیگر یا ارسال
    keyboard = [
        [InlineKeyboardButton("➕ افزودن دکمه دیگر", callback_data="add_button")],
        [InlineKeyboardButton("📤 ارسال پیام", callback_data="send_now")],
    ]
    await update.message.reply_text("✅ دکمه ذخیره شد. یکی از گزینه‌ها را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_BUTTON_SEND

async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دریافت آیدی کانال یا گروه و ارسال پیام نهایی شامل رسانه (در صورت وجود)، کپشن و دکمه‌ها.
    """
    chat_id = update.message.text.strip()
    user_data = context.user_data

    # ساختار دکمه‌ها را تبدیل به شکل [[InlineKeyboardButton,...], ...]
    buttons = [[InlineKeyboardButton(text, url=url)] for text, url in user_data.get("buttons", [])]
    markup = InlineKeyboardMarkup(buttons) if buttons else None

    try:
        if user_data.get("media_type") == "photo":
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=user_data.get("file_id"),
                caption=user_data.get("caption", ""),
                reply_markup=markup
            )
        elif user_data.get("media_type") == "video":
            await context.bot.send_video(
                chat_id=chat_id,
                video=user_data.get("file_id"),
                caption=user_data.get("caption", ""),
                reply_markup=markup
            )
        else:
            # حالت تنها متن
            await context.bot.send_message(
                chat_id=chat_id,
                text=user_data.get("caption", ""),
                reply_markup=markup
            )

        await update.message.reply_text("✅ پیام با موفقیت ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"❗️ خطا در ارسال پیام: {e}")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    لغو عملیات و پاک کردن داده‌ها.
    """
    await update.message.reply_text("🚫 عملیات لغو شد.")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    TOKEN = "7880763929:AAFXwLAo0wUOiz7iPPMfxqMpviGa13Tlcdg"  # ← توکن ربات خودت را اینجا قرار بده

    # تنظیم لاگ
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # منوی انتخاب مدیا یا متن
            SELECT_MODE: [CallbackQueryHandler(mode_selection, pattern="^choose_")],
            # دریافت عکس یا ویدئو
            RECEIVE_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO, receive_media)],
            # پس از دریافت رسانه، دکمه برای رفتن به کپشن
            WAIT_CAPTION: [CallbackQueryHandler(to_caption, pattern="^to_caption$")],
            # دریافت کپشن یا متن
            RECEIVE_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption)],
            # واکنش بعد از کپشن: افزودن دکمه یا ارسال
            CHOOSE_BUTTON_SEND: [CallbackQueryHandler(handle_after_caption, pattern="^(add_button|send_now)$")],
            # دریافت هر دکمه (متن و لینک)
            RECEIVE_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_button)],
            # دریافت آیدی مقصد و ارسال نهایی
            RECEIVE_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)
    print("ربات اجرا شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
