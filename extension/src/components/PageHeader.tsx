import React, { useState, useEffect } from 'react';
import { Globe, Clock, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';

interface PageHeaderProps {
  currentUrl: string | null;
  isLoading: boolean;
  onPageSelect: (url: string) => void;
}

interface TabHistoryItem {
  url: string;
  title: string;
  lastUpdated: number;
}

const PageHeader: React.FC<PageHeaderProps> = ({ currentUrl, isLoading, onPageSelect }) => {
  const [showHistory, setShowHistory] = useState(false);
  const [tabHistory, setTabHistory] = useState<TabHistoryItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname + urlObj.pathname;
    } catch {
      return url;
    }
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const loadTabHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const allData = await chrome.storage.local.get(null);
      const history = Object.entries(allData)
        .filter(([key]) => key.startsWith('tabState_'))
        .map(([key, value]) => {
          const url = key.replace('tabState_', '');
          const state = value as any;
          return {
            url,
            title: state.summary?.title || formatUrl(url),
            lastUpdated: state.lastUpdated || Date.now()
          };
        })
        .sort((a, b) => b.lastUpdated - a.lastUpdated)
        .slice(0, 10); // Show last 10 pages
      
      setTabHistory(history);
    } catch (error) {
      console.error('Error loading tab history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (showHistory) {
      loadTabHistory();
    }
  }, [showHistory]);

  if (!currentUrl) {
    return (
      <div className="p-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center space-x-2 text-gray-500">
          <Globe className="w-4 h-4" />
          <span className="text-sm">No page detected</span>
        </div>
      </div>
    );
  }

  return (
    <div className="border-b border-gray-200">
      {/* Current Page */}
      <div className="p-3 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 min-w-0 flex-1">
            <Globe className="w-4 h-4 text-synthra-600 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-gray-900 truncate">
                {isLoading ? 'Loading...' : formatUrl(currentUrl)}
              </div>
              <div className="text-xs text-gray-500 truncate">
                {currentUrl}
              </div>
            </div>
          </div>
          <a
            href={currentUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 text-gray-400 hover:text-synthra-600 transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* History Toggle */}
      <div className="px-3 py-2 bg-gray-50">
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors w-full"
        >
          <Clock className="w-4 h-4" />
          <span>Recent Pages</span>
          {showHistory ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>

      {/* History List */}
      {showHistory && (
        <div className="max-h-48 overflow-y-auto bg-white border-t border-gray-200">
          {isLoadingHistory ? (
            <div className="p-3 text-center text-sm text-gray-500">
              Loading history...
            </div>
          ) : tabHistory.length === 0 ? (
            <div className="p-3 text-center text-sm text-gray-500">
              No recent pages
            </div>
          ) : (
            <div className="py-1">
              {tabHistory.map((item) => (
                <button
                  key={item.url}
                  onClick={() => {
                    onPageSelect(item.url);
                    setShowHistory(false);
                  }}
                  className={`w-full px-3 py-2 text-left hover:bg-gray-50 transition-colors ${
                    item.url === currentUrl ? 'bg-synthra-50 text-synthra-700' : 'text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">
                        {item.title}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {formatUrl(item.url)}
                      </div>
                    </div>
                    <div className="text-xs text-gray-400 ml-2 flex-shrink-0">
                      {formatTime(item.lastUpdated)}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PageHeader;
