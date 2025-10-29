"""
Web Scraper Service for Synthra
Handles fetching and extracting content from web pages using enhanced parsing
"""

import logging
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
import re
import os

import httpx
from bs4 import BeautifulSoup
from .content_core_parser import ContentCoreParser

logger = logging.getLogger(__name__)

class WebScraperService:
    """Service for fetching and extracting web page content"""
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        # More realistic headers to avoid bot detection
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            follow_redirects=True
        )
        
        # Initialize Content Core parser
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.content_core_parser = ContentCoreParser(gemini_api_key=gemini_api_key)
        logger.info("Web scraper initialized with Content Core parser")
    
    async def fetch_page_content(self, url: str, use_enhanced_parser: bool = True) -> Dict[str, str]:
        """Fetch and extract content from a single URL"""
        try:
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            logger.info(f"Fetching content from: {url}")
            
            if use_enhanced_parser:
                # Use Content Core parser for better quality
                result = await self.content_core_parser.extract_with_ai_summary(url, context="Extract content for research and analysis")
                
                if result.get('success') and result.get('content'):
                    return {
                        'title': result.get('title', 'No title'),
                        'content': result.get('content', ''),
                        'url': url,
                        'author': result.get('author'),
                        'description': result.get('description'),
                        'reading_time': result.get('reading_time', 0),
                        'extraction_method': result.get('extraction_method', 'enhanced'),
                        'ai_enhanced': result.get('ai_enhanced', False),
                        'quality_metrics': result.get('quality_metrics', {}),
                        'images': await self._extract_images(url) if url else [],
                        'success': True
                    }
                else:
                    # Fall back to BeautifulSoup if Content Core parsing fails
                    logger.warning(f"Content Core parsing failed for {url}, falling back to BeautifulSoup")
                    return await self._extract_with_beautifulsoup(url)
            else:
                # Use original BeautifulSoup extraction
                return await self._extract_with_beautifulsoup(url)
            
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return {
                'title': f"Error fetching {url}",
                'content': f"Failed to fetch content: {str(e)}",
                'url': url,
                'error': str(e),
                'success': False
            }
    
    async def fetch_multiple_pages(self, urls: List[str]) -> List[Dict[str, str]]:
        """Fetch content from multiple URLs concurrently with rate limiting"""
        logger.info(f"Fetching content from {len(urls)} URLs")

        # Limit concurrent requests to avoid overwhelming servers and triggering anti-bot
        semaphore = asyncio.Semaphore(3)  # Reduced from 5 to 3

        async def fetch_with_semaphore(url: str, index: int) -> Dict[str, str]:
            async with semaphore:
                # Add delay between requests to appear more human-like
                if index > 0:
                    delay = 1.5 + (index * 0.5)  # Increasing delay: 1.5s, 2s, 2.5s, etc.
                    await asyncio.sleep(min(delay, 5))  # Cap at 5 seconds
                    logger.debug(f"Delayed {delay:.1f}s before fetching {url}")
                return await self.fetch_page_content(url)

        tasks = [fetch_with_semaphore(url, i) for i, url in enumerate(urls)]
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
    
    async def _extract_images(self, url: str) -> List[Dict[str, str]]:
        """Extract images from a web page"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            images = []
            
            # Find all img tags
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                src = img.get('src')
                if not src:
                    continue
                
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = f"https:{src}"
                elif src.startswith('/'):
                    src = urljoin(url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                
                # Get image metadata
                alt_text = img.get('alt', '').strip()
                title = img.get('title', '').strip()
                width = img.get('width')
                height = img.get('height')

                # Calculate priority score for smarter filtering
                priority_score = 0

                # Size-based scoring (if dimensions available)
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        # Skip tiny images (likely icons)
                        if w < 30 or h < 30:
                            continue
                        # Bonus for larger images (likely content)
                        if w > 200 or h > 200:
                            priority_score += 2
                        elif w > 100 or h > 100:
                            priority_score += 1
                    except (ValueError, TypeError):
                        pass

                # Text-based scoring (alt text and title indicate importance)
                combined_text = (alt_text + ' ' + title).lower()

                # High priority keywords (educational content)
                if any(term in combined_text for term in
                      ['diagram', 'chart', 'graph', 'flow', 'process', 'architecture',
                       'screenshot', 'example', 'illustration', 'figure', 'visual', 'demo']):
                    priority_score += 3

                # Medium priority (descriptive alt text suggests content image)
                elif len(alt_text) > 20:
                    priority_score += 1

                # Skip obvious decorative images
                skip_patterns = ['icon', 'logo', 'avatar', 'badge', 'button', 'arrow', 'bullet']
                if any(pattern in src.lower() for pattern in skip_patterns):
                    # Only skip if there's no descriptive text
                    if priority_score == 0:
                        continue

                image_info = {
                    'src': src,
                    'alt': alt_text,
                    'title': title,
                    'width': width,
                    'height': height,
                    'priority_score': priority_score
                }

                images.append(image_info)

            # Validate image URLs (check for 403 Forbidden and other access issues)
            validated_images = await self._validate_image_urls(images)

            # Sort by priority score (higher is better) and limit to most relevant
            validated_images.sort(key=lambda x: x.get('priority_score', 0), reverse=True)

            # Return up to 15 images (increased from 10 to be less restrictive)
            return validated_images[:15]
            
        except Exception as e:
            logger.warning(f"Failed to extract images from {url}: {e}")
            return []

    async def _validate_image_urls(self, images: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate image URLs to filter out protected/inaccessible images"""
        validated = []

        for image in images:
            src = image.get('src')
            if not src:
                continue

            try:
                # Send HEAD request to check if image is accessible
                # Use custom headers to mimic a browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                }

                response = await self.session.head(
                    src,
                    headers=headers,
                    timeout=5.0,
                    follow_redirects=True
                )

                # Check if accessible
                if response.status_code == 200:
                    validated.append(image)
                    logger.debug(f"✓ Image accessible: {src[:80]}")
                elif response.status_code == 403:
                    logger.info(f"✗ Image blocked (403 Forbidden): {src[:80]} - Skipping")
                elif response.status_code == 404:
                    logger.info(f"✗ Image not found (404): {src[:80]} - Skipping")
                else:
                    logger.info(f"✗ Image returned {response.status_code}: {src[:80]} - Skipping")

            except Exception as e:
                # If HEAD request fails, try GET with timeout
                try:
                    response = await self.session.get(
                        src,
                        headers=headers,
                        timeout=5.0,
                        follow_redirects=True
                    )
                    if response.status_code == 200:
                        validated.append(image)
                        logger.debug(f"✓ Image accessible (GET): {src[:80]}")
                    else:
                        logger.info(f"✗ Image inaccessible: {src[:80]} - {e}")
                except Exception as get_error:
                    logger.info(f"✗ Failed to validate image: {src[:80]} - {get_error}")

        logger.info(f"📸 Image validation: {len(validated)}/{len(images)} images accessible")
        return validated

    async def close(self):
        """Close the HTTP client"""
        await self.session.aclose()

# Global instance
web_scraper = WebScraperService()
