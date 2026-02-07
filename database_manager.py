"""Manages database interactions for the Telegram Ollama Bot."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, ChannelSettings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connection and channel-specific settings."""

    def __init__(self, config):
        self.config = config
        self.db_engine = None
        self.db_session = None
        self.channel_settings_cache = {}  # In-memory cache for per-channel settings

        self._init_database()
        self._load_channel_settings()

    def _init_database(self):
        """Initialize database connection and create tables."""
        config_dir_path = self.config.BOT_CONFIG_DIR
        db_file_path = config_dir_path / 'deepthought_bot.db'
        database_url = self.config.get('DATABASE_URL', f'sqlite:///{db_file_path}')
        self.db_engine = create_engine(database_url, echo=False)
        self.db_session = sessionmaker(bind=self.db_engine)

        # Create tables
        Base.metadata.create_all(self.db_engine)
        logger.info("Database initialized")

    def _load_channel_settings(self):
        """Load channel settings from database."""
        session = self.db_session()
        try:
            settings = session.query(ChannelSettings).all()
            for setting in settings:
                self.channel_settings_cache[setting.channel_id] = {
                    'provider': setting.provider,
                    'model': setting.model,
                    'host': setting.host,
                    'prompt': setting.prompt
                }
            logger.info(f"Loaded {len(settings)} channel settings from database")
        except Exception as e:
            logger.error(f"Error loading channel settings: {e}")
        finally:
            session.close()

    def save_channel_setting(self, channel_id: str, key: str, value):
        """Save a channel setting to database and memory cache."""
        session = self.db_session()
        try:
            # Get or create channel settings record
            channel_setting = session.query(ChannelSettings).filter_by(channel_id=channel_id).first()
            if not channel_setting:
                channel_setting = ChannelSettings(channel_id=channel_id)
                session.add(channel_setting)

            # Update the setting
            setattr(channel_setting, key, value)
            session.commit()

            # Update in-memory cache
            if channel_id not in self.channel_settings_cache:
                self.channel_settings_cache[channel_id] = {}
            self.channel_settings_cache[channel_id][key] = value

            logger.debug(f"Saved channel setting {channel_id}.{key} = {value}")

        except Exception as e:
            logger.error(f"Error saving channel setting: {e}")
            session.rollback()
        finally:
            session.close()

    def get_channel_setting(self, channel_id: str, key: str, default=None):
        """Get a channel setting from cache, falling back to global default if not set."""
        channel_settings = self.channel_settings_cache.get(channel_id, {})

        # If channel has the setting, return it
        if key in channel_settings and channel_settings[key] is not None:
            return channel_settings[key]
        
        return default