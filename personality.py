"""
Personality system for the bot - different conversation modes and styles.
"""

import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class Personality(Enum):
    """Available bot personalities"""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    HELPFUL = "helpful"
    CREATIVE = "creative"
    CONCISE = "concise"


class PersonalityManager:
    """Manages bot personalities and conversation styles."""

    def __init__(self):
        self.personalities = self._load_personalities()

    def _load_personalities(self) -> Dict[Personality, Dict[str, str]]:
        """Load personality configurations."""
        return {
            Personality.FRIENDLY: {
                "name": "Friendly",
                "prompt": "You are a friendly and approachable AI assistant. Use warm, conversational language and be encouraging. Add emojis occasionally to make responses more engaging.",
                "description": "Warm and friendly responses with emojis"
            },
            Personality.PROFESSIONAL: {
                "name": "Professional",
                "prompt": "You are a professional AI assistant. Provide clear, accurate, and well-structured responses. Use formal language and maintain objectivity.",
                "description": "Formal and professional responses"
            },
            Personality.HUMOROUS: {
                "name": "Humorous",
                "prompt": "You are a witty and humorous AI assistant. Use clever wordplay, jokes, and light-hearted responses while still being helpful and accurate.",
                "description": "Funny and entertaining responses"
            },
            Personality.HELPFUL: {
                "name": "Helpful",
                "prompt": "You are an exceptionally helpful AI assistant. Focus on being maximally useful, providing detailed explanations and offering additional assistance when possible.",
                "description": "Maximally helpful and detailed responses"
            },
            Personality.CREATIVE: {
                "name": "Creative",
                "prompt": "You are a creative and imaginative AI assistant. Think outside the box, offer innovative solutions, and express ideas in engaging, creative ways.",
                "description": "Creative and innovative responses"
            },
            Personality.CONCISE: {
                "name": "Concise",
                "prompt": "You are a concise AI assistant. Provide accurate information in the most efficient way possible. Be direct and avoid unnecessary elaboration.",
                "description": "Brief and to-the-point responses"
            }
        }

    def get_personality(self, personality: Personality) -> Dict[str, str]:
        """Get personality configuration."""
        return self.personalities.get(personality, self.personalities[Personality.HELPFUL])

    def get_system_prompt(self, personality: Personality, base_prompt: str = "") -> str:
        """Get the full system prompt for a personality."""
        personality_config = self.get_personality(personality)

        if base_prompt:
            return f"{personality_config['prompt']}\n\n{base_prompt}"
        else:
            return personality_config['prompt']

    def list_personalities(self) -> Dict[str, Dict[str, str]]:
        """List all available personalities."""
        return {
            p.value: {
                "name": config["name"],
                "description": config["description"]
            }
            for p, config in self.personalities.items()
        }


# Global personality manager instance
personality_manager = PersonalityManager()