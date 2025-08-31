# Synthra Setup Guide

Complete setup instructions for the Synthra AI Browser Agent.

## Prerequisites

- **Node.js** 18+ (for the extension and build tools)
- **Python** 3.8+ (for the backend)
- **Chrome Browser** (for testing the extension)
- **Google Gemini API Key** (required for AI features)
- **Notion Integration** (optional, for saving content)

## Quick Start

1. **Install all dependencies**:
   ```bash
   npm run install:all
   ```

2. **Configure the backend**:
   ```bash
   cd backend
   cp env.example .env
   # Edit .env with your Google Gemini API key
   ```

3. **Start development servers**:
   ```bash
   npm run dev
   ```

4. **Load the extension**:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (top right toggle)
   - Click "Load unpacked"
   - Select the `extension/dist` folder

## Detailed Setup

### 1. Backend Configuration

#### Environment Variables

Create `backend/.env` with the following:

```env
# Required
GEMINI_API_KEY=your-gemini-api-key-here

# Optional (recommended)
GEMINI_MODEL=gemini-1.5-flash
DEBUG=True
LOG_LEVEL=INFO

# Notion Integration (optional)
NOTION_TOKEN=secret_your-notion-integration-token
NOTION_DATABASE_ID=your-database-id-here

# CORS (update with your extension ID after installation)
ALLOWED_ORIGINS=chrome-extension://your-extension-id-here
```

#### Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Start Backend

```bash
cd backend
npm run dev
# or
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`.

### 2. Extension Setup

#### Install Dependencies

```bash
cd extension
npm install
```

#### Build Extension

```bash
cd extension
npm run build
```

#### Load in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" using the toggle in the top right
3. Click "Load unpacked" button
4. Navigate to and select the `extension/dist` folder
5. The extension should now appear in your extensions list

#### Configure Extension

1. Click the Synthra extension icon in your Chrome toolbar
2. Navigate to the "Settings" tab in the sidebar
3. Verify the backend URL is set to `http://localhost:8000`
4. Test the connection using the "Test" button

### 3. Notion Integration (Optional)

#### Create Notion Integration

1. Go to [Notion Developers](https://developers.notion.com/)
2. Click "New integration"
3. Fill in the integration details:
   - Name: "Synthra"
   - Associated workspace: Your workspace
   - Capabilities: Read content, Update content, Insert content
4. Save the integration and copy the "Internal Integration Token"

#### Create Database

1. Create a new page in Notion
2. Add a database with these properties:
   - **Name** (Title)
   - **Type** (Select: Summary, Highlight, Research, Content)
   - **URL** (URL)
   - **Created** (Date)
   - **Reading Time** (Number, optional)

3. Share the database with your integration:
   - Click "Share" on the database page
   - Add your integration by name
   - Give it edit permissions

4. Copy the database ID from the URL:
   - Database URL: `https://notion.so/workspace/DATABASE_ID?v=...`
   - Extract the DATABASE_ID part

#### Configure Backend

Add to your `backend/.env`:

```env
NOTION_TOKEN=secret_your-integration-token-here
NOTION_DATABASE_ID=your-database-id-here
```

#### Configure Extension

1. Open the extension settings
2. Enable "Notion Integration"
3. The integration should work automatically using the backend configuration

### 4. Development Workflow

#### Full Development Setup

Start all services for development:

```bash
# Root directory
npm run dev
```

This will start:
- Extension development server (Vite)
- Backend development server (FastAPI with auto-reload)

#### Making Changes

##### Extension Changes
- Edit files in `extension/src/`
- Changes will auto-reload in development mode
- Reload the extension in Chrome if needed

##### Backend Changes
- Edit files in `backend/`
- FastAPI will auto-reload on changes
- Check `http://localhost:8000/docs` for API documentation

##### Shared Types Changes
- Edit `shared/src/types.ts`
- Run `npm run build:shared` to update types
- Both extension and backend will need to be restarted

### 5. Building for Production

#### Build Everything

```bash
npm run build
```

#### Extension Package

```bash
cd extension
npm run build
```

The extension will be built to `extension/dist/` and packaged as `extension/dist-zip/synthra-extension.zip`.

#### Backend Deployment

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

For production, make sure to:
- Set `DEBUG=False`
- Use HTTPS
- Configure proper CORS origins
- Use environment variables for secrets

## Troubleshooting

### Extension Issues

**Extension not loading:**
- Check that you selected the `dist` folder, not the `extension` folder
- Make sure the build completed successfully
- Check Chrome developer console for errors

**API connection failed:**
- Verify the backend is running on `http://localhost:8000`
- Check the backend URL in extension settings
- Look for CORS errors in the browser console

### Backend Issues

**Gemini API errors:**
- Verify your API key is correct and has appropriate quotas
- Check the model name in your `.env` file
- Monitor rate limits and usage

**Notion integration errors:**
- Verify the integration token and database ID
- Ensure the database is shared with your integration
- Check that required properties exist in the database

### General Issues

**Type errors:**
- Run `npm run build:shared` to update shared types
- Restart both extension and backend development servers
- Check for TypeScript compilation errors

**Dependencies:**
- Run `npm run install:all` to reinstall all dependencies
- Clear node_modules and reinstall if needed
- Check Node.js and Python versions

## Support

For issues and questions:
1. Check the browser console for error messages
2. Check the backend logs for API errors
3. Verify all environment variables are set correctly
4. Ensure all services are running and accessible
