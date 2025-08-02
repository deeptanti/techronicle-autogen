"""
Slack Publishing Tool for Techronicle AutoGen
Publishes articles to Slack channels via webhooks
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from utils.config import config

logger = logging.getLogger(__name__)

@dataclass
class SlackMessage:
    """Structured Slack message format"""
    title: str
    content: str
    author: str = ""
    source: str = ""
    url: str = ""
    published_at: str = ""
    crypto_relevance: float = 0.0
    word_count: int = 0
    session_id: str = ""
    approved_by: str = ""

class SlackPublisher:
    """Handles publishing to Slack via webhooks"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or config.slack_webhook_url
        self.session = requests.Session()
        
        if not self.webhook_url:
            logger.warning("No Slack webhook URL configured")
    
    def publish_article(self, message: SlackMessage) -> Dict[str, Any]:
        """Publish article to Slack channel"""
        if not self.webhook_url:
            return {
                "success": False,
                "error": "No Slack webhook URL configured"
            }
        
        try:
            # Create rich Slack message
            slack_payload = self._create_slack_payload(message)
            
            # Send to Slack
            response = self.session.post(
                self.webhook_url,
                json=slack_payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info(f"Successfully published to Slack: {message.title}")
            
            return {
                "success": True,
                "message": "Article published to Slack",
                "webhook_response": response.text,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to publish to Slack: {e}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error publishing to Slack: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _create_slack_payload(self, message: SlackMessage) -> Dict[str, Any]:
        """Create formatted Slack message payload"""
        
        # Determine color based on crypto relevance
        color = self._get_relevance_color(message.crypto_relevance)
        
        # Create main attachment
        attachment = {
            "color": color,
            "title": f"📰 {message.title}",
            "title_link": message.url if message.url else None,
            "text": self._format_content_preview(message.content),
            "fields": [
                {
                    "title": "Source",
                    "value": message.source or "Unknown",
                    "short": True
                },
                {
                    "title": "Author", 
                    "value": message.author or "Unknown",
                    "short": True
                },
                {
                    "title": "Crypto Relevance",
                    "value": f"{message.crypto_relevance*100:.1f}%" if message.crypto_relevance else "N/A",
                    "short": True
                },
                {
                    "title": "Word Count",
                    "value": str(message.word_count) if message.word_count else "N/A",
                    "short": True
                }
            ],
            "footer": f"Techronicle AutoGen • Session: {message.session_id}",
            "footer_icon": "https://ca.slack-edge.com/T0266FRGM-U024BE7LH-1a9b7e6c-512",
            "ts": int(datetime.now().timestamp())
        }
        
        # Add approval information if available
        if message.approved_by:
            attachment["fields"].append({
                "title": "Approved By",
                "value": f"✅ {message.approved_by}",
                "short": True
            })
        
        # Create main payload
        payload = {
            "text": f"🚀 *New Article Published* by Techronicle AutoGen",
            "attachments": [attachment],
            "username": "Techronicle Bot",
            "icon_emoji": ":newspaper:"
        }
        
        # Add action buttons if URL is available
        if message.url:
            attachment["actions"] = [
                {
                    "type": "button",
                    "text": "📖 Read Full Article",
                    "url": message.url,
                    "style": "primary"
                }
            ]
        
        return payload
    
    def _get_relevance_color(self, relevance: float) -> str:
        """Get color based on crypto relevance score"""
        if relevance >= 0.8:
            return "#36a64f"  # Green - High relevance
        elif relevance >= 0.6:
            return "#ffcc02"  # Yellow - Medium relevance  
        elif relevance >= 0.4:
            return "#ff9500"  # Orange - Low relevance
        else:
            return "#ff4444"  # Red - Very low relevance
    
    def _format_content_preview(self, content: str, max_length: int = 300) -> str:
        """Format content preview for Slack"""
        if not content:
            return "_No content preview available_"
        
        # Clean content
        content = content.strip()
        
        # Truncate if too long
        if len(content) > max_length:
            content = content[:max_length].rsplit(' ', 1)[0] + "..."
        
        return content
    
    def publish_session_summary(self, session_results: Dict[str, Any]) -> Dict[str, Any]:
        """Publish editorial session summary to Slack"""
        if not self.webhook_url:
            return {
                "success": False,
                "error": "No Slack webhook URL configured"
            }
        
        try:
            payload = self._create_session_summary_payload(session_results)
            
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info(f"Published session summary to Slack: {session_results.get('session_id')}")
            
            return {
                "success": True,
                "message": "Session summary published to Slack"
            }
            
        except Exception as e:
            logger.error(f"Failed to publish session summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_session_summary_payload(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create session summary payload for Slack"""
        
        # Determine session status color
        success = results.get("success", False)
        color = "#36a64f" if success else "#ff4444"
        
        attachment = {
            "color": color,
            "title": f"📊 Editorial Session Complete: {results.get('session_id', 'Unknown')}",
            "fields": [
                {
                    "title": "Articles Discussed",
                    "value": str(results.get("articles_discussed", 0)),
                    "short": True
                },
                {
                    "title": "Articles Published", 
                    "value": str(results.get("articles_published", 0)),
                    "short": True
                },
                {
                    "title": "Total Messages",
                    "value": str(results.get("total_messages", 0)),
                    "short": True
                },
                {
                    "title": "Session Status",
                    "value": "✅ Success" if success else "❌ Failed",
                    "short": True
                }
            ],
            "footer": "Techronicle AutoGen Session Report",
            "ts": int(datetime.now().timestamp())
        }
        
        # Add participants if available
        participants = results.get("participants", [])
        if participants:
            attachment["fields"].append({
                "title": "Participants",
                "value": ", ".join(participants),
                "short": False
            })
        
        # Add published articles list
        published_articles = results.get("approved_articles", [])
        if published_articles:
            articles_text = "\n".join([
                f"• {article.get('title', 'Untitled')[:50]}..."
                for article in published_articles[:3]  # Limit to 3
            ])
            attachment["fields"].append({
                "title": "Published Articles",
                "value": articles_text,
                "short": False
            })
        
        return {
            "text": f"🎉 Techronicle Editorial Session Report",
            "attachments": [attachment],
            "username": "Techronicle Bot",
            "icon_emoji": ":chart_with_upwards_trend:"
        }
    
    def test_webhook(self) -> Dict[str, Any]:
        """Test Slack webhook connectivity"""
        if not self.webhook_url:
            return {
                "success": False,
                "error": "No webhook URL configured"
            }
        
        try:
            test_payload = {
                "text": "🧪 Techronicle AutoGen webhook test",
                "attachments": [{
                    "color": "#36a64f",
                    "title": "Webhook Test Successful",
                    "text": "Your Slack integration is working correctly!",
                    "footer": "Techronicle AutoGen",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            response = self.session.post(
                self.webhook_url,
                json=test_payload,
                timeout=10
            )
            
            response.raise_for_status()
            
            return {
                "success": True,
                "message": "Webhook test successful",
                "response_code": response.status_code
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Utility functions for agents
def publish_to_slack(article_data: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Utility function for agents to publish articles to Slack"""
    
    # Convert article data to SlackMessage
    message = SlackMessage(
        title=article_data.get("title", "Untitled Article"),
        content=article_data.get("summary", "") or article_data.get("content", ""),
        author=article_data.get("author", ""),
        source=article_data.get("source", ""),
        url=article_data.get("link", "") or article_data.get("url", ""),
        published_at=article_data.get("published", ""),
        crypto_relevance=article_data.get("crypto_relevance", 0.0),
        word_count=article_data.get("word_count", 0),
        session_id=article_data.get("session_id", ""),
        approved_by=article_data.get("approved_by", "")
    )
    
    publisher = SlackPublisher(webhook_url)
    return publisher.publish_article(message)

def publish_session_summary_to_slack(session_results: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Utility function to publish session summary to Slack"""
    publisher = SlackPublisher(webhook_url)
    return publisher.publish_session_summary(session_results)

def test_slack_webhook(webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Test Slack webhook connectivity"""
    publisher = SlackPublisher(webhook_url)
    return publisher.test_webhook()