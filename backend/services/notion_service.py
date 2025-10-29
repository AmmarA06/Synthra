"""
Notion Service for Synthra
Handles Notion API integration for saving content
"""

import os
import logging
import re
import html
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urljoin, urlparse

from notion_client import AsyncClient
from shared.types import Summary, Highlight, Research

logger = logging.getLogger(__name__)

class NotionService:
    """Service for Notion integration"""

    def __init__(self, token: str):
        self.client = AsyncClient(auth=token)
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        # Initialize clean content parser (optimized for Notion)
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        from .clean_content_parser import CleanContentParser
        self.content_parser = CleanContentParser(gemini_api_key=gemini_api_key)
        # Cache for database schemas to avoid repeated API calls
        self._schema_cache = {}
        logger.info("Notion service initialized with CleanContentParser")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Notion API connection"""
        try:
            logger.info("Testing Notion connection...")
            user = await self.client.users.me()
            logger.info(f"Notion API response: {user}")
            logger.info(f"Response type: {type(user)}")
            
            # Handle case where user response is None or malformed
            if not user:
                logger.error("Notion API returned None response")
                return {
                    'success': False,
                    'error': 'Invalid response from Notion API'
                }
            
            # Extract user info with safe fallbacks
            user_name = 'Notion User'
            workspace_name = 'Notion Workspace'
            user_id = None
            
            if isinstance(user, dict):
                logger.info(f"User dict keys: {list(user.keys())}")
                logger.info(f"User dict content: {user}")
                
                # Try different ways to get user name/email
                user_name = (
                    user.get('name') or 
                    user.get('person', {}).get('email') or 
                    user.get('email') or 
                    'Notion User'
                )
                
                # Try different ways to get workspace name
                workspace_name = (
                    user.get('workspace_name') or 
                    user.get('workspace', {}).get('name') or 
                    'Notion Workspace'
                )
                
                user_id = user.get('id')
            else:
                logger.error(f"User response is not a dict: {type(user)}")
            
            result = {
                'success': True,
                'workspace': workspace_name,
                'user_id': user_id,
                'user_email': user_name
            }
            logger.info(f"Returning result: {result}")
            return result
        except Exception as e:
            logger.error(f"Notion connection test failed: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_databases(self) -> Dict[str, Any]:
        """Get available databases for the user"""
        try:
            logger.info("Getting Notion databases...")
            response = await self.client.search(
                query="",
                filter={"property": "object", "value": "database"},
                sort={"direction": "descending", "timestamp": "last_edited_time"}
            )
            logger.info(f"Search response: {response}")
            logger.info(f"Response type: {type(response)}")
            
            # Handle case where response is None or malformed
            if not response:
                logger.error("Notion search API returned None response")
                return {
                    'success': False,
                    'databases': [],
                    'error': 'Invalid response from Notion API'
                }
            
            if not isinstance(response, dict):
                logger.error(f"Notion search response is not a dict: {type(response)}")
                return {
                    'success': False,
                    'databases': [],
                    'error': f'Invalid response type from Notion API: {type(response)}'
                }
            
            databases = []
            results = response.get('results', [])
            logger.info(f"Found {len(results)} results")
            
            for i, item in enumerate(results):
                logger.info(f"Processing item {i}: {type(item)}")
                # Skip if item is None
                if not item:
                    logger.warning(f"Skipping None item at index {i}")
                    continue
                    
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict item at index {i}: {type(item)}")
                    continue
                # Extract title with better fallback handling
                title = 'Untitled Database'
                if item.get('title') and isinstance(item['title'], list) and len(item['title']) > 0:
                    title = item['title'][0].get('plain_text', title)
                elif item.get('title') and isinstance(item['title'], str):
                    title = item['title']
                
                # Clean up title - remove URLs and use a better fallback
                if title.startswith('http') or 'notion.so/icons/' in title:
                    title = 'Untitled Database'
                
                # Extract description
                description = ''
                if item.get('description') and isinstance(item['description'], list) and len(item['description']) > 0:
                    description = item['description'][0].get('plain_text', '')
                elif item.get('description') and isinstance(item['description'], str):
                    description = item['description']
                
                # Extract icon with proper null checking
                icon = ''
                icon_data = item.get('icon')
                if icon_data:
                    if icon_data.get('emoji'):
                        icon = icon_data['emoji']
                    elif icon_data.get('external', {}).get('url'):
                        icon = icon_data['external']['url']
                    elif icon_data.get('file', {}).get('url'):
                        icon = icon_data['file']['url']
                
                databases.append({
                    'id': item['id'],
                    'title': title,
                    'description': description,
                    'url': item.get('url', ''),
                    'icon': icon
                })
            
            result = {
                'success': True,
                'databases': databases
            }
            logger.info(f"Successfully retrieved {len(databases)} databases")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get databases: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'databases': []
            }
    
    async def authenticate(self, code: Optional[str] = None, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Handle Notion OAuth authentication (if needed for public integration)"""
        # For internal integrations, authentication is handled via token
        # This method is here for future OAuth implementation
        
        try:
            # Test the current token
            user = await self.client.users.me()
            
            return {
                'access_token': 'existing_token',
                'workspace_name': user.get('name', 'Unknown'),
                'user_id': user.get('id')
            }
            
        except Exception as e:
            logger.error(f"Error in Notion authentication: {str(e)}")
            raise
    
    async def save_content(
        self, 
        content: Any, 
        content_type: str, 
        title: Optional[str] = None,
        url: Optional[str] = None,
        database_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save content to Notion database with better error handling"""
        
        # Use provided database_id or fall back to environment variable
        target_database_id = database_id or self.database_id
        if not target_database_id:
            raise ValueError("Notion database ID not provided")
        
        try:
            # Prepare page properties based on content type
            # (This will fetch database schema if needed, which validates access)
            properties = await self._prepare_page_properties(content, content_type, title, url, target_database_id)

            # Prepare content blocks
            children_blocks = await self._prepare_page_content(content, content_type, title or '', url or '')
            logger.info(f"Prepared {len(children_blocks)} blocks for Notion page")

            # Ensure we have blocks to add
            if not children_blocks or len(children_blocks) == 0:
                logger.warning("No blocks generated, creating minimal page")
                children_blocks = []

            # Limit to 100 blocks (Notion API hard limit)
            if len(children_blocks) > 100:
                logger.warning(f"Too many blocks ({len(children_blocks)}), truncating to 100")
                children_blocks = children_blocks[:100]

            # Create the page with blocks
            page = await self.client.pages.create(
                parent={"database_id": target_database_id},
                properties=properties,
                children=children_blocks
            )

            return {
                'page_id': page['id'],
                'page_url': page['url'],
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error saving to Notion: {str(e)}")
            # Provide more specific error messages
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "forbidden" in error_msg:
                raise ValueError("Notion integration not authorized. Please check your token and database permissions.")
            elif "not found" in error_msg or "object_not_found" in error_msg:
                raise ValueError("Notion database not found. Please check your database ID.")
            elif "invalid_request" in error_msg:
                raise ValueError("Invalid request to Notion. Please check your content format.")
            else:
                raise ValueError(f"Failed to save to Notion: {str(e)}")

    async def delete_page(self, page_id: str) -> bool:
        """Delete a Notion page (archive it)"""
        try:
            await self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            logger.info(f"Successfully archived/deleted page {page_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete page {page_id}: {e}")
            raise ValueError(f"Failed to delete Notion page: {str(e)}")

    async def _prepare_page_properties(
        self, 
        content: Any, 
        content_type: str, 
        title: Optional[str],
        url: Optional[str],
        database_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare page properties for Notion"""
        
        # Get database schema to know which properties exist
        database_schema = await self._get_database_schema(database_id)
        
        properties = {}
        
        # Always set the title property (required)
        title_prop = self._find_property_by_type(database_schema, "title")
        if title_prop:
            properties[title_prop] = {
                "title": [
                    {
                        "text": {
                            "content": title or f"Synthra {content_type.title()}"
                        }
                    }
                ]
            }
        
        # Set Type property if it exists
        type_prop = self._find_property_by_name(database_schema, ["Type", "type", "Content Type", "content_type"])
        if type_prop:
            properties[type_prop] = {
                "select": {
                    "name": content_type.title()
                }
            }
        
        # Set Created/Date property if it exists
        date_prop = self._find_property_by_name(database_schema, ["Created", "created", "Date", "date", "Created Time", "created_time"])
        if date_prop:
            properties[date_prop] = {
                "date": {
                    "start": datetime.now().isoformat()
            }
        }
        
        # Set URL property if it exists
        if url:
            url_prop = self._find_property_by_name(database_schema, ["URL", "url", "Link", "link", "Source", "source"])
            if url_prop:
                properties[url_prop] = {
                "url": url
            }
        
        # Add content-specific properties
        if content_type == "summary" and hasattr(content, 'reading_time_minutes'):
            reading_time_prop = self._find_property_by_name(database_schema, ["Reading Time", "reading_time", "Time", "time", "Minutes", "minutes"])
            if reading_time_prop:
                properties[reading_time_prop] = {
                "number": content.reading_time_minutes
            }
        
        return properties
    
    async def _get_database_schema(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """Get database schema to understand available properties (cached)"""
        try:
            target_database_id = database_id or self.database_id
            if not target_database_id:
                logger.warning("No database ID provided, returning empty schema")
                return {}

            # Check cache first
            if target_database_id in self._schema_cache:
                logger.debug(f"Using cached schema for database {target_database_id}")
                return self._schema_cache[target_database_id]

            # Retrieve database to get schema
            logger.debug(f"Fetching schema for database {target_database_id}")
            database = await self.client.databases.retrieve(database_id=target_database_id)
            schema = database.get('properties', {})

            # Cache it
            self._schema_cache[target_database_id] = schema
            return schema
        except Exception as e:
            logger.error(f"Failed to get database schema: {str(e)}")
            return {}
    
    def _find_property_by_type(self, schema: Dict[str, Any], property_type: str) -> Optional[str]:
        """Find a property by its type (e.g., 'title', 'select', 'date')"""
        for prop_name, prop_data in schema.items():
            if prop_data.get('type') == property_type:
                return prop_name
        return None
    
    def _find_property_by_name(self, schema: Dict[str, Any], possible_names: list) -> Optional[str]:
        """Find a property by trying multiple possible names"""
        for prop_name in possible_names:
            if prop_name in schema:
                return prop_name
        return None
    
    async def _prepare_page_content(self, content: Any, content_type: str, title: str = '', url: str = '') -> list:
        """Prepare page content blocks for Notion"""

        blocks = []

        # Auto-detect content type and convert dictionary format to proper objects
        parsed_content = self._try_parse_content_dict(content)

        # For ALL content types, use CleanContentParser for proper markdown formatting
        # This ensures consistent, beautiful formatting regardless of content type

        # Use provided title and URL (passed as parameters)
        # Extract raw content based on content type
        raw_content = ''

        if content_type == "summary" or self._is_summary_dict(parsed_content):
            # Extract from Summary object
            summary_obj = parsed_content if not isinstance(parsed_content, dict) else self._dict_to_summary_object(parsed_content)

            # Use title/url from summary if not provided as parameters
            if not title:
                title = getattr(summary_obj, 'title', 'Study Notes')
            if not url:
                url = getattr(summary_obj, 'url', '')

            # Reconstruct content from summary fields for better formatting
            content_parts = []
            if hasattr(summary_obj, 'summary') and summary_obj.summary:
                content_parts.append(str(summary_obj.summary))
            if hasattr(summary_obj, 'key_points') and summary_obj.key_points:
                content_parts.append('\n\nKey Points:\n' + '\n'.join([f'- {p}' for p in summary_obj.key_points]))
            if hasattr(summary_obj, 'key_concepts') and summary_obj.key_concepts:
                content_parts.append('\n\nKey Concepts:\n' + '\n'.join([f'- {c}' for c in summary_obj.key_concepts]))

            raw_content = '\n\n'.join(content_parts)

        elif content_type == "highlight" or (isinstance(content, list) and len(content) > 0 and hasattr(content[0], 'term')):
            # Use old formatter for highlights (less critical)
            blocks.extend(self._format_highlight_content(content))
            return blocks

        elif content_type == "research" or (hasattr(content, 'summary') and hasattr(content, 'key_findings')):
            # Use old formatter for research (less critical)
            blocks.extend(self._format_research_content(content))
            return blocks

        else:
            # Generic content - use as-is
            raw_content = str(content)

        # Extract images if we have a URL (for content type saves)
        images = []
        if url and not url.startswith(('chrome-extension://', 'moz-extension://', 'about:', 'data:')):
            try:
                from .web_scraper import web_scraper
                logger.info(f"📸 Extracting images from {url} for Notion")
                images = await web_scraper._extract_images(url)
                logger.info(f"📸 Found {len(images)} images for Notion page")
                if images:
                    logger.info(f"📸 Image URLs: {[img.get('src', '')[:60] for img in images[:3]]}")
                else:
                    logger.warning(f"📸 No images extracted from {url}")
            except Exception as e:
                logger.error(f"📸 Failed to extract images: {e}", exc_info=True)

        # Use CleanContentParser to create beautifully formatted study notes
        try:
            blocks = self.content_parser.parse_and_format_for_notion(
                raw_content=raw_content,
                title=title,
                url=url,
                use_ai=True,
                images=images  # Pass extracted images
            )
            logger.info(f"CleanContentParser created {len(blocks)} Notion blocks")
        except Exception as e:
            logger.error(f"CleanContentParser failed: {e}")
            # Fallback to basic formatting
            blocks = [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Error parsing content: {str(e)}"}}]
                }
            }]
        
        # Ensure we have at least some content
        if not blocks or len(blocks) == 0:
            logger.error("No blocks generated after parsing! Creating fallback block")
            blocks = [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Content: {raw_content[:1000] if raw_content else 'No content available'}"}}]
                }
            }]

        # Check if we exceed the 100 block limit
        if len(blocks) > 100:
            logger.warning(f"Too many blocks ({len(blocks)}), consolidating to stay under 100 blocks")
            # Consolidate blocks by merging content
            consolidated_blocks = self._consolidate_blocks(blocks)
            return consolidated_blocks

        logger.info(f"Returning {len(blocks)} blocks from _prepare_page_content")
        return blocks
    
    def _convert_text_to_notion_blocks(self, text: str) -> list:
        """Convert plain text with markdown to Notion blocks"""
        blocks = []
        lines = text.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Empty line - finish current paragraph if any
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": ' '.join(current_paragraph)}
                            }]
                        }
                    })
                    current_paragraph = []
                continue
            
            # Handle markdown headers
            if line.startswith('# '):
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": ' '.join(current_paragraph)}
                            }]
                        }
                    })
                    current_paragraph = []
                
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": line[2:].strip()}
                        }]
                    }
                })
            elif line.startswith('## '):
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": ' '.join(current_paragraph)}
                            }]
                        }
                    })
                    current_paragraph = []
                
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": line[3:].strip()}
                        }]
                    }
                })
            elif line.startswith('### '):
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": ' '.join(current_paragraph)}
                            }]
                        }
                    })
                    current_paragraph = []
                
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": line[4:].strip()}
                        }]
                    }
                })
            elif line.lstrip().startswith(('- ', '• ')):
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": ' '.join(current_paragraph)}
                            }]
                        }
                    })
                    current_paragraph = []

                # Calculate indentation level (number of spaces before bullet)
                indent_level = len(line) - len(line.lstrip())
                # Get the bullet content
                stripped_line = line.lstrip()
                bullet_content = stripped_line[2:].strip() if stripped_line.startswith(('- ', '• ')) else stripped_line.strip()

                # Create the bullet block
                bullet_block = {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": bullet_content}
                        }]
                    }
                }

                # If this is a nested bullet (indented), add it as a child of the last bullet
                if indent_level > 0 and blocks and blocks[-1].get("type") == "bulleted_list_item":
                    # Add as child to the previous bullet
                    if "children" not in blocks[-1]["bulleted_list_item"]:
                        blocks[-1]["bulleted_list_item"]["children"] = []
                    blocks[-1]["bulleted_list_item"]["children"].append(bullet_block)
                else:
                    # Top-level bullet
                    blocks.append(bullet_block)
            else:
                # Regular text line - add to current paragraph
                current_paragraph.append(line)
        
        # Add any remaining paragraph
        if current_paragraph:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": ' '.join(current_paragraph)}
                    }]
                }
            })
        
        return blocks
    
    def _split_long_content(self, content: str, max_length: int = 2000, max_blocks: int = 100) -> list:
        """Split long content into Notion blocks respecting both character and block limits"""
        blocks = []
        
        # If content is short enough, return as single block
        if len(content) <= max_length:
            return [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }]
        
        # Calculate optimal chunk size to stay under block limit
        total_length = len(content)
        optimal_chunk_size = max(total_length // max_blocks, max_length)
        
        # Ensure chunk size doesn't exceed Notion's limit
        optimal_chunk_size = min(optimal_chunk_size, max_length)
        
        logger.info(f"Content length: {total_length}, Optimal chunk size: {optimal_chunk_size}, Max blocks: {max_blocks}")
        
        # Split content into chunks
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed the optimal chunk size
            test_chunk = current_chunk + ('\n\n' if current_chunk else '') + paragraph
            
            if len(test_chunk) <= optimal_chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If single paragraph is too long, split it further
                if len(paragraph) > optimal_chunk_size:
                    # Split by sentences
                    sentences = paragraph.split('. ')
                    temp_chunk = ""
                    
                    for sentence in sentences:
                        test_sentence_chunk = temp_chunk + ('. ' if temp_chunk else '') + sentence
                        
                        if len(test_sentence_chunk) <= optimal_chunk_size:
                            temp_chunk = test_sentence_chunk
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = sentence
                    
                    current_chunk = temp_chunk
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # If we still have too many chunks, merge them
        if len(chunks) > max_blocks:
            logger.warning(f"Too many chunks ({len(chunks)}), merging to stay under {max_blocks} blocks")
            merged_chunks = []
            current_merged = ""
            
            for chunk in chunks:
                test_merged = current_merged + ('\n\n' if current_merged else '') + chunk
                
                if len(test_merged) <= 1900 and len(merged_chunks) < max_blocks - 1:
                    current_merged = test_merged
                else:
                    if current_merged:
                        merged_chunks.append(current_merged)
                    current_merged = chunk
            
            if current_merged:
                merged_chunks.append(current_merged)
            
            chunks = merged_chunks
        
        # Create blocks for each chunk
        for i, chunk in enumerate(chunks):
            # Final safety check
            if len(chunk) > 2000:
                logger.warning(f"Chunk {i} is still too long: {len(chunk)} chars, truncating...")
                chunk = chunk[:1997] + "..."
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": chunk
                            }
                        }
                    ]
                }
            })
        
        logger.info(f"Created {len(blocks)} blocks for content of length {len(content)}")
        return blocks
    
    def _consolidate_blocks(self, blocks: list, max_blocks: int = 100) -> list:
        """Consolidate blocks to stay under the 100 block limit"""
        if len(blocks) <= max_blocks:
            return blocks
        
        logger.info(f"Consolidating {len(blocks)} blocks to stay under {max_blocks} blocks")
        
        # Extract text content from all blocks
        all_text = []
        for block in blocks:
            if block.get('type') == 'paragraph' and block.get('paragraph', {}).get('rich_text'):
                text_content = block['paragraph']['rich_text'][0].get('text', {}).get('content', '')
                if text_content:
                    all_text.append(text_content)
        
        # Join all text and split into fewer, larger blocks
        combined_text = '\n\n'.join(all_text)
        
        # Calculate how many blocks we need
        blocks_needed = min(max_blocks, len(blocks))
        chunk_size = len(combined_text) // blocks_needed
        
        # Ensure chunk size doesn't exceed 1900 characters
        chunk_size = min(chunk_size, 1900)
        
        consolidated_blocks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = combined_text.split('\n\n')
        
        for paragraph in paragraphs:
            test_chunk = current_chunk + ('\n\n' if current_chunk else '') + paragraph
            
            if len(test_chunk) <= chunk_size and len(consolidated_blocks) < blocks_needed - 1:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    consolidated_blocks.append({
                "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                                    "text": {
                                        "content": current_chunk
                                    }
                        }
                    ]
                }
            })
                current_chunk = paragraph
            
        # Add the last chunk
        if current_chunk:
            consolidated_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": current_chunk
                            }
                        }
                    ]
                }
            })
        
        logger.info(f"Consolidated to {len(consolidated_blocks)} blocks")
        return consolidated_blocks
    
    def _format_summary_content(self, summary: Summary) -> list:
        """Format summary content for Notion with enhanced markdown styling"""
        blocks = []
        
        # Title with emoji
        if hasattr(summary, 'title') and summary.title:
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"📚 {summary.title}"}
                        }
                    ]
                }
            })
        
        # Main summary with emoji
        if summary.summary:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "📝 Summary"}
                        }
                    ]
                }
            })
            
            content_str = str(summary.summary)
            blocks.extend(self._smart_split_content(content_str))
        
        # Key points with emoji
        if summary.key_points:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "🎯 Key Points"}
                        }
                    ]
                }
            })

            for point in summary.key_points:
                # Check if point contains nested bullets (newlines with indented bullets)
                point_str = str(point)
                if '\n' in point_str and any(line.lstrip().startswith(('- ', '• ')) for line in point_str.split('\n')[1:]):
                    # Parse nested structure
                    lines = point_str.split('\n')
                    main_text = lines[0].strip()

                    # Create main bullet
                    main_bullet = {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": self._convert_markdown_to_rich_text(main_text),
                            "children": []
                        }
                    }

                    # Add nested bullets as children
                    for line in lines[1:]:
                        line = line.strip()
                        if line.startswith(('- ', '• ')):
                            child_text = line[2:].strip()
                            main_bullet["bulleted_list_item"]["children"].append({
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": self._convert_markdown_to_rich_text(child_text)
                                }
                            })

                    blocks.append(main_bullet)
                else:
                    # Regular flat bullet
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": self._convert_markdown_to_rich_text(point_str)
                        }
                    })
        
        # Key concepts with emoji
        if hasattr(summary, 'key_concepts') and summary.key_concepts:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "💡 Key Concepts"}
                        }
                    ]
                }
            })
            
            # Display each concept as a separate bulleted list item
            for concept in summary.key_concepts:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self._convert_markdown_to_rich_text(concept)
                    }
                })
        
        # Skip reading time for study notes - not needed
        
        # Add educational images with strict filtering
        if hasattr(summary, 'images') and summary.images:
            # Apply strict filtering for educational/content images only
            educational_images = []
            for img in summary.images:
                img_alt = img.get('alt', '').lower()
                img_src = img.get('src', '').lower()
                img_title = img.get('title', '').lower()
                
                # Smart filtering - skip clearly non-educational images
                skip_keywords = [
                    'app store', 'play store', 'appstore', 'playstore', 'googleplay',
                    'apple', 'download', 'rating', 'star', 'badge', 'advertisement', 
                    'ad', 'sponsor', 'promo', 'marketing', 'brand', 'social', 'profile',
                    'avatar', 'thumbnail', 'video', 'youtube', 'vimeo', 'player'
                ]
                
                # Skip if contains critical skip keywords
                if any(keyword in img_alt or keyword in img_src or keyword in img_title for keyword in skip_keywords):
                    continue
                
                # Prioritize educational content
                high_value_keywords = [
                    'workflow', 'trigger', 'node', 'automation', 'integration', 'setup',
                    'configuration', 'gmail', 'slack', 'n8n', 'diagram', 'graph', 'chart', 
                    'code', 'example', 'illustration', 'tutorial', 'step', 'process', 
                    'algorithm', 'flowchart', 'tree', 'structure', 'visualization', 
                    'screenshot', 'demo', 'implementation', 'interface', 'dashboard'
                ]
                
                has_educational_content = any(keyword in img_alt or keyword in img_src or keyword in img_title 
                                            for keyword in high_value_keywords)
                
                # Check for descriptive content or educational domains
                has_good_alt = img_alt and len(img_alt) > 8 and not img_alt.lower().startswith(('image', 'img', 'picture', 'photo'))
                is_educational_domain = any(domain in img_src for domain in [
                    'geeksforgeeks', 'stackoverflow', 'github', 'docs.', 'tutorials',
                    'xray.tech', 'medium.com', 'dev.to', 'codepen'
                ])
                
                # Include if it has educational value OR good descriptive content
                if has_educational_content or has_good_alt or is_educational_domain:
                    # Determine priority
                    if has_educational_content:
                        priority = 'high'
                    elif has_good_alt and is_educational_domain:
                        priority = 'medium'
                    else:
                        priority = 'low'
                    
                    educational_images.append({
                        'img': img,
                        'priority': priority
                    })
            
            # Sort by priority and limit to top 1-2 most relevant
            educational_images.sort(key=lambda x: (x['priority'] == 'high', len(x['img'].get('alt', ''))), reverse=True)
            
            if educational_images:
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "📊 Visual Examples"}
                            }
                        ]
                    }
                })
                
                for item in educational_images[:3]:  # Limit to 3 most relevant images
                    img = item['img']
                    img_url = img.get('src', '')
                    
                    if img_url and img_url.startswith(('http://', 'https://')):
                        blocks.append({
                            "object": "block",
                            "type": "image",
                            "image": {
                                "type": "external",
                                "external": {"url": img_url},
                                "caption": []
                            }
                        })
                        
                        # Add meaningful description
                        description = self._generate_image_description(img)
                        if description:
                            blocks.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": f"💡 {description}"},
                                            "annotations": {
                                                "italic": True,
                                                "bold": False,
                                                "strikethrough": False,
                                                "underline": False,
                                                "code": False,
                                                "color": "default"
                                            }
                                        }
                                    ]
                                }
                            })

        # Skip timestamp for study notes - not needed for learning
        
        return blocks
    
    def _generate_image_description(self, img: dict) -> str:
        """Generate a meaningful description for educational images"""
        alt_text = img.get('alt', '')
        title_text = img.get('title', '')
        src_url = img.get('src', '')
        
        # Use alt text if it's descriptive
        if alt_text and len(alt_text) > 8 and not alt_text.lower().startswith(('image', 'img', 'picture', 'photo')):
            return alt_text
        
        # Use title if alt text isn't good
        if title_text and len(title_text) > 8:
            return title_text
        
        # Generate description based on URL patterns and content
        url_lower = src_url.lower()
        
        # Specific workflow/automation descriptions
        if any(keyword in url_lower for keyword in ['workflow', 'trigger', 'node', 'n8n']):
            return "Workflow automation interface showing node configuration"
        elif any(keyword in url_lower for keyword in ['gmail', 'slack', 'integration']):
            return "Integration setup demonstrating app connection"
        elif 'graph' in url_lower:
            return "Graph visualization showing data structure and relationships"
        elif 'diagram' in url_lower:
            return "Diagram illustrating the concept or process"
        elif any(keyword in url_lower for keyword in ['code', 'implementation']):
            return "Code example demonstrating the implementation"
        elif any(keyword in url_lower for keyword in ['example', 'demo']):
            return "Example showing practical application"
        elif any(keyword in url_lower for keyword in ['algorithm', 'flowchart']):
            return "Algorithm visualization or flowchart"
        elif any(keyword in url_lower for keyword in ['interface', 'screenshot', 'dashboard']):
            return "Interface screenshot showing the application"
        elif any(keyword in url_lower for keyword in ['tutorial', 'step', 'guide']):
            return "Tutorial step demonstrating the process"
        
        # Fallback to generic but informative description
        return "Visual example illustrating the concept"
    
    def _smart_split_content(self, content: str) -> list:
        """
        Smart content splitting that respects Notion's 2000 character limit per rich text element.
        Preserves natural AI output by breaking at optimal points.
        """
        if len(content) <= 2000:
            return [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": self._convert_markdown_to_rich_text(content)
                }
            }]
        
        blocks = []
        remaining = content
        
        while remaining:
            if len(remaining) <= 2000:
                blocks.append({
                    "object": "block",
                    "type": "paragraph", 
                    "paragraph": {
                        "rich_text": self._convert_markdown_to_rich_text(remaining)
                    }
                })
                break
            
            # Find optimal break point within 2000 chars
            chunk = remaining[:2000]
            break_point = self._find_best_break_point(chunk)
            
            if break_point == -1:
                # Force break at last space if no good break point
                break_point = chunk.rfind(' ')
                if break_point == -1:
                    break_point = 1999  # Emergency fallback
            
            # Create block for this chunk
            chunk_content = remaining[:break_point].strip()
            if chunk_content:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": self._convert_markdown_to_rich_text(chunk_content)
                    }
                })
            
            # Move to next part
            remaining = remaining[break_point:].strip()
        
        return blocks
    
    def _find_best_break_point(self, text: str) -> int:
        """Find the best place to break text, prioritizing natural boundaries"""
        max_pos = len(text)
        min_pos = int(max_pos * 0.5)  # Don't break too early
        
        # Priority 1: Double newlines (paragraph breaks)
        for i in range(max_pos - 2, min_pos - 1, -1):
            if text[i:i+2] == '\n\n':
                return i + 2
        
        # Priority 2: Single newlines with list markers
        import re
        for match in re.finditer(r'\n\s*[-•*]\s+|\n\s*\d+\.\s+', text):
            if min_pos <= match.start() <= max_pos:
                return match.start()
        
        # Priority 3: Sentence endings
        for i in range(max_pos - 2, min_pos - 1, -1):
            if text[i:i+2] in ['. ', '! ', '? ']:
                return i + 2
        
        # Priority 4: Commas and semicolons (in latter half for better flow)
        for i in range(max_pos - 2, int(max_pos * 0.7) - 1, -1):
            if text[i:i+2] in [', ', '; ']:
                return i + 2
        
        # Priority 5: Any space
        for i in range(max_pos - 1, min_pos - 1, -1):
            if text[i] == ' ':
                return i + 1
        
        return -1  # No good break point found
    
    def _try_parse_content_dict(self, content: Any) -> Any:
        """Try to parse content if it's a stringified dictionary, otherwise return as-is"""
        if not isinstance(content, str):
            return content
        
        # Check if it looks like a dictionary string
        content_str = content.strip()
        if not (content_str.startswith('{') and content_str.endswith('}')):
            return content
        
        # Try to parse as dictionary using multiple strategies
        try:
            # Strategy 1: Try ast.literal_eval (safest)
            import ast
            return ast.literal_eval(content_str)
        except (ValueError, SyntaxError):
            try:
                # Strategy 2: Try JSON parsing
                import json
                return json.loads(content_str)
            except json.JSONDecodeError:
                try:
                    # Strategy 3: Try eval (less safe but handles Python dict syntax)
                    # Only use if content looks like a dictionary
                    if 'summary' in content_str and 'key_points' in content_str:
                        return eval(content_str)
                except:
                    pass
        
        # If all parsing fails, return original content
        return content
    
    def _convert_markdown_to_rich_text(self, text: str) -> List[Dict]:
        """Convert markdown text to Notion rich text format with proper annotations"""
        import re
        
        if not text:
            return [{"type": "text", "text": {"content": ""}}]
        
        rich_text_parts = []
        current_pos = 0
        
        # Find all markdown patterns (order matters - longer patterns first)
        patterns = [
            (r'\*\*(.*?)\*\*', 'bold'),           # **bold**
            (r'\*(.*?)\*', 'italic'),             # *italic*
            (r'`([^`]+)`', 'code'),               # `code` (improved pattern)
            (r'~~(.*?)~~', 'strikethrough'),      # ~~strikethrough~~
        ]
        
        # Collect all matches with their positions
        all_matches = []
        for pattern, annotation_type in patterns:
            for match in re.finditer(pattern, text):
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'content': match.group(1),
                    'annotation': annotation_type,
                    'full_match': match.group(0)
                })
        
        # Sort matches by position
        all_matches.sort(key=lambda x: x['start'])
        
        # Process text with annotations
        for match in all_matches:
            # Add text before this match
            if current_pos < match['start']:
                before_text = text[current_pos:match['start']]
                if before_text:
                    rich_text_parts.append({
                        "type": "text",
                        "text": {"content": before_text}
                    })
            
            # Add the annotated text
            annotations = {
                "bold": match['annotation'] == 'bold',
                "italic": match['annotation'] == 'italic', 
                "strikethrough": match['annotation'] == 'strikethrough',
                "underline": False,
                "code": match['annotation'] == 'code',
                "color": "default"
            }
            
            rich_text_parts.append({
                "type": "text",
                "text": {"content": match['content']},
                "annotations": annotations
            })
            
            current_pos = match['end']
        
        # Add remaining text
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text:
                rich_text_parts.append({
                    "type": "text", 
                    "text": {"content": remaining_text}
                })
        
        # If no markdown found, return plain text
        if not rich_text_parts:
            rich_text_parts = [{"type": "text", "text": {"content": text}}]
        
        return rich_text_parts
    
    def _detect_and_create_special_blocks(self, content: str) -> List[Dict]:
        """Detect and create special blocks like code blocks and equations"""
        import re
        blocks = []
        
        # Split content by code blocks and equations
        lines = content.split('\n')
        current_block = []
        in_code_block = False
        code_language = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Detect code block start
            code_block_match = re.match(r'^```(\w+)?', line.strip())
            if code_block_match and not in_code_block:
                # Save previous content as paragraph
                if current_block:
                    paragraph_content = '\n'.join(current_block).strip()
                    if paragraph_content:
                        blocks.extend(self._smart_split_content(paragraph_content))
                    current_block = []
                
                # Start code block
                in_code_block = True
                code_language = code_block_match.group(1) or 'plain text'
                i += 1
                continue
            
            # Detect code block end
            if line.strip() == '```' and in_code_block:
                # Create code block
                if current_block:
                    code_content = '\n'.join(current_block)
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": code_content}}],
                            "language": self._map_language_for_notion(code_language)
                        }
                    })
                    current_block = []
                
                in_code_block = False
                code_language = None
                i += 1
                continue
            
            # Detect equations (LaTeX style)
            equation_match = re.match(r'^\$\$(.*?)\$\$$', line.strip(), re.DOTALL)
            if equation_match and not in_code_block:
                # Save previous content
                if current_block:
                    paragraph_content = '\n'.join(current_block).strip()
                    if paragraph_content:
                        blocks.extend(self._smart_split_content(paragraph_content))
                    current_block = []
                
                # Create equation block (Notion doesn't have native equation blocks, use code)
                equation_content = equation_match.group(1).strip()
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": equation_content}}],
                        "language": "latex"
                    }
                })
                i += 1
                continue
            
            # Add line to current block
            current_block.append(line)
            i += 1
        
        # Handle remaining content
        if current_block:
            if in_code_block:
                # Unclosed code block
                code_content = '\n'.join(current_block)
                blocks.append({
                    "object": "block",
                    "type": "code", 
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": code_content}}],
                        "language": self._map_language_for_notion(code_language or 'plain text')
                    }
                })
            else:
                # Regular paragraph content
                paragraph_content = '\n'.join(current_block).strip()
                if paragraph_content:
                    blocks.extend(self._smart_split_content(paragraph_content))
        
        return blocks if blocks else self._smart_split_content(content)
    
    def _map_language_for_notion(self, language: str) -> str:
        """Map language identifiers to Notion-supported languages"""
        language_map = {
            'cpp': 'c++',
            'c++': 'c++',
            'cxx': 'c++',
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'sh': 'shell',
            'bash': 'shell',
            'latex': 'latex',
            'tex': 'latex',
            'sql': 'sql',
            'html': 'markup',
            'xml': 'markup',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'java': 'java',
            'go': 'go',
            'rust': 'rust',
            'php': 'php',
            'ruby': 'ruby',
            'swift': 'swift',
            'kotlin': 'kotlin',
            'scala': 'scala'
        }
        
        return language_map.get(language.lower(), 'plain text')
    
    def _is_summary_dict(self, content: Any) -> bool:
        """Check if content is a dictionary that represents a Summary object"""
        if not isinstance(content, dict):
            return False
        
        # Check for Summary-specific fields
        summary_fields = ['summary', 'key_points', 'key_concepts', 'reading_time_minutes']
        return any(field in content for field in summary_fields)
    
    def _dict_to_summary_object(self, content_dict: dict):
        """Convert a dictionary to a Summary-like object for formatting"""
        from shared.types import Summary
        
        # Create a Summary object from the dictionary
        return Summary(
            summary=content_dict.get('summary', ''),
            key_points=content_dict.get('key_points', content_dict.get('keyPoints', [])),
            key_concepts=content_dict.get('key_concepts', content_dict.get('keyConcepts', [])),
            reading_time_minutes=content_dict.get('reading_time_minutes', content_dict.get('readingTimeMinutes')),
            timestamp=content_dict.get('timestamp'),
            url=content_dict.get('url', ''),
            title=content_dict.get('title', ''),
            images=content_dict.get('images', [])
        )
    
    def _format_highlight_content(self, highlights) -> list:
        """Format highlight content for Notion"""
        blocks = []
        
        if hasattr(highlights, 'highlights') and highlights.highlights:
            for highlight in highlights.highlights:
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": str(highlight)}
                            }
                        ]
                    }
                })
        
        return blocks
    
    def _format_research_content(self, research: Research) -> list:
        """Format research content for Notion"""
        blocks = []
        
        # Research question
        if research.question:
            blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                            "text": {"content": "Research Question"}
                        }
                    ]
                }
            })
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": str(research.question)}
                        }
                    ]
                }
            })
        
        # Key findings
        if research.key_findings:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Key Findings"}
                        }
                    ]
                }
            })
            
            for finding in research.key_findings:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": str(finding)}
                            }
                        ]
                    }
                })
        
        return blocks
    