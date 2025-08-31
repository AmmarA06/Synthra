# Synthra Shared Types

Shared TypeScript types and Python dataclasses for the Synthra project.

## Overview

This package contains the shared data structures used across the Synthra Chrome extension and FastAPI backend. It ensures type safety and consistency between the frontend and backend.

## Features

- **TypeScript types** for the Chrome extension
- **Python dataclasses** auto-generated from TypeScript
- **JSON schemas** for API requests/responses
- **Utility functions** for type conversion

## Usage

### TypeScript (Extension)

```typescript
import { Summary, Highlight, Research } from '@shared/types';

const summary: Summary = {
  summary: "Main content summary",
  keyPoints: ["Point 1", "Point 2"],
  keyConcepts: ["Concept 1", "Concept 2"],
  readingTimeMinutes: 5
};
```

### Python (Backend)

```python
from shared.types import Summary, Highlight, Research

summary = Summary(
    summary="Main content summary",
    key_points=["Point 1", "Point 2"],
    key_concepts=["Concept 1", "Concept 2"],
    reading_time_minutes=5
)
```

## Types

### Core Data Types

- **TabContent**: Web page content and metadata
- **Summary**: AI-generated page summaries
- **Highlight**: Key term explanations and highlights
- **Research**: Multi-tab research results
- **NextStep**: Learning path suggestions

### API Types

- **Request/Response** types for all API endpoints
- **Chrome message** types for extension communication
- **Settings** types for user preferences

## Development

### Building Types

```bash
npm run build        # Build TypeScript
npm run generate:python  # Generate Python types
npm run build:all    # Build both
```

### Type Generation

Python types are automatically generated from TypeScript definitions using a custom script. This ensures consistency between frontend and backend types while maintaining language-specific conventions (camelCase vs snake_case).

## Conventions

### TypeScript
- camelCase for property names
- PascalCase for type names
- Optional properties marked with `?`

### Python
- snake_case for property names
- PascalCase for class names
- Optional properties use `Optional[T]` type hints

## Adding New Types

1. Define the TypeScript interface in `src/types.ts`
2. Run `npm run build:all` to generate Python types
3. Update both extension and backend code to use new types
4. Ensure proper conversion functions if needed
