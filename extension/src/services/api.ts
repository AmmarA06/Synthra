/**
 * API Service for Synthra Extension
 * Handles all communication with the FastAPI backend
 */

import {
  TabContent,
  Summary,
  Highlight,
  Research,
  NextStep,
  SummarizeRequest,
  SummarizeResponse,
  HighlightRequest,
  HighlightResponse,
  MultiTabResearchRequest,
  MultiTabResearchResponse,
  SuggestNextStepsRequest,
  SuggestNextStepsResponse,
  NotionSaveRequest,
  NotionSaveResponse,
  UrlResearchRequest,
  UrlResearchResponse
} from '@shared/types';

// API Configuration
interface ApiConfig {
  baseUrl: string;
  timeout: number;
}

// Default configuration
const DEFAULT_CONFIG: ApiConfig = {
  baseUrl: 'http://localhost:8000',
  timeout: 30000 // 30 seconds
};

// API Error class
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// API Service class
export class ApiService {
  private config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Update the API base URL
   */
  updateBaseUrl(baseUrl: string): void {
    this.config.baseUrl = baseUrl;
  }

  /**
   * Make HTTP request with proper error handling
   */
  private async makeRequest<T>(
    endpoint: string,
    data: any,
    method: 'GET' | 'POST' = 'POST'
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: method === 'POST' ? JSON.stringify(data) : undefined,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new ApiError(
          `HTTP ${response.status}: ${errorText}`,
          response.status,
          errorText
        );
      }

      const result = await response.json();
      return result as T;

    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError('Request timeout');
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new ApiError('Network error - check if backend is running');
      }

      throw new ApiError(`Request failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Test API connection
   */
  async testConnection(): Promise<{ status: string; timestamp: number }> {
    return this.makeRequest('/health', {}, 'GET');
  }

  /**
   * Test echo endpoint
   */
  async testEcho(title: string, url: string): Promise<{ received: string; timestamp: number; success: boolean }> {
    return this.makeRequest('/echo', { title, url, source: 'api-service' });
  }

  /**
   * Summarize content
   */
  async summarize(content: string, title: string, url: string): Promise<Summary> {
    const request: SummarizeRequest = {
      content,
      title,
      url
    };

    const response = await this.makeRequest<SummarizeResponse>('/summarize', request);
    
    if (!response.success) {
      throw new ApiError(response.error || 'Summarization failed');
    }

    return response.summary;
  }

  /**
   * Highlight key terms in text
   */
  async highlight(content: string, context?: string): Promise<Highlight[]> {
    const request: HighlightRequest = {
      content,
      url: window.location?.href || '',
      context
    };

    const response = await this.makeRequest<HighlightResponse>('/highlight', request);
    
    if (!response.success) {
      throw new ApiError(response.error || 'Highlighting failed');
    }

    return response.highlights;
  }

  /**
   * Perform multi-tab research
   */
  async research(query: string, tabs: TabContent[]): Promise<Research> {
    const request: MultiTabResearchRequest = {
      query,
      tabs
    };

    const response = await this.makeRequest<MultiTabResearchResponse>('/multi-tab-research', request);
    
    if (!response.success) {
      throw new ApiError(response.error || 'Research failed');
    }

    return response.research;
  }

  /**
   * Suggest next learning steps
   */
  async suggestNextSteps(
    content: string, 
    summary: Summary, 
    userGoal?: string
  ): Promise<NextStep[]> {
    const request: SuggestNextStepsRequest = {
      content,
      summary,
      userGoal
    };

    const response = await this.makeRequest<SuggestNextStepsResponse>('/suggest-next-steps', request);
    
    if (!response.success) {
      throw new ApiError(response.error || 'Next steps suggestion failed');
    }

    return response.steps;
  }

  /**
   * Save content to Notion
   */
  async notionSave(
    content: any,
    type: 'summary' | 'highlight' | 'research' | 'content',
    title?: string,
    url?: string
  ): Promise<{ pageId?: string; pageUrl?: string }> {
    const request: NotionSaveRequest = {
      content,
      type,
      title,
      url
    };

    const response = await this.makeRequest<NotionSaveResponse>('/notion/save', request);
    
    if (!response.success) {
      throw new ApiError(response.error || 'Notion save failed');
    }

    return {
      pageId: response.pageId,
      pageUrl: response.pageUrl
    };
  }

  /**
   * Research multiple URLs with comparison analysis
   */
  async urlResearch(urls: string[], query?: string): Promise<UrlResearchResponse> {
    const request: UrlResearchRequest = {
      urls,
      query
    };

    const response = await this.makeRequest<UrlResearchResponse>('/url-research', request);
    
    if (!response.success) {
      throw new ApiError(response.error || 'URL research failed');
    }

    return response;
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Convenience functions for direct use
export const api = {
  /**
   * Summarize text content
   */
  summarize: async (text: string, title: string = '', url: string = ''): Promise<Summary> => {
    return apiService.summarize(text, title, url);
  },

  /**
   * Highlight key terms in text
   */
  highlight: async (text: string, context?: string): Promise<Highlight[]> => {
    return apiService.highlight(text, context);
  },

  /**
   * Perform research across multiple tabs
   */
  research: async (query: string, tabs: TabContent[]): Promise<Research> => {
    return apiService.research(query, tabs);
  },

  /**
   * Suggest next learning steps
   */
  suggestNextSteps: async (
    text: string, 
    summary: Summary, 
    userGoal?: string
  ): Promise<NextStep[]> => {
    return apiService.suggestNextSteps(text, summary, userGoal);
  },

  /**
   * Save content to Notion
   */
  notionSave: async (
    content: any,
    type: 'summary' | 'highlight' | 'research' | 'content',
    title?: string,
    url?: string
  ): Promise<{ pageId?: string; pageUrl?: string }> => {
    return apiService.notionSave(content, type, title, url);
  },

  /**
   * Test API connection
   */
  testConnection: async (): Promise<{ status: string; timestamp: number }> => {
    return apiService.testConnection();
  },

  /**
   * Test echo functionality
   */
  testEcho: async (title: string, url: string): Promise<{ received: string; timestamp: number; success: boolean }> => {
    return apiService.testEcho(title, url);
  },

  /**
   * Update API base URL
   */
  updateBaseUrl: (baseUrl: string): void => {
    apiService.updateBaseUrl(baseUrl);
  },

  /**
   * Research multiple URLs with comparison
   */
  urlResearch: async (urls: string[], query?: string): Promise<UrlResearchResponse> => {
    return apiService.urlResearch(urls, query);
  }
};

// Export types for external use
export type {
  ApiConfig,
  TabContent,
  Summary,
  Highlight,
  Research,
  NextStep
};

export default api;
