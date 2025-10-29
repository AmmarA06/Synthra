"""
Clean Content Parser for Notion
Focuses on extracting only educational content and formatting for study-ready Notion pages
"""

import re
import html
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import google.generativeai as genai

logger = logging.getLogger(__name__)

class CleanContentParser:
    """
    Single, focused content parser optimized for Notion study notes.
    Aggressively removes UI/nav elements and formats content for learning.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
        # Note: No caching - each save creates a fresh parser instance
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            self.model = None
            logger.warning("No Gemini API key provided - AI enhancement disabled")

        # Aggressive filtering patterns for non-educational content
        self.skip_patterns = [
            re.compile(r'skip to|sign in|log in|register|subscribe|newsletter', re.I),
            re.compile(r'menu|navigation|nav|footer|header|sidebar', re.I),
            re.compile(r'cookie|gdpr|privacy|terms|legal|copyright', re.I),
            re.compile(r'advertisement|sponsored|promo|marketing', re.I),
            re.compile(r'share|like|comment|follow|social', re.I),
            re.compile(r'related articles|you might also|popular posts', re.I),
            re.compile(r'table of contents', re.I),
            re.compile(r'all rights reserved|back to top', re.I),
            re.compile(r'corporate.{0,20}address|registered address|communications address', re.I),
            re.compile(r'tower|sector|apartment|floor.{0,30}noida|floor.{0,30}uttar pradesh', re.I),
            re.compile(r'contact us|advertise with|about us|careers', re.I),
        ]

        # Patterns for educational content
        self.keep_patterns = [
            re.compile(r'\b(algorithm|implementation|example|code|syntax|definition|concept)\b', re.I),
            re.compile(r'\b(tutorial|guide|how to|step|process|method)\b', re.I),
            re.compile(r'\b(formula|equation|theorem|proof|property)\b', re.I),
        ]

    def parse_and_format_for_notion(
        self,
        raw_content: str,
        title: str = "",
        url: str = "",
        use_ai: bool = True,
        images: List[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Main entry point: parse content and return Notion-ready blocks

        Args:
            raw_content: Raw HTML/text content from web page
            title: Page title
            url: Source URL
            use_ai: Whether to use AI for enhancement (default True)
            images: List of image dictionaries with src, alt, title (optional)

        Returns:
            List of Notion block dictionaries ready for API
        """
        logger.info(f"Parsing content for Notion: {title}")
        self.page_images = images or []  # Store images for later use

        # Step 1: Clean and extract educational content only
        clean_content = self._extract_educational_content(raw_content)

        if not clean_content or len(clean_content.strip()) < 100:
            logger.warning(f"Insufficient educational content extracted: {len(clean_content) if clean_content else 0} chars")
            logger.warning(f"Raw content preview: {raw_content[:200]}")
            # Be more lenient - if we have ANY content, try to format it
            if clean_content and len(clean_content.strip()) > 0:
                logger.info("Proceeding with limited content")
            else:
                return self._create_error_blocks("No educational content found on this page")

        # Step 2: Use AI to structure into study-ready format
        if use_ai and self.model:
            try:
                notion_blocks = self._ai_structure_for_notion(clean_content, title, url)
                if notion_blocks and len(notion_blocks) > 0:
                    logger.info(f"AI successfully created {len(notion_blocks)} Notion blocks")
                    return notion_blocks
                else:
                    logger.warning("AI returned empty blocks, falling back to manual formatting")
            except Exception as e:
                logger.error(f"AI structuring failed: {e}, falling back to manual formatting")

        # Step 3: Fallback to manual formatting if AI unavailable/failed
        return self._manual_structure_for_notion(clean_content, title, url)

    def _extract_educational_content(self, raw_content: str) -> str:
        """Extract only educational content, aggressively filter UI/nav elements"""

        # Handle dictionary format if present
        if raw_content.startswith("{'content':"):
            try:
                import ast
                content_dict = ast.literal_eval(raw_content)
                if isinstance(content_dict, dict) and 'content' in content_dict:
                    content = content_dict['content']
                else:
                    content = raw_content
            except:
                content = raw_content
        else:
            content = raw_content

        # Detect if content is from a blocked/error page
        blocked_indicators = [
            'securitycompromiseerror',
            'access blocked',
            'ddos attack suspected',
            'too many requests',
            'code 451',
            'anonymous access blocked',
            'cloudflare',
            'you have been blocked',
            'access denied',
            'rate limit exceeded',
            'bot detection',
        ]

        content_lower = content.lower()
        if any(indicator in content_lower for indicator in blocked_indicators):
            # Check if this is mostly error content vs actual content
            error_ratio = sum(1 for ind in blocked_indicators if ind in content_lower) / len(blocked_indicators)
            if error_ratio > 0.2 or len(content) < 500:  # More than 20% match or very short content
                logger.warning(f"⚠️ Detected bot/access block in content (error ratio: {error_ratio:.2%})")
                raise ValueError("Website blocked access - possible bot detection. Try again later or use a different method.")

        # Remove HTML tags and decode entities
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.I)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.I)
        content = re.sub(r'<[^>]+>', ' ', content)
        content = html.unescape(content)

        # Split into lines and filter
        lines = content.split('\n')
        educational_lines = []
        footer_detected = False

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # Detect footer section - stop processing after this
            if re.search(r'corporate.{0,20}address|registered address|^\s*K\s+\d+|^A-\d+', line, re.I):
                footer_detected = True
                logger.info(f"Footer detected, stopping content extraction at: {line[:50]}")
                break

            if footer_detected:
                break

            # Skip lines matching unwanted patterns
            if any(pattern.search(line) for pattern in self.skip_patterns):
                continue

            # Keep substantial lines (more lenient - just need to be text)
            if len(line) > 20:
                # Check if line is mostly text (not special chars)
                alpha_ratio = len(re.findall(r'[a-zA-Z]', line)) / len(line)
                if alpha_ratio > 0.4:  # More lenient: 40% instead of 50%
                    educational_lines.append(line)

        # Join and clean up whitespace
        clean_content = '\n'.join(educational_lines)
        clean_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_content)

        logger.info(f"Extracted {len(clean_content)} chars of educational content from {len(raw_content)} chars")
        return clean_content.strip()

    def _ai_structure_for_notion(
        self,
        clean_content: str,
        title: str,
        url: str
    ) -> List[Dict[str, Any]]:
        """Use AI to structure clean content into study-ready Notion blocks"""

        # Prepare image information for AI
        image_context = ""
        logger.info(f"AI Prompt Preparation: Received {len(self.page_images)} images")
        if self.page_images:
            logger.info(f"Adding images to AI context: {[img.get('src', '')[:50] for img in self.page_images[:5]]}")
            image_context = "\n\nAVAILABLE IMAGES (use these URLs):\n"
            for img in self.page_images[:5]:  # Limit to top 5 images
                img_url = img.get('src', '')
                img_alt = img.get('alt', 'Untitled')
                img_type = img.get('type', 'content')
                if img_url:
                    image_context += f"- ![{img_alt}]({img_url}) (Type: {img_type})\n"
                    logger.debug(f"Added image to context: {img_url[:80]}")
        else:
            logger.warning("No images available for AI context")

        prompt = f"""
You are an expert educational content formatter creating study notes for Notion.

SOURCE:
Title: {title}
URL: {url}{image_context}

CONTENT:
{clean_content[:6000]}

TASK:
Transform this content into beautifully formatted, study-ready markdown for Notion.

CRITICAL FORMATTING REQUIREMENTS:

1. **ALWAYS start with # H1 title** - Never skip this
2. **Add a brief overview paragraph** (2-3 sentences) right after the title
3. **Use ## H2 headings** for major sections - at least 3-4 sections
4. **Use ### H3 headings** for sub-topics within sections
5. **NEVER use #### H4 or deeper** - Notion only supports H1, H2, H3 (use H3 instead)
6. **Use - bullet points** for lists, features, and key points
7. **Use **bold** extensively** for:
   - Important terms and concepts
   - Key numbers and metrics
   - Product/service names and technical terminology
   - Critical takeaways and definitions
8. **Use `code`** for technical terms, commands, and inline code
9. **CRITICAL CODE BLOCK FORMAT** - Code blocks MUST be multi-line:
   - Opening: ``` followed by language (jsx, cpp, python, etc.) on its OWN line
   - Body: Code content on separate lines (properly indented)
   - Closing: ``` on its OWN line
   - **NEVER put code on same line as ```**
   - **NEVER omit closing ```**
   - Correct format:
     ```jsx
     function MyComponent() {{
       return <div>Hello</div>;
     }}
     ```
   - Language tags: ```jsx (React), ```cpp (C++), ```python, ```typescript
   - If you put code inline with ```, it WILL fail to render properly
10. **Add blank lines** between sections for readability
11. **Include images** using markdown syntax: ![alt text](image-url)
    - **USE THE PROVIDED IMAGE URLs** from the "AVAILABLE IMAGES" section above
    - Place images in relevant sections where they add educational value
    - Prioritize images marked as "educational" type
    - Skip decorative images - only include diagrams, charts, screenshots, workflows
    - If no images are provided, you may describe visual concepts textually
12. **CRITICAL MATH RULE: ONLY $$ (DOUBLE DOLLAR) - NEVER SINGLE $**
    - **MANDATORY:** ALL math MUST use $$ (double dollar signs)
    - **FORBIDDEN:** Single $ is NEVER allowed - it will break rendering
    - Inline math: The complexity is $$O(n)$$ where $$n$$ is input size
    - Variables: $$V$$ vertices, $$E$$ edges, $$u \\to v$$ edge
    - Expressions: $$O(V + E)$$, $$2^n$$, $$\\log n$$
    - Display (own line): $$E = mc^2$$
    - **ABSOLUTELY WRONG:** $V$, $E$, $O(n)$, $u \\to v$ ❌❌❌
    - **ABSOLUTELY RIGHT:** $$V$$, $$E$$, $$O(n)$$, $$u \\to v$$ ✅✅✅
    - If you use single $, the math will NOT render - ALWAYS double $$
13. **Remove ALL** footer content, addresses, contact info, navigation

STRUCTURE PATTERN:
```
# Main Title

Brief overview paragraph explaining what this teaches and why it matters.

## First Major Section

Overview of this section concept.

- **Key point**: Explanation
- **Another point**: Details
- Third point with specifics

### Subsection If Needed

More detailed information here.

## Second Major Section

Continue with clear structure...
```

QUALITY CHECKLIST (verify before returning):
✅ H1 title at the very top
✅ Multiple H2 sections (at least 3)
✅ Bold used for important terms (at least 10-15 **bold** items)
✅ Bullets organized in logical groups
✅ Clear spacing between sections
✅ No footer/address/contact info
✅ Technical terms in `code` format
✅ Professional, scannable structure
✅ Code blocks: opening ``` on own line, closing ``` on own line
✅ Math: ALL variables/expressions use $$double$$ dollar signs

CRITICAL FORMATTING RULES - MISTAKES CAUSE RENDERING FAILURES:

1. CODE BLOCKS - Must have proper line breaks:
❌ WRONG: ```jsx function MyComponent() {{ return <div>Hello</div>; }}```
✅ RIGHT:
```jsx
function MyComponent() {{
  return <div>Hello</div>;
}}
```

2. MATH EXPRESSIONS - Must ALWAYS use $$double dollars$$:
❌ WRONG: The complexity is $O(V + E)$ where $V$ and $E$ are used
❌ WRONG: Processing takes $O(n)$ time with $n$ items
✅ RIGHT: The complexity is $$O(V + E)$$ where $$V$$ and $$E$$ are used
✅ RIGHT: Processing takes $$O(n)$$ time with $$n$$ items
✅ RIGHT: Edges $$u \\to v$$ and $$v \\to u$$ represent connections

REMEMBER: Single $ breaks math rendering in Notion! ALWAYS use $$

EXAMPLE STRUCTURE (adapt to any topic - technical or non-technical):

# [Main Topic Title]

[Opening paragraph explaining what this topic is and why it matters - 2-3 sentences]

## [First Major Section]

[Brief overview of this section's concept]

- **Key term or concept**: Explanation with relevant details
- **Another important point**: Description with context
- **Third point**: Additional information

### [Subsection If Needed]

[More detailed explanation here]

## [Second Major Section]

### [Subsection with Code Example]

[Brief context for the code]

```[language]
// Code example properly formatted
function example() {{
  return "Code on separate lines";
}}
```

### [Subsection with Math]

[Brief context for the math]

- **Complexity**: The algorithm runs in $$O(n)$$ time where $$n$$ is the input size
- **Formula**: Use $$E = mc^2$$ format for equations
- **Variables**: Express as $$x$$ or $$y$$ with double dollar signs

## [Third Major Section]

[Continue with clear structure matching the content type - whether it's programming, science, business, history, or any other subject]

FINAL CRITICAL REMINDERS BEFORE YOU START:
⚠️ MATH: Use $$O(n)$$ NOT $O(n)$ - single $ will break!
⚠️ CODE: Put ``` on separate lines, NOT inline
⚠️ VERIFY: Check every $ in your output - ALL must be $$

NOW FORMAT THE PROVIDED CONTENT WITH THIS LEVEL OF QUALITY:
"""

        try:
            logger.info(f"Making Gemini API call for {url}")
            response = self.model.generate_content(prompt)
            markdown_content = response.text.strip()

            # Remove code block wrapper if AI added it
            if markdown_content.startswith('```markdown'):
                markdown_content = markdown_content[11:]
            if markdown_content.startswith('```'):
                markdown_content = markdown_content[3:]
            if markdown_content.endswith('```'):
                markdown_content = markdown_content[:-3]
            markdown_content = markdown_content.strip()

            # Convert markdown to Notion blocks
            blocks = self._markdown_to_notion_blocks(markdown_content, url)
            return blocks

        except Exception as e:
            logger.error(f"AI structuring failed: {e}")
            # Check if it's a rate limit error
            if "429" in str(e) or "RATE_LIMIT" in str(e) or "quota" in str(e).lower():
                logger.error("RATE LIMIT EXCEEDED: Gemini API quota exhausted")
                logger.error("Please wait a few minutes or get a new API key")
            raise

    def _markdown_to_notion_blocks(self, markdown: str, base_url: str = "") -> List[Dict[str, Any]]:
        """Convert markdown text to Notion block format"""
        blocks = []
        lines = markdown.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            # Empty line - skip
            if not line:
                i += 1
                continue

            # Code block (handle indented code blocks within lists)
            stripped_line = line.lstrip()
            if stripped_line.startswith('```'):
                # Handle both proper markdown and malformed (code on same line as ```)
                rest_of_line = stripped_line[3:]  # Everything after ```

                # Check if closing ``` is on the same line (malformed: ```jsx code```)
                if '```' in rest_of_line:
                    # Malformed all-on-one-line format
                    parts = rest_of_line.split('```', 1)
                    opening_part = parts[0].strip()

                    # Extract language and code
                    lang_and_code = opening_part.split(None, 1)
                    if len(lang_and_code) == 2:
                        language = lang_and_code[0]
                        code_content = lang_and_code[1]
                    elif len(lang_and_code) == 1:
                        language = lang_and_code[0]
                        code_content = ''
                    else:
                        language = 'plain text'
                        code_content = ''

                    if code_content:
                        blocks.append(self._create_code_block(code_content, language))
                    i += 1
                    continue

                # Extract language and check if code starts on same line
                parts = rest_of_line.split(None, 1)  # Split on first whitespace
                if len(parts) == 2:
                    language = parts[0] or 'plain text'
                    first_code_line = parts[1]  # Code on same line as ```
                    code_lines = [first_code_line]
                elif len(parts) == 1:
                    language = parts[0] or 'plain text'
                    code_lines = []
                else:
                    language = 'plain text'
                    code_lines = []

                i += 1

                # Collect remaining code lines until closing ``` (handle indentation)
                while i < len(lines) and not lines[i].lstrip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1

                if code_lines:
                    code_content = '\n'.join(code_lines)
                    # Split long code blocks to respect Notion's 2000 char limit
                    if len(code_content) <= 2000:
                        blocks.append(self._create_code_block(code_content, language))
                    else:
                        # Split into multiple blocks
                        chunks = [code_content[i:i+1900] for i in range(0, len(code_content), 1900)]
                        for chunk in chunks:
                            blocks.append(self._create_code_block(chunk, language))

                i += 1
                continue

            # H1 heading
            if line.startswith('# '):
                blocks.append(self._create_heading(line[2:].strip(), 1))
                i += 1
                continue

            # H2 heading
            if line.startswith('## '):
                blocks.append(self._create_heading(line[3:].strip(), 2))
                i += 1
                continue

            # H3 heading
            if line.startswith('### '):
                blocks.append(self._create_heading(line[4:].strip(), 3))
                i += 1
                continue

            # H4+ headings (Notion only supports up to H3, so convert H4+ to H3)
            if line.startswith('#### '):
                # Strip all # symbols and convert to H3
                heading_text = line.lstrip('#').strip()
                blocks.append(self._create_heading(heading_text, 3))
                i += 1
                continue

            # Math equation block $$...$$ (must be on its own line)
            if line.strip().startswith('$$') and line.strip().endswith('$$') and len(line.strip()) > 4:
                equation = line.strip()[2:-2].strip()
                blocks.append(self._create_equation_block(equation))
                i += 1
                continue

            # Image ![alt](url) - handle multiple images on same line
            # Check if line contains any image markdown
            if '![' in line and '](' in line:
                # Find ALL images in the line
                image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                images = re.findall(image_pattern, line)
                logger.info(f"Found {len(images)} image(s) in markdown line")

                if images:
                    for alt_text, image_url_raw in images:
                        image_url = image_url_raw.split('"')[0].strip()  # Remove title if present
                        logger.info(f"Processing image: {image_url[:80]} (alt: {alt_text[:30]})")
                        # Validate URL before creating block
                        if image_url and image_url.startswith(('http://', 'https://')):
                            blocks.append(self._create_image_block(image_url, alt_text))
                            logger.info(f"✓ Created image block for: {image_url[:50]}")
                        else:
                            logger.warning(f"✗ Skipping invalid image URL: {image_url}")

                    # Check if there's any text besides images
                    text_without_images = re.sub(image_pattern, '', line).strip()
                    if text_without_images:
                        # Add remaining text as paragraph
                        blocks.append(self._create_paragraph(text_without_images))

                    i += 1
                    continue

            # Bullet point
            if line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                blocks.append(self._create_bullet(text))
                i += 1
                continue

            # Numbered list
            numbered_match = re.match(r'^\d+\.\s+(.+)$', line)
            if numbered_match:
                text = numbered_match.group(1)
                blocks.append(self._create_numbered_item(text))
                i += 1
                continue

            # Markdown table - convert to bullet points
            if line.startswith('|'):
                table_lines = []
                # Collect all consecutive table rows
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1

                if table_lines:
                    # Parse and convert table to bullet points
                    table_blocks = self._parse_markdown_table(table_lines)
                    blocks.extend(table_blocks)
                continue

            # Regular paragraph
            # Collect consecutive lines into one paragraph
            para_lines = [line]
            i += 1
            while i < len(lines) and lines[i] and not self._is_special_line(lines[i]):
                para_lines.append(lines[i])
                i += 1

            para_text = ' '.join(para_lines)
            blocks.append(self._create_paragraph(para_text))

        return blocks

    def _is_special_line(self, line: str) -> bool:
        """Check if line starts a special block (heading, list, code)"""
        line = line.lstrip()
        return (line.startswith('#') or
                line.startswith('- ') or
                line.startswith('* ') or
                line.startswith('```') or
                line.startswith('|') or  # Tables are special lines too
                re.match(r'^\d+\.\s+', line) is not None)

    def _parse_markdown_table(self, table_lines: List[str]) -> List[Dict[str, Any]]:
        """Parse markdown table and convert to bullet points for better readability"""
        blocks = []

        if not table_lines:
            return blocks

        # Parse table rows
        rows = []
        header_row = None
        separator_idx = -1

        for idx, line in enumerate(table_lines):
            # Split by | and strip whitespace
            cells = [cell.strip() for cell in line.split('|')]
            # Remove empty first/last cells (from leading/trailing |)
            cells = [c for c in cells if c]

            # Check if this is a separator row (contains :--- or ---:)
            if all(re.match(r'^:?-+:?$', cell) for cell in cells if cell):
                separator_idx = idx
                continue

            if not cells:
                continue

            if header_row is None:
                header_row = cells
            else:
                rows.append(cells)

        # Convert to a Notion table
        if not header_row or not rows:
            return blocks

        # Determine number of columns
        num_columns = len(header_row)

        # Create table block with header row
        table_block = {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": num_columns,
                "has_column_header": True,
                "has_row_header": False,
                "children": []
            }
        }

        # Add header row
        header_cells = []
        for header in header_row:
            header_cells.append({
                "rich_text": self._create_rich_text(header)
            })

        table_block["table"]["children"].append({
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": header_cells
            }
        })

        # Add data rows
        for row in rows:
            # Ensure row has the same number of columns (pad if needed)
            while len(row) < num_columns:
                row.append("")

            row_cells = []
            for cell_value in row[:num_columns]:  # Limit to num_columns
                row_cells.append({
                    "rich_text": self._create_rich_text(str(cell_value))
                })

            table_block["table"]["children"].append({
                "object": "block",
                "type": "table_row",
                "table_row": {
                    "cells": row_cells
                }
            })

        blocks.append(table_block)
        return blocks

    def _manual_structure_for_notion(
        self,
        clean_content: str,
        title: str,
        url: str
    ) -> List[Dict[str, Any]]:
        """Fallback: manually structure content into basic Notion blocks"""
        blocks = []

        # Add title
        if title:
            blocks.append(self._create_heading(title, 1))

        # Add source URL
        if url:
            blocks.append(self._create_paragraph(f"Source: {url}"))

        # Split content into paragraphs and create blocks
        paragraphs = clean_content.split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if it looks like a heading
            if len(para) < 100 and not para.endswith('.'):
                blocks.append(self._create_heading(para, 2))
            # Check if it looks like a list item
            elif para.startswith(('-', '•', '*')):
                text = para[1:].strip()
                blocks.append(self._create_bullet(text))
            # Regular paragraph
            else:
                blocks.append(self._create_paragraph(para))

        return blocks

    def _create_heading(self, text: str, level: int) -> Dict[str, Any]:
        """Create a Notion heading block"""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._create_rich_text(text)
            }
        }

    def _create_paragraph(self, text: str) -> Dict[str, Any]:
        """Create a Notion paragraph block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._create_rich_text(text)
            }
        }

    def _create_bullet(self, text: str) -> Dict[str, Any]:
        """Create a Notion bulleted list item"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._create_rich_text(text)
            }
        }

    def _create_numbered_item(self, text: str) -> Dict[str, Any]:
        """Create a Notion numbered list item"""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self._create_rich_text(text)
            }
        }

    def _create_image_block(self, image_url: str, caption: str = "") -> Dict[str, Any]:
        """Create a Notion image block with URL validation"""

        # Validate image URL
        # Notion requires URLs to be properly encoded and accessible
        if not image_url or len(image_url) > 2000:
            logger.warning(f"Invalid image URL length: {len(image_url) if image_url else 0}")
            # Return a paragraph with image info instead
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"[Image: {caption or 'Untitled'}]"}}]
                }
            }

        # Check for common issues that break Notion image rendering
        problematic_patterns = [
            'localhost', '127.0.0.1', 'file://', 'data:image',
            'blob:', 'javascript:', 'about:',  # Browser-specific protocols
        ]

        url_lower = image_url.lower()
        if any(pattern in url_lower for pattern in problematic_patterns):
            logger.warning(f"Skipping unsupported image URL: {image_url[:100]}")
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"📷 [Image not accessible: {caption or 'External image'}]"}}]
                }
            }

        # Check if URL needs encoding (has spaces or special chars)
        import urllib.parse
        try:
            # Parse and reconstruct URL to ensure it's properly formatted
            parsed = urllib.parse.urlparse(image_url)
            # If URL has issues, urlparse will still work but may produce invalid results
            if not parsed.scheme or not parsed.netloc:
                logger.warning(f"Invalid URL structure: {image_url[:100]}")
                return {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": f"📷 [Invalid image URL: {caption or 'Untitled'}]"}}]
                    }
                }

            # Encode the URL properly (handle spaces and special characters)
            # Only encode the path and query, not the scheme/netloc
            encoded_url = f"{parsed.scheme}://{parsed.netloc}{urllib.parse.quote(parsed.path, safe='/:')}"
            if parsed.query:
                encoded_url += f"?{urllib.parse.quote(parsed.query, safe='&=')}"

        except Exception as e:
            logger.error(f"Failed to parse image URL: {e}")
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"📷 [Image: {caption or 'Untitled'}]"}}]
                }
            }

        block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": encoded_url  # Use encoded URL
                }
            }
        }

        # Add caption if provided
        if caption:
            block["image"]["caption"] = [
                {
                    "type": "text",
                    "text": {"content": caption[:2000]}  # Notion limit
                }
            ]

        return block

    def _create_equation_block(self, expression: str) -> Dict[str, Any]:
        """Create a Notion equation block for LaTeX math"""
        return {
            "object": "block",
            "type": "equation",
            "equation": {
                "expression": expression[:2000]  # Notion limit
            }
        }

    def _create_code_block(self, code: str, language: str = "plain text") -> Dict[str, Any]:
        """Create a Notion code block with language validation"""
        # Map common language aliases to Notion-supported languages
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'jsx': 'javascript',  # Notion displays JSX with JavaScript highlighting
            'react': 'javascript',
            'tsx': 'typescript',
            'ts': 'typescript',
            'cpp': 'c++',
            'c++': 'c++',
            'cxx': 'c++',
            'sh': 'shell',
            'bash': 'shell',
            'zsh': 'shell',
            'yml': 'yaml',
            'dockerfile': 'docker',
            'makefile': 'makefile',
            'txt': 'plain text',
            'text': 'plain text',
            'plaintext': 'plain text',
            'console': 'shell',
            'cmd': 'powershell',
        }

        # Normalize language name
        normalized_lang = lang_map.get(language.lower().strip(), language.lower().strip())

        # Valid Notion languages (as of 2025)
        valid_languages = {
            "abap", "abc", "agda", "arduino", "ascii art", "assembly", "bash", "basic", "bnf",
            "c", "c#", "c++", "clojure", "coffeescript", "coq", "css", "dart", "dhall", "diff",
            "docker", "ebnf", "elixir", "elm", "erlang", "f#", "flow", "fortran", "gherkin",
            "glsl", "go", "graphql", "groovy", "haskell", "hcl", "html", "idris", "java",
            "javascript", "json", "julia", "kotlin", "latex", "less", "lisp", "livescript",
            "llvm ir", "lua", "makefile", "markdown", "markup", "matlab", "mathematica",
            "mermaid", "nix", "notion formula", "objective-c", "ocaml", "pascal", "perl",
            "php", "plain text", "powershell", "prolog", "protobuf", "purescript", "python",
            "r", "racket", "reason", "ruby", "rust", "sass", "scala", "scheme", "scss",
            "shell", "smalltalk", "solidity", "sql", "swift", "toml", "typescript", "vb.net",
            "verilog", "vhdl", "visual basic", "webassembly", "xml", "yaml", "java/c/c++/c#"
        }

        # Use plain text if language not supported
        final_language = normalized_lang if normalized_lang in valid_languages else "plain text"

        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code[:2000]}}],
                "language": final_language
            }
        }

    def _create_rich_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Create Notion rich text with markdown formatting support
        Handles **bold**, *italic*, and `code` inline formatting
        """
        if len(text) <= 2000:
            return self._parse_inline_formatting(text)

        # Split long text into chunks
        chunks = []
        current = 0
        while current < len(text):
            chunk = text[current:current + 1900]
            chunks.extend(self._parse_inline_formatting(chunk))
            current += 1900

        return chunks[:100]  # Notion limit: 100 rich text elements

    def _parse_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        """Parse inline markdown formatting (**bold**, *italic*, `code`, $$math$$)"""
        import re

        parts = []
        current_pos = 0

        # Find all formatting patterns in order of precedence
        # Process equations before bold/italic to avoid conflicts with $ and * symbols
        # Only match $$ - AI is instructed to ALWAYS use double dollar signs
        patterns = [
            (r'\$\$(.+?)\$\$', 'equation'),           # $$equation$$ - ONLY math format accepted
            (r'\*\*(.+?)\*\*', 'bold'),               # **bold** - must come before italic
            (r'\*(.+?)\*', 'italic'),                  # *italic*
            (r'`([^`]+?)`', 'code'),                   # `code`
        ]

        # Collect all matches with their positions
        matches = []
        for pattern, format_type in patterns:
            for match in re.finditer(pattern, text):
                # Skip if this position is already covered by a previous match
                overlap = False
                for existing in matches:
                    if (match.start() >= existing['start'] and match.start() < existing['end']) or \
                       (match.end() > existing['start'] and match.end() <= existing['end']):
                        overlap = True
                        break

                if not overlap:
                    matches.append({
                        'start': match.start(),
                        'end': match.end(),
                        'content': match.group(1),
                        'format': format_type,
                        'full_match': match.group(0)
                    })

        # Sort by position
        matches.sort(key=lambda x: x['start'])

        # Build rich text parts, handling nested formatting (bold/italic containing equations)
        for match in matches:
            # Skip if we've already processed past this point
            if current_pos > match['start']:
                continue

            # Add plain text before this match
            if current_pos < match['start']:
                plain_text = text[current_pos:match['start']]
                if plain_text:
                    parts.append({"type": "text", "text": {"content": plain_text}})

            # Handle equation differently - it's a special type in Notion
            if match['format'] == 'equation':
                parts.append({
                    "type": "equation",
                    "equation": {"expression": match['content']}
                })
            # For bold/italic, check if content contains equations and split if needed
            elif match['format'] in ('bold', 'italic'):
                # Check if the content contains equations ($$...$$)
                equation_pattern = r'\$\$(.+?)\$\$'
                equations_in_content = list(re.finditer(equation_pattern, match['content']))

                if equations_in_content:
                    # Split bold/italic text around equations
                    inner_pos = 0
                    for eq_match in equations_in_content:
                        # Add bold/italic text before equation
                        if eq_match.start() > inner_pos:
                            text_before = match['content'][inner_pos:eq_match.start()]
                            if text_before:
                                annotations = {
                                    'bold': match['format'] == 'bold',
                                    'italic': match['format'] == 'italic',
                                    'code': False,
                                }
                                parts.append({
                                    "type": "text",
                                    "text": {"content": text_before},
                                    "annotations": annotations
                                })

                        # Add equation (not bold/italic - equations can't have annotations)
                        parts.append({
                            "type": "equation",
                            "equation": {"expression": eq_match.group(1)}
                        })
                        inner_pos = eq_match.end()

                    # Add any remaining bold/italic text after last equation
                    if inner_pos < len(match['content']):
                        text_after = match['content'][inner_pos:]
                        if text_after:
                            annotations = {
                                'bold': match['format'] == 'bold',
                                'italic': match['format'] == 'italic',
                                'code': False,
                            }
                            parts.append({
                                "type": "text",
                                "text": {"content": text_after},
                                "annotations": annotations
                            })
                else:
                    # No equations inside, add as normal formatted text
                    annotations = {
                        'bold': match['format'] == 'bold',
                        'italic': match['format'] == 'italic',
                        'code': False,
                    }
                    parts.append({
                        "type": "text",
                        "text": {"content": match['content']},
                        "annotations": annotations
                    })
            else:
                # Code formatting (can't contain equations)
                annotations = {
                    'bold': False,
                    'italic': False,
                    'code': match['format'] == 'code',
                }
                parts.append({
                    "type": "text",
                    "text": {"content": match['content']},
                    "annotations": annotations
                })

            current_pos = match['end']

        # Add remaining text
        if current_pos < len(text):
            remaining = text[current_pos:]
            if remaining:
                parts.append({"type": "text", "text": {"content": remaining}})

        # If no formatting found, return plain text
        if not parts:
            return [{"type": "text", "text": {"content": text}}]

        return parts

    def _create_error_blocks(self, error_message: str) -> List[Dict[str, Any]]:
        """Create error message blocks"""
        return [
            self._create_heading("⚠️ Content Extraction Error", 1),
            self._create_paragraph(error_message),
            self._create_paragraph(
                "Try opening the page directly or check if it contains educational content."
            )
        ]
