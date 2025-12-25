import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working! Type /buttons to test inline buttons.")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Test Button 1", callback_data="test1")],
        [InlineKeyboardButton("Test Button 2", callback_data="test2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Test buttons:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=== CALLBACK RECEIVED ===")
    try:
        query = update.callback_query
        logger.info(f"Query object: {query}")
        logger.info(f"Query data: {query.data}")
        logger.info(f"Query type: {type(query)}")
        
        await query.answer()
        logger.info("Answer sent successfully")
        
        await query.edit_message_text(f"You clicked: {query.data}")
        logger.info("Message edited successfully")
        
    except Exception as e:
        logger.error(f"Error in callback: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            if 'query' in locals():
                await query.answer()
                logger.info("Answer sent in error handler")
        except Exception as e2:
            logger.error(f"Error in error handler: {e2}")

def main():
    app = Application.builder().token("8169504801:AAFRVaabKhHR14D9AFEAnSFFj-9Br89OORE").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buttons", buttons))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Starting test bot...")
    app.run_polling()

if __name__ == "__main__":
    main()