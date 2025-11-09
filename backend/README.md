## Setup

1. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables (Optional for development)**:

   ```bash
   cp env.example .env
   # Edit .env with your API keys (optional - can be configured in extension settings)
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   # or
   uvicorn main:app --reload
   ```

## Environment Variables (Optional)

For development convenience, you can create a `.env` file with the following variables. **Note:** The extension now allows users to configure their API key in the settings, making the `.env` file optional.

```env
GEMINI_API_KEY=your_gemini_api_key_here  # Optional - falls back to extension settings
GEMINI_MODEL=gemini-flash-latest         # Optional - defaults to gemini-flash-latest
```

**For production/Chrome Web Store:** Users configure their Gemini API key directly in the extension settings. No backend configuration needed!
