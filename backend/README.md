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
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
```
