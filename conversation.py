"""Conversation context management for maintaining chat history"""

import logging
from collections import defaultdict, deque
from typing import Dict, List, Deque, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    token_count: Optional[int] = None


class ConversationManager:
    """Manages conversation history for users"""

    def __init__(
        self,
        max_messages_per_user: int = 50,
        max_age_hours: int = 24,
        max_context_length: int = 4000
    ):
        self.max_messages_per_user = max_messages_per_user
        self.max_age_hours = max_age_hours
        self.max_context_length = max_context_length

        # Store conversations per user (chat_id -> deque of messages)
        self.conversations: Dict[int, Deque[Message]] = defaultdict(
            lambda: deque(maxlen=max_messages_per_user)
        )

        logger.info(f"ConversationManager initialized with max_messages={max_messages_per_user}, max_age={max_age_hours}h")

    def add_user_message(self, chat_id: int, content: str) -> None:
        """Add a user message to conversation history"""
        message = Message(
            role="user",
            content=content,
            timestamp=datetime.now()
        )
        self.conversations[chat_id].append(message)
        self._cleanup_old_messages(chat_id)
        logger.debug(f"Added user message to chat {chat_id}")

    def add_assistant_message(self, chat_id: int, content: str) -> None:
        """Add an assistant message to conversation history"""
        message = Message(
            role="assistant",
            content=content,
            timestamp=datetime.now()
        )
        self.conversations[chat_id].append(message)
        self._cleanup_old_messages(chat_id)
        logger.debug(f"Added assistant message to chat {chat_id}")

    def get_context(self, chat_id: int, system_prompt: str = "") -> str:
        """Get conversation context as formatted string"""
        messages = list(self.conversations[chat_id])

        if not messages:
            return system_prompt

        # Build context string
        context_parts = []
        if system_prompt:
            context_parts.append(system_prompt)

        total_length = len(system_prompt)

        # Add messages in chronological order
        for msg in messages:
            msg_text = f"{msg.role.title()}: {msg.content}\n"
            msg_length = len(msg_text)

            # Check if adding this message would exceed context limit
            if total_length + msg_length > self.max_context_length:
                logger.info(f"Context limit reached for chat {chat_id}, truncating history")
                break

            context_parts.append(msg_text)
            total_length += msg_length

        return "\n".join(context_parts)

    def clear_conversation(self, chat_id: int) -> None:
        """Clear conversation history for a user"""
        if chat_id in self.conversations:
            self.conversations[chat_id].clear()
            logger.info(f"Cleared conversation history for chat {chat_id}")

    def get_conversation_stats(self, chat_id: int) -> dict:
        """Get statistics about a conversation"""
        messages = list(self.conversations[chat_id])
        if not messages:
            return {"message_count": 0, "oldest_message": None, "newest_message": None}

        return {
            "message_count": len(messages),
            "oldest_message": messages[0].timestamp,
            "newest_message": messages[-1].timestamp
        }

    def _cleanup_old_messages(self, chat_id: int) -> None:
        """Remove messages older than max_age_hours"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        conversation = self.conversations[chat_id]

        # Remove old messages from the left (oldest)
        while conversation and conversation[0].timestamp < cutoff_time:
            removed_msg = conversation.popleft()
            logger.debug(f"Removed old message from chat {chat_id}: {removed_msg.timestamp}")

    def cleanup_all_conversations(self) -> None:
        """Clean up old messages across all conversations"""
        for chat_id in list(self.conversations.keys()):
            self._cleanup_old_messages(chat_id)
            # Remove empty conversations
            if not self.conversations[chat_id]:
                del self.conversations[chat_id]

        logger.info("Cleaned up old messages across all conversations")