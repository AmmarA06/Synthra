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
    TabContent, Summary, Highlight, Research,
    ResearchComparison, ResearchSource
)

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI operations using Google Gemini"""
    
    def __init__(self, api_key: str, model: str = None, vector_service=None):
        genai.configure(api_key=api_key)
        self.model_name = model or os.getenv('GEMINI_MODEL', 'gemini-flash-latest')
        self.model = genai.GenerativeModel(self.model_name)
        self.vector_service = vector_service
        logger.info(f"AI Service initialized with model: {self.model_name}")
    
    async def summarize_content(self, content: str, title: str, url: str) -> Summary:
        """Generate a summary of web page content with enhanced parsing and vector context"""
        
        # Get enhanced content if web scraper used enhanced parsing
        enhanced_context = ""
        similar_content_context = ""
        
        # If vector service is available, find similar content for context
        if self.vector_service:
            try:
                # Search for similar content to provide context
                similar_results = await self.vector_service.search_similar(
                    query=f"{title} {content[:500]}",  # Use title + content start as query
                    k=3,
                    threshold=0.3
                )
                
                if similar_results:
                    similar_titles = [doc['title'] for doc in similar_results if doc.get('title')]
                    if similar_titles:
                        similar_content_context = f"\n\nRELATED CONTENT CONTEXT:\nSimilar topics you've researched: {', '.join(similar_titles[:3])}\nConsider connections and build upon previous knowledge."
                
            except Exception as e:
                logger.warning(f"Could not get vector context for summary: {e}")
        
        prompt = f"""
        You are an expert content analyst and summarization specialist with access to your research history. Analyze the following web page content and create a concise, actionable summary that builds upon your existing knowledge.

        CONTENT TO ANALYZE:
        Title: {title}
        URL: {url}
        Content: {content[:8000]}{similar_content_context}

        STUDY NOTES REQUIREMENTS:
        Create clean, scannable study notes optimized for Notion pages.

        FORMATTING RULES FOR NOTION:
        - Write concise, direct content - NO fluff or unnecessary words
        - Use precise technical terminology
        - Include actual examples and code from the source
        - Make content easy to scan and review

        1. SUMMARY (2-3 sentences max):
           One clear paragraph explaining:
           - What this content teaches
           - Why it matters for learning
           - How it connects to broader topics

        2. KEY POINTS (4-6 points):
           Each point should be 1-2 sentences covering:
           - One specific concept or technique
           - A concrete example or use case
           - Why it's important (when applicable)

           IMPORTANT FORMATTING:
           - Use nested bullets for sub-points (indent with 2 spaces)
           - Main point at top level, details/examples nested underneath
           - Format as short, scannable bullets - NOT long paragraphs
           - Include code snippets, formulas, or data when relevant

           Example format:
           "Main concept or technique
             - Specific detail or example
             - Another detail or use case"

        3. KEY CONCEPTS (4-6 terms):
           "TermName: One sentence definition and significance"

           Focus on:
           - Technical terms that need explanation
           - Algorithms, data structures, patterns
           - Tools, frameworks, methodologies

           Keep definitions under 20 words - clear and concise.

        QUALITY OVER QUANTITY:
        - Extract real examples and code from content
        - Include numbers, measurements, benchmarks
        - Be specific, not generic
        - Make it practical for implementation

        Format as JSON:
        {{
            "summary": "Comprehensive explanation of what this content teaches and its learning value",
            "keyPoints": [
                "Detailed explanation of first key concept with examples and context",
                "Step-by-step breakdown of important process or methodology",
                "Practical application with specific examples or use cases",
                "Technical details, code snippets, or formulas if relevant"
            ],
            "keyConcepts": [
                "Technical Term: Clear definition and significance",
                "Algorithm Name: What it does and when to use it",
                "Methodology: How it works and its applications"
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
            
            return Summary(
                summary=result.get('summary', ''),
                key_points=result.get('keyPoints', []),
                key_concepts=result.get('keyConcepts', []),
                reading_time_minutes=None,  # Not needed for study notes
                timestamp=int(datetime.now().timestamp() * 1000),
                url=url,
                title=title
            )
            
        except Exception as e:
            logger.error(f"Error in summarize_content: {str(e)}")
            raise
    
    async def highlight_terms(self, content: str, context: Optional[str] = None, url: str = None) -> List[Highlight]:
        """Identify and explain key terms in content with vector-enhanced context"""
        
        context_text = f"Context: {context}" if context else ""
        vector_context = ""
        
        # If vector service is available, get related terms context
        if self.vector_service and url:
            try:
                # Search for similar content to understand domain context
                similar_results = await self.vector_service.search_similar(
                    query=content[:300],  # Use beginning of content as query
                    k=2,
                    threshold=0.4
                )
                
                if similar_results:
                    related_domains = set()
                    for doc in similar_results:
                        if doc.get('metadata', {}).get('type'):
                            related_domains.add(doc['metadata']['type'])
                        # Extract domain from title/content
                        title = doc.get('title', '').lower()
                        if any(tech in title for tech in ['ai', 'machine learning', 'python', 'javascript', 'react']):
                            related_domains.add('technology')
                        elif any(biz in title for biz in ['business', 'marketing', 'finance']):
                            related_domains.add('business')
                    
                    if related_domains:
                        vector_context = f"\n\nDOMAIN CONTEXT: This content appears to be related to: {', '.join(related_domains)}. Prioritize terms relevant to these domains."
                        
            except Exception as e:
                logger.warning(f"Could not get vector context for highlights: {e}")
        
        prompt = f"""
        You are an expert educator and domain specialist with knowledge of the user's research history. Analyze the content and identify key terms that would help someone better understand the material. Think like a teacher explaining complex concepts to students.

        {context_text}{vector_context}

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
    
    async def enhanced_multi_tab_research(self, tabs: List[TabContent], query: str) -> Research:
        """Enhanced multi-tab research using vector similarity"""
        
        if self.vector_service is None:
            # Fall back to regular multi-tab research if vector service not available
            return await self.multi_tab_research(tabs, query)
        
        try:
            # Find similar content across tabs using vector search
            if len(tabs) > 1:
                # Use the first tab as reference and find similar content in others
                similar_results = await self.vector_service.find_similar_content(
                    content=tabs[0].content,
                    tab_contents=tabs[1:],
                    k=min(3, len(tabs) - 1)
                )
                
                # Calculate content diversity
                all_contents = [tab.content for tab in tabs]
                diversity_score = await self.vector_service.get_content_diversity_score(all_contents)
                
                # Add diversity information to the research context
                diversity_context = f"\nContent Diversity Score: {diversity_score:.2f} (0=identical, 1=completely different)"
                if diversity_score < 0.3:
                    diversity_context += "\nNote: Sources appear to be very similar in content."
                elif diversity_score > 0.7:
                    diversity_context += "\nNote: Sources provide diverse perspectives on the topic."
            else:
                similar_results = []
                diversity_context = ""
            
            # Prepare enhanced tab contents with similarity scores
            tab_contents = []
            for i, tab in enumerate(tabs):
                similarity_info = ""
                if i > 0 and similar_results:
                    # Find similarity score for this tab
                    for result in similar_results:
                        if result['url'] == tab.url:
                            similarity_info = f" (Similarity to main source: {result['similarity_score']:.2f})"
                            break
                
                tab_contents.append(f"""
                Tab {i + 1}: {tab.title}{similarity_info}
                URL: {tab.url}
                Content: {tab.content[:3000]}
                """)
            
            combined_content = "\n\n".join(tab_contents)
            
            prompt = f"""
            You are an expert research analyst conducting multi-source analysis with advanced similarity detection. Your goal is to synthesize information from multiple sources to provide actionable insights.

            RESEARCH QUERY: {query}

            SOURCES TO ANALYZE:
            {combined_content}

            {diversity_context}

            ENHANCED ANALYSIS REQUIREMENTS:

            1. SUMMARY (1-2 sentences):
               - Directly address the research query with a clear answer
               - Highlight the most important discovery or conclusion
               - Consider source diversity in your analysis

            2. KEY FINDINGS (3-4 evidence-based insights):
               - Present specific, actionable discoveries
               - Include supporting evidence or data points from sources
               - Note any patterns revealed by similarity analysis
               - Highlight unique insights that emerge from combining sources

            3. SOURCE COMPARISONS (2-3 comparative analyses):
               - Compare how sources approach the topic differently
               - Identify areas of agreement and disagreement
               - Use similarity scores to explain content relationships
               - Note if high similarity affects the reliability of conclusions

            4. SOURCE EVALUATION:
               - Rate each source's relevance to the query (0.0-1.0)
               - Consider similarity scores in your evaluation
               - Account for content diversity in determining source value

            ENHANCED RESEARCH QUALITY STANDARDS:
            - Leverage similarity analysis to identify redundant information
            - Use diversity scores to assess the breadth of perspectives
            - Highlight when similar sources reinforce findings vs. when diverse sources provide broader insights
            - Be transparent about limitations when sources are too similar

            Format as JSON:
            {{
                "query": "{query}",
                "summary": "Clear, direct answer addressing the research query",
                "keyFindings": [
                    "Evidence-based insight with source support",
                    "Another key discovery with data points",
                    "Third insight considering source relationships"
                ],
                "comparisons": [
                    {{
                        "aspect": "Comparative dimension",
                        "details": "How sources differ/agree on this aspect"
                    }}
                ],
                "sources": [
                    {{
                        "title": "Source title",
                        "url": "Source URL", 
                        "relevance": 0.85
                    }}
                ]
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse the JSON response
            try:
                import json
                research_data = json.loads(response.text.strip())
                
                # Convert to Research object with proper structure
                comparisons = [
                    ResearchComparison(
                        aspect=comp['aspect'],
                        details=comp['details']
                    ) for comp in research_data.get('comparisons', [])
                ]
                
                sources = [
                    ResearchSource(
                        title=source['title'],
                        url=source['url'],
                        relevance=source.get('relevance', 0.5)
                    ) for source in research_data.get('sources', [])
                ]
                
                return Research(
                    query=research_data.get('query', query),
                    summary=research_data.get('summary', 'Unable to generate summary'),
                    key_findings=research_data.get('keyFindings', []),
                    comparisons=comparisons,
                    sources=sources,
                    timestamp=int(datetime.now().timestamp() * 1000)
                )
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response, falling back to regular research")
                return await self.multi_tab_research(tabs, query)
                
        except Exception as e:
            logger.error(f"Error in enhanced_multi_tab_research: {str(e)}")
            # Fall back to regular research on error
            return await self.multi_tab_research(tabs, query)
    
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