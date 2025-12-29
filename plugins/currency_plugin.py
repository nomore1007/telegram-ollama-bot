"""
Currency Converter Plugin for Telegram Ollama Bot
Provides real-time currency conversion using free APIs
"""

import logging
import re
from typing import List
from telegram import Update
from telegram.ext import ContextTypes

from .base import Plugin

logger = logging.getLogger(__name__)


class CurrencyPlugin(Plugin):
    """Plugin that provides currency conversion functionality"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        logger.info("Currency plugin initialized")

    def initialize(self, bot_instance) -> None:
        """Initialize the plugin with bot instance"""
        super().initialize(bot_instance)

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return ["convert", "currency", "exchange"]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "💱 *Currency Converter Plugin*\n\n"
            "`/convert <amount> <from_currency> to <to_currency>` - Convert currency\n"
            "`/currency <amount> <from> <to>` - Same as convert\n"
            "`/exchange <amount> <from> <to>` - Same as convert\n\n"
            "*Examples:*\n"
            "• `/convert 100 USD to EUR`\n"
            "• `/convert 50 GBP to JPY`\n"
            "• `/convert 1000 CNY to USD`\n\n"
            "*Supported Currencies:*\n"
            "USD, EUR, GBP, JPY, CNY, CAD, AUD, CHF, SEK, NOK, DKK, PLN, CZK, HUF, RON, BGN, HRK, RUB, TRY, ILS, ZAR, MXN, BRL, ARS, CLP, COP, PEN, UYU, etc.\n\n"
            "*Note:* Uses real-time exchange rates from free API"
        )

    async def handle_convert(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /convert command"""
        await self._convert_currency(update, context)

    async def handle_currency(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /currency command"""
        await self._convert_currency(update, context)

    async def handle_exchange(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /exchange command"""
        await self._convert_currency(update, context)

    async def _convert_currency(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle currency conversion logic"""
        if not update.message:
            return

        if not context.args or len(context.args) < 4:
            await update.message.reply_text(
                "❌ Please provide conversion details.\n\n"
                "💡 *Usage:* `/convert <amount> <from_currency> to <to_currency>`\n"
                "📝 *Example:* `/convert 100 USD to EUR`\n\n"
                "Use `/convert help` for more examples.",
                parse_mode="Markdown"
            )
            return

        args = context.args

        if args[0].lower() == 'help':
            await update.message.reply_text(self.get_help_text(), parse_mode="Markdown")
            return

        # Parse the arguments
        # Support formats: "100 USD to EUR" or "100 USD EUR"
        amount_str = args[0]
        from_currency = args[1].upper()

        # Check if third argument is "to" or the target currency
        if len(args) >= 4 and args[2].lower() == 'to':
            to_currency = args[3].upper()
        elif len(args) >= 3:
            to_currency = args[2].upper()
        else:
            await update.message.reply_text(
                "❌ Invalid format.\n\n"
                "💡 *Usage:* `/convert <amount> <from_currency> to <to_currency>`",
                parse_mode="Markdown"
            )
            return

        try:
            amount = float(amount_str)
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a number.")
            return

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0.")
            return

        # Validate currency codes (basic check)
        if len(from_currency) != 3 or len(to_currency) != 3:
            await update.message.reply_text("❌ Invalid currency codes. Use 3-letter codes like USD, EUR, GBP.")
            return

        try:
            # Use exchangerate-api.com (free, no API key required)
            import aiohttp

            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        await update.message.reply_text("❌ Unable to fetch exchange rates. Please try again later.")
                        return

                    data = await response.json()

                    if 'rates' not in data:
                        await update.message.reply_text("❌ Invalid response from exchange rate service.")
                        return

                    rates = data['rates']

                    if to_currency not in rates:
                        await update.message.reply_text(f"❌ Unsupported currency: {to_currency}")
                        return

                    # Get exchange rate
                    rate = rates[to_currency]

                    # Calculate converted amount
                    converted_amount = amount * rate

                    # Format response
                    response_text = (
                        f"💱 *Currency Conversion*\n\n"
                        f"• Amount: `{amount:,.2f} {from_currency}`\n"
                        f"• To: `{to_currency}`\n"
                        f"• Rate: `1 {from_currency} = {rate:.4f} {to_currency}`\n"
                        f"• Result: `{converted_amount:,.2f} {to_currency}`\n\n"
                        f"📊 *Exchange Rate Data*\n"
                        f"• Base: `{data.get('base', from_currency)}`\n"
                        f"• Last Updated: `{data.get('date', 'Unknown')}`"
                    )

                    await update.message.reply_text(response_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            await update.message.reply_text("❌ Error performing currency conversion. Please try again later.")