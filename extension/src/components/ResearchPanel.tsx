import React, { useState, useEffect } from 'react';
import { Search, ExternalLink, Plus, X, ArrowRight, CheckCircle, AlertCircle, ChevronDown, ChevronRight, Maximize2 } from 'lucide-react';
import { UrlResearchResponse, PageAnalysis } from '@shared/types';
import { api, ApiError } from '../services/api';
import ComparisonModal from './ComparisonModal';

interface ResearchPanelProps {
  onResearchComplete?: (result: UrlResearchResponse) => void;
}

const ResearchPanel: React.FC<ResearchPanelProps> = ({ onResearchComplete }) => {
  const [urls, setUrls] = useState<string[]>(['']);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<UrlResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    summary: true,
    themes: false,
    differences: false,
    table: false,
    individual: false
  });

  // Auto-populate with open tabs
  useEffect(() => {
    loadOpenTabs();
  }, []);

  const loadOpenTabs = async () => {
    try {
      const tabs = await chrome.tabs.query({});
      const validTabs = tabs
        .filter(tab => 
          tab.url && 
          !tab.url.startsWith('chrome://') && 
          !tab.url.startsWith('chrome-extension://') &&
          !tab.url.startsWith('moz-extension://')
        )
        .slice(0, 5) // Limit to first 5 tabs
        .map(tab => tab.url!);
      
      if (validTabs.length > 0) {
        setUrls(validTabs.concat([''])); // Add empty field for new URLs
      }
    } catch (error) {
      console.error('Failed to load tabs:', error);
    }
  };

  const addUrlField = () => {
    setUrls([...urls, '']);
  };

  const removeUrlField = (index: number) => {
    if (urls.length > 1) {
      setUrls(urls.filter((_, i) => i !== index));
    }
  };

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const handleResearch = async () => {
    const validUrls = urls.filter(url => url.trim() !== '');
    
    if (validUrls.length < 2) {
      setError('Please provide at least 2 URLs for comparison');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const research = await api.urlResearch(validUrls, query || undefined);
      setResult(research);
      onResearchComplete?.(research);
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Research failed';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
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

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Research Query (Optional)
          </label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'Compare pricing models', 'Find key differences'"
            className="input-field"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              URLs to Compare ({urls.filter(url => url.trim()).length})
            </label>
            <button
              onClick={loadOpenTabs}
              className="text-xs text-synthra-600 hover:text-synthra-700"
            >
              Load Open Tabs
            </button>
          </div>
          
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {urls.map((url, index) => (
              <div key={index} className="flex items-center space-x-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => updateUrl(index, e.target.value)}
                  placeholder="https://example.com"
                  className="flex-1 input-field text-sm"
                />
                {urls.length > 1 && (
                  <button
                    onClick={() => removeUrlField(index)}
                    className="p-1 text-red-500 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
          
          <button
            onClick={addUrlField}
            className="mt-2 flex items-center space-x-1 text-sm text-synthra-600 hover:text-synthra-700"
          >
            <Plus className="w-4 h-4" />
            <span>Add URL</span>
          </button>
        </div>

        <button
          onClick={handleResearch}
          disabled={isLoading || urls.filter(url => url.trim()).length < 2}
          className="w-full btn-primary flex items-center justify-center space-x-2"
        >
          <Search className="w-4 h-4" />
          <span>{isLoading ? 'Researching...' : 'Start Research'}</span>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="space-y-4">
          {/* Quick Summary - Always Visible */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">Quick Summary</h3>
              <button
                onClick={() => setShowModal(true)}
                className="text-synthra-600 hover:text-synthra-700 flex items-center space-x-1 text-xs"
              >
                <Maximize2 className="w-3 h-3" />
                <span>View Full Analysis</span>
              </button>
            </div>
            <p className="text-sm text-gray-600">{result.comparison.summary}</p>
          </div>

          {/* Collapsible Sections */}
          <div className="space-y-2">
            {/* Common Themes */}
            {result.comparison.commonThemes.length > 0 && (
              <div className="card">
                <button
                  onClick={() => toggleSection('themes')}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h4 className="text-sm font-medium text-gray-700">Common Themes ({result.comparison.commonThemes.length})</h4>
                  {expandedSections.themes ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </button>
                {expandedSections.themes && (
                  <ul className="mt-3 space-y-1">
                    {result.comparison.commonThemes.map((theme, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                        <CheckCircle className="w-3 h-3 text-green-500 mt-1 flex-shrink-0" />
                        <span>{theme}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Key Differences */}
            {result.comparison.keyDifferences.length > 0 && (
              <div className="card">
                <button
                  onClick={() => toggleSection('differences')}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h4 className="text-sm font-medium text-gray-700">Key Differences ({result.comparison.keyDifferences.length})</h4>
                  {expandedSections.differences ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </button>
                {expandedSections.differences && (
                  <ul className="mt-3 space-y-1">
                    {result.comparison.keyDifferences.map((difference, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                        <ArrowRight className="w-3 h-3 text-synthra-500 mt-1 flex-shrink-0" />
                        <span>{difference}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Quick Comparison Table */}
            <div className="card">
              <button
                onClick={() => toggleSection('table')}
                className="flex items-center justify-between w-full text-left"
              >
                <h4 className="text-sm font-medium text-gray-700">Quick Comparison</h4>
                {expandedSections.table ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
              {expandedSections.table && (
                <div className="mt-3 overflow-x-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-1 font-medium text-gray-700">Page</th>
                        <th className="text-left p-1 font-medium text-gray-700">Summary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.pages.filter(page => !page.error).map((page, index) => (
                        <tr key={index} className="border-b">
                          <td className="p-1 align-top">
                            <a 
                              href={page.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-synthra-600 hover:text-synthra-700 flex items-center space-x-1"
                            >
                              <span className="truncate max-w-20">{formatUrl(page.url)}</span>
                              <ExternalLink className="w-3 h-3 flex-shrink-0" />
                            </a>
                          </td>
                          <td className="p-1 align-top text-gray-600">
                            {page.summary}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Individual Page Analysis */}
            <div className="card">
              <button
                onClick={() => toggleSection('individual')}
                className="flex items-center justify-between w-full text-left"
              >
                <h4 className="text-sm font-medium text-gray-700">Individual Analysis ({result.pages.length} pages)</h4>
                {expandedSections.individual ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
              {expandedSections.individual && (
                <div className="mt-3 space-y-3">
                  {result.pages.map((page, index) => (
                    <PageCard key={index} page={page} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      <ComparisonModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        data={result}
      />
    </div>
  );
};

// Individual Page Card Component
const PageCard: React.FC<{ page: PageAnalysis }> = ({ page }) => {
  if (page.error) {
    return (
      <div className="card border-red-200">
        <div className="flex items-center space-x-2 mb-2">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <h4 className="text-sm font-medium text-red-700">{page.title}</h4>
        </div>
        <p className="text-sm text-red-600">{page.error}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-900 truncate flex-1">{page.title}</h4>
        <a 
          href={page.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-synthra-600 hover:text-synthra-700 ml-2 flex-shrink-0"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{page.summary}</p>
      
      <div className="grid grid-cols-1 gap-2">
        <div>
          <h5 className="text-xs font-medium text-gray-700 mb-1">Key Points</h5>
          <ul className="space-y-1">
            {page.keyPoints.slice(0, 2).map((point, index) => (
              <li key={index} className="text-xs text-gray-600">• {point}</li>
            ))}
          </ul>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          <div>
            <h5 className="text-xs font-medium text-green-700 mb-1">Pros</h5>
            <ul className="space-y-1">
              {page.pros.slice(0, 2).map((pro, index) => (
                <li key={index} className="text-xs text-green-600">+ {pro}</li>
              ))}
            </ul>
          </div>
          
          <div>
            <h5 className="text-xs font-medium text-red-700 mb-1">Cons</h5>
            <ul className="space-y-1">
              {page.cons.slice(0, 2).map((con, index) => (
                <li key={index} className="text-xs text-red-600">- {con}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchPanel;
