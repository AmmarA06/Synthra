import React, { useState, useEffect } from 'react';
import { Settings, Save, RotateCcw, ExternalLink } from 'lucide-react';
import { useChrome } from '../hooks/useChrome';
import { api, ApiError } from '../services/api';

interface SettingsData {
  apiBaseUrl: string;
  autoSummarize: boolean;
  notionEnabled: boolean;
  highlightEnabled: boolean;
  notionToken?: string;
  notionDatabaseId?: string;
}

const SettingsSection: React.FC = () => {
  const [settings, setSettings] = useState<SettingsData>({
    apiBaseUrl: 'http://localhost:8000',
    autoSummarize: true,
    notionEnabled: false,
    highlightEnabled: true
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const { getStorage, setStorage } = useChrome();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const stored = await getStorage([
        'apiBaseUrl',
        'autoSummarize',
        'notionEnabled',
        'highlightEnabled',
        'notionToken',
        'notionDatabaseId'
      ]);
      
      setSettings(prev => ({
        ...prev,
        ...(stored as Partial<SettingsData>)
      }));
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    setIsLoading(true);
    setIsSaved(false);

    try {
      await setStorage(settings);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const resetSettings = async () => {
    const defaultSettings: SettingsData = {
      apiBaseUrl: 'http://localhost:8000',
      autoSummarize: true,
      notionEnabled: false,
      highlightEnabled: true
    };
    
    setSettings(defaultSettings);
    await setStorage(defaultSettings);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  const handleInputChange = (key: keyof SettingsData, value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const testConnection = async () => {
    setIsLoading(true);
    
    try {
      // Update API base URL
      api.updateBaseUrl(settings.apiBaseUrl);
      
      const response = await api.testConnection();
      alert(`✅ Connection successful!\nStatus: ${response.status}`);
    } catch (error) {
      if (error instanceof ApiError) {
        alert(`❌ Connection failed: ${error.message}`);
      } else {
        alert('❌ Connection failed. Make sure the backend is running.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const testEcho = async () => {
    setIsLoading(true);
    
    try {
      // Update API base URL
      api.updateBaseUrl(settings.apiBaseUrl);
      
      // Get current tab info
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const currentTab = tabs[0];
      
      const response = await api.testEcho(
        currentTab?.title || 'Test Page',
        currentTab?.url || 'https://example.com'
      );
      
      alert(`✅ Echo test successful!\nReceived: "${response.received}"\nTimestamp: ${new Date(response.timestamp).toLocaleTimeString()}`);
    } catch (error) {
      if (error instanceof ApiError) {
        alert(`❌ Echo test failed: ${error.message}`);
      } else {
        alert(`❌ Echo test failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-2">
        <Settings className="w-5 h-5 text-synthra-600" />
        <h2 className="text-lg font-semibold text-gray-900">Settings</h2>
      </div>

      {/* API Configuration */}
      <div className="card space-y-4">
        <h3 className="text-sm font-medium text-gray-900">API Configuration</h3>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Backend URL
            </label>
            <div className="flex space-x-2">
              <input
                type="url"
                value={settings.apiBaseUrl}
                onChange={(e) => handleInputChange('apiBaseUrl', e.target.value)}
                className="flex-1 input-field"
                placeholder="http://localhost:8000"
              />
              <button
                onClick={testConnection}
                disabled={isLoading}
                className="btn-secondary px-3"
              >
                Health
              </button>
              <button
                onClick={testEcho}
                disabled={isLoading}
                className="btn-secondary px-3"
              >
                Echo
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              URL of your Synthra backend server. Use "Health" to test connection, "Echo" to test full communication flow.
            </p>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="card space-y-4">
        <h3 className="text-sm font-medium text-gray-900">Features</h3>
        
        <div className="space-y-4">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={settings.autoSummarize}
              onChange={(e) => handleInputChange('autoSummarize', e.target.checked)}
              className="h-4 w-4 text-synthra-600 rounded border-gray-300"
            />
            <div>
              <div className="text-sm font-medium text-gray-900">Auto-summarize</div>
              <div className="text-xs text-gray-500">Automatically summarize when switching tabs</div>
            </div>
          </label>

          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={settings.highlightEnabled}
              onChange={(e) => handleInputChange('highlightEnabled', e.target.checked)}
              className="h-4 w-4 text-synthra-600 rounded border-gray-300"
            />
            <div>
              <div className="text-sm font-medium text-gray-900">Highlights</div>
              <div className="text-xs text-gray-500">Enable automatic term highlighting</div>
            </div>
          </label>

          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={settings.notionEnabled}
              onChange={(e) => handleInputChange('notionEnabled', e.target.checked)}
              className="h-4 w-4 text-synthra-600 rounded border-gray-300"
            />
            <div>
              <div className="text-sm font-medium text-gray-900">Notion Integration</div>
              <div className="text-xs text-gray-500">Save summaries and highlights to Notion</div>
            </div>
          </label>
        </div>
      </div>

      {/* Notion Configuration */}
      {settings.notionEnabled && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">Notion Configuration</h3>
            <a
              href="https://developers.notion.com/docs/create-a-notion-integration"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-synthra-600 hover:text-synthra-700 flex items-center space-x-1"
            >
              <ExternalLink className="w-3 h-3" />
              <span>Setup Guide</span>
            </a>
          </div>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Integration Token
              </label>
              <input
                type="password"
                value={settings.notionToken || ''}
                onChange={(e) => handleInputChange('notionToken', e.target.value)}
                className="input-field"
                placeholder="secret_..."
              />
              <p className="text-xs text-gray-500 mt-1">
                Your Notion integration secret token
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Database ID
              </label>
              <input
                type="text"
                value={settings.notionDatabaseId || ''}
                onChange={(e) => handleInputChange('notionDatabaseId', e.target.value)}
                className="input-field"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              />
              <p className="text-xs text-gray-500 mt-1">
                The ID of your Notion database for saving content
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex space-x-3">
        <button
          onClick={saveSettings}
          disabled={isLoading}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg font-medium transition-colors ${
            isSaved
              ? 'bg-green-600 text-white'
              : 'btn-primary'
          }`}
        >
          <Save className="w-4 h-4" />
          <span>{isSaved ? 'Saved!' : 'Save Settings'}</span>
        </button>

        <button
          onClick={resetSettings}
          className="btn-secondary flex items-center justify-center space-x-2 px-4"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset</span>
        </button>
      </div>

      {/* Version Info */}
      <div className="border-t pt-4">
        <div className="text-xs text-gray-500 space-y-1">
          <div>Synthra Extension v1.0.0</div>
          <div>Manifest Version 3</div>
        </div>
      </div>
    </div>
  );
};

export default SettingsSection;
