"""
Weather Plugin for Telegram Ollama Bot
Provides weather information using OpenWeatherMap API
"""

import logging
import aiohttp
import time
from typing import List, Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes

from .base import Plugin

logger = logging.getLogger(__name__)


class WeatherPlugin(Plugin):
    """Plugin that provides weather information"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 600  # 10 minutes cache
        logger.info("Weather plugin initialized")

    def initialize(self, bot_instance) -> None:
        """Initialize the plugin with bot instance"""
        super().initialize(bot_instance)

    @property
    def api_key(self) -> Optional[str]:
        """Get the OpenWeatherMap API key from config"""
        return self.config.get('api_key')

    def _get_cached_weather(self, city: str) -> Optional[str]:
        """Get cached weather response if available and not expired"""
        cache_key = city.lower()
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['response']
            else:
                # Remove expired cache
                del self.cache[cache_key]
        return None

    def _cache_weather(self, city: str, response: str) -> None:
        """Cache weather response"""
        cache_key = city.lower()
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return ["weather"]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🌤️ *Weather Plugin*\n\n"
            "`/weather <city>` - Get current weather and forecast\n\n"
            "*Examples:*\n"
            "• `/weather New York`\n"
            "• `/weather London,UK`\n"
            "• `/weather Tokyo`\n\n"
            "*Note:* Requires OpenWeatherMap API key configuration"
        )

    async def handle_weather(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weather command"""
        if not update.message:
            return

        if not self.api_key:
            await update.message.reply_text(
                "❌ Weather plugin not configured.\n\n"
                "Please set OPENWEATHERMAP_API_KEY in your environment variables.",
                parse_mode="Markdown"
            )
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please specify a city.\n\n"
                "💡 *Usage:* `/weather <city>`\n"
                "📝 *Example:* `/weather New York`",
                parse_mode="Markdown"
            )
            return

        city = " ".join(context.args)
        logger.info(f"Getting weather for: {city}")

        # Check cache first
        cached_data = self._get_cached_weather(city)
        if cached_data:
            logger.info(f"Using cached weather data for: {city}")
            await update.message.reply_text(cached_data, parse_mode="Markdown")
            return

        try:
            # Get current weather
            current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
            async with aiohttp.ClientSession() as session:
                async with session.get(current_url) as response:
                    if response.status != 200:
                        await update.message.reply_text(f"❌ City '{city}' not found or API error.")
                        return

                    current_data = await response.json()

            # Get 5-day forecast
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.api_key}&units=metric"
            async with aiohttp.ClientSession() as session:
                async with session.get(forecast_url) as response:
                    forecast_data = await response.json() if response.status == 200 else None

            # Format current weather
            weather = current_data['weather'][0]
            main = current_data['main']
            wind = current_data['wind']

            response = (
                f"🌤️ *Weather for {current_data['name']}, {current_data['sys']['country']}*\n\n"
                f"📊 *Current Conditions:*\n"
                f"• Weather: {weather['description'].title()}\n"
                f"• Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)\n"
                f"• Humidity: {main['humidity']}%\n"
                f"• Wind: {wind['speed']} m/s\n"
                f"• Pressure: {main['pressure']} hPa\n\n"
            )

            # Add forecast if available
            if forecast_data and 'list' in forecast_data:
                response += "📅 *5-Day Forecast:*\n"
                daily_forecasts = {}

                # Group by date
                for item in forecast_data['list'][:16]:  # Next 2 days worth
                    date = item['dt_txt'].split()[0]
                    if date not in daily_forecasts:
                        daily_forecasts[date] = item

                for date, data in list(daily_forecasts.items())[:3]:  # Show next 3 days
                    temp = data['main']['temp']
                    desc = data['weather'][0]['description'].title()
                    response += f"• {date}: {temp}°C, {desc}\n"

            await update.message.reply_text(response, parse_mode="Markdown")

            # Cache the response
            self._cache_weather(city, response)

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            await update.message.reply_text("❌ Error fetching weather data. Please try again later.")