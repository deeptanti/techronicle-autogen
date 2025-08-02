"""
Personalities package for TechRonicle AutoGen

Contains different AI personality modules for the newsroom agent.
"""

from .gary_poussin import create_gary_agent
from .aravind_rajen import create_aravind_agent
from .tijana_jekic import create_tijana_agent
from .jerin_sojan import create_jerin_agent
from .aayushi_patel import create_aayushi_agent
from .james_guerra import create_james_agent

# Base personality class that others can inherit from
class BasePersonality:
    """Base class for all agent personalities"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def get_system_prompt(self) -> str:
        """Return the system prompt for this personality"""
        raise NotImplementedError("Subclasses must implement get_system_prompt")
    
    def format_response(self, content: str) -> str:
        """Format response according to personality style"""
        return content

# Registry of available personality creation functions
PERSONALITY_CREATORS = {
    "gary_poussin": create_gary_agent,
    "aravind_rajen": create_aravind_agent,
    "tijana_jekic": create_tijana_agent,
    "jerin_sojan": create_jerin_agent,
    "aayushi_patel": create_aayushi_agent,
    "james_guerra": create_james_agent,
}

def create_agent(personality_name: str):
    """Create an agent instance by personality name"""
    if personality_name not in PERSONALITY_CREATORS:
        raise ValueError(f"Unknown personality: {personality_name}")
    return PERSONALITY_CREATORS[personality_name]()

def list_personalities() -> list:
    """List all available personality names"""
    return list(PERSONALITY_CREATORS.keys())

__all__ = [
    "BasePersonality",
    "create_gary_agent",
    "create_aravind_agent",
    "create_tijana_agent", 
    "create_jerin_agent",
    "create_aayushi_agent",
    "create_james_agent",
    "PERSONALITY_CREATORS",
    "create_agent",
    "list_personalities"
]