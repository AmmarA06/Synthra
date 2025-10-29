# Synthra Backend

FastAPI backend for the Synthra AI browser agent.

## Features

- **AI-powered content analysis** using Google Gemini models
- **Content summarization** with key points and concepts
- **Intelligent highlighting** of key terms and explanations
- **Multi-tab research** comparing content across browser tabs
- **URL research** for comparing multiple webpages
- **Notion integration** for saving structured content

## Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   # or
   uvicorn main:app --reload
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
GEMINI_MODEL=gemini-1.5-flash
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here
ALLOWED_ORIGINS=chrome-extension://your-extension-id
DEBUG=True
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /echo` - Test endpoint for extension communication
- `POST /summarize` - Summarize content with enhanced parsing
- `POST /highlight` - Highlight key terms
- `POST /multi-tab-research` - Research across tabs
- `POST /multi-tab-research-enhanced` - Enhanced research with vector similarity
- `POST /url-research` - Fetch and compare multiple URLs
- `POST /notion/test-connection` - Test Notion API connection
- `POST /notion/databases` - Get available Notion databases
- `POST /notion/save` - Save content to Notion

## Development

The API documentation is available at `http://localhost:8000/docs` when running the server.

## Production Deployment

For production deployment, make sure to:

1. Set appropriate CORS origins
2. Use environment variables for all secrets
3. Enable HTTPS
4. Set `DEBUG=False`
