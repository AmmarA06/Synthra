"""
Synthra FastAPI Backend
AI-powered browser agent for summarizing, highlighting, research, and learning assistance
"""

import os
import logging
import asyncio
from typing import List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn

from services.ai_service import AIService
from services.notion_service import NotionService
from services.web_scraper import WebScraperService
from shared.types import (
    SummarizeRequest, SummarizeResponse,
    HighlightRequest, HighlightResponse,
    MultiTabResearchRequest, MultiTabResearchResponse,
    NotionAuthRequest, NotionAuthResponse,
    NotionSaveRequest, NotionSaveResponse,
    UrlResearchRequest, UrlResearchResponse, PageAnalysis,
    APIError
)

load_dotenv()
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

notion_service: Optional[NotionService] = None
web_scraper: Optional[WebScraperService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global notion_service, web_scraper
    
    logger.info("Starting Synthra backend...")
    
    web_scraper = WebScraperService()
    logger.info("Web scraper service initialized")
    
    notion_token = os.getenv('NOTION_TOKEN')
    if notion_token:
        notion_service = NotionService(token=notion_token)
        logger.info("Notion service initialized")
    else:
        notion_service = None
    
    yield
    
    logger.info("Shutting down Synthra backend...")

app = FastAPI(
    title="Synthra API",
    description="AI-powered browser agent backend",
    version="1.0.0",
    lifespan=lifespan
)

allowed_origins = os.getenv('ALLOWED_ORIGINS', 'chrome-extension://*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins + ["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ai_service_from_request(api_key: Optional[str]) -> AIService:
    """Create AI service instance from request API key"""
    if not api_key:
        # Try environment variable as fallback for development
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=400, 
                detail="Gemini API key is required. Please provide it in the request or configure it in settings."
            )
    
    try:
        return AIService(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize AI service: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid Gemini API key: {str(e)}")

def get_notion_service() -> NotionService:
    if notion_service is None:
        raise HTTPException(status_code=500, detail="Notion service not available")
    return notion_service

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Synthra API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_service": ai_service is not None,
        "notion_service": notion_service is not None
    }

@app.post("/echo")
async def echo_test(request: dict):
    """Echo test endpoint to verify extension-backend communication"""
    logger.info(f"Echo test received: {request}")
    
    title = request.get('title', 'No title provided')
    return {
        "received": title,
        "timestamp": int(datetime.now().timestamp() * 1000),
        "success": True
    }

@app.post("/test-gemini")
async def test_gemini_connection(request: dict):
    """Test Gemini API connection"""
    try:
        api_key = request.get('apiKey')
        if not api_key:
            return {"success": False, "error": "API key is required"}
        
        # Test the AI service initialization
        ai_service = get_ai_service_from_request(api_key)
        
        # Try a simple test call
        test_summary = await ai_service.summarize_content(
            content="This is a test content to verify the Gemini API connection.",
            title="Test",
            url="test://connection"
        )
        
        return {
            "success": True,
            "message": "Gemini API connection successful",
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    except Exception as e:
        logger.error(f"Gemini connection test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_content(request: SummarizeRequest):
    """Summarize web page content with enhanced parsing"""
    try:
        logger.info(f"Summarizing content from: {request.url}")
        
        # Get AI service with API key from request
        ai_service = get_ai_service_from_request(request.gemini_api_key)
        
        enhanced_content = request.content
        try:
            if request.url and not request.url.startswith(('chrome-extension://', 'moz-extension://', 'about:', 'data:')):
                parsed_result = await web_scraper.fetch_page_content(request.url, use_enhanced_parser=True)
                if parsed_result.get('success') and len(parsed_result.get('content', '')) > len(request.content):
                    enhanced_content = parsed_result['content']
                    logger.info(f"Enhanced parsing improved content: {len(request.content)} → {len(enhanced_content)} chars")
        except Exception as e:
            logger.warning(f"Enhanced parsing failed, using browser content: {e}")
        
        summary = await ai_service.summarize_content(
            content=enhanced_content,
            title=request.title,
            url=request.url
        )
        
        if request.url and not request.url.startswith(('chrome-extension://', 'moz-extension://', 'about:', 'data:')):
            try:
                parsed_result = await web_scraper.fetch_page_content(request.url, use_enhanced_parser=True)
                if parsed_result.get('images'):
                    summary.images = parsed_result['images']
                    logger.info(f"Added {len(parsed_result['images'])} images to summary")
            except Exception as e:
                logger.warning(f"Failed to extract images for summary: {e}")
        
        
        return SummarizeResponse(summary=summary, success=True)
    
    except Exception as e:
        logger.error(f"Error summarizing content: {str(e)}")
        return SummarizeResponse(
            summary=None,
            success=False,
            error=str(e)
        )

@app.post("/highlight", response_model=HighlightResponse)
async def highlight_terms(request: HighlightRequest):
    """Identify and explain key terms in content with enhanced parsing"""
    try:
        logger.info(f"Highlighting terms for: {request.url}")
        
        # Get AI service with API key from request
        ai_service = get_ai_service_from_request(request.gemini_api_key)
        
        enhanced_content = request.content
        try:
            if request.url and not request.url.startswith(('chrome-extension://', 'moz-extension://', 'about:', 'data:')):
                parsed_result = await web_scraper.fetch_page_content(request.url, use_enhanced_parser=True)
                if parsed_result.get('success') and len(parsed_result.get('content', '')) > len(request.content):
                    enhanced_content = parsed_result['content']
                    logger.info(f"Enhanced parsing improved content for highlights: {len(request.content)} → {len(enhanced_content)} chars")
        except Exception as e:
            logger.warning(f"Enhanced parsing failed for highlights, using browser content: {e}")
        
        highlights = await ai_service.highlight_terms(
            content=enhanced_content,
            context=request.context,
            url=request.url
        )
        
        
        return HighlightResponse(highlights=highlights, success=True)
    
    except Exception as e:
        logger.error(f"Error highlighting terms: {str(e)}")
        return HighlightResponse(
            highlights=[],
            success=False,
            error=str(e)
        )

@app.post("/multi-tab-research", response_model=MultiTabResearchResponse)
async def multi_tab_research(request: MultiTabResearchRequest):
    """Perform enhanced research across multiple tabs with vector search"""
    try:
        logger.info(f"Performing enhanced multi-tab research: {request.query}")
        
        # Get AI service with API key from request
        ai_service = get_ai_service_from_request(request.gemini_api_key)
        
        research = await ai_service.enhanced_multi_tab_research(
            tabs=request.tabs,
            query=request.query
        )
        return MultiTabResearchResponse(research=research, success=True)
    
    except Exception as e:
        logger.error(f"Error in enhanced multi-tab research, falling back to basic: {str(e)}")
        try:
            # Get AI service with API key from request for fallback
            ai_service = get_ai_service_from_request(request.gemini_api_key)
            research = await ai_service.multi_tab_research(
                tabs=request.tabs,
                query=request.query
            )
            return MultiTabResearchResponse(research=research, success=True)
        except Exception as e2:
            logger.error(f"Error in fallback multi-tab research: {str(e2)}")
            return MultiTabResearchResponse(
                research=None,
                success=False,
                error=str(e2)
            )

@app.post("/multi-tab-research-enhanced", response_model=MultiTabResearchResponse)
async def enhanced_multi_tab_research(request: MultiTabResearchRequest):
    """Perform enhanced research across multiple tabs using vector similarity"""
    try:
        logger.info(f"Performing enhanced multi-tab research: {request.query}")
        
        # Get AI service with API key from request
        ai_service = get_ai_service_from_request(request.gemini_api_key)
        
        research = await ai_service.enhanced_multi_tab_research(
            tabs=request.tabs,
            query=request.query
        )
        return MultiTabResearchResponse(research=research, success=True)
    
    except Exception as e:
        logger.error(f"Error in enhanced multi-tab research: {str(e)}")
        return MultiTabResearchResponse(
            research=None,
            success=False,
            error=str(e)
        )

@app.post("/notion/auth", response_model=NotionAuthResponse)
async def notion_auth(
    request: NotionAuthRequest,
    notion_service: NotionService = Depends(get_notion_service)
):
    """Handle Notion OAuth authentication"""
    try:
        logger.info("Processing Notion authentication")
        result = await notion_service.authenticate(
            code=request.code,
            redirect_uri=request.redirect_uri
        )
        return NotionAuthResponse(
            access_token=result.get('access_token'),
            workspace_name=result.get('workspace_name'),
            success=True
        )
    
    except Exception as e:
        logger.error(f"Error in Notion auth: {str(e)}")
        return NotionAuthResponse(
            success=False,
            error=str(e)
        )

@app.post("/notion/test-connection")
async def test_notion_connection(request: dict):
    """Test Notion API connection"""
    try:
        notion_token = request.get('notion_token') or request.get('notionToken')
        
        if not notion_token:
            return {
                "success": False,
                "error": "Notion token not provided"
            }
        
        notion_service = NotionService(token=notion_token)
        result = await notion_service.test_connection()
        
        return result
    
    except Exception as e:
        logger.error(f"Error testing Notion connection: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/notion/databases")
async def get_notion_databases(request: dict):
    """Get available Notion databases"""
    try:
        notion_token = request.get('notion_token') or request.get('notionToken')
        
        if not notion_token:
            return {
                "success": False,
                "error": "Notion token not provided",
                "databases": []
            }
        
        notion_service = NotionService(token=notion_token)
        result = await notion_service.get_databases()
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting Notion databases: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "databases": []
        }

@app.post("/notion/save", response_model=NotionSaveResponse)
async def save_to_notion(
    request: dict,
    ai_service: AIService = Depends(get_ai_service)
):
    """Save content to Notion with enhanced context and error rollback"""
    created_page_id = None

    try:
        logger.info(f"Saving {request.get('type')} to Notion")
        logger.debug(f"Content type: {type(request.get('content'))}")
        logger.debug(f"Content preview: {str(request.get('content'))[:200]}...")

        notion_token = request.get('notion_token') or request.get('notionToken')
        database_id = request.get('database_id') or request.get('databaseId')
        content = request.get('content')
        title = request.get('title', '')
        url = request.get('url', '')
        content_type = request.get('type', 'content')

        if not notion_token:
            return NotionSaveResponse(
                success=False,
                error="Notion token not provided. Please configure Notion integration in settings."
            )

        should_rescrape = False
        if url and not url.startswith(('chrome-extension://', 'moz-extension://', 'about:', 'data:')):
            content_str = str(content) if content else ""
            if len(content_str) < 500:
                should_rescrape = True
                logger.info(f"Content too short ({len(content_str)} chars), will re-scrape")

        if should_rescrape:
            try:
                logger.info(f"Re-scraping {url} for better content")
                parsed_result = await web_scraper.fetch_page_content(url, use_enhanced_parser=True)

                if not parsed_result.get('success'):
                    error_msg = parsed_result.get('error', 'Failed to scrape content')
                    logger.error(f"Scraping failed: {error_msg}")
                    return NotionSaveResponse(
                        success=False,
                        error=f"Could not access website: {error_msg}. The site may have blocked automated access."
                    )

                if parsed_result.get('content'):
                    content = parsed_result['content']
                    content_type = 'content'
                    logger.info(f"Using fresh content: {len(content)} chars")
                else:
                    logger.warning("No content extracted from page")
                    return NotionSaveResponse(
                        success=False,
                        error="No readable content found on this page. The page may be empty or protected."
                    )
            except ValueError as ve:
                logger.error(f"Access blocked: {str(ve)}")
                return NotionSaveResponse(
                    success=False,
                    error=str(ve)
                )
            except Exception as e:
                logger.warning(f"Re-scraping failed: {e}")
                return NotionSaveResponse(
                    success=False,
                    error=f"Failed to fetch content from website: {str(e)}"
                )
        
        enhanced_content = content
        notion_service = NotionService(token=notion_token)

        try:
            result = await notion_service.save_content(
                content=enhanced_content,
                content_type=content_type,
                title=title,
                url=url,
                database_id=database_id
            )
            created_page_id = result.get('page_id')

            return NotionSaveResponse(
                page_id=result.get('page_id'),
                page_url=result.get('page_url'),
                success=True
            )

        except ValueError as ve:
            logger.error(f"Content validation failed: {str(ve)}")
            return NotionSaveResponse(
                success=False,
                error=f"Content Error: {str(ve)}"
            )
        except Exception as save_error:
            if created_page_id:
                try:
                    logger.warning(f"Attempting to delete incomplete page {created_page_id} due to error")
                    await notion_service.delete_page(created_page_id)
                    logger.info(f"Successfully cleaned up incomplete page {created_page_id}")
                except Exception as delete_error:
                    logger.error(f"Failed to delete incomplete page: {delete_error}")

            error_message = str(save_error)
            logger.error(f"Error saving to Notion: {error_message}")

            if "validation" in error_message.lower():
                error_message = f"Content format invalid for Notion: {error_message}"
            elif "unauthorized" in error_message.lower():
                error_message = "Notion access denied. Please check your token and database permissions."
            elif "not found" in error_message.lower():
                error_message = "Notion database not found. Please verify your database ID."

            return NotionSaveResponse(
                success=False,
                error=error_message
            )

    except Exception as e:
        logger.error(f"Unexpected error in save_to_notion: {str(e)}")

        if created_page_id:
            try:
                notion_service = NotionService(token=notion_token)
                await notion_service.delete_page(created_page_id)
                logger.info(f"Cleaned up page {created_page_id} after unexpected error")
            except:
                pass

        return NotionSaveResponse(
            success=False,
            error=f"An unexpected error occurred: {str(e)}"
        )

@app.post("/url-research", response_model=UrlResearchResponse)
async def url_research(request: UrlResearchRequest):
    """Fetch and analyze multiple URLs for comparison with enhanced parsing"""
    try:
        logger.info(f"Starting enhanced URL research for {len(request.urls)} URLs")
        
        # Get AI service with API key from request
        ai_service = get_ai_service_from_request(request.gemini_api_key)
        
        page_contents = []
        for url in request.urls:
            try:
                content = await web_scraper.fetch_page_content(url, use_enhanced_parser=True)
                page_contents.append(content)
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                page_contents.append({
                    'title': f'Error fetching {url}',
                    'content': f'Failed to fetch content: {str(e)}',
                    'url': url,
                    'error': str(e)
                })
        
        page_analyses = []
        for page_content in page_contents:
            if page_content.get('error'):
                page_analyses.append(PageAnalysis(
                    title=page_content.get('title', 'Error'),
                    url=page_content['url'],
                    keyPoints=[],
                    pros=[],
                    cons=[],
                    summary=f"Failed to fetch content: {page_content['error']}",
                    error=page_content['error']
                ))
                continue
            
            analysis = await ai_service.analyze_page_for_comparison(
                title=page_content['title'],
                content=page_content['content'],
                url=page_content['url'],
                context=request.query or ""
            )
            
            page_analyses.append(PageAnalysis(
                title=analysis['title'],
                url=analysis['url'],
                keyPoints=analysis['keyPoints'],
                pros=analysis['pros'],
                cons=analysis['cons'],
                summary=analysis['summary'],
                error=analysis.get('error')
            ))
        
        comparison = await ai_service.compare_pages(
            [page.__dict__ for page in page_analyses if not page.error],
            request.query or ""
        )
        
        return UrlResearchResponse(
            pages=page_analyses,
            comparison=comparison,
            success=True
        )
    
    except Exception as e:
        logger.error(f"Error in URL research: {str(e)}")
        return UrlResearchResponse(
            pages=[],
            comparison={
                'summary': f"Research failed: {str(e)}",
                'commonThemes': [],
                'keyDifferences': []
            },
            success=False,
            error=str(e)
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 8000)),
        reload=os.getenv('DEBUG', 'False').lower() == 'true'
    )
