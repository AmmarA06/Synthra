// Shared types for Synthra

// Base interfaces
export interface TabContent {
  title: string;
  url: string;
  content: string;
  html?: string;
  timestamp?: number;
}

export interface Summary {
  summary: string;
  keyPoints: string[];
  keyConcepts: string[];
  readingTimeMinutes?: number;
  timestamp?: number;
  url?: string;
  title?: string;
}

export interface Highlight {
  term: string;
  explanation: string;
  context?: string;
  importance?: 'low' | 'medium' | 'high';
  category?: string;
  position?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface Research {
  query: string;
  summary: string;
  keyFindings: string[];
  comparisons: {
    aspect: string;
    details: string;
  }[];
  sources: {
    title: string;
    url: string;
    relevance?: number;
  }[];
  timestamp?: number;
}

// Vector Search and Similarity types
export interface VectorDocument {
  id: number;
  title: string;
  url: string;
  content: string;
  metadata: Record<string, any>;
  addedAt: string;
  similarityScore?: number;
  rank?: number;
}

export interface SimilarContent {
  title: string;
  url: string;
  content: string;
  similarityScore: number;
  rank: number;
}

export interface ContentCluster {
  clusters: number[][];
  labels: number[];
  centroids: number[][];
  nClusters: number;
}

// API Request/Response types
export interface SummarizeRequest {
  content: string;
  url: string;
  title: string;
}

export interface SummarizeResponse {
  summary: Summary;
  success: boolean;
  error?: string;
}

export interface HighlightRequest {
  content: string;
  url: string;
  context?: string;
}

export interface HighlightResponse {
  highlights: Highlight[];
  success: boolean;
  error?: string;
}

export interface MultiTabResearchRequest {
  tabs: TabContent[];
  query: string;
}

export interface MultiTabResearchResponse {
  research: Research;
  success: boolean;
  error?: string;
}

// New URL-based multi-tab research types
export interface UrlResearchRequest {
  urls: string[];
  query?: string;
}

export interface PageAnalysis {
  title: string;
  url: string;
  keyPoints: string[];
  pros: string[];
  cons: string[];
  summary: string;
  error?: string;
}

export interface UrlResearchResponse {
  pages: PageAnalysis[];
  comparison: {
    summary: string;
    commonThemes: string[];
    keyDifferences: string[];
  };
  success: boolean;
  error?: string;
}

// Vector Search API types
export interface VectorSearchRequest {
  query: string;
  k?: number;
  threshold?: number;
}

export interface VectorSearchResponse {
  results: VectorDocument[];
  success: boolean;
  error?: string;
}

export interface AddDocumentsRequest {
  documents: {
    content: string;
    title?: string;
    url?: string;
    metadata?: Record<string, any>;
  }[];
}

export interface AddDocumentsResponse {
  documentIds: number[];
  success: boolean;
  error?: string;
}

export interface FindSimilarContentRequest {
  content: string;
  tabContents: TabContent[];
  k?: number;
}

export interface FindSimilarContentResponse {
  similarContents: SimilarContent[];
  success: boolean;
  error?: string;
}

export interface ContentDiversityRequest {
  contents: string[];
}

export interface ContentDiversityResponse {
  diversityScore: number;
  success: boolean;
  error?: string;
}

export interface ClusterContentRequest {
  contents: string[];
  nClusters?: number;
}

export interface ClusterContentResponse {
  clusters: ContentCluster;
  success: boolean;
  error?: string;
}

export interface NotionAuthRequest {
  code?: string;
  redirectUri?: string;
}

export interface NotionAuthResponse {
  accessToken?: string;
  workspaceName?: string;
  success: boolean;
  error?: string;
}

export interface NotionSaveRequest {
  content: any;
  type: 'summary' | 'highlight' | 'research' | 'content';
  title?: string;
  url?: string;
  notionToken?: string;
  databaseId?: string;
}

export interface NotionSaveResponse {
  pageId?: string;
  pageUrl?: string;
  success: boolean;
  error?: string;
}

// Chrome Extension specific types
export interface ChromeMessage {
  type: string;
  data?: any;
  [key: string]: any;
}

export interface ChromeResponse {
  success: boolean;
  data?: any;
  error?: string;
}

// Settings types
export interface ExtensionSettings {
  apiBaseUrl: string;
  autoSummarize: boolean;
  notionEnabled: boolean;
  highlightEnabled: boolean;
  notionToken?: string;
  notionDatabaseId?: string;
}

// Error types
export interface APIError {
  message: string;
  code?: string;
  details?: any;
}

// Utility types
export type HighlightImportance = Highlight['importance'];

// Export everything as default for easier importing
export default {
  // Types (these are just for documentation, not runtime)
  TabContent: {} as TabContent,
  Summary: {} as Summary,
  Highlight: {} as Highlight,
  Research: {} as Research,
  SummarizeRequest: {} as SummarizeRequest,
  SummarizeResponse: {} as SummarizeResponse,
  HighlightRequest: {} as HighlightRequest,
  HighlightResponse: {} as HighlightResponse,
  MultiTabResearchRequest: {} as MultiTabResearchRequest,
  MultiTabResearchResponse: {} as MultiTabResearchResponse,
  NotionAuthRequest: {} as NotionAuthRequest,
  NotionAuthResponse: {} as NotionAuthResponse,
  NotionSaveRequest: {} as NotionSaveRequest,
  NotionSaveResponse: {} as NotionSaveResponse,
  ChromeMessage: {} as ChromeMessage,
  ChromeResponse: {} as ChromeResponse,
  ExtensionSettings: {} as ExtensionSettings,
  APIError: {} as APIError
};
