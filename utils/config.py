"""
Configuration management for Techronicle AutoGen
Updated with web scraping and Slack integration
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from dataclasses import dataclass

# Load environment variables
load_dotenv()

@dataclass
class NewsroomConfig:
    """Configuration for the newsroom application"""
    
    # API Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-1106-preview")
    serper_api_key: Optional[str] = os.getenv("SERPER_API_KEY")
    brave_search_api_key: Optional[str] = os.getenv("BRAVE_SEARCH_API_KEY")
    
    # Slack Integration
    slack_webhook_url: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    slack_enable: bool = os.getenv("SLACK_ENABLE", "false").lower() == "true"
    
    # Web Scraping Settings
    scraping_enabled: bool = os.getenv("SCRAPING_ENABLED", "true").lower() == "true"
    scraping_delay_min: float = float(os.getenv("SCRAPING_DELAY_MIN", "1.0"))
    scraping_delay_max: float = float(os.getenv("SCRAPING_DELAY_MAX", "3.0"))
    scraping_timeout: int = int(os.getenv("SCRAPING_TIMEOUT", "30"))
    paywall_detection: bool = os.getenv("PAYWALL_DETECTION", "true").lower() == "true"
    
    # Content Processing
    min_crypto_relevance: float = float(os.getenv("MIN_CRYPTO_RELEVANCE", "0.4"))
    min_word_count: int = int(os.getenv("MIN_WORD_COUNT", "100"))
    max_articles_to_scrape: int = int(os.getenv("MAX_ARTICLES_TO_SCRAPE", "10"))
    
    # Newsroom Settings
    max_articles_per_session: int = int(os.getenv("MAX_ARTICLES_PER_SESSION", "5"))
    conversation_timeout: int = int(os.getenv("CONVERSATION_TIMEOUT", "300"))
    max_rounds: int = int(os.getenv("MAX_ROUNDS", "20"))
    
    # RSS Feeds
    rss_feeds: List[str] = None
    
    # File Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    conversations_dir: Path = data_dir / "conversations"
    articles_dir: Path = data_dir / "articles"
    decisions_dir: Path = data_dir / "decisions"
    published_dir: Path = data_dir / "published"
    scraped_dir: Path = data_dir / "scraped"
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    save_conversations: bool = os.getenv("SAVE_CONVERSATIONS", "true").lower() == "true"
    save_articles: bool = os.getenv("SAVE_ARTICLES", "true").lower() == "true"
    save_scraped_content: bool = os.getenv("SAVE_SCRAPED_CONTENT", "true").lower() == "true"
    
    # Streamlit
    streamlit_port: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    auto_refresh_interval: int = int(os.getenv("AUTO_REFRESH_INTERVAL", "2"))
    
    def __post_init__(self):
        """Initialize after creation"""
        # Set default RSS feeds if not provided
        if self.rss_feeds is None:
            feeds_env = os.getenv("RSS_FEEDS", "")
            if feeds_env:
                self.rss_feeds = [feed.strip() for feed in feeds_env.split(",")]
            else:
                self.rss_feeds = [
                    "https://cointelegraph.com/rss",
                    "https://decrypt.co/feed",
                    "https://www.coindesk.com/arc/outboundfeeds/rss/",
                    "https://cryptonews.com/news/feed/",
                    "https://www.crypto-news-flash.com/feed/"
                ]
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.conversations_dir, 
                         self.articles_dir, self.decisions_dir, 
                         self.published_dir, self.scraped_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        if not self.rss_feeds:
            raise ValueError("At least one RSS feed is required")
        
        # Warn about optional configurations
        if self.slack_enable and not self.slack_webhook_url:
            print("Warning: Slack enabled but no webhook URL provided")
        
        if not self.scraping_enabled:
            print("Warning: Web scraping disabled - will use RSS content only")
        
        return True
    
    def get_scraping_config(self) -> dict:
        """Get web scraping configuration"""
        return {
            "enabled": self.scraping_enabled,
            "delay_min": self.scraping_delay_min,
            "delay_max": self.scraping_delay_max,
            "timeout": self.scraping_timeout,
            "paywall_detection": self.paywall_detection,
            "min_relevance": self.min_crypto_relevance,
            "min_word_count": self.min_word_count
        }
    
    def get_slack_config(self) -> dict:
        """Get Slack configuration"""
        return {
            "enabled": self.slack_enable,
            "webhook_url": self.slack_webhook_url
        }

# Global configuration instance
config = NewsroomConfig()

# AutoGen LLM configuration
def get_llm_config(temperature: float = 0.8) -> dict:
    """Get LLM configuration for AutoGen agents"""
    return {
        "model": config.openai_model,
        "api_key": config.openai_api_key,
        "temperature": temperature,
        "timeout": 120,
    }