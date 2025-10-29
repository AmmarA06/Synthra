"""
Content Core Parser for Synthra
Advanced content extraction using the Content Core library
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ContentCoreParser:
    """
    Advanced content parser using Content Core library
    Handles multiple formats with AI-powered extraction
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
        self.content_core = None
        
        try:
            import content_core as cc
            self.content_core = cc
            logger.info("Content Core parser initialized successfully")
        except ImportError as e:
            logger.warning(f"Content Core library not available: {e}")
            logger.info("Falling back to basic parsing methods")
            self.content_core = None
        
    async def extract_content(self, source: str, source_type: str = "auto") -> Dict[str, Any]:
        """
        Extract content using Content Core with automatic format detection
        
        Args:
            source: URL, file path, or raw content
            source_type: "url", "file", "content", or "auto"
            
        Returns:
            Dict with extracted content, metadata, and quality metrics
        """
        if not self.content_core:
            return await self._fallback_extraction(source, source_type)
        
        try:
            # Prepare extraction request
            extraction_request = {}
            
            if source_type == "auto":
                # Auto-detect source type
                if source.startswith(("http://", "https://")):
                    extraction_request["url"] = source
                elif os.path.exists(source):
                    extraction_request["file_path"] = source
                else:
                    extraction_request["content"] = source
            elif source_type == "url":
                extraction_request["url"] = source
            elif source_type == "file":
                extraction_request["file_path"] = source
            else:
                extraction_request["content"] = source
            
            # Extract content using Content Core
            result = await self.content_core.extract_content(extraction_request)
            
            # Process the result
            if hasattr(result, 'content') and result.content:
                return {
                    'success': True,
                    'content': result.content,
                    'title': getattr(result, 'title', 'Extracted Content'),
                    'metadata': {
                        'source_type': getattr(result, 'source_type', source_type),
                        'extraction_method': 'content_core',
                        'timestamp': datetime.now().isoformat(),
                        'content_length': len(result.content),
                        'has_structured_data': hasattr(result, 'structured_data')
                    },
                    'quality_metrics': {
                        'content_length': len(result.content),
                        'estimated_reading_time': self._estimate_reading_time(result.content),
                        'extraction_confidence': 'high'  # Content Core is generally high quality
                    }
                }
            else:
                logger.warning("Content Core returned empty result")
                return await self._fallback_extraction(source, source_type)
                
        except Exception as e:
            logger.error(f"Content Core extraction failed: {e}")
            return await self._fallback_extraction(source, source_type)
    
    async def extract_and_clean(self, source: str, source_type: str = "auto") -> Dict[str, Any]:
        """
        Extract and clean content using Content Core's cleanup functionality
        """
        if not self.content_core:
            return await self.extract_content(source, source_type)
        
        try:
            # First extract the content
            extraction_result = await self.extract_content(source, source_type)
            
            if not extraction_result.get('success'):
                return extraction_result
            
            # Clean the content using Content Core
            cleaned_content = await self.content_core.clean(extraction_result['content'])
            
            # Update the result with cleaned content
            extraction_result['content'] = cleaned_content
            extraction_result['metadata']['cleaned'] = True
            extraction_result['metadata']['cleaning_method'] = 'content_core'
            
            logger.info(f"Content extracted and cleaned: {len(cleaned_content)} chars")
            return extraction_result
            
        except Exception as e:
            logger.error(f"Content Core cleaning failed: {e}")
            return await self.extract_content(source, source_type)
    
    async def extract_with_ai_summary(self, source: str, context: str = None, source_type: str = "auto") -> Dict[str, Any]:
        """
        Extract content and generate AI summary using Content Core
        """
        if not self.content_core:
            return await self.extract_content(source, source_type)
        
        try:
            # Extract content
            extraction_result = await self.extract_content(source, source_type)
            
            if not extraction_result.get('success'):
                return extraction_result
            
            # Skip AI summary generation since Content Core requires OpenAI API key
            # We're using Gemini for AI operations, so just return the extracted content
            logger.debug("Skipping Content Core AI summary - using Gemini for AI operations instead")
            extraction_result['ai_summary'] = None
            extraction_result['metadata']['has_ai_summary'] = False
            extraction_result['metadata']['summary_context'] = context or "AI summary skipped"
            
            logger.info(f"Content extracted without AI summary: {len(extraction_result.get('content', ''))} chars")
            return extraction_result
            
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return await self.extract_content(source, source_type)
    
    async def _fallback_extraction(self, source: str, source_type: str) -> Dict[str, Any]:
        """
        Fallback extraction method when Content Core is not available
        """
        try:
            if source_type == "url" or (source_type == "auto" and source.startswith(("http://", "https://"))):
                # Use simple requests + BeautifulSoup fallback
                import requests
                from bs4 import BeautifulSoup
                
                response = requests.get(source, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Extract text content
                content = soup.get_text()
                # Clean up whitespace
                content = '\n'.join(line.strip() for line in content.splitlines() if line.strip())
                
                title = soup.title.string if soup.title else "Extracted Content"
                
                return {
                    'success': True,
                    'content': content,
                    'title': title.strip() if title else "Extracted Content",
                    'metadata': {
                        'source_type': 'url',
                        'extraction_method': 'fallback_beautifulsoup',
                        'timestamp': datetime.now().isoformat(),
                        'content_length': len(content)
                    },
                    'quality_metrics': {
                        'content_length': len(content),
                        'estimated_reading_time': self._estimate_reading_time(content),
                        'extraction_confidence': 'medium'
                    }
                }
            else:
                # Handle raw content
                content = source
                return {
                    'success': True,
                    'content': content,
                    'title': 'Raw Content',
                    'metadata': {
                        'source_type': 'content',
                        'extraction_method': 'fallback_raw',
                        'timestamp': datetime.now().isoformat(),
                        'content_length': len(content)
                    },
                    'quality_metrics': {
                        'content_length': len(content),
                        'estimated_reading_time': self._estimate_reading_time(content),
                        'extraction_confidence': 'low'
                    }
                }
                
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return {
                'success': False,
                'content': '',
                'title': 'Extraction Failed',
                'error': str(e),
                'metadata': {
                    'extraction_method': 'failed',
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def _estimate_reading_time(self, text: str, wpm: int = 200) -> int:
        """Estimate reading time in minutes"""
        if not text:
            return 0
        word_count = len(text.split())
        return max(1, round(word_count / wpm))
    
    def parse_dictionary_content(self, dict_string: str) -> str:
        """
        Robust parsing of dictionary-formatted content strings
        This handles the specific issue we've been seeing
        """
        if not dict_string.startswith("{'content':"):
            return dict_string
        
        try:
            # Method 1: Try ast.literal_eval (safest)
            import ast
            content_dict = ast.literal_eval(dict_string)
            if isinstance(content_dict, dict) and 'content' in content_dict:
                logger.debug(f"Extracted content using ast.literal_eval: {len(content_dict['content'])} chars")
                return content_dict['content']
        except Exception as e:
            logger.debug(f"ast.literal_eval failed: {e}")
        
        try:
            # Method 2: Regex extraction (most robust)
            import re
            # Look for 'content': followed by either single or double quoted string
            pattern = r"'content':\s*['\"](.+?)['\"]"
            match = re.search(pattern, dict_string, re.DOTALL)
            if match:
                content = match.group(1)
                # Unescape common escape sequences
                content = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                content = content.replace("\\'", "'").replace('\\"', '"')
                logger.debug(f"Extracted content using regex: {len(content)} chars")
                return content
        except Exception as e:
            logger.debug(f"Regex extraction failed: {e}")
        
        # If all methods fail, return the original string
        logger.warning("All content extraction methods failed, returning original string")
        return dict_string

