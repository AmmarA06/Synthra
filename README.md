# Synthra — AI-Powered Notion Study Notes

Turn any webpage into beautiful, study-ready Notion pages with one click.

## Why Synthra?

While tools like Perplexity's Comet offer general web research, **Synthra focuses exclusively on creating perfect study notes in Notion**.

### Features

- Extracts clean content using enhanced parsing (no ads or clutter)
- AI-powered content summarization with key points
- Smart term highlighting with explanations
- Multi-tab and URL research for comparing sources
- Formats perfectly for Notion (headings, bullets, code blocks)

### Perfect For

- Students saving lecture notes and research
- Developers documenting tutorials and code
- Researchers organizing articles
- Anyone building a knowledge base in Notion

## Quick Start

### 1. Install Dependencies

```bash
npm run install:all
```

### 2. Configure Backend

Create `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key
```

**Get Notion credentials:**

1. [Create integration](https://www.notion.so/my-integrations) → Copy token
2. Share database with integration → Copy database ID from URL

### 3. Start Development

```bash
npm run dev
```

### 4. Load Extension

```bash
cd extension
npm run build
```

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → Select `extension/dist`

## Usage

1. Browse to any webpage
2. Click Synthra icon in Chrome to open the side panel
3. **Summarize**: Get AI-powered summary with key points
4. **Highlight**: Identify and explain key terms on the page
5. **Research**: Compare multiple tabs or URLs
6. **Save to Notion**: Export summaries and content to your Notion workspace

### Notion Integration

1. Click "Settings" in the extension
2. Connect your Notion account
3. Select a database to save to
4. All summaries and research can be saved with one click

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
