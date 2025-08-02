"""
Advanced Web Scraping Tool for Techronicle AutoGen
Handles paywalls, bot detection, and content extraction
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Dict, Optional, List
import logging
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import re
from utils.config import config

logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """Result of web scraping operation"""
    url: str
    success: bool
    title: str = ""
    content: str = ""
    author: str = ""
    publish_date: str = ""
    paywall_detected: bool = False
    bot_blocked: bool = False
    error_message: str = ""
    word_count: int = 0
    images: List[str] = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = []

class WebScraper:
    """Advanced web scraper with paywall and bot detection"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        
        # Paywall indicators
        self.paywall_indicators = [
            "subscribe to continue",
            "premium content",
            "paywall",
            "subscription required",
            "become a member",
            "unlock this article",
            "subscribe now",
            "premium subscriber",
            "login to continue",
            "create account to read"
        ]
        
        # Bot blocking indicators
        self.bot_indicators = [
            "access denied",
            "bot detected",
            "captcha",
            "cloudflare",
            "checking your browser",
            "ddos protection",
            "please verify you are human",
            "security check",
            "rate limited"
        ]
        
        # Content selectors (prioritized)
        self.content_selectors = [
            'article[role="main"]',
            'main article',
            '[role="main"]',
            '.article-content',
            '.post-content', 
            '.entry-content',
            '.content-body',
            '.article-body',
            '.story-content',
            '.post-body',
            'article',
            '.content'
        ]
        
    def setup_session(self):
        """Setup session with headers and configuration"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Random delay between requests
        self.min_delay = 1
        self.max_delay = 3
    
    def scrape_article(self, url: str) -> ScrapingResult:
        """Main scraping method with comprehensive error handling"""
        logger.info(f"Scraping article: {url}")
        
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(self.min_delay, self.max_delay))
            
            # Make request with timeout
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check for bot blocking
            if self._is_bot_blocked(response.text, response.status_code):
                return ScrapingResult(
                    url=url,
                    success=False,
                    bot_blocked=True,
                    error_message="Bot detection triggered"
                )
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article data
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            images = self._extract_images(soup, url)
            
            # Check for paywall
            paywall_detected = self._detect_paywall(content, soup)
            
            # If paywall detected, try alternative extraction
            if paywall_detected:
                logger.warning(f"Paywall detected for {url}")
                # Could implement paywall bypass techniques here
                # For now, we'll mark it and continue with available content
            
            result = ScrapingResult(
                url=url,
                success=True,
                title=title,
                content=content,
                author=author,
                publish_date=publish_date,
                paywall_detected=paywall_detected,
                word_count=len(content.split()) if content else 0,
                images=images
            )
            
            logger.info(f"Successfully scraped: {title} ({result.word_count} words)")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return ScrapingResult(
                url=url,
                success=False,
                error_message=f"Request failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return ScrapingResult(
                url=url,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _is_bot_blocked(self, content: str, status_code: int) -> bool:
        """Check if the request was blocked by bot detection"""
        if status_code in [403, 429, 503]:
            return True
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in self.bot_indicators)
    
    def _detect_paywall(self, content: str, soup: BeautifulSoup) -> bool:
        """Detect if content is behind a paywall"""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # Check for paywall text indicators
        paywall_text = any(indicator in content_lower for indicator in self.paywall_indicators)
        
        # Check for short content (possible paywall truncation)
        word_count = len(content.split())
        suspiciously_short = word_count < 100
        
        # Check for paywall-specific elements
        paywall_elements = soup.find_all(['div', 'section'], class_=re.compile(r'paywall|subscription|premium', re.I))
        paywall_structure = len(paywall_elements) > 0
        
        return paywall_text or (suspiciously_short and paywall_structure)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors
        selectors = [
            'h1.headline',
            'h1.title',
            'h1.article-title',
            'h1.entry-title',
            '.article-header h1',
            'article h1',
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        # Fallback to meta tags
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            return meta_title.get('content', '').strip()
        
        # Final fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        return "No title found"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try content selectors in order of preference
        for selector in self.content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Clean and extract text
                text = self._clean_text(content_elem.get_text())
                if len(text.split()) > 50:  # Minimum word threshold
                    return text
        
        # Fallback: try to find largest text block
        all_paragraphs = soup.find_all('p')
        if all_paragraphs:
            content = ' '.join([p.get_text() for p in all_paragraphs])
            return self._clean_text(content)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        # Try various author selectors
        author_selectors = [
            '[rel="author"]',
            '.author-name',
            '.author',
            '.byline',
            '.article-author',
            '[itemprop="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        # Try meta tags
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author:
            return meta_author.get('content', '').strip()
        
        return ""
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract publish date"""
        # Try time elements
        time_elem = soup.find('time')
        if time_elem:
            return time_elem.get('datetime', time_elem.get_text().strip())
        
        # Try meta tags
        date_metas = [
            soup.find('meta', property='article:published_time'),
            soup.find('meta', attrs={'name': 'publish-date'}),
            soup.find('meta', attrs={'name': 'date'})
        ]
        
        for meta in date_metas:
            if meta:
                return meta.get('content', '').strip()
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract article images"""
        images = []
        
        # Find images in article content
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, src)
                images.append(full_url)
        
        return images[:5]  # Limit to first 5 images
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Normalize whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def test_url(self, url: str) -> Dict:
        """Test URL accessibility and return diagnostics"""
        try:
            response = self.session.head(url, timeout=10)
            return {
                'url': url,
                'status_code': response.status_code,
                'accessible': response.status_code == 200,
                'headers': dict(response.headers),
                'content_type': response.headers.get('content-type', ''),
                'server': response.headers.get('server', '')
            }
        except Exception as e:
            return {
                'url': url,
                'accessible': False,
                'error': str(e)
            }

# Utility functions for agents
def scrape_article_content(url: str) -> ScrapingResult:
    """Utility function for agents to scrape article content"""
    scraper = WebScraper()
    return scraper.scrape_article(url)

def test_article_accessibility(url: str) -> Dict:
    """Test if an article URL is accessible"""
    scraper = WebScraper()
    return scraper.test_url(url)

def batch_scrape_articles(urls: List[str]) -> List[ScrapingResult]:
    """Scrape multiple articles with rate limiting"""
    scraper = WebScraper()
    results = []
    
    for url in urls:
        result = scraper.scrape_article(url)
        results.append(result)
        
        # Add delay between requests
        if len(results) < len(urls):  # Don't delay after last request
            time.sleep(random.uniform(2, 5))
    
    return results