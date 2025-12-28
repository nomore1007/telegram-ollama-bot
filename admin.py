"""
Admin system for managing bot administrators.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class AdminManager:
    """Manages bot administrators and permissions."""

    def __init__(self, admin_user_ids: Optional[List[int]] = None):
        self.admin_user_ids = set(admin_user_ids or [])
        self.allow_initial_setup = len(self.admin_user_ids) == 0  # Allow setup if no admins exist

    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an administrator."""
        return user_id in self.admin_user_ids

    def add_admin(self, user_id: int, requesting_user_id: Optional[int] = None, force: bool = False) -> bool:
        """Add a new admin.

        Args:
            user_id: The user ID to add as admin
            requesting_user_id: User ID making the request (None for initial setup)
            force: Force add without permission checks (for CLI/setup use)
        """
        # Allow initial setup if no admins exist
        if self.allow_initial_setup and requesting_user_id is None:
            self.admin_user_ids.add(user_id)
            self.allow_initial_setup = len(self.admin_user_ids) == 0  # Update flag
            logger.info(f"Added initial admin: {user_id}")
            return True

        # Force add (for CLI/admin scripts)
        if force:
            self.admin_user_ids.add(user_id)
            logger.info(f"Force added admin: {user_id}")
            return True

        # Normal admin check
        if requesting_user_id is None or not self.is_admin(requesting_user_id):
            return False

        self.admin_user_ids.add(user_id)
        logger.info(f"Added admin: {user_id}")
        return True

    def remove_admin(self, user_id: int, requesting_user_id: Optional[int] = None, force: bool = False) -> bool:
        """Remove an admin.

        Args:
            user_id: The user ID to remove from admins
            requesting_user_id: User ID making the request (None for CLI)
            force: Force remove without permission checks (for CLI/admin scripts)
        """
        # Force remove (for CLI/admin scripts)
        if force:
            if user_id in self.admin_user_ids:
                self.admin_user_ids.discard(user_id)
                logger.info(f"Force removed admin: {user_id}")
                return True
            return False

        # Normal admin check
        if requesting_user_id is None or not self.is_admin(requesting_user_id):
            return False

        # Prevent removing the last admin
        if len(self.admin_user_ids) <= 1:
            return False

        self.admin_user_ids.discard(user_id)
        logger.info(f"Removed admin: {user_id}")
        return True

    def get_admins(self) -> List[int]:
        """Get list of all admin user IDs."""
        return list(self.admin_user_ids)

def require_admin(func):
    """Decorator to require admin permissions for a plugin method."""
    async def wrapper(self, update, context, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if not user_id or not self.bot_instance.admin_manager.is_admin(user_id):
            response = "❌ This command requires administrator privileges."
            if update.message:
                await update.message.reply_text(response)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(response)
            return None
        return await func(self, update, context, *args, **kwargs)
    return wrapper