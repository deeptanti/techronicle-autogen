"""
RSS feed collection tools for Techronicle AutoGen
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from utils.config import config

logger = logging.getLogger(__name__)

class RSSCollector:
    """Collects and processes RSS feeds for crypto news"""
    
    def __init__(self):
        self.feeds = config.rss_feeds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Techronicle News Aggregator 1.0'
        })
    
    def collect_articles(self, max_articles: int = None) -> List[Dict]:
        """Collect articles from all RSS feeds"""
        max_articles = max_articles or config.max_articles_per_session
        all_articles = []
        
        logger.info(f"Collecting articles from {len(self.feeds)} RSS feeds")
        
        for feed_url in self.feeds:
            try:
                articles = self._process_feed(feed_url, max_per_feed=2)
                all_articles.extend(articles)
                
                if len(all_articles) >= max_articles:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing feed {feed_url}: {e}")
                continue
        
        # Sort by published date (newest first) and limit
        all_articles.sort(key=lambda x: x.get('published_parsed', datetime.min), reverse=True)
        selected_articles = all_articles[:max_articles]
        
        logger.info(f"Collected {len(selected_articles)} articles")
        return selected_articles
    
    def _process_feed(self, feed_url: str, max_per_feed: int = 2) -> List[Dict]:
        """Process a single RSS feed"""
        logger.debug(f"Processing feed: {feed_url}")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed may have issues: {feed_url}")
            
            articles = []
            
            for entry in feed.entries[:max_per_feed * 2]:  # Get extra in case some fail
                if len(articles) >= max_per_feed:
                    break
                
                article = self._process_entry(entry, feed)
                if article:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
            return []
    
    def _process_entry(self, entry, feed) -> Optional[Dict]:
        """Process a single RSS entry"""
        try:
            # Extract basic information
            article = {
                'title': entry.get('title', '').strip(),
                'link': entry.get('link', ''),
                'summary': self._clean_html(entry.get('summary', '')),
                'published': entry.get('published', ''),
                'published_parsed': getattr(entry, 'published_parsed', None),
                'source': feed.feed.get('title', 'Unknown Source'),
                'source_url': feed.href,
                'author': entry.get('author', ''),
                'tags': [tag.term for tag in getattr(entry, 'tags', [])],
                'collected_at': datetime.now().isoformat()
            }
            
            # Skip if essential fields are missing
            if not article['title'] or not article['link']:
                return None
            
            # Skip if too old (older than 7 days)
            if article['published_parsed']:
                pub_date = datetime(*article['published_parsed'][:6])
                if datetime.now() - pub_date > timedelta(days=7):
                    return None
            
            # Extract full content if possible
            content = self._extract_full_content(article['link'])
            if content:
                article['content'] = content
                article['word_count'] = len(content.split())
            
            # Determine if crypto-related
            article['crypto_relevance'] = self._assess_crypto_relevance(article)
            
            return article
            
        except Exception as e:
            logger.error(f"Error processing entry: {e}")
            return None
    
    def _extract_full_content(self, url: str) -> Optional[str]:
        """Extract full article content from URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try to find main content
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.article-content',
                '.post-content',
                'main'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text()
                    break
            
            # Fallback to body if no specific content found
            if not content_text:
                content_text = soup.get_text()
            
            # Clean and limit the content
            content_text = self._clean_text(content_text)
            
            # Limit to reasonable length (about 2000 words)
            words = content_text.split()
            if len(words) > 2000:
                content_text = ' '.join(words[:2000]) + '...'
            
            return content_text
            
        except Exception as e:
            logger.debug(f"Could not extract content from {url}: {e}")
            return None
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content to plain text"""
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Normalize whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _assess_crypto_relevance(self, article: Dict) -> float:
        """Assess how relevant an article is to crypto (0.0 to 1.0)"""
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency', 'crypto',
            'blockchain', 'defi', 'nft', 'web3', 'dao', 'altcoin', 'stablecoin',
            'mining', 'wallet', 'exchange', 'trading', 'hodl', 'satoshi',
            'coinbase', 'binance', 'solana', 'cardano', 'polkadot', 'avalanche'
        ]
        
        # Combine title, summary, and tags for analysis
        text_to_analyze = ' '.join([
            article.get('title', ''),
            article.get('summary', ''),
            ' '.join(article.get('tags', []))
        ]).lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in crypto_keywords if keyword in text_to_analyze)
        
        # Calculate relevance score
        relevance = min(matches / 3.0, 1.0)  # Normalize to 0-1, cap at 1.0
        
        return relevance
    
    def get_feed_health(self) -> Dict[str, Dict]:
        """Check the health status of all RSS feeds"""
        feed_status = {}
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                status = {
                    'url': feed_url,
                    'title': feed.feed.get('title', 'Unknown'),
                    'last_updated': feed.feed.get('updated', 'Unknown'),
                    'entry_count': len(feed.entries),
                    'bozo': feed.bozo,
                    'status': 'healthy' if not feed.bozo and len(feed.entries) > 0 else 'issues'
                }
                
                if feed.bozo:
                    status['bozo_exception'] = str(getattr(feed, 'bozo_exception', 'Unknown error'))
                
                feed_status[feed_url] = status
                
            except Exception as e:
                feed_status[feed_url] = {
                    'url': feed_url,
                    'status': 'error',
                    'error': str(e)
                }
        
        return feed_status
    
    def test_single_feed(self, feed_url: str) -> Dict:
        """Test a single RSS feed and return detailed info"""
        try:
            feed = feedparser.parse(feed_url)
            
            result = {
                'url': feed_url,
                'feed_title': feed.feed.get('title', 'Unknown'),
                'feed_description': feed.feed.get('description', ''),
                'last_updated': feed.feed.get('updated', 'Unknown'),
                'entry_count': len(feed.entries),
                'bozo': feed.bozo,
                'status': 'success',
                'sample_entries': []
            }
            
            # Add sample entries
            for entry in feed.entries[:3]:
                sample = {
                    'title': entry.get('title', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:200] + '...' if entry.get('summary') else ''
                }
                result['sample_entries'].append(sample)
            
            if feed.bozo:
                result['bozo_exception'] = str(getattr(feed, 'bozo_exception', 'Unknown error'))
                result['status'] = 'warning'
            
            return result
            
        except Exception as e:
            return {
                'url': feed_url,
                'status': 'error',
                'error': str(e)
            }

# Utility functions for agents to use
def collect_latest_crypto_news(max_articles: int = 5) -> List[Dict]:
    """Utility function for agents to collect latest crypto news"""
    collector = RSSCollector()
    return collector.collect_articles(max_articles)

def get_rss_feed_status() -> Dict[str, Dict]:
    """Utility function to check RSS feed health"""
    collector = RSSCollector()
    return collector.get_feed_health()