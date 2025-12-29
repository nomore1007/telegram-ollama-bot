"""
Calculator Plugin for Telegram Ollama Bot
Provides mathematical calculations and expression evaluation
"""

import logging
import re
from typing import List
from telegram import Update
from telegram.ext import ContextTypes

from .base import Plugin

logger = logging.getLogger(__name__)


class CalculatorPlugin(Plugin):
    """Plugin that provides calculator functionality"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        logger.info("Calculator plugin initialized")

    def get_commands(self) -> List[str]:
        """Return list of commands this plugin handles."""
        return ["calc", "calculate", "math"]

    def get_help_text(self) -> str:
        """Return help text for this plugin."""
        return (
            "🧮 *Calculator Plugin*\n\n"
            "`/calc <expression>` - Evaluate mathematical expressions\n"
            "`/calculate <expression>` - Same as /calc\n"
            "`/math <expression>` - Same as /calc\n\n"
            "*Supported Operations:*\n"
            "• Basic: `+`, `-`, `*`, `/`\n"
            "• Advanced: `**` (power), `//` (floor division), `%` (modulo)\n"
            "• Functions: `sqrt()`, `sin()`, `cos()`, `tan()`, `log()`, `exp()`\n"
            "• Constants: `pi`, `e`\n\n"
            "*Examples:*\n"
            "• `/calc 2 + 2 * 3`\n"
            "• `/calc sqrt(16) + pi`\n"
            "• `/calc sin(45) ** 2`\n"
            "• `/calc 100 / (2 + 3)`\n\n"
            "*Safety:* Expressions are evaluated in a restricted environment"
        )

    async def handle_calc(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /calc command"""
        await self._calculate(update, context)

    async def handle_calculate(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /calculate command"""
        await self._calculate(update, context)

    async def handle_math(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /math command"""
        await self._calculate(update, context)

    async def _calculate(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Handle calculation logic"""
        if not update.message:
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a mathematical expression.\n\n"
                "💡 *Usage:* `/calc <expression>`\n"
                "📝 *Example:* `/calc 2 + 2 * 3`\n\n"
                "Use `/calc help` for more examples.",
                parse_mode="Markdown"
            )
            return

        expression = " ".join(context.args)

        if expression.lower() in ['help', 'examples']:
            await update.message.reply_text(self.get_help_text(), parse_mode="Markdown")
            return

        try:
            # Evaluate the expression safely
            result = self._safe_eval(expression)

            await update.message.reply_text(
                f"🧮 *Calculation:*\n`{expression}`\n\n"
                f"✅ *Result:* `{result}`",
                parse_mode="Markdown"
            )

        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid expression: {e}")
        except ZeroDivisionError:
            await update.message.reply_text("❌ Division by zero!")
        except OverflowError:
            await update.message.reply_text("❌ Result too large!")
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            await update.message.reply_text("❌ Error evaluating expression. Please check your syntax.")

    def _safe_eval(self, expression: str):
        """Safely evaluate mathematical expressions"""
        import math
        import operator

        # Remove whitespace
        expression = re.sub(r'\s+', '', expression)

        # Basic security check - only allow mathematical characters
        if not re.match(r'^[0-9+\-*/().sqrtcosintanlogexplnpi%e\s]+$', expression):
            raise ValueError("Invalid characters in expression")

        # Create safe evaluation environment
        safe_dict = {
            # Math constants
            'pi': math.pi,
            'e': math.e,

            # Basic operators
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '**': operator.pow,
            '//': operator.floordiv,
            '%': operator.mod,

            # Math functions
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'log': math.log,
            'ln': math.log,  # Natural log alias
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'ceil': math.ceil,
            'floor': math.floor,

            # Additional functions
            'radians': math.radians,
            'degrees': math.degrees,
        }

        # Replace ^ with ** for power (common notation)
        expression = expression.replace('^', '**')

        # Evaluate with restricted globals/locals
        try:
            result = eval(expression, {"__builtins__": {}}, safe_dict)

            # Check for reasonable result size
            if isinstance(result, (int, float)):
                if abs(result) > 1e10:  # Too large
                    raise OverflowError("Result too large")
                return result
            else:
                raise ValueError("Expression must evaluate to a number")

        except NameError as e:
            raise ValueError(f"Unknown function or variable: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid operation: {e}")
        except SyntaxError:
            raise ValueError("Invalid syntax")