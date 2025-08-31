"""
Synthra FastAPI Backend
AI-powered browser agent for summarizing, highlighting, research, and learning assistance
"""

import os
import logging
from typing import List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn

# Import our modules
from services.ai_service import AIService
from services.notion_service import NotionService
from services.web_scraper import web_scraper
from shared.types import (
    SummarizeRequest, SummarizeResponse,
    HighlightRequest, HighlightResponse,
    MultiTabResearchRequest, MultiTabResearchResponse,
    SuggestNextStepsRequest, SuggestNextStepsResponse,
    NotionAuthRequest, NotionAuthResponse,
    NotionSaveRequest, NotionSaveResponse,
    UrlResearchRequest, UrlResearchResponse, PageAnalysis,
    APIError
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
ai_service: Optional[AIService] = None
notion_service: Optional[NotionService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global ai_service, notion_service
    
    # Startup
    logger.info("Starting Synthra backend...")
    
    # Initialize AI service
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise ValueError("GEMINI_API_KEY is required")
    
    ai_service = AIService(api_key=gemini_api_key)
    logger.info("AI service initialized")
    
    # Initialize Notion service (optional)
    notion_token = os.getenv('NOTION_TOKEN')
    if notion_token:
        notion_service = NotionService(token=notion_token)
        logger.info("Notion service initialized")
    else:
        logger.info("Notion service not initialized (no token provided)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Synthra backend...")

# Create FastAPI app
app = FastAPI(
    title="Synthra API",
    description="AI-powered browser agent backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'chrome-extension://*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins + ["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get AI service
def get_ai_service() -> AIService:
    if ai_service is None:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    return ai_service

# Dependency to get Notion service
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

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_content(
    request: SummarizeRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Summarize web page content"""
    try:
        logger.info(f"Summarizing content from: {request.url}")
        summary = await ai_service.summarize_content(
            content=request.content,
            title=request.title,
            url=request.url
        )
        return SummarizeResponse(summary=summary, success=True)
    
    except Exception as e:
        logger.error(f"Error summarizing content: {str(e)}")
        return SummarizeResponse(
            summary=None,
            success=False,
            error=str(e)
        )

@app.post("/highlight", response_model=HighlightResponse)
async def highlight_terms(
    request: HighlightRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Identify and explain key terms in content"""
    try:
        logger.info(f"Highlighting terms for: {request.url}")
        highlights = await ai_service.highlight_terms(
            content=request.content,
            context=request.context
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
async def multi_tab_research(
    request: MultiTabResearchRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Perform research across multiple tabs"""
    try:
        logger.info(f"Performing multi-tab research: {request.query}")
        research = await ai_service.multi_tab_research(
            tabs=request.tabs,
            query=request.query
        )
        return MultiTabResearchResponse(research=research, success=True)
    
    except Exception as e:
        logger.error(f"Error in multi-tab research: {str(e)}")
        return MultiTabResearchResponse(
            research=None,
            success=False,
            error=str(e)
        )

@app.post("/suggest-next-steps", response_model=SuggestNextStepsResponse)
async def suggest_next_steps(
    request: SuggestNextStepsRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Suggest next learning steps based on content"""
    try:
        logger.info("Generating next step suggestions")
        steps = await ai_service.suggest_next_steps(
            content=request.content,
            summary=request.summary,
            user_goal=request.user_goal
        )
        return SuggestNextStepsResponse(steps=steps, success=True)
    
    except Exception as e:
        logger.error(f"Error suggesting next steps: {str(e)}")
        return SuggestNextStepsResponse(
            steps=[],
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

@app.post("/notion/save", response_model=NotionSaveResponse)
async def save_to_notion(
    request: NotionSaveRequest,
    notion_service: NotionService = Depends(get_notion_service)
):
    """Save content to Notion"""
    try:
        logger.info(f"Saving {request.type} to Notion")
        result = await notion_service.save_content(
            content=request.content,
            content_type=request.type,
            title=request.title,
            url=request.url
        )
        return NotionSaveResponse(
            page_id=result.get('page_id'),
            page_url=result.get('page_url'),
            success=True
        )
    
    except Exception as e:
        logger.error(f"Error saving to Notion: {str(e)}")
        return NotionSaveResponse(
            success=False,
            error=str(e)
        )

@app.post("/url-research", response_model=UrlResearchResponse)
async def url_research(
    request: UrlResearchRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Fetch and analyze multiple URLs for comparison"""
    try:
        logger.info(f"Starting URL research for {len(request.urls)} URLs")
        
        # Fetch content from all URLs
        page_contents = await web_scraper.fetch_multiple_pages(request.urls)
        
        # Analyze each page individually
        page_analyses = []
        for page_content in page_contents:
            if page_content.get('error'):
                # Handle failed fetches
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
        
        # Generate comparative analysis
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
    """Global exception handler"""
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
