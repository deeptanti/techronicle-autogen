"""
Tools package for TechRonicle AutoGen

Contains tools and utilities that agents can use to perform their tasks.
"""

from .rss_collector import RSSCollector, collect_latest_crypto_news, get_rss_feed_status

# Base tool class that others can inherit from
class BaseTool:
    """Base class for all agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    async def execute(self, *args, **kwargs):
        """Execute the tool with given parameters"""
        raise NotImplementedError("Subclasses must implement execute")
    
    def get_schema(self) -> dict:
        """Return the tool schema for agent integration"""
        raise NotImplementedError("Subclasses must implement get_schema")

# Registry of available tools
TOOLS = {
    "rss_collector": RSSCollector,
}

def get_tool(name: str) -> BaseTool:
    """Get a tool instance by name"""
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return TOOLS[name]()

def list_tools() -> list:
    """List all available tool names"""
    return list(TOOLS.keys())

def execute_rss_collection(max_articles: int = 5):
    """Execute RSS collection with given parameters"""
    return collect_latest_crypto_news(max_articles)

__all__ = [
    "BaseTool",
    "RSSCollector",
    "collect_latest_crypto_news",
    "get_rss_feed_status",
    "TOOLS", 
    "get_tool",
    "list_tools",
    "execute_rss_collection"
]