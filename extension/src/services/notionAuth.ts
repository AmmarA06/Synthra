// Notion Integration Service
export interface NotionAuthState {
  isAuthenticated: boolean;
  accessToken?: string;
  workspaceName?: string;
  workspaceId?: string;
  userId?: string;
  userEmail?: string;
}

export interface NotionDatabase {
  id: string;
  title: string;
  description?: string;
  url: string;
  icon?: string;
  lastEditedTime: string;
}

class NotionAuthService {
  // private readonly API_BASE = 'https://api.notion.com/v1'; // Not used anymore - using backend API

  // Start authentication with integration token
  async startAuth(integrationToken: string): Promise<void> {
    try {
      // Import the API service dynamically to avoid circular imports
      const { api } = await import('./api');
      
      // Test the token using our backend
      const testResult = await api.testNotionConnection(integrationToken);
      
      if (!testResult.success) {
        throw new Error(testResult.error || 'Invalid integration token. Please check your token and try again.');
      }
      
      // Store the token and user info
      await this.storeAuthData({
        accessToken: integrationToken,
        userId: (testResult as any).user_id || 'unknown',
        userEmail: (testResult as any).user_email || 'Notion User',
        workspaceName: testResult.workspace || 'Notion Workspace'
      });
    } catch (error) {
      console.error('Authentication failed:', error);
      throw new Error(error instanceof Error ? error.message : 'Authentication failed');
    }
  }

  // Get list of accessible databases
  async getDatabases(): Promise<NotionDatabase[]> {
    const authState = await this.getAuthState();
    if (!authState.isAuthenticated || !authState.accessToken) {
      throw new Error('Not authenticated with Notion');
    }

    try {
      // Import the API service dynamically to avoid circular imports
      const { api } = await import('./api');
      
      // Get databases using our backend
      const result = await api.getNotionDatabases(authState.accessToken);
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to load databases. Please try again.');
      }
      
      return result.databases;
    } catch (error) {
      console.error('Failed to fetch databases:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to load databases. Please try again.');
    }
  }

  // Test connection to Notion
  async testConnection(): Promise<boolean> {
    const authState = await this.getAuthState();
    if (!authState.isAuthenticated || !authState.accessToken) {
      return false;
    }

    try {
      // Import the API service dynamically to avoid circular imports
      const { api } = await import('./api');
      
      // Test connection using our backend
      const result = await api.testNotionConnection(authState.accessToken);
      return result.success;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }

  // Store authentication data
  private async storeAuthData(authData: Partial<NotionAuthState>): Promise<void> {
    const currentState = await this.getAuthState();
    const newState: NotionAuthState = {
      ...currentState,
      ...authData,
      isAuthenticated: true
    };

    await chrome.storage.sync.set({
      notionAuth: newState
    });
  }

  // Get current authentication state
  async getAuthState(): Promise<NotionAuthState> {
    try {
      const result = await chrome.storage.sync.get(['notionAuth']);
      return result.notionAuth || {
        isAuthenticated: false
      };
    } catch (error) {
      console.error('Failed to get auth state:', error);
      return { isAuthenticated: false };
    }
  }

  // Clear authentication data
  async logout(): Promise<void> {
    await chrome.storage.sync.remove(['notionAuth', 'selectedDatabaseId']);
  }

  // Get access token for API calls
  async getAccessToken(): Promise<string | null> {
    const authState = await this.getAuthState();
    return authState.accessToken || null;
  }

  // Get selected database ID
  async getSelectedDatabaseId(): Promise<string | null> {
    try {
      const result = await chrome.storage.sync.get(['selectedDatabaseId']);
      return result.selectedDatabaseId || null;
    } catch (error) {
      console.error('Failed to get selected database ID:', error);
      return null;
    }
  }

  // Set selected database ID
  async setSelectedDatabaseId(databaseId: string): Promise<void> {
    await chrome.storage.sync.set({ selectedDatabaseId: databaseId });
  }
}

export const notionAuth = new NotionAuthService();
