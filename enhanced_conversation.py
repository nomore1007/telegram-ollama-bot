"""Enhanced conversation context management with long-term memory"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Enhanced conversation context with metadata"""
    user_id: int
    conversation_id: str
    messages: List[Dict[str, Any]]
    topics: List[str]
    entities: List[str]
    sentiment: str
    last_activity: datetime
    context_summary: str
    preferences: Dict[str, Any]
    memory_items: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['last_activity'] = self.last_activity.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary"""
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        return cls(**data)

class ContextAnalyzer:
    """Analyze conversation content for context extraction"""

    def __init__(self):
        # Topic keywords for categorization
        self.topic_keywords = {
            'coding': ['code', 'programming', 'python', 'javascript', 'function', 'class', 'debug', 'error'],
            'writing': ['write', 'essay', 'story', 'article', 'content', 'blog', 'document'],
            'learning': ['learn', 'study', 'course', 'tutorial', 'explain', 'understand', 'teach'],
            'technical': ['server', 'database', 'api', 'deployment', 'docker', 'kubernetes', 'aws'],
            'creative': ['design', 'art', 'music', 'creative', 'imagine', 'story', 'draw'],
            'business': ['business', 'marketing', 'sales', 'strategy', 'company', 'product'],
            'personal': ['feel', 'emotion', 'relationship', 'friend', 'family', 'life']
        }

        # Entity patterns
        self.entity_patterns = {
            'urls': r'https?://[^\s]+',
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'dates': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            'times': r'\b\d{1,2}:\d{2}(?:\s?[ap]m)?\b',
            'numbers': r'\b\d+(?:\.\d+)?\b'
        }

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze a single message for context"""
        analysis = {
            'topics': [],
            'entities': [],
            'sentiment': 'neutral',
            'keywords': [],
            'question_type': None
        }

        # Extract topics
        message_lower = message.lower()
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                analysis['topics'].append(topic)

        # Extract entities
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, message)
            if matches:
                analysis['entities'].extend([f"{entity_type}:{match}" for match in matches[:3]])  # Limit to 3

        # Basic sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'happy', 'awesome']
        negative_words = ['bad', 'terrible', 'hate', 'sad', 'angry', 'awful', 'horrible']

        pos_count = sum(1 for word in positive_words if word in message_lower)
        neg_count = sum(1 for word in negative_words if word in message_lower)

        if pos_count > neg_count:
            analysis['sentiment'] = 'positive'
        elif neg_count > pos_count:
            analysis['sentiment'] = 'negative'

        # Detect question types
        if message.startswith(('what', 'how', 'why', 'when', 'where', 'who', 'which')):
            analysis['question_type'] = 'factual'
        elif any(word in message_lower for word in ['explain', 'describe', 'tell me about']):
            analysis['question_type'] = 'explanatory'
        elif any(word in message_lower for word in ['help', 'assist', 'can you']):
            analysis['question_type'] = 'assistance'

        return analysis

    def generate_context_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a summary of the conversation context"""
        if not messages:
            return "New conversation"

        # Get last 5 messages for summary
        recent_messages = messages[-5:]

        # Extract key topics and themes
        all_topics = set()
        user_questions = []
        assistant_responses = []

        for msg in recent_messages:
            analysis = self.analyze_message(msg.get('content', ''))

            all_topics.update(analysis.get('topics', []))
            if msg.get('role') == 'user':
                if analysis.get('question_type'):
                    user_questions.append(msg.get('content', '')[:100])
            elif msg.get('role') == 'assistant':
                assistant_responses.append(msg.get('content', '')[:100])

        # Generate summary
        summary_parts = []

        if all_topics:
            summary_parts.append(f"Topics: {', '.join(list(all_topics)[:3])}")

        if user_questions:
            summary_parts.append(f"Recent questions: {len(user_questions)}")

        if assistant_responses:
            summary_parts.append(f"Assistant responses: {len(assistant_responses)}")

        return " | ".join(summary_parts) if summary_parts else "General conversation"

class EnhancedConversationManager:
    """Enhanced conversation manager with advanced context management"""

    def __init__(self, max_conversations_per_user: int = 10, max_messages_per_conversation: int = 100):
        self.max_conversations_per_user = max_conversations_per_user
        self.max_messages_per_conversation = max_messages_per_conversation
        self.context_analyzer = ContextAnalyzer()

        # In-memory storage (would be replaced with database in production)
        self.conversations: Dict[int, List[ConversationContext]] = defaultdict(list)
        self.user_preferences: Dict[int, Dict[str, Any]] = defaultdict(dict)

        logger.info("Enhanced ConversationManager initialized")

    async def add_message(self, user_id: int, content: str, role: str = 'user',
                         message_type: str = 'text') -> str:
        """Add a message to the user's current conversation"""
        # Get or create current conversation
        conversation = self._get_current_conversation(user_id)
        if not conversation:
            conversation = self._create_new_conversation(user_id)

        # Create message entry
        message = {
            'content': content,
            'role': role,
            'type': message_type,
            'timestamp': datetime.now(),
            'analysis': self.context_analyzer.analyze_message(content)
        }

        # Add to conversation
        conversation.messages.append(message)
        conversation.last_activity = datetime.now()

        # Update conversation metadata
        self._update_conversation_metadata(conversation, message)

        # Trim old messages if needed
        if len(conversation.messages) > self.max_messages_per_conversation:
            conversation.messages = conversation.messages[-self.max_messages_per_conversation:]

        # Clean up old conversations
        self._cleanup_old_conversations(user_id)

        logger.info(f"Added {role} message to user {user_id}'s conversation")
        return conversation.conversation_id

    async def get_context(self, user_id: int, system_prompt: str = "", max_tokens: int = 2000) -> str:
        """Get enhanced conversation context for AI processing"""
        conversation = self._get_current_conversation(user_id)
        if not conversation or not conversation.messages:
            return system_prompt

        # Build context from recent messages
        context_parts = []
        if system_prompt:
            context_parts.append(f"System: {system_prompt}")

        # Add conversation summary
        if conversation.context_summary:
            context_parts.append(f"Context: {conversation.context_summary}")

        # Add user preferences
        preferences = self.user_preferences.get(user_id, {})
        if preferences:
            pref_text = ", ".join([f"{k}: {v}" for k, v in preferences.items() if v])
            if pref_text:
                context_parts.append(f"User preferences: {pref_text}")

        # Add recent messages (within token limit)
        total_tokens = sum(len(part.split()) for part in context_parts)

        for message in reversed(conversation.messages):
            msg_text = f"{message['role'].title()}: {message['content']}"

            # Estimate tokens (rough approximation)
            msg_tokens = len(msg_text.split())
            if total_tokens + msg_tokens > max_tokens:
                break

            context_parts.insert(-1, msg_text)  # Insert before context summary
            total_tokens += msg_tokens

        return "\n\n".join(context_parts)

    async def get_memory_items(self, user_id: int, topic: str = None) -> List[Dict[str, Any]]:
        """Retrieve relevant memory items for context"""
        conversation = self._get_current_conversation(user_id)
        if not conversation:
            return []

        # Filter memory items by topic if specified
        memory_items = conversation.memory_items
        if topic:
            memory_items = [item for item in memory_items if topic in item.get('topics', [])]

        # Return most recent relevant items
        return sorted(memory_items, key=lambda x: x.get('timestamp', datetime.min), reverse=True)[:5]

    async def add_memory_item(self, user_id: int, content: str, importance: str = 'medium') -> None:
        """Add an important item to long-term memory"""
        conversation = self._get_current_conversation(user_id)
        if not conversation:
            conversation = self._create_new_conversation(user_id)

        analysis = self.context_analyzer.analyze_message(content)

        memory_item = {
            'content': content,
            'timestamp': datetime.now(),
            'importance': importance,
            'topics': analysis.get('topics', []),
            'entities': analysis.get('entities', []),
            'sentiment': analysis.get('sentiment', 'neutral')
        }

        conversation.memory_items.append(memory_item)

        # Keep only most important/recent memories
        conversation.memory_items.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}[x['importance']],
            x['timestamp']
        ), reverse=True)

        conversation.memory_items = conversation.memory_items[:20]  # Max 20 memories

        logger.info(f"Added memory item to user {user_id}")

    async def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> None:
        """Update user preferences for better responses"""
        self.user_preferences[user_id].update(preferences)
        logger.info(f"Updated preferences for user {user_id}: {preferences}")

    async def get_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about user's conversations"""
        conversations = self.conversations.get(user_id, [])
        total_messages = sum(len(conv.messages) for conv in conversations)
        total_memories = sum(len(conv.memory_items) for conv in conversations)

        return {
            'conversation_count': len(conversations),
            'total_messages': total_messages,
            'total_memories': total_memories,
            'active_topics': list(set(topic for conv in conversations for topic in conv.topics)),
            'last_activity': max((conv.last_activity for conv in conversations), default=None)
        }

    def _get_current_conversation(self, user_id: int) -> Optional[ConversationContext]:
        """Get the user's current active conversation"""
        conversations = self.conversations.get(user_id, [])
        if not conversations:
            return None

        # Return most recently active conversation
        return max(conversations, key=lambda c: c.last_activity)

    def _create_new_conversation(self, user_id: int) -> ConversationContext:
        """Create a new conversation for the user"""
        conversation_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"

        conversation = ConversationContext(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=[],
            topics=[],
            entities=[],
            sentiment='neutral',
            last_activity=datetime.now(),
            context_summary="",
            preferences={},
            memory_items=[]
        )

        self.conversations[user_id].append(conversation)

        # Clean up old conversations
        self._cleanup_old_conversations(user_id)

        return conversation

    def _update_conversation_metadata(self, conversation: ConversationContext,
                                    message: Dict[str, Any]) -> None:
        """Update conversation metadata based on new message"""
        analysis = message.get('analysis', {})

        # Update topics
        new_topics = analysis.get('topics', [])
        for topic in new_topics:
            if topic not in conversation.topics:
                conversation.topics.append(topic)

        # Update entities
        new_entities = analysis.get('entities', [])
        for entity in new_entities:
            if entity not in conversation.entities:
                conversation.entities.append(entity)

        # Update sentiment (simple majority)
        sentiments = [msg.get('analysis', {}).get('sentiment', 'neutral')
                     for msg in conversation.messages[-10:]]  # Last 10 messages
        if sentiments:
            conversation.sentiment = max(set(sentiments), key=sentiments.count)

        # Update context summary
        conversation.context_summary = self.context_analyzer.generate_context_summary(
            conversation.messages
        )

    def _cleanup_old_conversations(self, user_id: int) -> None:
        """Clean up old/inactive conversations"""
        conversations = self.conversations[user_id]

        # Keep only recent conversations
        cutoff_date = datetime.now() - timedelta(days=7)  # 7 days
        conversations[:] = [c for c in conversations if c.last_activity > cutoff_date]

        # Limit total conversations per user
        if len(conversations) > self.max_conversations_per_user:
            # Sort by activity and keep most recent
            conversations.sort(key=lambda c: c.last_activity, reverse=True)
            conversations[:] = conversations[:self.max_conversations_per_user]

# Global instance
enhanced_conversation_manager = EnhancedConversationManager()

__all__ = [
    'ConversationContext',
    'ContextAnalyzer',
    'EnhancedConversationManager',
    'enhanced_conversation_manager'
]