# LLM prompts module
from .extraction import EXTRACTION_PROMPT
from .so_what import SO_WHAT_PROMPT
from .chat import CHAT_SYSTEM_PROMPTS
from .minister import MINISTER_PROMPTS

__all__ = [
    "EXTRACTION_PROMPT",
    "SO_WHAT_PROMPT", 
    "CHAT_SYSTEM_PROMPTS",
    "MINISTER_PROMPTS"
]
