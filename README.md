# Synthra — AI Browser & Learning Agent

A Chrome Extension + Backend agent that helps users summarize, highlight, research, and suggest follow-up resources while browsing.

## Project Structure

```
synthra/
├── extension/          # Chrome Extension (MV3, React + Vite, TypeScript)
├── backend/           # FastAPI Backend (Python)
├── shared/            # Shared JSON schemas and types
└── package.json       # Monorepo configuration
```

## Features

- **Summarize** current tab content (concise bullets)
- **Highlight & explain** key terms
- **Multi-tab research** automation (compare pages, consolidate)
- **Suggest follow-up** resources for continued learning
- **Notion integration** (save summaries, highlights)
- **Sidebar UI** (React + Tailwind)
- **Secure backend API** (FastAPI, never exposing keys)

## Quick Start

1. **Install dependencies**:
   ```bash
   npm run install:all
   ```

2. **Start development**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

## Development

### Extension Development
- Navigate to `chrome://extensions/`
- Enable "Developer mode"
- Click "Load unpacked" and select the `extension/dist` folder

### Backend Development
- The FastAPI server runs on `http://localhost:8000`
- API documentation available at `http://localhost:8000/docs`

## Tech Stack

- **Chrome Extension**: Manifest V3, React + Vite, TypeScript, Tailwind
- **Backend**: FastAPI (Python), Google Gemini, Notion SDK, Pydantic
- **Shared**: JSON schemas for summaries/highlights

## Security

- API keys stored only on backend (.env)
- HTTPS enforced in production
- CORS restricted to extension ID
