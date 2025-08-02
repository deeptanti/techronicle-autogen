"""
Content Processing Tool for Techronicle AutoGen
Processes scraped content and prepares for publication
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from dataclasses import dataclass
from .web_scraper import ScrapingResult
from .slack_publisher import publish_to_slack
from utils.config import config

logger = logging.getLogger(__name__)

@dataclass
class ProcessedArticle:
    """Processed article ready for editorial review"""
    original_url: str
    title: str
    content: str
    summary: str
    author: str
    source: str
    published_date: str
    word_count: int
    crypto_relevance: float
    readability_score: float
    key_topics: List[str]
    sentiment: str
    images: List[str]
    processing_status: str
    error_messages: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "original_url": self.original_url,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "author": self.author,
            "source": self.source,
            "published_date": self.published_date,
            "word_count": self.word_count,
            "crypto_relevance": self.crypto_relevance,
            "readability_score": self.readability_score,
            "key_topics": self.key_topics,
            "sentiment": self.sentiment,
            "images": self.images,
            "processing_status": self.processing_status,
            "error_messages": self.error_messages,
            "processed_at": datetime.now().isoformat()
        }

class ContentProcessor:
    """Processes scraped content for editorial review"""
    
    def __init__(self):
        # Crypto-specific keywords for relevance scoring
        self.crypto_keywords = {
            'primary': ['bitcoin', 'ethereum', 'cryptocurrency', 'crypto', 'blockchain', 'btc', 'eth'],
            'secondary': ['defi', 'nft', 'web3', 'dao', 'altcoin', 'stablecoin', 'mining', 'wallet'],
            'exchanges': ['coinbase', 'binance', 'kraken', 'gemini', 'ftx', 'okx'],
            'protocols': ['uniswap', 'aave', 'compound', 'opensea', 'makerdao', 'chainlink'],
            'topics': ['regulation', 'sec', 'etf', 'adoption', 'institutional', 'retail']
        }
        
        # Sentiment indicators
        self.positive_words = ['growth', 'bullish', 'surge', 'rally', 'adoption', 'breakthrough', 'innovation']
        self.negative_words = ['crash', 'bearish', 'decline', 'hack', 'scam', 'regulation', 'ban']
        
    def process_scraped_content(self, scraping_result: ScrapingResult) -> ProcessedArticle:
        """Process scraped content into structured article"""
        logger.info(f"Processing content from: {scraping_result.url}")
        
        error_messages = []
        
        # Check if scraping was successful
        if not scraping_result.success:
            return ProcessedArticle(
                original_url=scraping_result.url,
                title="",
                content="",
                summary="",
                author="",
                source="",
                published_date="",
                word_count=0,
                crypto_relevance=0.0,
                readability_score=0.0,
                key_topics=[],
                sentiment="neutral",
                images=[],
                processing_status="failed",
                error_messages=[f"Scraping failed: {scraping_result.error_message}"]
            )
        
        # Handle paywall or bot blocking
        if scraping_result.paywall_detected:
            error_messages.append("Paywall detected - content may be incomplete")
        
        if scraping_result.bot_blocked:
            error_messages.append("Bot blocking detected - content unavailable")
        
        # Process content
        try:
            # Generate summary if content is available
            summary = self._generate_summary(scraping_result.content) if scraping_result.content else ""
            
            # Calculate crypto relevance
            crypto_relevance = self._calculate_crypto_relevance(
                scraping_result.title + " " + scraping_result.content
            )
            
            # Calculate readability score
            readability_score = self._calculate_readability(scraping_result.content)
            
            # Extract key topics
            key_topics = self._extract_key_topics(scraping_result.title + " " + scraping_result.content)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(scraping_result.content)
            
            # Determine processing status
            status = "success"
            if scraping_result.paywall_detected or scraping_result.bot_blocked:
                status = "partial"
            elif not scraping_result.content or scraping_result.word_count < 50:
                status = "incomplete"
                error_messages.append("Insufficient content extracted")
            
            processed_article = ProcessedArticle(
                original_url=scraping_result.url,
                title=scraping_result.title,
                content=scraping_result.content,
                summary=summary,
                author=scraping_result.author,
                source=self._extract_source_domain(scraping_result.url),
                published_date=scraping_result.publish_date,
                word_count=scraping_result.word_count,
                crypto_relevance=crypto_relevance,
                readability_score=readability_score,
                key_topics=key_topics,
                sentiment=sentiment,
                images=scraping_result.images,
                processing_status=status,
                error_messages=error_messages
            )
            
            logger.info(f"Successfully processed: {processed_article.title} (Relevance: {crypto_relevance:.2f})")
            return processed_article
            
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            return ProcessedArticle(
                original_url=scraping_result.url,
                title=scraping_result.title,
                content="",
                summary="",
                author=scraping_result.author,
                source="",
                published_date="",
                word_count=0,
                crypto_relevance=0.0,
                readability_score=0.0,
                key_topics=[],
                sentiment="neutral",
                images=[],
                processing_status="error",
                error_messages=[f"Processing error: {str(e)}"]
            )
    
    def process_batch_articles(self, articles_data: List[Dict[str, Any]]) -> List[ProcessedArticle]:
        """Process multiple articles from RSS/other sources"""
        processed_articles = []
        
        for article_data in articles_data:
            try:
                # Extract URL for scraping
                url = article_data.get('link', '') or article_data.get('url', '')
                
                if not url:
                    logger.warning(f"No URL found for article: {article_data.get('title', 'Unknown')}")
                    continue
                
                # Scrape content if enabled
                if config.scraping_enabled:
                    from .web_scraper import scrape_article_content
                    scraping_result = scrape_article_content(url)
                    processed_article = self.process_scraped_content(scraping_result)
                else:
                    # Process RSS data directly without scraping
                    processed_article = self._process_rss_only(article_data)
                
                processed_articles.append(processed_article)
                
            except Exception as e:
                logger.error(f"Error processing article {url}: {e}")
                # Create error article
                error_article = ProcessedArticle(
                    original_url=url,
                    title=article_data.get('title', 'Unknown'),
                    content="",
                    summary=article_data.get('summary', ''),
                    author=article_data.get('author', ''),
                    source=article_data.get('source', ''),
                    published_date=article_data.get('published', ''),
                    word_count=0,
                    crypto_relevance=article_data.get('crypto_relevance', 0.0),
                    readability_score=0.0,
                    key_topics=[],
                    sentiment="neutral",
                    images=[],
                    processing_status="error",
                    error_messages=[f"Processing failed: {str(e)}"]
                )
                processed_articles.append(error_article)
        
        return processed_articles
    
    def _process_rss_only(self, article_data: Dict[str, Any]) -> ProcessedArticle:
        """Process article using only RSS data (no scraping)"""
        title = article_data.get('title', '')
        content = article_data.get('content', '') or article_data.get('summary', '')
        
        # Calculate metrics based on available data
        crypto_relevance = self._calculate_crypto_relevance(title + " " + content)
        readability_score = self._calculate_readability(content)
        key_topics = self._extract_key_topics(title + " " + content)
        sentiment = self._analyze_sentiment(content)
        
        return ProcessedArticle(
            original_url=article_data.get('link', ''),
            title=title,
            content=content,
            summary=self._generate_summary(content),
            author=article_data.get('author', ''),
            source=article_data.get('source', ''),
            published_date=article_data.get('published', ''),
            word_count=len(content.split()) if content else 0,
            crypto_relevance=crypto_relevance,
            readability_score=readability_score,
            key_topics=key_topics,
            sentiment=sentiment,
            images=[],
            processing_status="rss_only",
            error_messages=[]
        )
    
    def _generate_summary(self, content: str, max_sentences: int = 3) -> str:
        """Generate article summary from content"""
        if not content or len(content.split()) < 50:
            return ""
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 5]
        
        # Take first few sentences as summary
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)
        
        # Ensure it ends properly
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary
    
    def _calculate_crypto_relevance(self, text: str) -> float:
        """Calculate crypto relevance score (0.0 to 1.0)"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # Count keyword matches with weights
        for category, keywords in self.crypto_keywords.items():
            weight = {
                'primary': 0.3,
                'secondary': 0.2,
                'exchanges': 0.15,
                'protocols': 0.15,
                'topics': 0.1
            }.get(category, 0.1)
            
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            score += matches * weight
        
        # Normalize to 0-1 range
        max_possible_score = 3.0  # Reasonable maximum
        normalized_score = min(score / max_possible_score, 1.0)
        
        return round(normalized_score, 2)
    
    def _calculate_readability(self, content: str) -> float:
        """Calculate readability score (simple implementation)"""
        if not content:
            return 0.0
        
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Simple readability metrics
        avg_words_per_sentence = len(words) / len(sentences)
        avg_chars_per_word = sum(len(word) for word in words) / len(words)
        
        # Simple score calculation (higher = more readable)
        # Penalize very long sentences and very long words
        readability = 100.0 - (avg_words_per_sentence * 1.5) - (avg_chars_per_word * 5)
        
        # Normalize to 0-100 range
        readability = max(0, min(100, readability))
        
        return round(readability, 1)
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key crypto topics from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        topics = []
        
        # Define topic patterns
        topic_patterns = {
            'Bitcoin': ['bitcoin', 'btc'],
            'Ethereum': ['ethereum', 'eth', 'ether'],
            'DeFi': ['defi', 'decentralized finance', 'yield farming', 'liquidity'],
            'NFT': ['nft', 'non-fungible token', 'opensea', 'digital art'],
            'Regulation': ['regulation', 'sec', 'regulatory', 'compliance'],
            'Trading': ['trading', 'exchange', 'price', 'market'],
            'Mining': ['mining', 'miners', 'hash rate', 'proof of work'],
            'Institutional': ['institutional', 'corporate', 'treasury', 'etf'],
            'Technology': ['blockchain', 'smart contract', 'protocol', 'network']
        }
        
        for topic, keywords in topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics[:5]  # Limit to top 5 topics
    
    def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of the content"""
        if not content:
            return "neutral"
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in content_lower)
        negative_count = sum(1 for word in self.negative_words if word in content_lower)
        
        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        else:
            return "neutral"
    
    def _extract_source_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "Unknown"
    
    def publish_processed_article(self, processed_article: ProcessedArticle, 
                                session_id: str = "", approved_by: str = "") -> Dict[str, Any]:
        """Publish processed article to Slack and save locally"""
        
        # Add session and approval info
        article_data = processed_article.to_dict()
        article_data.update({
            "session_id": session_id,
            "approved_by": approved_by,
            "published_at": datetime.now().isoformat()
        })
        
        results = {"local_save": None, "slack_publish": None}
        
        # Save locally
        try:
            filename = f"published_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = config.published_dir / filename
            
            import json
            with open(filepath, 'w') as f:
                json.dump(article_data, f, indent=2, default=str)
            
            results["local_save"] = {
                "success": True,
                "filepath": str(filepath),
                "message": f"Article saved locally: {filename}"
            }
            
            logger.info(f"Saved article locally: {filepath}")
            
        except Exception as e:
            results["local_save"] = {
                "success": False,
                "error": f"Failed to save locally: {str(e)}"
            }
        
        # Publish to Slack if enabled
        if config.slack_enable:
            try:
                slack_result = publish_to_slack(article_data)
                results["slack_publish"] = slack_result
                
                if slack_result.get("success"):
                    logger.info(f"Published to Slack: {processed_article.title}")
                else:
                    logger.warning(f"Slack publish failed: {slack_result.get('error')}")
                    
            except Exception as e:
                results["slack_publish"] = {
                    "success": False,
                    "error": f"Slack publish failed: {str(e)}"
                }
        else:
            results["slack_publish"] = {
                "success": False,
                "error": "Slack publishing disabled in configuration"
            }
        
        return results
    
    def save_processed_articles(self, articles: List[ProcessedArticle], 
                              session_id: str = "") -> Dict[str, Any]:
        """Save multiple processed articles to file"""
        try:
            # Create session data
            session_data = {
                "session_id": session_id,
                "processed_at": datetime.now().isoformat(),
                "article_count": len(articles),
                "articles": [article.to_dict() for article in articles],
                "summary": {
                    "total_articles": len(articles),
                    "successful": len([a for a in articles if a.processing_status == "success"]),
                    "partial": len([a for a in articles if a.processing_status == "partial"]),
                    "failed": len([a for a in articles if a.processing_status in ["failed", "error"]]),
                    "avg_relevance": sum(a.crypto_relevance for a in articles) / len(articles) if articles else 0,
                    "top_topics": self._get_top_topics(articles)
                }
            }
            
            # Save to file
            filename = f"processed_articles_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = config.scraped_dir / filename
            
            import json
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(articles)} processed articles to: {filepath}")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "articles_saved": len(articles),
                "summary": session_data["summary"]
            }
            
        except Exception as e:
            logger.error(f"Error saving processed articles: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_top_topics(self, articles: List[ProcessedArticle], top_n: int = 5) -> List[str]:
        """Get most common topics across articles"""
        topic_counts = {}
        
        for article in articles:
            for topic in article.key_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort by frequency and return top N
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:top_n]]

# Utility functions for agents
def process_article_from_url(url: str) -> ProcessedArticle:
    """Process article from URL (scrape + process)"""
    from .web_scraper import scrape_article_content
    
    # Scrape content
    scraping_result = scrape_article_content(url)
    
    # Process content
    processor = ContentProcessor()
    return processor.process_scraped_content(scraping_result)

def process_multiple_articles(urls: List[str]) -> List[ProcessedArticle]:
    """Process multiple articles from URLs"""
    from .web_scraper import batch_scrape_articles
    
    # Scrape all articles
    scraping_results = batch_scrape_articles(urls)
    
    # Process all results
    processor = ContentProcessor()
    processed_articles = []
    
    for result in scraping_results:
        processed_article = processor.process_scraped_content(result)
        processed_articles.append(processed_article)
    
    return processed_articles

def process_rss_articles(rss_articles: List[Dict[str, Any]]) -> List[ProcessedArticle]:
    """Process articles from RSS feed data"""
    processor = ContentProcessor()
    return processor.process_batch_articles(rss_articles)

def filter_articles_by_relevance(articles: List[ProcessedArticle], 
                                min_relevance: float = 0.5) -> List[ProcessedArticle]:
    """Filter articles by crypto relevance score"""
    return [
        article for article in articles 
        if article.crypto_relevance >= min_relevance and article.processing_status in ["success", "partial"]
    ]

def get_best_articles(articles: List[ProcessedArticle], 
                     max_articles: int = 5) -> List[ProcessedArticle]:
    """Get best articles sorted by relevance and quality"""
    # Filter successful articles
    valid_articles = [a for a in articles if a.processing_status in ["success", "partial", "rss_only"]]
    
    # Sort by crypto relevance (descending) and word count (descending)
    valid_articles.sort(
        key=lambda x: (x.crypto_relevance, x.word_count), 
        reverse=True
    )
    
    return valid_articles[:max_articles]

def get_processing_statistics(articles: List[ProcessedArticle]) -> Dict[str, Any]:
    """Get statistics about processed articles"""
    if not articles:
        return {"total": 0, "message": "No articles to analyze"}
    
    return {
        "total_articles": len(articles),
        "successful": len([a for a in articles if a.processing_status == "success"]),
        "partial": len([a for a in articles if a.processing_status == "partial"]),
        "rss_only": len([a for a in articles if a.processing_status == "rss_only"]),
        "failed": len([a for a in articles if a.processing_status in ["failed", "error"]]),
        "avg_relevance": round(sum(a.crypto_relevance for a in articles) / len(articles), 2),
        "avg_word_count": round(sum(a.word_count for a in articles) / len(articles)),
        "avg_readability": round(sum(a.readability_score for a in articles) / len(articles), 1),
        "top_sources": list(set(a.source for a in articles if a.source))[:5],
        "sentiment_distribution": {
            "positive": len([a for a in articles if a.sentiment == "positive"]),
            "neutral": len([a for a in articles if a.sentiment == "neutral"]),
            "negative": len([a for a in articles if a.sentiment == "negative"])
        }
    }
    
    def _generate_summary(self, content: str, max_sentences: int = 3) -> str:
        """Generate article summary from content"""
        if not content or len(content.split()) < 50:
            return ""
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 5]
        
        # Take first few sentences as summary
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)
        
        # Ensure it ends properly
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary
    
    def _calculate_crypto_relevance(self, text: str) -> float:
        """Calculate crypto relevance score (0.0 to 1.0)"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # Count keyword matches with weights
        for category, keywords in self.crypto_keywords.items():
            weight = {
                'primary': 0.3,
                'secondary': 0.2,
                'exchanges': 0.15,
                'protocols': 0.15,
                'topics': 0.1
            }.get(category, 0.1)
            
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            score += matches * weight
        
        # Normalize to 0-1 range
        max_possible_score = 3.0  # Reasonable maximum
        normalized_score = min(score / max_possible_score, 1.0)
        
        return round(normalized_score, 2)
    
    def _calculate_readability(self, content: str) -> float:
        """Calculate readability score (simple implementation)"""
        if not content:
            return 0.0
        
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Simple readability metrics
        avg_words_per_sentence = len(words) / len(sentences)
        avg_chars_per_word = sum(len(word) for word in words) / len(words)
        
        # Simple score calculation (higher = more readable)
        # Penalize very long sentences and very long words
        readability = 100.0 - (avg_words_per_sentence * 1.5) - (avg_chars_per_word * 5)
        
        # Normalize to 0-100 range
        readability = max(0, min(100, readability))
        
        return round(readability, 1)
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key crypto topics from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        topics = []
        
        # Define topic patterns
        topic_patterns = {
            'Bitcoin': ['bitcoin', 'btc'],
            'Ethereum': ['ethereum', 'eth', 'ether'],
            'DeFi': ['defi', 'decentralized finance', 'yield farming', 'liquidity'],
            'NFT': ['nft', 'non-fungible token', 'opensea', 'digital art'],
            'Regulation': ['regulation', 'sec', 'regulatory', 'compliance'],
            'Trading': ['trading', 'exchange', 'price', 'market'],
            'Mining': ['mining', 'miners', 'hash rate', 'proof of work'],
            'Institutional': ['institutional', 'corporate', 'treasury', 'etf'],
            'Technology': ['blockchain', 'smart contract', 'protocol', 'network']
        }
        
        for topic, keywords in topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics[:5]  # Limit to top 5 topics
    
    def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of the content"""
        if not content:
            return "neutral"
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in content_lower)
        negative_count = sum(1 for word in self.negative_words if word in content_lower)
        
        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        else:
            return "neutral"
    
    def _extract_source_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "Unknown"
    
    def publish_processed_article(self, processed_article: ProcessedArticle, 
                                session_id: str = "", approved_by: str = "") -> Dict[str, Any]:
        """Publish processed article to Slack and save locally"""
        
        # Add session and approval info
        article_data = processed_article.to_dict()
        article_data.update({
            "session_id": session_id,
            "approved_by": approved_by,
            "published_at": datetime.now().isoformat()
        })
        
        results = {"local_save": None, "slack_publish": None}
        
        # Save locally
        try:
            filename = f"published_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = config.published_dir / filename
            
            import json
            with open(filepath, 'w') as f:
                json.dump(article_data, f, indent=2, default=str)
            
            results["local_save"] = {
                "success": True,
                "filepath": str(filepath),
                "message": f"Article saved locally: {filename}"
            }
            
            logger.info(f"Saved article locally: {filepath}")
            
        except Exception as e:
            results["local_save"] = {
                "success": False,
                "error": f"Failed to save locally: {str(e)}"
            }
        
        # Publish to Slack
        try:
            slack_result = publish_to_slack(article_data)
            results["slack_publish"] = slack_result
            
            if slack_result.get("success"):
                logger.info(f"Published to Slack: {processed_article.title}")
            else:
                logger.warning(f"Slack publish failed: {slack_result.get('error')}")
                
        except Exception as e:
            results["slack_publish"] = {
                "success": False,
                "error": f"Slack publish failed: {str(e)}"
            }
        
        return results

# Utility functions for agents
def process_article_from_url(url: str) -> ProcessedArticle:
    """Process article from URL (scrape + process)"""
    from .web_scraper import scrape_article_content
    
    # Scrape content
    scraping_result = scrape_article_content(url)
    
    # Process content
    processor = ContentProcessor()
    return processor.process_scraped_content(scraping_result)

def process_multiple_articles(urls: List[str]) -> List[ProcessedArticle]:
    """Process multiple articles from URLs"""
    from .web_scraper import batch_scrape_articles
    
    # Scrape all articles
    scraping_results = batch_scrape_articles(urls)
    
    # Process all results
    processor = ContentProcessor()
    processed_articles = []
    
    for result in scraping_results:
        processed_article = processor.process_scraped_content(result)
        processed_articles.append(processed_article)
    
    return processed_articles

def filter_articles_by_relevance(articles: List[ProcessedArticle], 
                                min_relevance: float = 0.5) -> List[ProcessedArticle]:
    """Filter articles by crypto relevance score"""
    return [
        article for article in articles 
        if article.crypto_relevance >= min_relevance and article.processing_status == "success"
    ]

def get_best_articles(articles: List[ProcessedArticle], 
                     max_articles: int = 5) -> List[ProcessedArticle]:
    """Get best articles sorted by relevance and quality"""
    # Filter successful articles
    valid_articles = [a for a in articles if a.processing_status in ["success", "partial"]]
    
    # Sort by crypto relevance (descending) and word count (descending)
    valid_articles.sort(
        key=lambda x: (x.crypto_relevance, x.word_count), 
        reverse=True
    )
    
    return valid_articles[:max_articles]