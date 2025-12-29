"""
Trivia Plugin for Telegram Ollama Bot
Provides trivia questions and quizzes
"""

import logging
import random
import json
from typing import List, Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes

from .base import Plugin

logger = logging.getLogger(__name__)


class TriviaPlugin(Plugin):
    """Plugin that provides trivia questions and quizzes"""

    def __init__(self, name: str, config: Optional[dict] = None):
        super().__init__(name, config)
        self.questions = self._load_questions()
        logger.info("Trivia plugin initialized")

    def initialize(self, bot_instance) -> None:
        """Initialize the plugin with bot instance"""
        super().initialize(bot_instance)

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return ["trivia", "quiz", "question"]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🧠 *Trivia Plugin*\n\n"
            "`/trivia` - Start a trivia quiz with random questions\n"
            "`/trivia <category>` - Start trivia in specific category\n"
            "`/quiz` - Alias for /trivia\n"
            "`/question` - Get a single random question\n\n"
            "*Available Categories:*\n"
            "• General Knowledge\n"
            "• Science\n"
            "• History\n"
            "• Geography\n"
            "• Sports\n"
            "• Entertainment\n"
            "• Technology\n\n"
            "*How to Play:*\n"
            "• Bot will ask a question\n"
            "• Reply with your answer\n"
            "• Bot will tell you if you're correct\n"
            "• Use `/trivia` to start a 5-question quiz\n\n"
            "*Scoring:*\n"
            "• Correct answers give you points\n"
            "• Try to get the highest score!"
        )

    async def handle_trivia(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trivia command"""
        await self._start_trivia(update, context)

    async def handle_quiz(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz command"""
        await self._start_trivia(update, context)

    async def handle_question(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /question command - single question"""
        if not update.message:
            return

        question = await self._generate_question()
        if not question:
            await update.message.reply_text("❌ Unable to generate trivia question.")
            return

        # Store the question in user context for checking answer
        if context.user_data is not None:
            context.user_data['current_question'] = question

        await update.message.reply_text(
            f"🧠 *Trivia Question*\n\n"
            f"**{question['question']}**\n\n"
            f"💡 *Hint:* Reply with your answer!",
            parse_mode="Markdown"
        )

    async def _start_trivia(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Start a trivia quiz"""
        if not update.message:
            return

        # Check for category
        category = None
        if context.args:
            category_input = " ".join(context.args).lower()
            available_categories = self._get_categories()

            # Find matching category
            for cat in available_categories:
                if category_input in cat.lower():
                    category = cat
                    break

            if not category and category_input != "help":
                await update.message.reply_text(
                    f"❌ Category '{category_input}' not found.\n\n"
                    f"📋 Available categories: {', '.join(available_categories)}\n\n"
                    f"Use `/trivia` for random questions or `/trivia help` for more info."
                )
                return

        if context.args and context.args[0].lower() == 'help':
            await update.message.reply_text(self.get_help_text(), parse_mode="Markdown")
            return

        # Start quiz
        if context.user_data is not None:
            context.user_data['quiz_active'] = True
            context.user_data['quiz_score'] = 0
            context.user_data['quiz_questions'] = 0
            context.user_data['quiz_category'] = category

        category_text = f" in *{category}*" if category else ""
        await update.message.reply_text(
            f"🎯 *Trivia Quiz Started!*{category_text}\n\n"
            f"📊 I'll ask you 5 questions.\n"
            f"💬 Reply with your answers.\n"
            f"🏆 Try to get the highest score!\n\n"
            f"Ready? Let's begin!",
            parse_mode="Markdown"
        )

        # Ask first question
        await self.ask_next_question(update, context)

    async def ask_next_question(self, update, context):
        """Ask the next question in the quiz"""
        if context.user_data is None:
            return

        quiz_active = context.user_data.get('quiz_active', False)
        if not quiz_active:
            return

        questions_asked = context.user_data.get('quiz_questions', 0)
        if questions_asked >= 5:
            # Quiz finished
            score = context.user_data.get('quiz_score', 0)
            await self._end_quiz(update, context, score)
            return

        # Get question based on category
        category = context.user_data.get('quiz_category')
        question = await self._generate_question(category)

        if not question:
            await update.message.reply_text("❌ No more questions available. Quiz ended.")
            await self._end_quiz(update, context, context.user_data.get('quiz_score', 0))
            return

        # Store question
        context.user_data['current_question'] = question
        context.user_data['quiz_questions'] = questions_asked + 1

        question_num = questions_asked + 1
        await update.message.reply_text(
            f"🧠 *Question {question_num}/5*\n\n"
            f"**{question['question']}**\n\n"
            f"💡 *Reply with your answer!*",
            parse_mode="Markdown"
        )

    async def _end_quiz(self, update, context, score):
        """End the quiz and show final score"""
        if context.user_data is not None:
            context.user_data['quiz_active'] = False

        total_questions = 5
        percentage = (score / total_questions) * 100

        # Determine message based on score
        if percentage >= 80:
            emoji = "🏆"
            message = "Excellent! You're a trivia master!"
        elif percentage >= 60:
            emoji = "🥈"
            message = "Great job! Well done!"
        elif percentage >= 40:
            emoji = "🥉"
            message = "Not bad! Keep practicing!"
        else:
            emoji = "💪"
            message = "Keep trying! Everyone starts somewhere!"

        await update.message.reply_text(
            f"{emoji} *Quiz Complete!*\n\n"
            f"📊 *Final Score:* {score}/{total_questions} ({percentage:.1f}%)\n\n"
            f"🎉 {message}\n\n"
            f"Want to play again? Use `/trivia`!",
            parse_mode="Markdown"
        )

    def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance) -> Optional[str]:
        """Check if message is an answer to a trivia question"""
        # This method is not currently called by the bot architecture
        # Trivia functionality is handled through commands only
        return None

    def _load_questions(self) -> List[Dict[str, Any]]:
        """Load trivia questions (built-in questions for now)"""
        return [
            # General Knowledge
            {"question": "What is the capital of France?", "answer": "Paris", "category": "General Knowledge"},
            {"question": "Who painted the Mona Lisa?", "answer": "Leonardo da Vinci", "category": "General Knowledge"},
            {"question": "What is 2 + 2 × 3?", "answer": "8", "category": "General Knowledge"},
            {"question": "What is the largest planet in our solar system?", "answer": "Jupiter", "category": "General Knowledge"},
            {"question": "Who wrote 'Romeo and Juliet'?", "answer": "William Shakespeare", "category": "General Knowledge"},

            # Science
            {"question": "What is the chemical symbol for water?", "answer": "H2O", "category": "Science"},
            {"question": "What is the speed of light?", "answer": "299,792,458 m/s", "category": "Science"},
            {"question": "What is the powerhouse of the cell?", "answer": "Mitochondria", "category": "Science"},
            {"question": "What is the atomic number of carbon?", "answer": "6", "category": "Science"},
            {"question": "What gas do plants absorb from the atmosphere?", "answer": "Carbon dioxide", "category": "Science"},

            # History
            {"question": "In which year did World War II end?", "answer": "1945", "category": "History"},
            {"question": "Who was the first president of the United States?", "answer": "George Washington", "category": "History"},
            {"question": "Which ancient civilization built the pyramids?", "answer": "Egyptians", "category": "History"},
            {"question": "When was the Declaration of Independence signed?", "answer": "1776", "category": "History"},
            {"question": "Which empire was ruled by Julius Caesar?", "answer": "Roman Empire", "category": "History"},

            # Geography
            {"question": "What is the longest river in the world?", "answer": "Nile River", "category": "Geography"},
            {"question": "Which is the largest ocean?", "answer": "Pacific Ocean", "category": "Geography"},
            {"question": "What is the capital of Japan?", "answer": "Tokyo", "category": "Geography"},
            {"question": "Which continent is the Sahara Desert in?", "answer": "Africa", "category": "Geography"},
            {"question": "What is the highest mountain in the world?", "answer": "Mount Everest", "category": "Geography"},

            # Sports
            {"question": "How many players are on a basketball team on the court?", "answer": "5", "category": "Sports"},
            {"question": "In which sport is the term 'home run' used?", "answer": "Baseball", "category": "Sports"},
            {"question": "How many rings are on the Olympic symbol?", "answer": "5", "category": "Sports"},
            {"question": "Which country has won the most FIFA World Cups?", "answer": "Brazil", "category": "Sports"},
            {"question": "In tennis, what does 'love' mean?", "answer": "Zero", "category": "Sports"},

            # Entertainment
            {"question": "Who directed the movie 'Inception'?", "answer": "Christopher Nolan", "category": "Entertainment"},
            {"question": "What is the highest-grossing film of all time?", "answer": "Avatar", "category": "Entertainment"},
            {"question": "Who played Iron Man in the Marvel movies?", "answer": "Robert Downey Jr.", "category": "Entertainment"},
            {"question": "What is the name of the first book in the Harry Potter series?", "answer": "Harry Potter and the Philosopher's Stone", "category": "Entertainment"},
            {"question": "Which band released the album 'Abbey Road'?", "answer": "The Beatles", "category": "Entertainment"},

            # Technology
            {"question": "What does CPU stand for?", "answer": "Central Processing Unit", "category": "Technology"},
            {"question": "Who founded Microsoft?", "answer": "Bill Gates", "category": "Technology"},
            {"question": "What is the main programming language used for web development?", "answer": "JavaScript", "category": "Technology"},
            {"question": "What does AI stand for?", "answer": "Artificial Intelligence", "category": "Technology"},
            {"question": "Which company developed the iPhone?", "answer": "Apple", "category": "Technology"},
        ]

    def _get_categories(self) -> List[str]:
        """Get list of available categories"""
        categories = set()
        for question in self.questions:
            categories.add(question['category'])
        return sorted(list(categories))

    async def _generate_question(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Generate a new trivia question using the LLM"""
        try:
            # Get bot instance to access LLM
            if not self.bot_instance:
                logger.warning("No bot instance available for trivia question generation")
                return self._get_fallback_question(category)

            # Determine category for the question
            available_categories = ["General Knowledge", "Science", "History", "Geography", "Sports", "Entertainment", "Technology"]
            if category and category in available_categories:
                selected_category = category
            else:
                selected_category = random.choice(available_categories)

            # Create prompt for LLM
            json_format = '''{
    "question": "The question text here?",
    "answer": "The correct answer",
    "category": "''' + selected_category + '''"
}'''

            prompt = "Generate a single trivia question in the category: " + selected_category + ".\n\n"
            prompt += "Please respond with a JSON object in this exact format:\n"
            prompt += json_format + "\n\n"
            prompt += """Requirements:
- Make the question interesting and educational
- The answer should be factual and accurate
- Keep the question and answer concise
- Use proper grammar and spelling"""

            # Generate using LLM
            llm_client = self.bot_instance.llm
            response = await llm_client.generate(prompt)

            # Parse JSON response
            import json
            try:
                # Try to extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    question_data = json.loads(json_str)

                    # Validate required fields
                    if all(key in question_data for key in ['question', 'answer', 'category']):
                        # Clean up the data
                        question_data['question'] = question_data['question'].strip()
                        question_data['answer'] = question_data['answer'].strip()
                        return question_data

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response}")

            # Fallback: try to parse manually from text
            question = self._extract_field(response, 'question')
            answer = self._extract_field(response, 'answer')
            parsed_category = selected_category

            if question and answer:
                return {
                    "question": question,
                    "answer": answer,
                    "category": parsed_category
                }

        except Exception as e:
            logger.error(f"Error generating trivia question: {e}")

        # Fallback to static questions if LLM generation fails
        logger.info("Falling back to static trivia questions")
        return self._get_fallback_question(category)

    def _extract_field(self, text: str, field: str) -> str:
        """Extract a field value from text response"""
        import re

        # Try JSON-like patterns
        patterns = [
            rf'"{field}"\s*:\s*"([^"]*)"',  # "field": "value"
            rf'"{field}"\s*:\s*([^\n,}}]+)',  # "field": value
            rf'{field}\s*:\s*"([^"]*)"',     # field: "value"
            rf'{field}\s*:\s*([^\n,}}]+)',    # field: value
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().strip('"')
                if value:
                    return value

        return ""

    def _get_random_question(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get a random question from fallback list"""
        return self._get_fallback_question(category)

    def _get_fallback_question(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get a fallback question from static list"""
        if category:
            filtered_questions = [q for q in self.questions if q['category'].lower() == category.lower()]
            if filtered_questions:
                return random.choice(filtered_questions)

        return random.choice(self.questions)