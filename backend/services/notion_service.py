"""
Notion Service for Synthra
Handles Notion API integration for saving content
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from notion_client import AsyncClient
from shared.types import Summary, Highlight, Research

logger = logging.getLogger(__name__)

class NotionService:
    """Service for Notion integration"""
    
    def __init__(self, token: str):
        self.client = AsyncClient(auth=token)
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        logger.info("Notion service initialized")
    
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
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save content to Notion database"""
        
        if not self.database_id:
            raise ValueError("Notion database ID not configured")
        
        try:
            # Prepare page properties based on content type
            properties = self._prepare_page_properties(content, content_type, title, url)
            
            # Create the page
            page = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=self._prepare_page_content(content, content_type)
            )
            
            return {
                'page_id': page['id'],
                'page_url': page['url']
            }
            
        except Exception as e:
            logger.error(f"Error saving to Notion: {str(e)}")
            raise
    
    def _prepare_page_properties(
        self, 
        content: Any, 
        content_type: str, 
        title: Optional[str],
        url: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare page properties for Notion"""
        
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title or f"Synthra {content_type.title()}"
                        }
                    }
                ]
            },
            "Type": {
                "select": {
                    "name": content_type.title()
                }
            },
            "Created": {
                "date": {
                    "start": datetime.now().isoformat()
                }
            }
        }
        
        if url:
            properties["URL"] = {
                "url": url
            }
        
        # Add content-specific properties
        if content_type == "summary" and hasattr(content, 'reading_time_minutes'):
            properties["Reading Time"] = {
                "number": content.reading_time_minutes
            }
        
        return properties
    
    def _prepare_page_content(self, content: Any, content_type: str) -> list:
        """Prepare page content blocks for Notion"""
        
        blocks = []
        
        if content_type == "summary":
            blocks.extend(self._format_summary_content(content))
        elif content_type == "highlight":
            blocks.extend(self._format_highlight_content(content))
        elif content_type == "research":
            blocks.extend(self._format_research_content(content))
        else:
            # Generic content
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": str(content)
                            }
                        }
                    ]
                }
            })
        
        return blocks
    
    def _format_summary_content(self, summary: Summary) -> list:
        """Format summary content for Notion"""
        blocks = []
        
        # Main summary
        if summary.summary:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Summary"}
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
                            "text": {"content": summary.summary}
                        }
                    ]
                }
            })
        
        # Key points
        if summary.key_points:
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Key Points"}
                        }
                    ]
                }
            })
            
            for point in summary.key_points:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": point}
                            }
                        ]
                    }
                })
        
        # Key concepts
        if summary.key_concepts:
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Key Concepts"}
                        }
                    ]
                }
            })
            
            concept_text = ", ".join(summary.key_concepts)
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": concept_text}
                        }
                    ]
                }
            })
        
        return blocks
    
    def _format_highlight_content(self, highlights) -> list:
        """Format highlights content for Notion"""
        blocks = []
        
        if not isinstance(highlights, list):
            highlights = [highlights]
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Key Terms & Highlights"}
                    }
                ]
            }
        })
        
        for highlight in highlights:
            # Term as heading
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": highlight.term}
                        }
                    ]
                }
            })
            
            # Explanation
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": highlight.explanation}
                        }
                    ]
                }
            })
            
            # Additional info
            if highlight.importance or highlight.category:
                info_parts = []
                if highlight.importance:
                    info_parts.append(f"Importance: {highlight.importance}")
                if highlight.category:
                    info_parts.append(f"Category: {highlight.category}")
                
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": " • ".join(info_parts)
                                },
                                "annotations": {
                                    "italic": True,
                                    "color": "gray"
                                }
                            }
                        ]
                    }
                })
        
        return blocks
    
    def _format_research_content(self, research: Research) -> list:
        """Format research content for Notion"""
        blocks = []
        
        # Query
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Research: {research.query}"}
                    }
                ]
            }
        })
        
        # Summary
        if research.summary:
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Summary"}
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
                            "text": {"content": research.summary}
                        }
                    ]
                }
            })
        
        # Key findings
        if research.key_findings:
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
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
                                "text": {"content": finding}
                            }
                        ]
                    }
                })
        
        # Sources
        if research.sources:
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Sources"}
                        }
                    ]
                }
            })
            
            for source in research.sources:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": source.title},
                                "href": source.url if source.url else None
                            }
                        ]
                    }
                })
        
        return blocks
