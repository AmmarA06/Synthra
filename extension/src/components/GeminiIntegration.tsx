import React, { useState, useEffect } from 'react';
import { Brain, CheckCircle, AlertCircle, Loader2, Key, Eye, EyeOff } from 'lucide-react';
import { useChrome } from '../hooks/useChrome';

const GeminiIntegration: React.FC = () => {
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [storedApiKey, setStoredApiKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  const { getStorage, setStorage } = useChrome();

  useEffect(() => {
    loadStoredApiKey();
  }, []);

  const loadStoredApiKey = async () => {
    try {
      const settings = await getStorage(['geminiApiKey']) as { geminiApiKey?: string };
      if (settings.geminiApiKey) {
        setStoredApiKey(settings.geminiApiKey);
      }
    } catch (error) {
      console.error('Failed to load Gemini API key:', error);
    }
  };

  const handleSaveApiKey = async () => {
    if (!geminiApiKey.trim()) {
      setError('Please enter your Gemini API key');
      return;
    }

    // Basic API key validation
    if (!geminiApiKey.trim().startsWith('AIza')) {
      setError('Gemini API keys typically start with "AIza". Please check your key.');
      return;
    }

    if (geminiApiKey.trim().length < 20) {
      setError('API key appears to be too short');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await setStorage({ geminiApiKey: geminiApiKey.trim() });
      setStoredApiKey(geminiApiKey.trim());
      setGeminiApiKey(''); // Clear the input for security
      setSuccess('Gemini API key saved successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error('Failed to save Gemini API key:', error);
      setError('Failed to save API key. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveApiKey = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await setStorage({ geminiApiKey: null });
      setStoredApiKey(null);
      setGeminiApiKey('');
      setSuccess('Gemini API key removed successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error('Failed to remove Gemini API key:', error);
      setError('Failed to remove API key. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async () => {
    if (!storedApiKey) {
      setError('No API key stored to test');
      return;
    }

    setIsTestingConnection(true);
    setError(null);
    setSuccess(null);

    try {
      // Get the current API base URL from storage
      const settings = await chrome.storage.sync.get(['apiBaseUrl']);
      const baseUrl = settings.apiBaseUrl || 'http://localhost:8000';
      
      // Test the connection by making a simple API call
      const response = await fetch(`${baseUrl}/test-gemini`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ apiKey: storedApiKey })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        setSuccess('Connection test successful! Gemini API is working.');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(result.error || 'Connection test failed. Please check your API key.');
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      setError('Connection test failed. Please check your API key and internet connection.');
    } finally {
      setIsTestingConnection(false);
    }
  };

  const maskedApiKey = storedApiKey ? `${storedApiKey.slice(0, 8)}...${storedApiKey.slice(-4)}` : '';

  if (storedApiKey) {
    return (
      <div className="card space-y-4">
        {/* Header with connection status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="text-sm font-medium text-gray-900">Gemini AI Connected</h3>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={testConnection}
              disabled={isTestingConnection}
              className="text-xs text-synthra-600 hover:text-synthra-700 transition-colors"
              title="Test API connection"
            >
              {isTestingConnection ? 'Testing...' : 'Test'}
            </button>
            <button
              onClick={handleRemoveApiKey}
              disabled={isLoading}
              className="text-xs text-gray-500 hover:text-red-600 transition-colors"
            >
              Remove
            </button>
          </div>
        </div>

        {/* API Key info */}
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="text-sm font-medium text-gray-900 mb-1">
            API Key Configured
          </div>
          <div className="text-xs text-gray-500 font-mono">
            {maskedApiKey}
          </div>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <p className="text-green-800 text-sm">{success}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Status */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-blue-600" />
            <div className="text-sm text-blue-800">
              <div className="font-medium">AI Features Enabled</div>
              <div className="text-xs text-blue-600 mt-1">
                Content summarization and highlighting are now available
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center space-x-2">
        <Brain className="w-5 h-5 text-synthra-600" />
        <h3 className="text-sm font-medium text-gray-900">Gemini AI Integration</h3>
      </div>
      
      <div className="text-sm text-gray-600">
        Connect your Gemini API key to enable AI-powered content summarization and highlighting.
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Gemini API Key
          </label>
          <div className="flex space-x-2">
            <div className="flex-1 relative">
              <input
                type={showApiKey ? "text" : "password"}
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
                className="w-full input-field pr-10"
                placeholder="Enter your Gemini API key"
                disabled={isLoading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !isLoading && geminiApiKey.trim()) {
                    handleSaveApiKey();
                  }
                }}
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showApiKey ? (
                  <EyeOff className="w-4 h-4 text-gray-400" />
                ) : (
                  <Eye className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
            <button
              onClick={handleSaveApiKey}
              disabled={isLoading || !geminiApiKey.trim()}
              className="btn-primary px-4 flex items-center space-x-2"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Key className="w-4 h-4" />
              )}
              <span>{isLoading ? 'Saving...' : 'Save'}</span>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Get your API key from <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-synthra-600 hover:underline">Google AI Studio</a>
          </p>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <p className="text-green-800 text-sm">{success}</p>
          </div>
        </div>
      )}

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
            <div className="font-medium mb-2">How to get your Gemini API key:</div>
            <ol className="list-decimal list-inside space-y-1 text-xs">
              <li>Go to <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline font-medium">Google AI Studio</a></li>
              <li>Sign in with your Google account</li>
              <li>Click <span className="font-medium">"Create API Key"</span></li>
              <li>Select or create a Google Cloud project</li>
              <li>Copy the generated API key</li>
              <li>Paste it above and click <span className="font-medium">"Save"</span></li>
            </ol>
            <div className="mt-2 p-2 bg-blue-100 rounded text-xs">
              <strong>💡 Tip:</strong> Keep your API key secure and don't share it with others!
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeminiIntegration;
