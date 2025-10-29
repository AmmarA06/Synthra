# Synthra — AI-Powered Notion Study Notes

Turn any webpage into beautiful, study-ready Notion pages with one click.

## Why Synthra?

While tools like Perplexity's Comet offer general web research, **Synthra focuses exclusively on creating perfect study notes in Notion**.

### Features

- Extracts clean educational content (no ads, navigation, or clutter)
- AI-structures content into scannable study format
- Formats perfectly for Notion (headings, bullets, code blocks)
- Optimized for learning and quick review

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

1. Browse to any educational webpage
2. Click Synthra icon in Chrome
3. Click "Summarize" to process with AI
4. Click "Save" to send to Notion

The extension automatically:

- Removes navigation, ads, and clutter
- Extracts educational content
- Structures with clear headings and sections
- Formats code blocks with syntax highlighting
- Creates scannable bullet points

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
