import React, { useState, useEffect } from 'react';
import { Search, ExternalLink, Globe } from 'lucide-react';
import { Research, UrlResearchResponse } from '@shared/types';
import { useChrome } from '../hooks/useChrome';
import ResearchPanel from './ResearchPanel';

interface ResearchSectionProps {
  research: Research | null;
  onResearch: (query: string, tabIds: number[]) => void;
  isLoading: boolean;
}

const ResearchSection: React.FC<ResearchSectionProps> = ({
  research,
  onResearch,
  isLoading
}) => {
  const [activeMode, setActiveMode] = useState<'tabs' | 'urls'>('urls');
  const [query, setQuery] = useState('');
  const [selectedTabs, setSelectedTabs] = useState<number[]>([]);
  const [availableTabs, setAvailableTabs] = useState<chrome.tabs.Tab[]>([]);
  const [, setUrlResearch] = useState<UrlResearchResponse | null>(null);
  const { getAllTabs } = useChrome();

  useEffect(() => {
    loadAvailableTabs();
  }, []);

  const loadAvailableTabs = async () => {
    try {
      const tabs = await getAllTabs();
      // Filter out extension pages and special pages
      const validTabs = tabs.filter(tab => 
        tab.url && 
        !tab.url.startsWith('chrome://') && 
        !tab.url.startsWith('chrome-extension://') &&
        !tab.url.startsWith('moz-extension://')
      );
      setAvailableTabs(validTabs);
    } catch (error) {
      console.error('Failed to load tabs:', error);
    }
  };

  const handleTabToggle = (tabId: number) => {
    setSelectedTabs(prev => 
      prev.includes(tabId)
        ? prev.filter(id => id !== tabId)
        : [...prev, tabId]
    );
  };

  const handleResearch = () => {
    if (query.trim() && selectedTabs.length > 0) {
      onResearch(query.trim(), selectedTabs);
    }
  };

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname + urlObj.pathname;
    } catch {
      return url;
    }
  };

  const handleUrlResearch = (result: UrlResearchResponse) => {
    setUrlResearch(result);
  };

  return (
    <div className="p-4 space-y-4">
      {/* Mode Toggle */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setActiveMode('urls')}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
            activeMode === 'urls'
              ? 'bg-white text-synthra-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <Globe className="w-4 h-4" />
          <span>URL Research</span>
        </button>
        <button
          onClick={() => setActiveMode('tabs')}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
            activeMode === 'tabs'
              ? 'bg-white text-synthra-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <Search className="w-4 h-4" />
          <span>Tab Research</span>
        </button>
      </div>
      {/* Content based on active mode */}
      {activeMode === 'urls' ? (
        <ResearchPanel onResearchComplete={handleUrlResearch} />
      ) : (
        <div className="space-y-4">
          {/* Research Query */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Research Question
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What would you like to research across your open tabs? e.g., 'Compare pricing models', 'Find common themes', 'Summarize key differences'"
              className="textarea-field h-20"
            />
          </div>

          {/* Tab Selection */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">
                Select Tabs to Research ({selectedTabs.length})
              </label>
              <button
                onClick={loadAvailableTabs}
                className="text-xs text-synthra-600 hover:text-synthra-700"
              >
                Refresh
              </button>
            </div>
            
            <div className="max-h-40 overflow-y-auto space-y-2 border rounded-md p-2">
              {availableTabs.map((tab) => (
                <div
                  key={tab.id}
                  className={`flex items-center space-x-3 p-2 rounded cursor-pointer transition-colors ${
                    selectedTabs.includes(tab.id!)
                      ? 'bg-synthra-50 border border-synthra-200'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                  onClick={() => handleTabToggle(tab.id!)}
                >
                  <input
                    type="checkbox"
                    checked={selectedTabs.includes(tab.id!)}
                    onChange={() => handleTabToggle(tab.id!)}
                    className="h-4 w-4 text-synthra-600 rounded border-gray-300"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {tab.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {formatUrl(tab.url!)}
                    </p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0" />
                </div>
              ))}
              
              {availableTabs.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  No suitable tabs found for research
                </p>
              )}
            </div>
          </div>

          {/* Research Button */}
          <button
            onClick={handleResearch}
            disabled={!query.trim() || selectedTabs.length === 0 || isLoading}
            className="w-full btn-primary flex items-center justify-center space-x-2"
          >
            <Search className="w-4 h-4" />
            <span>Start Research</span>
          </button>
        </div>
      )}

      {/* Research Results */}
      {research && (
        <div className="card animate-fade-in space-y-4">
          <div className="flex items-center space-x-2">
            <Search className="w-4 h-4 text-synthra-600" />
            <h3 className="text-sm font-medium text-gray-900">Research Results</h3>
          </div>

          {/* Query */}
          <div className="bg-gray-50 p-3 rounded">
            <p className="text-sm text-gray-700">
              <span className="font-medium">Query:</span> {research.query}
            </p>
          </div>

          {/* Summary */}
          {research.summary && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                {research.summary}
              </p>
            </div>
          )}

          {/* Key Findings */}
          {research.keyFindings && research.keyFindings.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Key Findings</h4>
              <ul className="space-y-2">
                {research.keyFindings.map((finding, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                    <span className="text-synthra-500 mt-1 flex-shrink-0">•</span>
                    <span>{finding}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Comparisons */}
          {research.comparisons && research.comparisons.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Comparisons</h4>
              <div className="space-y-3">
                {research.comparisons.map((comparison, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded">
                    <h5 className="text-sm font-medium text-gray-800 mb-1">
                      {comparison.aspect}
                    </h5>
                    <p className="text-sm text-gray-600">{comparison.details}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sources */}
          {research.sources && research.sources.length > 0 && (
            <div className="border-t pt-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Sources</h4>
              <div className="space-y-2">
                {research.sources.map((source, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <ExternalLink className="w-3 h-3 text-gray-400 mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {source.title}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {formatUrl(source.url)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!research && !isLoading && (
        <div className="text-center py-8">
          <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-gray-900 mb-2">Multi-Tab Research</h3>
          <p className="text-xs text-gray-500 mb-4">
            Compare and analyze content across multiple tabs to get comprehensive insights
          </p>
        </div>
      )}
    </div>
  );
};

export default ResearchSection;
