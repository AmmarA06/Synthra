# Synthra

Turn any webpage into beautiful, study-ready Notion pages with one click.

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

### 2. Start Development

```bash
npm run dev
```

### 3. Load Extension

```bash
cd extension
npm run build
```

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → Select `extension/dist`

## Usage

### Initial Setup

1. Click Synthra icon in Chrome to open the side panel
2. Go to **Settings** tab
3. **Configure Gemini AI:**
   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Paste it in the Gemini API Key field
   - Click "Save" and test the connection
4. **Configure Notion (Optional):**
   - [Create integration](https://www.notion.so/my-integrations) → Copy token
   - Paste token and connect your account
   - Select a database to save content to

### Using the Extension

1. Browse to any webpage
2. **Summarize**: Get AI-powered summary with key points
3. **Highlight**: Identify and explain key terms on the page
4. **Research**: Compare multiple tabs or URLs
5. **Save to Notion**: Export summaries and content to your Notion workspace (if configured)

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Optional:** For development, you can create `backend/.env` with `GEMINI_API_KEY=your_key` to avoid configuring it in the extension each time. The extension will fall back to environment variables if no API key is configured in settings.
