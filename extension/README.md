# Synthra Chrome Extension

AI-powered browser agent for summarizing, highlighting, research, and learning assistance.

## Features

- **Smart Summarization**: Get concise summaries of web pages with key points
- **Intelligent Highlighting**: Automatically identify and explain key terms
- **Multi-Tab Research**: Compare and analyze content across multiple tabs
- **Learning Suggestions**: Get personalized next steps for continued learning
- **Notion Integration**: Save summaries and highlights to your Notion workspace
- **Sidebar Interface**: Clean, modern sidebar UI that doesn't interfere with browsing

## Development Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

4. **Load in Chrome**:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `dist` folder

## Project Structure

```
extension/
├── public/           # Static assets and icons
├── src/             # React source code
│   ├── components/  # UI components
│   ├── hooks/       # Custom React hooks
│   └── main.tsx     # Entry point
├── background.js    # Service worker
├── content.js       # Content script
├── manifest.json    # Extension manifest
└── sidebar.html     # Sidebar entry point
```

## Configuration

The extension connects to the Synthra backend API. Configure the backend URL in the settings panel within the extension.

Default backend URL: `http://localhost:8000`

## Features in Detail

### Summarization
- Extracts key points from web pages
- Identifies important concepts
- Estimates reading time
- Preserves context and source information

### Highlighting
- Identifies technical terms and jargon
- Provides clear explanations
- Categories terms by importance
- Shows contextual tooltips on hover

### Multi-Tab Research
- Compare content across multiple tabs
- Generate comprehensive research reports
- Find connections and differences
- Cite sources automatically

### Next Steps
- Suggest relevant learning resources
- Provide actionable next steps
- Categorize by type (read, practice, research)
- Include time estimates and difficulty levels

## Permissions

The extension requires the following permissions:

- `tabs`: Access to browser tabs for content analysis
- `storage`: Save user preferences and settings
- `scripting`: Inject content scripts for highlighting
- `activeTab`: Access current tab content
- `sidePanel`: Display the sidebar interface

## Privacy

- All AI processing happens on the configured backend server
- No API keys are stored in the extension
- User data is only sent to the configured backend
- Content is processed temporarily and not stored permanently
