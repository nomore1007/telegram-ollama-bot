"""
Discord plugin for the Telegram Ollama Bot.

This plugin handles Discord bot functionality.
"""

import logging
from typing import Optional, List

import discord
from discord.ext import commands

from .base import Plugin


logger = logging.getLogger(__name__)


class DiscordPlugin(Plugin):
    """Plugin that handles Discord bot functionality."""

    def __init__(self, name: str, config: Optional[dict] = None):
        super().__init__(name, config)
        self.bot_instance = None
        self.discord_bot = None

    def initialize(self, bot_instance) -> None:
        """Initialize the plugin with the bot instance."""
        self.bot_instance = bot_instance
        logger.info("Discord plugin initialized")

        # Create Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        self.discord_bot = commands.Bot(command_prefix='!', intents=intents)

        # Register commands
        self._register_commands()

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return ["ask", "model", "search", "addadmin", "removeadmin", "listadmins"]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🤖 *Deepthought Discord Bot - Command Guide*\n\n"
            "💬 *AI Chat:*\n"
            "`!ask <message>` - Direct AI conversation\n"
            "Just mention me in any message for AI responses!\n\n"
            "🔍 *Web Search:*\n"
            "`!search <query>` - Real-time web search with AI analysis\n"
            "*Examples:*\n"
            "• `!search latest gaming news`\n"
            "• `!search Discord bot development`\n\n"
             "⚙️ *Bot Information:*\n"
             "`!model` - Show current AI model and provider\n\n"
             "👑 *Admin Commands (Admin Only):*\n"
             "`!addadmin @user` - Add a user as administrator\n"
             "`!removeadmin @user` - Remove administrator privileges\n"
             "`!listadmins` - Show all bot administrators\n\n"
            "📱 *Auto-Features (Always Active):*\n"
            "📰 *News URLs* - Automatic article summarization\n"
            "🎬 *YouTube Links* - Automatic video analysis\n"
            "💡 *Smart Context* - Remembers conversation history\n\n"
            "🔒 *Security:*\n"
            "• Input validation and content filtering\n"
            "• Rate limiting and abuse prevention\n"
            "• Safe URL handling and content sanitization\n\n"
            "💡 *Pro Tips:*\n"
            "• Use detailed search queries for better results\n"
            "• Combine with context for specialized responses\n"
            "• Bot responds to mentions and direct messages"
        )

    def _register_commands(self):
        """Register Discord commands."""

        @self.discord_bot.event
        async def on_ready():
            logger.info(f'Discord bot logged in as {self.discord_bot.user}')

        @self.discord_bot.command(name='ask')
        async def ask(ctx, *, message: str):
            """Ask AI a question."""
            try:
                # Process message similar to Telegram
                response = await self._process_message(message, ctx.author.mention)
                await ctx.send(response)
            except Exception as e:
                logger.error(f"Discord ask error: {e}")
                await ctx.send("❌ Error processing request.")

        @self.discord_bot.command(name='model')
        async def model(ctx):
            """Show current model."""
            try:
                model_info = f"🧠 Model: `{self.bot_instance.llm.model}`\n🌐 Provider: `{self.bot_instance.llm.provider_name}`"
                await ctx.send(model_info)
            except Exception as e:
                logger.error(f"Discord model error: {e}")
                await ctx.send("❌ Error getting model info.")

        @self.discord_bot.command(name='search')
        async def search(ctx, *, query: str):
            """Search the web."""
            try:
                await ctx.send("🔍 Searching the web...")
                search_results = await self._perform_web_search(query)
                response = await self.bot_instance.llm.generate(f"Based on these search results, answer: {query}\n\n{search_results}")
                await ctx.send(response[:2000])  # Discord message limit
            except Exception as e:
                logger.error(f"Discord search error: {e}")
                await ctx.send("❌ Error performing search.")

        @self.discord_bot.command(name='addadmin')
        async def addadmin(ctx, member: discord.Member = None):
            """Add an admin (admin only)."""
            if ctx.author.id not in self.bot_instance.admin_manager.get_admins():
                await ctx.send("❌ You are not authorized to manage admins.")
                return

            if not member:
                await ctx.send("❌ Usage: `!addadmin @user`")
                return

            user_id = member.id
            if self.bot_instance.admin_manager.add_admin(user_id, ctx.author.id):
                await ctx.send(f"✅ Added {member.mention} as administrator.")
            else:
                await ctx.send("❌ Failed to add admin.")

        @self.discord_bot.command(name='removeadmin')
        async def removeadmin(ctx, member: discord.Member = None):
            """Remove an admin (admin only)."""
            if ctx.author.id not in self.bot_instance.admin_manager.get_admins():
                await ctx.send("❌ You are not authorized to manage admins.")
                return

            if not member:
                await ctx.send("❌ Usage: `!removeadmin @user`")
                return

            user_id = member.id
            if self.bot_instance.admin_manager.remove_admin(user_id, ctx.author.id):
                await ctx.send(f"✅ Removed {member.mention} from administrators.")
            else:
                await ctx.send("❌ Failed to remove admin.")

        @self.discord_bot.command(name='listadmins')
        async def listadmins(ctx):
            """List all admins (admin only)."""
            if ctx.author.id not in self.bot_instance.admin_manager.get_admins():
                await ctx.send("❌ You are not authorized to manage admins.")
                return

            admins = self.bot_instance.admin_manager.get_admins()
            if not admins:
                await ctx.send("👑 No administrators configured.")
            else:
                admin_list = "\n".join(f"• <@{admin_id}>" for admin_id in admins)
                await ctx.send(f"👑 **Bot Administrators**\n{admin_list}")

        @self.discord_bot.event
        async def on_message(message):
            if message.author == self.discord_bot.user:
                return

            # Check for URLs and process automatically
            content = message.content

            # News URLs
            news_urls = self.bot_instance.news_summarizer.extract_news_urls(content)
            if news_urls:
                await message.channel.send("📰 News detected! Summarizing...")
                for url in news_urls[:2]:  # Limit
                    try:
                        summary = await self.bot_instance.news_summarizer.summarize_url(url)
                        await message.channel.send(f"📄 **{summary['title']}**\n{summary['summary'][:1500]}...")
                    except Exception as e:
                        logger.error(f"News summary error: {e}")

            # YouTube URLs
            yt_urls = self.bot_instance.youtube_summarizer.extract_video_urls(content)
            if yt_urls:
                await message.channel.send("🎬 YouTube video detected! Summarizing...")
                for url in yt_urls[:2]:  # Limit
                    try:
                        summary = await self.bot_instance.youtube_summarizer.summarize_url(url)
                        await message.channel.send(f"🎥 **{summary['title']}**\n{summary['summary'][:1500]}...")
                    except Exception as e:
                        logger.error(f"YouTube summary error: {e}")

            await self.discord_bot.process_commands(message)

    async def _process_message(self, message: str, mention: str) -> str:
        """Process a message and return AI response."""
        try:
            # Check for bot mention (similar to Telegram group chat)
            if mention in message:
                message = message.replace(mention, "").strip()

            # Generate context and respond
            context = self.bot_instance.conversation_manager.build_context(message, user_id=str(mention))
            response = await self.bot_instance.llm.generate(context)

            # Store in conversation
            self.bot_instance.conversation_manager.add_message(str(mention), "user", message)
            self.bot_instance.conversation_manager.add_message(str(mention), "assistant", response)

            return response[:4000]  # Discord limit
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            return "❌ Error processing message."

    async def _perform_web_search(self, query: str) -> str:
        """Perform web search (mock for now)."""
        # TODO: Implement real web search
        return f"Mock search results for: {query}"

    def run_discord_bot(self, token: str):
        """Run the Discord bot."""
        if self.discord_bot:
            self.discord_bot.run(token)