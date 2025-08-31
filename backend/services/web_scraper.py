"""
Web Scraper Service for Synthra
Handles fetching and extracting content from web pages
"""

import logging
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urlparse
import re

import httpx
from bs4 import BeautifulSoup
# import newspaper
# from newspaper import Article

logger = logging.getLogger(__name__)

class WebScraperService:
    """Service for fetching and extracting web page content"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
    
    async def fetch_page_content(self, url: str) -> Dict[str, str]:
        """Fetch and extract content from a single URL"""
        try:
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            logger.info(f"Fetching content from: {url}")
            
            # Use BeautifulSoup for content extraction
            return await self._extract_with_beautifulsoup(url)
            
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return {
                'title': f"Error fetching {url}",
                'content': f"Failed to fetch content: {str(e)}",
                'url': url,
                'error': str(e)
            }
    
    async def fetch_multiple_pages(self, urls: List[str]) -> List[Dict[str, str]]:
        """Fetch content from multiple URLs concurrently"""
        logger.info(f"Fetching content from {len(urls)} URLs")
        
        # Limit concurrent requests to avoid overwhelming servers
        semaphore = asyncio.Semaphore(5)
        
        async def fetch_with_semaphore(url: str) -> Dict[str, str]:
            async with semaphore:
                return await self.fetch_page_content(url)
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'title': f"Error fetching {urls[i]}",
                    'content': f"Failed to fetch content: {str(result)}",
                    'url': urls[i],
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    # async def _extract_with_newspaper(self, url: str) -> Dict[str, str]:
    #     """Extract content using newspaper3k library"""
    #     article = Article(url)
    #     
    #     # Download and parse in a thread pool to avoid blocking
    #     await asyncio.get_event_loop().run_in_executor(
    #         None, self._download_and_parse_article, article
    #     )
    #     
    #     return {
    #         'title': article.title or self._extract_title_from_url(url),
    #         'content': article.text or '',
    #         'url': url,
    #         'authors': article.authors,
    #         'publish_date': str(article.publish_date) if article.publish_date else None,
    #         'top_image': article.top_image,
    #         'summary': article.summary or ''
    #     }
    # 
    # def _download_and_parse_article(self, article: Article) -> None:
    #     """Download and parse article in a synchronous context"""
    #     article.download()
    #     article.parse()
    #     article.nlp()
    
    async def _extract_with_beautifulsoup(self, url: str) -> Dict[str, str]:
        """Extract content using BeautifulSoup as fallback"""
        response = await self.session.get(url, follow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else self._extract_title_from_url(url)
        
        # Extract main content
        content = self._extract_main_content(soup)
        
        return {
            'title': title,
            'content': content,
            'url': url
        }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from BeautifulSoup object"""
        # Try to find main content areas
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '#content',
            '#main'
        ]
        
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                return self._clean_text(content_area.get_text())
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return self._clean_text(body.get_text())
        
        return self._clean_text(soup.get_text())
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a reasonable title from URL if no title found"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/').replace('/', ' - ')
        return f"{domain}: {path}" if path else domain
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate if URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.session.aclose()

# Global instance
web_scraper = WebScraperService()
