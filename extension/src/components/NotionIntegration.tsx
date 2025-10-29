import React, { useState, useEffect } from 'react';
import { LogIn, Database, CheckCircle, AlertCircle, Loader2, Key } from 'lucide-react';
import { notionAuth, NotionAuthState, NotionDatabase } from '../services/notionAuth';

const NotionIntegration: React.FC = () => {
  const [authState, setAuthState] = useState<NotionAuthState>({ isAuthenticated: false });
  const [databases, setDatabases] = useState<NotionDatabase[]>([]);
  const [selectedDatabaseId, setSelectedDatabaseId] = useState<string | null>(null);
  const [integrationToken, setIntegrationToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAuthState();
  }, []);

  useEffect(() => {
    if (authState.isAuthenticated) {
      loadDatabases();
      loadSelectedDatabase();
    }
  }, [authState.isAuthenticated]);

  const loadAuthState = async () => {
    try {
      const state = await notionAuth.getAuthState();
      setAuthState(state);
    } catch (error) {
      console.error('Failed to load auth state:', error);
    }
  };

  const loadDatabases = async () => {
    if (!authState.isAuthenticated) return;

    setIsLoadingDatabases(true);
    setError(null);

    try {
      const dbList = await notionAuth.getDatabases();
      setDatabases(dbList);
      
      // If no databases found, show a helpful message
      if (dbList.length === 0) {
        setError('No databases found. Make sure you have created databases in your Notion workspace and that your integration has access to them.');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load databases';
      setError(errorMessage);
      console.error('Failed to load databases:', error);
      
      // Provide more specific error messages
      if (errorMessage.includes('unauthorized') || errorMessage.includes('forbidden')) {
        setError('Access denied. Please check that your integration has permission to access databases in your Notion workspace.');
      } else if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
        setError('Network error. Please check your internet connection and try again.');
      }
    } finally {
      setIsLoadingDatabases(false);
    }
  };

  const loadSelectedDatabase = async () => {
    try {
      const dbId = await notionAuth.getSelectedDatabaseId();
      setSelectedDatabaseId(dbId);
    } catch (error) {
      console.error('Failed to load selected database:', error);
    }
  };

  const handleLogin = async () => {
    if (!integrationToken.trim()) {
      setError('Please enter your integration token');
      return;
    }

    // Basic token validation - Notion tokens can have different formats
    if (integrationToken.trim().length < 10) {
      setError('Integration token appears to be too short');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await notionAuth.startAuth(integrationToken.trim());
      await loadAuthState();
      setIntegrationToken(''); // Clear the token input for security
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      setError(errorMessage);
      
      // Provide more helpful error messages
      if (errorMessage.includes('unauthorized') || errorMessage.includes('forbidden')) {
        setError('Invalid token. Please check your integration token and make sure it has the correct permissions.');
      } else if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
        setError('Network error. Please check your internet connection and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    setIsLoading(true);

    try {
      await notionAuth.logout();
      setAuthState({ isAuthenticated: false });
      setDatabases([]);
      setSelectedDatabaseId(null);
      setError(null);
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDatabaseSelect = async (databaseId: string) => {
    try {
      await notionAuth.setSelectedDatabaseId(databaseId);
      setSelectedDatabaseId(databaseId);
      setError(null); // Clear any previous errors
    } catch (error) {
      console.error('Failed to save database selection:', error);
      setError('Failed to save database selection. Please try again.');
    }
  };


  if (!authState.isAuthenticated) {
    return (
      <div className="card space-y-4">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 text-synthra-600" />
          <h3 className="text-sm font-medium text-gray-900">Notion Integration</h3>
        </div>
        
        <div className="text-sm text-gray-600">
          Connect your Notion workspace to save summaries and highlights directly to your databases.
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Integration Token
            </label>
            <div className="flex space-x-2">
              <input
                type="password"
                value={integrationToken}
                onChange={(e) => setIntegrationToken(e.target.value)}
                className="flex-1 input-field"
                placeholder="Enter your integration token"
                disabled={isLoading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !isLoading && integrationToken.trim()) {
                    handleLogin();
                  }
                }}
              />
              <button
                onClick={handleLogin}
                disabled={isLoading || !integrationToken.trim()}
                className="btn-primary px-4 flex items-center space-x-2"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <LogIn className="w-4 h-4" />
                )}
                <span>{isLoading ? 'Connecting...' : 'Connect'}</span>
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Get your token from <a href="https://www.notion.so/my-integrations" target="_blank" rel="noopener noreferrer" className="text-synthra-600 hover:underline">Notion Integrations</a>
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          </div>
        )}

        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="flex items-start space-x-2">
            <Key className="w-4 h-4 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <div className="font-medium mb-2">How to set up Notion integration:</div>
              <ol className="list-decimal list-inside space-y-1 text-xs">
                <li>Go to <a href="https://www.notion.so/my-integrations" target="_blank" rel="noopener noreferrer" className="underline font-medium">Notion Integrations</a></li>
                <li>Click <span className="font-medium">"New integration"</span></li>
                <li>Name it <span className="font-medium">"Synthra Browser Agent"</span></li>
                <li>Select your workspace</li>
                <li>Copy the <span className="font-medium">"Internal Integration Token"</span></li>
                <li>Paste it above and click <span className="font-medium">"Connect"</span></li>
                <li>Create a database in Notion (or use existing one)</li>
                <li>Share the database with your integration in the database settings</li>
              </ol>
              <div className="mt-2 p-2 bg-blue-100 rounded text-xs">
                <strong>💡 Tip:</strong> Make sure to share your database with the integration after connecting!
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      {/* Header with connection status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <h3 className="text-sm font-medium text-gray-900">Connected to Notion</h3>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={loadDatabases}
            disabled={isLoadingDatabases}
            className="text-xs text-synthra-600 hover:text-synthra-700 transition-colors"
            title="Test connection and refresh databases"
          >
            {isLoadingDatabases ? 'Testing...' : 'Test'}
          </button>
          <button
            onClick={handleLogout}
            disabled={isLoading}
            className="text-xs text-gray-500 hover:text-red-600 transition-colors"
          >
            Disconnect
          </button>
        </div>
      </div>

      {/* Workspace info */}
      <div className="bg-gray-50 p-3 rounded-lg">
        <div className="text-sm font-medium text-gray-900">
          {authState.workspaceName || 'Notion Workspace'}
        </div>
        {authState.userEmail && (
          <div className="text-xs text-gray-500">
            {authState.userEmail}
          </div>
        )}
      </div>

      {/* Database Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Target Database
          </label>
          <button
            onClick={loadDatabases}
            disabled={isLoadingDatabases}
            className="text-xs text-synthra-600 hover:text-synthra-700"
          >
            {isLoadingDatabases ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {isLoadingDatabases ? (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
            <span className="ml-2 text-sm text-gray-500">Loading databases...</span>
          </div>
        ) : databases.length === 0 ? (
          <div className="text-center py-6">
            <Database className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500 mb-2">No databases found</p>
            <p className="text-xs text-gray-400">
              Make sure you have created databases in your Notion workspace and that your integration has access to them.
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {databases.map((db) => (
              <button
                key={db.id}
                onClick={() => handleDatabaseSelect(db.id)}
                className={`w-full p-3 text-left rounded-lg border transition-all duration-200 ${
                  selectedDatabaseId === db.id
                    ? 'border-synthra-600 bg-synthra-50 shadow-sm'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      {db.icon && (
                        <span className="text-sm flex-shrink-0">{db.icon}</span>
                      )}
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {db.title}
                      </div>
                    </div>
                    {db.description && (
                      <div className="text-xs text-gray-500 mt-1 truncate">
                        {db.description}
                      </div>
                    )}
                  </div>
                  {selectedDatabaseId === db.id && (
                    <CheckCircle className="w-4 h-4 text-synthra-600 flex-shrink-0" />
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        </div>
      )}

      {selectedDatabaseId && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <div className="text-sm text-green-800">
              <div className="font-medium">Ready to save content!</div>
              <div className="text-xs text-green-600 mt-1">
                Summaries, highlights, and research will be saved to your selected database
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotionIntegration;
