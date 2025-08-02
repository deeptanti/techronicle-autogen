"""
Agents package for TechRonicle AutoGen

Contains the newsroom agent and associated personalities and tools.
"""

from .newsroom import TechronicleNewsroom
from . import personalities
from . import tools

# Import key personality creation functions for easy access
from .personalities.gary_poussin import create_gary_agent
from .personalities.aravind_rajen import create_aravind_agent
from .personalities.tijana_jekic import create_tijana_agent
from .personalities.jerin_sojan import create_jerin_agent
from .personalities.aayushi_patel import create_aayushi_agent
from .personalities.james_guerra import create_james_agent

# Import key tool classes
from .tools.rss_collector import RSSCollector, collect_latest_crypto_news

__all__ = [
    "TechronicleNewsroom",
    "personalities",
    "tools",
    "create_gary_agent",
    "create_aravind_agent", 
    "create_tijana_agent",
    "create_jerin_agent",
    "create_aayushi_agent",
    "create_james_agent",
    "RSSCollector",
    "collect_latest_crypto_news"
]