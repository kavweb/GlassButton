import logging
import os
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

SELECT_MODE, RECEIVE_MEDIA, WAIT_CAPTION, RECEIVE_CAPTION, CHOOSE_BUTTON_SEND, RECEIVE_BUTTON, RECEIVE_TARGET = range(7)

translations = {
    "fa": {
        "start_message": "سلام! لطفاً یکی از گزینه‌ها را انتخاب کن:",
        "choose_media": "🖼 ارسال عکس/ویدیو",
        "choose_text": "📝 ارسال تنها متن",
        "send_caption": "📝 ارسال کپشن",
        "media_received": "✅ رسانه دریافت شد. برای ادامه و ارسال کپشن دکمه را بزن.",
        "enter_caption": "📋 لطفاً کپشن (یا متن پیام) را وارد کن:",
        "caption_received": "✅ کپشن دریافت شد. حالا انتخاب کن:",
        "add_button": "➕ افزودن دکمه",
        "send_now": "📤 ارسال پیام",
        "enter_button_text_url": "📥 برای افزودن هر دکمه، ابتدا متن دکمه را در یک خط و سپس لینک را در خط بعد وارد کن.\nمثال:\nورود\nhttps://example.com",
        "invalid_button_format": "❌ فرمت اشتباه است. لطفاً ابتدا متن دکمه را بنویس و خط بعدی لینک را بفرست.",
        "button_saved": "✅ دکمه ذخیره شد. یکی از گزینه‌ها را انتخاب کن:",
        "enter_target": "📥 لطفاً آیدی کانال یا گروه را وارد کن (مثلاً: @mychannel یا -1001234567890):",
        "sent_success": "✅ پیام با موفقیت ارسال شد.",
        "send_error": "❗️ خطا در ارسال پیام: {error}",
        "cancelled": "🚫 عملیات لغو شد.",
        "choose_language": "🌐 لطفاً زبان خود را انتخاب کنید:",
        "lang_fa": "🇮🇷 فارسی",
        "lang_en": "🇬🇧 English",
        "invalid_media": "❌ لطفاً دقیقاً یک عکس یا یک ویدیو ارسال کن.",
    },
    "en": {
        "start_message": "Hello! Please choose one of the options:",
        "choose_media": "🖼 Send Photo/Video",
        "choose_text": "📝 Send Text Only",
        "send_caption": "📝 Send Caption",
        "media_received": "✅ Media received. Click the button to continue and send caption.",
        "enter_caption": "📋 Please enter the caption (or message text):",
        "caption_received": "✅ Caption received. Now choose an option:",
        "add_button": "➕ Add Button",
        "send_now": "📤 Send Message",
        "enter_button_text_url": "📥 To add a button, send the text in the first line and the link in the second line.\nExample:\nJoin\nhttps://example.com",
        "invalid_button_format": "❌ Invalid format. Send text in first line and link in second.",
        "button_saved": "✅ Button saved. Choose next step:",
        "enter_target": "📥 Please enter the channel or group ID (e.g., @mychannel or -1001234567890):",
        "sent_success": "✅ Message sent successfully.",
        "send_error": "❗️ Error while sending message: {error}",
        "cancelled": "🚫 Operation canceled.",
        "choose_language": "🌐 Please choose your language:",
        "lang_fa": "🇮🇷 Persian",
        "lang_en": "🇬🇧 English",
        "invalid_media": "❌ Please send exactly one photo or one video.",
    }
}


def t(context, key):
    lang = context.user_data.get("lang", "fa")
    return translations[lang].get(key, key)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 لطفاً زبان خود را انتخاب کنید:", reply_markup=reply_markup)
    return SELECT_MODE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_lang = query.data.split("_")[-1]
    context.user_data["lang"] = selected_lang
    context.user_data["buttons"] = []

    keyboard = [
        [InlineKeyboardButton(t(context, "choose_media"), callback_data="choose_media")],
        [InlineKeyboardButton(t(context, "choose_text"), callback_data="choose_text")],
    ]
    await query.edit_message_text(t(context, "start_message"), reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_MODE


async def mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data
    context.user_data["buttons"] = []

    if mode == "choose_media":
        await query.edit_message_text(t(context, "choose_media"))
        return RECEIVE_MEDIA
    else:
        context.user_data["media_type"] = None
        await query.edit_message_text(t(context, "enter_caption"))
        return RECEIVE_CAPTION


async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.photo:
        context.user_data["media_type"] = "photo"
        context.user_data["file_id"] = message.photo[-1].file_id
    elif message.video:
        context.user_data["media_type"] = "video"
        context.user_data["file_id"] = message.video.file_id
    else:
        await message.reply_text(t(context, "invalid_media"))
        return RECEIVE_MEDIA

    keyboard = [[InlineKeyboardButton(t(context, "send_caption"), callback_data="to_caption")]]
    await message.reply_text(t(context, "media_received"), reply_markup=InlineKeyboardMarkup(keyboard))
    return WAIT_CAPTION


async def to_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t(context, "enter_caption"))
    return RECEIVE_CAPTION


async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["caption"] = update.message.text
    keyboard = [
        [InlineKeyboardButton(t(context, "add_button"), callback_data="add_button")],
        [InlineKeyboardButton(t(context, "send_now"), callback_data="send_now")],
    ]
    await update.message.reply_text(t(context, "caption_received"), reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_BUTTON_SEND


async def handle_after_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "add_button":
        await query.edit_message_text(t(context, "enter_button_text_url"))
        return RECEIVE_BUTTON
    else:
        await query.edit_message_text(t(context, "enter_target"))
        return RECEIVE_TARGET


async def receive_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split("\n")
    if len(text) != 2:
        await update.message.reply_text(t(context, "invalid_button_format"))
        return RECEIVE_BUTTON

    btn_text, btn_url = text[0].strip(), text[1].strip()
    context.user_data["buttons"].append((btn_text, btn_url))

    keyboard = [
        [InlineKeyboardButton(t(context, "add_button"), callback_data="add_button")],
        [InlineKeyboardButton(t(context, "send_now"), callback_data="send_now")],
    ]
    await update.message.reply_text(t(context, "button_saved"), reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_BUTTON_SEND


async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.text.strip()
    user_data = context.user_data
    buttons = [[InlineKeyboardButton(text, url=url)] for text, url in user_data.get("buttons", [])]
    markup = InlineKeyboardMarkup(buttons) if buttons else None

    try:
        if user_data.get("media_type") == "photo":
            await context.bot.send_photo(chat_id=chat_id, photo=user_data["file_id"], caption=user_data.get("caption", ""), reply_markup=markup)
        elif user_data.get("media_type") == "video":
            await context.bot.send_video(chat_id=chat_id, video=user_data["file_id"], caption=user_data.get("caption", ""), reply_markup=markup)
        else:
            await context.bot.send_message(chat_id=chat_id, text=user_data.get("caption", ""), reply_markup=markup)

        await update.message.reply_text(t(context, "sent_success"))
    except Exception as e:
        await update.message.reply_text(t(context, "send_error").format(error=e))

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t(context, "cancelled"))
    context.user_data.clear()
    return ConversationHandler.END


def main():
    TOKEN = os.getenv("BOT_TOKEN") or "Put your token here"
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_MODE: [
                CallbackQueryHandler(set_language, pattern="^lang_"),
                CallbackQueryHandler(mode_selection, pattern="^choose_"),
            ],
            RECEIVE_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO, receive_media)],
            WAIT_CAPTION: [CallbackQueryHandler(to_caption, pattern="^to_caption$")],
            RECEIVE_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption)],
            CHOOSE_BUTTON_SEND: [CallbackQueryHandler(handle_after_caption, pattern="^(add_button|send_now)$")],
            RECEIVE_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_button)],
            RECEIVE_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)
    print("Bot start..")
    app.run_polling()


if __name__ == "__main__":
    main()
