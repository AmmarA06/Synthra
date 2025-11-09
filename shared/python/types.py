"""
Auto-generated Python types for Synthra
Generated from TypeScript definitions
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

@dataclass
class TabContent:
    title: str
    url: str
    content: str
    html: Optional[str] = None
    timestamp: Optional[int] = None

@dataclass
class Summary:
    summary: str
    key_points: List[str]
    key_concepts: List[str]
    reading_time_minutes: Optional[int] = None
    timestamp: Optional[int] = None
    url: Optional[str] = None
    title: Optional[str] = None

@dataclass
class HighlightPosition:
    x: float
    y: float
    width: float
    height: float

@dataclass
class Highlight:
    term: str
    explanation: str
    context: Optional[str] = None
    importance: Optional[str] = None  # 'low' | 'medium' | 'high'
    category: Optional[str] = None
    position: Optional[HighlightPosition] = None

@dataclass
class ResearchComparison:
    aspect: str
    details: str

@dataclass
class ResearchSource:
    title: str
    url: str
    relevance: Optional[float] = None

@dataclass
class Research:
    query: str
    summary: str
    key_findings: List[str]
    comparisons: List[ResearchComparison]
    sources: List[ResearchSource]
    timestamp: Optional[int] = None

@dataclass
class NextStepResource:
    title: str
    url: str
    type: str  # 'article' | 'video' | 'course' | 'documentation' | 'tool'

@dataclass
class NextStep:
    title: str
    description: str
    type: str  # 'read' | 'action' | 'research' | 'practice'
    priority: str  # 'low' | 'medium' | 'high'
    estimated_time_minutes: Optional[int] = None
    resources: List[NextStepResource] = field(default_factory=list)
    tags: Optional[List[str]] = None

# Request/Response types for API
@dataclass
class SummarizeRequest:
    content: str
    url: str
    title: str
    gemini_api_key: Optional[str] = None

@dataclass
class SummarizeResponse:
    summary: Summary
    success: bool
    error: Optional[str] = None

@dataclass
class HighlightRequest:
    content: str
    url: str
    context: Optional[str] = None
    gemini_api_key: Optional[str] = None

@dataclass
class HighlightResponse:
    highlights: List[Highlight]
    success: bool
    error: Optional[str] = None

@dataclass
class MultiTabResearchRequest:
    tabs: List[TabContent]
    query: str
    gemini_api_key: Optional[str] = None

@dataclass
class MultiTabResearchResponse:
    research: Research
    success: bool
    error: Optional[str] = None

@dataclass
class UrlResearchRequest:
    urls: List[str]
    query: Optional[str] = None
    gemini_api_key: Optional[str] = None

@dataclass
class PageAnalysis:
    title: str
    url: str
    key_points: List[str]
    pros: List[str]
    cons: List[str]
    summary: str
    error: Optional[str] = None

@dataclass
class UrlResearchResponse:
    pages: List[PageAnalysis]
    comparison: Dict[str, Any]
    success: bool
    error: Optional[str] = None

@dataclass
class SuggestNextStepsRequest:
    content: str
    summary: Summary
    user_goal: Optional[str] = None

@dataclass
class SuggestNextStepsResponse:
    steps: List[NextStep]
    success: bool
    error: Optional[str] = None

@dataclass
class NotionAuthRequest:
    code: Optional[str] = None
    redirect_uri: Optional[str] = None

@dataclass
class NotionAuthResponse:
    access_token: Optional[str] = None
    workspace_name: Optional[str] = None
    success: bool = False
    error: Optional[str] = None

@dataclass
class NotionSaveRequest:
    content: Any
    type: str  # 'summary' | 'highlight' | 'research' | 'content'
    title: Optional[str] = None
    url: Optional[str] = None

@dataclass
class NotionSaveResponse:
    page_id: Optional[str] = None
    page_url: Optional[str] = None
    success: bool = False
    error: Optional[str] = None

@dataclass
class ExtensionSettings:
    api_base_url: str
    auto_summarize: bool
    notion_enabled: bool
    highlight_enabled: bool
    notion_token: Optional[str] = None
    notion_database_id: Optional[str] = None

@dataclass
class APIError:
    message: str
    code: Optional[str] = None
    details: Optional[Any] = None

# Utility functions for conversion
def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase"""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def dict_to_dataclass(cls, data: Dict[str, Any]):
    """Convert dictionary with camelCase keys to dataclass with snake_case fields"""
    if not isinstance(data, dict):
        return data
    
    converted = {}
    for key, value in data.items():
        snake_key = camel_to_snake(key)
        converted[snake_key] = value
    
    return cls(**converted)

def dataclass_to_dict(obj) -> Dict[str, Any]:
    """Convert dataclass to dictionary with camelCase keys"""
    from dataclasses import asdict, is_dataclass
    
    if is_dataclass(obj):
        data = asdict(obj)
        converted = {}
        for key, value in data.items():
            camel_key = snake_to_camel(key)
            if isinstance(value, list):
                converted[camel_key] = [dataclass_to_dict(item) if is_dataclass(item) else item for item in value]
            elif is_dataclass(value):
                converted[camel_key] = dataclass_to_dict(value)
            else:
                converted[camel_key] = value
        return converted
    
    return obj
