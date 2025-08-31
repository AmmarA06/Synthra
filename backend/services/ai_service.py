"""
AI Service for Synthra
Handles all AI-related operations using Google Gemini API
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import google.generativeai as genai

from shared.types import (
    TabContent, Summary, Highlight, Research, NextStep,
    ResearchComparison, ResearchSource, NextStepResource
)

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI operations using Google Gemini"""
    
    def __init__(self, api_key: str, model: str = None):
        genai.configure(api_key=api_key)
        self.model_name = model or os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"AI Service initialized with model: {self.model_name}")
    
    async def summarize_content(self, content: str, title: str, url: str) -> Summary:
        """Generate a summary of web page content"""
        
        prompt = f"""
        You are an expert content analyst and summarization specialist. Analyze the following web page content and create a concise, actionable summary.

        CONTENT TO ANALYZE:
        Title: {title}
        URL: {url}
        Content: {content[:8000]}

        ANALYSIS REQUIREMENTS:
        1. MAIN SUMMARY (1-2 sentences):
           - Capture the core message and purpose
           - Identify the target audience
           - Highlight the most valuable insight

        2. KEY POINTS (3-4 actionable points):
           - Focus on practical, actionable information
           - Include specific details, numbers, or examples where available
           - Prioritize information that would be useful for decision-making

        3. KEY CONCEPTS (3-5 terms):
           - Include technical terms, methodologies, tools, or frameworks mentioned
           - Add proper nouns, company names, or specific technologies
           - Include domain-specific terminology that's important to understand

        4. READING TIME:
           - Estimate based on average reading speed of 200-250 words per minute
           - Round to nearest minute

        QUALITY GUIDELINES:
        - Write in clear, professional language
        - Be specific rather than generic
        - Include quantitative information when available
        - Make each point distinct and valuable

        Format as JSON:
        {{
            "summary": "Concise 1-2 sentence summary that captures core value and purpose",
            "keyPoints": [
                "Specific actionable point with concrete details",
                "Another valuable insight with context or examples",
                "Practical information that aids decision-making"
            ],
            "keyConcepts": [
                "Technical Term",
                "Methodology Name", 
                "Company/Product Name"
            ],
            "readingTimeMinutes": 5
        }}

        Return only valid JSON, no additional text or formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return Summary(
                summary=result.get('summary', ''),
                key_points=result.get('keyPoints', []),
                key_concepts=result.get('keyConcepts', []),
                reading_time_minutes=result.get('readingTimeMinutes'),
                timestamp=int(datetime.now().timestamp() * 1000),
                url=url,
                title=title
            )
            
        except Exception as e:
            logger.error(f"Error in summarize_content: {str(e)}")
            raise
    
    async def highlight_terms(self, content: str, context: Optional[str] = None) -> List[Highlight]:
        """Identify and explain key terms in content"""
        
        context_text = f"Context: {context}" if context else ""
        
        prompt = f"""
        You are an expert educator and domain specialist. Analyze the content and identify key terms that would help someone better understand the material. Think like a teacher explaining complex concepts to students.

        {context_text}

        CONTENT TO ANALYZE:
        {content[:6000]}

        IDENTIFICATION CRITERIA:
        Identify 4-6 terms that are:
        - Technical jargon or specialized terminology
        - Industry-specific concepts or methodologies
        - Important proper nouns (companies, products, people, places)
        - Acronyms or abbreviations that need explanation
        - Complex processes or frameworks
        - Domain-specific tools or technologies

        EXPLANATION REQUIREMENTS:
        For each term provide:
        1. TERM: Exact term as it appears in the content
        2. EXPLANATION: 1-2 sentences that:
           - Define the term clearly and simply
           - Explain why it's important in this context
           - Provide practical examples when helpful
        3. IMPORTANCE: 
           - "high" = Critical for understanding the main content
           - "medium" = Helpful for deeper comprehension  
           - "low" = Useful background information
        4. CATEGORY: technical, business, academic, scientific, legal, medical, etc.

        QUALITY GUIDELINES:
        - Write explanations that are accessible to non-experts
        - Include practical context and real-world applications
        - Avoid circular definitions (don't use the term to define itself)
        - Make explanations educational and informative

        Format as JSON:
        {{
            "highlights": [
                {{
                    "term": "API",
                    "explanation": "Application Programming Interface - a set of protocols that allows different software applications to communicate with each other, acting like a bridge between systems.",
                    "importance": "high",
                    "category": "technical"
                }},
                {{
                    "term": "Machine Learning",
                    "explanation": "A subset of artificial intelligence that enables computers to learn and improve their performance by identifying patterns in data without explicit programming.",
                    "importance": "medium", 
                    "category": "technical"
                }}
            ]
        }}

        Return only valid JSON, no additional text or formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            highlights = []
            
            for item in result.get('highlights', []):
                highlights.append(Highlight(
                    term=item.get('term', ''),
                    explanation=item.get('explanation', ''),
                    importance=item.get('importance', 'medium'),
                    category=item.get('category'),
                    context=context
                ))
            
            return highlights
            
        except Exception as e:
            logger.error(f"Error in highlight_terms: {str(e)}")
            raise
    
    async def multi_tab_research(self, tabs: List[TabContent], query: str) -> Research:
        """Perform research across multiple tabs"""
        
        # Prepare tab contents
        tab_contents = []
        for i, tab in enumerate(tabs):
            tab_contents.append(f"""
            Tab {i + 1}: {tab.title}
            URL: {tab.url}
            Content: {tab.content[:3000]}
            """)
        
        combined_content = "\n\n".join(tab_contents)
        
        prompt = f"""
        You are an expert research analyst conducting multi-source analysis. Your goal is to synthesize information from multiple sources to provide actionable insights.

        RESEARCH QUERY: {query}

        SOURCES TO ANALYZE:
        {combined_content}

        ANALYSIS REQUIREMENTS:

        1. SUMMARY (1-2 sentences):
           - Directly address the research query with a clear answer
           - Highlight the most important discovery or conclusion
           - Provide context for why this matters

        2. KEY FINDINGS (3-4 evidence-based insights):
           - Present specific, actionable discoveries
           - Include supporting evidence or data points from sources
           - Prioritize findings that directly answer the research query
           - Note any conflicting information between sources

        3. SOURCE COMPARISONS (2-3 comparative analyses):
           - Compare how sources approach the topic differently
           - Identify areas of agreement and disagreement
           - Highlight unique insights from each source

        4. SOURCE EVALUATION:
           - Rate each source's relevance to the query (0.0-1.0)
           - Consider currency, authority, accuracy, and completeness

        RESEARCH QUALITY STANDARDS:
        - Base all findings on evidence from the provided sources
        - Distinguish between facts and opinions
        - Provide specific examples and data points
        - Ensure findings are actionable and useful for decision-making

        Format as JSON:
        {{
            "summary": "Concise synthesis that directly answers the research query with key insight",
            "keyFindings": [
                "Specific evidence-based finding with supporting data",
                "Actionable insight that addresses the core research question",
                "Important discovery with quantitative evidence where available"
            ],
            "comparisons": [
                {{
                    "aspect": "Methodological Approach",
                    "details": "Source A uses quantitative analysis while Source B relies on qualitative case studies, leading to different conclusions."
                }},
                {{
                    "aspect": "Target Audience",
                    "details": "Source A targets enterprise customers while Source B focuses on small business solutions."
                }}
            ],
            "sources": [
                {{
                    "title": "Exact title from the source",
                    "url": "source URL",
                    "relevance": 0.9
                }}
            ]
        }}

        Return only valid JSON, no additional text or formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Convert comparisons
            comparisons = []
            for comp in result.get('comparisons', []):
                comparisons.append(ResearchComparison(
                    aspect=comp.get('aspect', ''),
                    details=comp.get('details', '')
                ))
            
            # Convert sources
            sources = []
            for source in result.get('sources', []):
                sources.append(ResearchSource(
                    title=source.get('title', ''),
                    url=source.get('url', ''),
                    relevance=source.get('relevance')
                ))
            
            return Research(
                query=query,
                summary=result.get('summary', ''),
                key_findings=result.get('keyFindings', []),
                comparisons=comparisons,
                sources=sources,
                timestamp=int(datetime.now().timestamp() * 1000)
            )
            
        except Exception as e:
            logger.error(f"Error in multi_tab_research: {str(e)}")
            raise
    
    async def suggest_next_steps(
        self, 
        content: str, 
        summary: Summary, 
        user_goal: Optional[str] = None
    ) -> List[NextStep]:
        """Suggest next learning steps based on content and user goals"""
        
        goal_text = f"User's learning goal: {user_goal}" if user_goal else "General learning progression"
        
        prompt = f"""
        You are an expert learning advisor and curriculum designer. Create a personalized learning path that builds upon the current content and guides the user toward their goals.

        LEARNING CONTEXT:
        {goal_text}
        
        CURRENT KNOWLEDGE BASE:
        Content Summary: {summary.summary}
        Key Concepts Covered: {', '.join(summary.key_concepts)}
        
        SOURCE CONTENT:
        {content[:4000]}

        LEARNING PATH REQUIREMENTS:

        Create 3-4 progressive learning steps that:

        1. LOGICAL PROGRESSION:
           - Build systematically on current knowledge
           - Progress from foundational to advanced concepts
           - Fill critical knowledge gaps identified in the content
           - Connect to the user's stated learning goal

        2. DIVERSE LEARNING APPROACHES:
           - Mix different types: read (theory), practice (hands-on), research (exploration), action (implementation)
           - Balance passive learning with active application
           - Include both structured and exploratory activities

        3. PRACTICAL APPLICATION:
           - Include real-world projects or exercises
           - Suggest specific tools, platforms, or environments to use
           - Provide concrete deliverables or outcomes

        4. RESOURCE QUALITY:
           - Suggest 2-3 high-quality, specific resources per step
           - Include diverse resource types: articles, videos, courses, documentation, tools
           - Prioritize authoritative, up-to-date sources

        5. TIME MANAGEMENT:
           - Estimate realistic time commitments (15min-2hours per step)
           - Consider the complexity and scope of each activity

        STEP PRIORITIZATION:
        - "high" = Essential for achieving the learning goal, builds critical foundation
        - "medium" = Important for well-rounded understanding, enhances competency  
        - "low" = Valuable enrichment, provides additional context or advanced skills

        Format as JSON:
        {{
            "steps": [
                {{
                    "title": "Master React Hooks Fundamentals",
                    "description": "Deep dive into useState and useEffect to build a solid foundation for modern React development. Complete hands-on exercises building interactive components.",
                    "type": "practice",
                    "priority": "high",
                    "estimatedTimeMinutes": 90,
                    "resources": [
                        {{
                            "title": "React Hooks Documentation",
                            "url": "https://react.dev/reference/react",
                            "type": "documentation"
                        }},
                        {{
                            "title": "Building Interactive React Components",
                            "url": "https://react.dev/learn/adding-interactivity",
                            "type": "tutorial"
                        }}
                    ],
                    "tags": ["react", "hooks", "fundamentals", "hands-on"]
                }},
                {{
                    "title": "Build a Todo App with React",
                    "description": "Apply your React knowledge by building a full-featured todo application. Implement CRUD operations and component composition.",
                    "type": "action",
                    "priority": "high", 
                    "estimatedTimeMinutes": 120,
                    "resources": [
                        {{
                            "title": "React Todo App Tutorial",
                            "url": "https://react.dev/learn/tutorial-tic-tac-toe",
                            "type": "tutorial"
                        }},
                        {{
                            "title": "Create React App Getting Started",
                            "url": "https://create-react-app.dev/docs/getting-started",
                            "type": "documentation"
                        }}
                    ],
                    "tags": ["project", "portfolio", "crud", "practice"]
                }}
            ]
        }}

        Return only valid JSON, no additional text or formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            steps = []
            
            for step_data in result.get('steps', []):
                # Convert resources
                resources = []
                for res in step_data.get('resources', []):
                    resources.append(NextStepResource(
                        title=res.get('title', ''),
                        url=res.get('url', ''),
                        type=res.get('type', 'article')
                    ))
                
                steps.append(NextStep(
                    title=step_data.get('title', ''),
                    description=step_data.get('description', ''),
                    type=step_data.get('type', 'read'),
                    priority=step_data.get('priority', 'medium'),
                    estimated_time_minutes=step_data.get('estimatedTimeMinutes'),
                    resources=resources,
                    tags=step_data.get('tags', [])
                ))
            
            return steps
            
        except Exception as e:
            logger.error(f"Error in suggest_next_steps: {str(e)}")
            raise
    
    async def analyze_page_for_comparison(self, title: str, content: str, url: str, context: str = "") -> Dict[str, any]:
        """Analyze a single page for multi-page comparison"""
        
        context_text = f"Analysis Context: {context}" if context else ""
        
        prompt = f"""
        You are an expert content analyst conducting comparative analysis. Analyze this web page and extract structured information for comparison with other sources.

        {context_text}

        PAGE TO ANALYZE:
        Title: {title}
        URL: {url}
        Content: {content[:6000]}

        ANALYSIS REQUIREMENTS:

        1. KEY POINTS (2-3 main insights):
           - Extract the most important information from this page
           - Focus on unique value propositions, features, or arguments
           - Include specific data, numbers, or concrete examples
           - Make each point distinct and substantial

        2. PROS (2-3 positive aspects):
           - Identify strengths, benefits, or advantages mentioned
           - Include unique selling points or competitive advantages
           - Focus on what makes this approach/product/service appealing

        3. CONS (1-2 potential drawbacks):
           - Identify limitations, challenges, or potential negatives
           - Include costs, complexity, or resource requirements
           - Consider what might be missing or lacking

        4. SUMMARY (1 sentence):
           - Capture the core message and purpose of this page
           - Identify the target audience and main value proposition

        QUALITY GUIDELINES:
        - Be objective and balanced in analysis
        - Extract information actually present in the content
        - Make pros/cons specific and actionable
        - Ensure points are comparative-friendly
        - Include quantitative information when available

        Format as JSON:
        {{
            "keyPoints": [
                "Specific insight with concrete details or numbers",
                "Unique feature or approach that differentiates this source"
            ],
            "pros": [
                "Clear advantage or benefit with specific details",
                "Strength or unique selling point"
            ],
            "cons": [
                "Specific limitation or challenge identified"
            ],
            "summary": "Concise overview capturing the core value proposition and target audience of this page"
        }}

        Return only valid JSON, no additional text or formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                'title': title,
                'url': url,
                'keyPoints': result.get('keyPoints', []),
                'pros': result.get('pros', []),
                'cons': result.get('cons', []),
                'summary': result.get('summary', ''),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing page {url}: {str(e)}")
            return {
                'title': title,
                'url': url,
                'keyPoints': [f"Error analyzing content: {str(e)}"],
                'pros': [],
                'cons': [],
                'summary': f"Failed to analyze page: {str(e)}",
                'error': str(e)
            }
    
    async def compare_pages(self, pages: List[Dict[str, any]], query: str = "") -> Dict[str, any]:
        """Generate comparison analysis across multiple pages"""
        
        query_text = f"Comparison Focus: {query}" if query else "General comparison analysis"
        
        # Prepare page summaries for comparison
        page_summaries = []
        for i, page in enumerate(pages):
            if page.get('error'):
                continue
                
            page_summaries.append(f"""
            Page {i + 1}: {page['title']}
            URL: {page['url']}
            Summary: {page['summary']}
            Key Points: {'; '.join(page['keyPoints'])}
            Pros: {'; '.join(page['pros'])}
            Cons: {'; '.join(page['cons'])}
            """)
        
        combined_analysis = "\n\n".join(page_summaries)
        
        prompt = f"""
        You are an expert comparative analyst. Synthesize the following page analyses to provide comprehensive comparison insights.

        {query_text}

        PAGES TO COMPARE:
        {combined_analysis}

        COMPARISON REQUIREMENTS:

        1. SUMMARY (1-2 sentences):
           - Provide a quick overview of what was compared
           - Highlight the main pattern or key takeaway
           - Address the comparison focus if provided

        2. COMMON THEMES (2-3 shared patterns):
           - Identify concepts, features, or approaches that appear across multiple pages
           - Note consistent messaging or value propositions
           - Highlight shared challenges or solutions

        3. KEY DIFFERENCES (2-3 distinguishing factors):
           - Identify what makes each approach, product, or perspective unique
           - Note significant variations in features, pricing, or methodology
           - Highlight conflicting viewpoints or contradictory information

        ANALYSIS QUALITY:
        - Base findings on evidence from the analyzed pages
        - Make comparisons specific and actionable
        - Identify patterns that would help decision-making
        - Ensure insights are substantive and valuable

        Format as JSON:
        {{
            "summary": "Quick overview of the comparison analysis and main takeaway",
            "commonThemes": [
                "Shared pattern or approach found across multiple sources",
                "Consistent theme or value proposition identified"
            ],
            "keyDifferences": [
                "Unique approach or feature that distinguishes one source",
                "Significant variation in methodology or target audience"
            ]
        }}

        Return only valid JSON, no additional text or formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                'summary': result.get('summary', ''),
                'commonThemes': result.get('commonThemes', []),
                'keyDifferences': result.get('keyDifferences', [])
            }
            
        except Exception as e:
            logger.error(f"Error in compare_pages: {str(e)}")
            return {
                'summary': f"Failed to generate comparison: {str(e)}",
                'commonThemes': [],
                'keyDifferences': []
            }