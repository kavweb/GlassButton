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

SELECT_MODE, RECEIVE_MEDIA, WAIT_CAPTION, RECEIVE_CAPTION, CHOOSE_BUTTON_SEND, RECEIVE_BUTTON, RECEIVE_TARGET, EDIT_BUTTON_SELECT, EDIT_BUTTON_TEXT = range(9)

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
        "edit_button": "🛠 ویرایش دکمه‌ها",
        "send_now": "📤 ارسال پیام",
        "enter_button_text_url": "📥 برای افزودن یا ویرایش دکمه، ابتدا متن دکمه را در یک خط و سپس لینک را در خط بعد وارد کن.",
        "invalid_button_format": "❌ فرمت اشتباه است. لطفاً ابتدا متن دکمه را بنویس و خط بعدی لینک را بفرست.",
        "button_saved": "✅ دکمه ذخیره شد. یکی از گزینه‌ها را انتخاب کن:",
        "select_button_to_edit": "🔧 لطفاً یکی از دکمه‌ها را برای ویرایش انتخاب کن:",
        "button_edited": "✅ دکمه با موفقیت ویرایش شد.",
        "enter_target": "📥 لطفاً آیدی کانال یا گروه را وارد کن:",
        "sent_success": "✅ پیام با موفقیت ارسال شد.",
        "send_error": "❗️ خطا در ارسال پیام: {error}",
        "cancelled": "🚫 عملیات لغو شد.",
        "choose_language": "🌐 لطفاً زبان خود را انتخاب کنید:",
        "lang_fa": "🇮🇷 فارسی",
        "lang_en": "🇬🇧 English",
        "invalid_media": "❌ لطفاً دقیقاً یک عکس یا یک ویدیو ارسال کن.",
        "send_another": "🚀 ارسال پیام جدید",
        "exit": "❌ پایان"
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
    await update.message.reply_text("🌐 لطفاً زبان خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_MODE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[-1]
    context.user_data["lang"] = lang
    context.user_data["buttons"] = []

    keyboard = [
        [InlineKeyboardButton(t(context, "choose_media"), callback_data="choose_media")],
        [InlineKeyboardButton(t(context, "choose_text"), callback_data="choose_text")],
    ]
    await query.edit_message_text(t(context, "start_message"), reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_MODE

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    return await start(query, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(t(context, "cancelled"))
    else:
        await update.message.reply_text(t(context, "cancelled"))
    context.user_data.clear()
    return ConversationHandler.END

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
        [InlineKeyboardButton(t(context, "edit_button"), callback_data="edit_button")],
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
    elif choice == "edit_button":
        buttons = context.user_data.get("buttons", [])
        if not buttons:
            await query.edit_message_text("⛔️ دکمه‌ای برای ویرایش وجود ندارد.")
            return CHOOSE_BUTTON_SEND

        keyboard = [
            [InlineKeyboardButton(f"{i+1}. {text}", callback_data=f"edit_{i}")]
            for i, (text, _) in enumerate(buttons)
        ]
        await query.edit_message_text(t(context, "select_button_to_edit"), reply_markup=InlineKeyboardMarkup(keyboard))
        return EDIT_BUTTON_SELECT
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
        [InlineKeyboardButton(t(context, "edit_button"), callback_data="edit_button")],
        [InlineKeyboardButton(t(context, "send_now"), callback_data="send_now")],
    ]
    await update.message.reply_text(t(context, "button_saved"), reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_BUTTON_SEND

async def edit_button_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split("_")[1])
    context.user_data["edit_index"] = index
    await query.edit_message_text(t(context, "enter_button_text_url"))
    return EDIT_BUTTON_TEXT

async def edit_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data.get("edit_index")
    text = update.message.text.split("\n")
    if len(text) != 2 or index is None:
        await update.message.reply_text(t(context, "invalid_button_format"))
        return EDIT_BUTTON_TEXT

    btn_text, btn_url = text[0].strip(), text[1].strip()
    context.user_data["buttons"][index] = (btn_text, btn_url)
    context.user_data.pop("edit_index", None)

    keyboard = [
        [InlineKeyboardButton(t(context, "add_button"), callback_data="add_button")],
        [InlineKeyboardButton(t(context, "edit_button"), callback_data="edit_button")],
        [InlineKeyboardButton(t(context, "send_now"), callback_data="send_now")],
    ]
    await update.message.reply_text(t(context, "button_edited"), reply_markup=InlineKeyboardMarkup(keyboard))
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

        keyboard = [
            [InlineKeyboardButton(t(context, "send_another"), callback_data="restart")],
            [InlineKeyboardButton(t(context, "exit"), callback_data="cancel")],
        ]
        await update.message.reply_text(t(context, "sent_success"), reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await update.message.reply_text(t(context, "send_error").format(error=e))

    return ConversationHandler.END

def main():
    TOKEN = os.getenv("BOT_TOKEN") or "Your token bot"
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_MODE: [
                CallbackQueryHandler(set_language, pattern="^lang_"),
                CallbackQueryHandler(mode_selection, pattern="^choose_"),
                CallbackQueryHandler(restart, pattern="^restart$"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
            RECEIVE_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO, receive_media)],
            WAIT_CAPTION: [CallbackQueryHandler(to_caption, pattern="^to_caption$")],
            RECEIVE_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption)],
            CHOOSE_BUTTON_SEND: [
                CallbackQueryHandler(handle_after_caption, pattern="^(add_button|send_now|edit_button)$")
            ],
            RECEIVE_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_button)],
            EDIT_BUTTON_SELECT: [CallbackQueryHandler(edit_button_select, pattern="^edit_\\d+$")],
            EDIT_BUTTON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_button_text)],
            RECEIVE_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)
    print("✅ Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
