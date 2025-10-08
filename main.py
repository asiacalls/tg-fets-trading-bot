#!/usr/bin/env python3
"""
TG-Fets Trading Bot
A comprehensive Telegram bot for cryptocurrency trading and wallet management
"""

import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram import Update

from config import TELEGRAM_BOT_TOKEN, TRADING_STATES
from bot_handlers import BotHandlers, WAITING_FOR_PRIVATE_KEY, WAITING_FOR_TOKEN_ADDRESS

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot"""
    
    # Check if bot token is provided
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No Telegram bot token provided. Please set TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Initialize bot handlers
    bot_handlers = BotHandlers()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot_handlers.start_command))
    application.add_handler(CommandHandler("menu", bot_handlers.menu_command))
    
    # Add conversation handler for private key input
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_handlers.request_private_key, pattern="^import_wallet$")],
        states={
            WAITING_FOR_PRIVATE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_private_key_input)],
            WAITING_FOR_TOKEN_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_token_address_input)]
        },
        fallbacks=[CommandHandler("cancel", bot_handlers.cancel_conversation)]
    )
    application.add_handler(conv_handler)
    
    # Add conversation handler for token scanning
    token_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_handlers.request_token_address, pattern="^scan_token$")],
        states={
            WAITING_FOR_TOKEN_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_token_address_input)]
        },
        fallbacks=[CommandHandler("cancel", bot_handlers.cancel_conversation)]
    )
    application.add_handler(token_conv_handler)
    
    # Add conversation handler for trading - FIXED VERSION
    trading_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot_handlers.handle_trading_chain_selection, pattern="^trading_chain_")
        ],
        states={
            TRADING_STATES['WAITING_FOR_AMOUNT']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.request_trade_amount)
            ],
            TRADING_STATES['WAITING_FOR_TOKEN_ADDRESS']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.request_token_address_for_trade)
            ],
            TRADING_STATES['WAITING_FOR_TRADE_CONFIRMATION']: [
                CallbackQueryHandler(bot_handlers.execute_trade, pattern="^confirm_trade$"),
                CallbackQueryHandler(bot_handlers.cancel_trade, pattern="^cancel_trade$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(bot_handlers.cancel_trade, pattern="^cancel_trade$"),
            CallbackQueryHandler(bot_handlers.show_main_menu, pattern="^main_menu$"),
            CommandHandler("cancel", bot_handlers.cancel_conversation)
        ]
    )
    application.add_handler(trading_conv_handler)
    
    # Add callback query handler for all inline keyboard interactions
    application.add_handler(CallbackQueryHandler(bot_handlers.handle_callback_query))
    
    # Add error handler
    application.add_error_handler(bot_handlers.error_handler)
    
    # Start the bot
    logger.info("Starting TG-Fets Trading Bot...")
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    try:
        # Run the bot until stopped
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    main()
