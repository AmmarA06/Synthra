import { useState, useEffect } from 'react';
import { Brain, Settings, Lightbulb, Search, Save } from 'lucide-react';
import { TabContent } from '@shared/types';
import SummarySection from './components/SummarySection';
import HighlightSection from './components/HighlightSection';
import ResearchSection from './components/ResearchSection';
import SettingsSection from './components/SettingsSection';
import LoadingSpinner from './components/LoadingSpinner';
import PageTransitionIndicator from './components/PageTransitionIndicator';
import Toast from './components/Toast';
import { useChrome } from './hooks/useChrome';
import { useTabState } from './hooks/useTabState';
import { api, ApiError } from './services/api';

type ActiveTab = 'summary' | 'highlights' | 'research' | 'settings';

function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('summary');
  const [currentTabContent, setCurrentTabContent] = useState<TabContent | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { sendMessage, getStorage } = useChrome();
  const tabState = useTabState();

  // Load current tab content on mount
  useEffect(() => {
    loadCurrentTabContent();
  }, []);

  // Load API settings on mount
  useEffect(() => {
    loadApiSettings();
  }, []);

  // Listen for tab changes
  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === 'TAB_CHANGED' || message.type === 'TAB_UPDATED') {
        loadCurrentTabContent();
      }
    };

    chrome.runtime.onMessage.addListener(handleMessage);
    return () => chrome.runtime.onMessage.removeListener(handleMessage);
  }, []);

  // Also refresh content when user switches to highlights tab to ensure we have current content
  useEffect(() => {
    if (activeTab === 'highlights') {
      loadCurrentTabContent();
    }
  }, [activeTab]);

  const loadApiSettings = async () => {
    try {
      const settings = await getStorage(['apiBaseUrl']) as { apiBaseUrl?: string };
      const baseUrl = settings.apiBaseUrl || 'http://localhost:8000';
      api.updateBaseUrl(baseUrl);
    } catch (error) {
      console.error('Failed to load API settings:', error);
    }
  };

  const loadCurrentTabContent = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await sendMessage({ type: 'GET_TAB_CONTENT' });
      if (response.success) {
        setCurrentTabContent(response.data);
      } else {
        setError(response.error || 'Failed to load tab content');
      }
    } catch (err) {
      setError('Failed to communicate with background script');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarize = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch fresh content from current tab
      const response = await sendMessage({ type: 'GET_TAB_CONTENT' });
      if (!response.success) {
        throw new Error(response.error || 'Failed to get current page content');
      }

      const tabContent = response.data;
      if (!tabContent.content) {
        throw new Error('No content available to summarize');
      }

      const summary = await api.summarize(
        tabContent.content,
        tabContent.title,
        tabContent.url
      );
      await tabState.saveSummary(summary);
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to summarize content';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleHighlight = async (text?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      let contentToHighlight = text;
      
      // If no specific text provided, fetch fresh content from current tab
      if (!contentToHighlight) {
        const response = await sendMessage({ type: 'GET_TAB_CONTENT' });
        if (response.success) {
          contentToHighlight = response.data.content;
        } else {
          throw new Error(response.error || 'Failed to get current page content');
        }
      }

      if (!contentToHighlight) {
        throw new Error('No content available to highlight');
      }

      const newHighlights = await api.highlight(
        contentToHighlight,
        text ? 'selected' : 'full'
      );
      
      const updatedHighlights = [...tabState.currentState.highlights, ...newHighlights];
      await tabState.saveHighlights(updatedHighlights);
      
      // Send highlights to content script for display
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id!, {
          type: 'HIGHLIGHT_TERMS_ON_PAGE',
          terms: newHighlights
        });
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to highlight terms';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResearch = async (query: string, tabIds: number[]) => {
    setIsLoading(true);
    setError(null);

    try {
      // Get content from all specified tabs
      const tabs = await chrome.tabs.query({});
      const tabContents: TabContent[] = [];
      
      for (const tabId of tabIds) {
        const tab = tabs.find(t => t.id === tabId);
        
        if (tab) {
          try {
            const results = await chrome.scripting.executeScript({
              target: { tabId: tab.id! },
              func: () => {
                // Wait for page to be ready
                if (document.readyState !== 'complete') {
                  return { error: 'Page not fully loaded' };
                }
                
                // Try different content extraction methods
                let content = '';
                if (document.body) {
                  content = document.body.innerText || document.body.textContent || '';
                } else if (document.documentElement) {
                  content = document.documentElement.innerText || document.documentElement.textContent || '';
                }
                
                // Clean up the content
                content = content.replace(/\s+/g, ' ').trim();
                
                return {
                  title: document.title || 'Untitled',
                  url: window.location.href,
                  content: content,
                  timestamp: Date.now()
                };
              }
            });
            
            if (results[0].result.error) {
              // Skip tabs that can't be accessed (chrome:// URLs, etc.)
              continue;
            }
            
            tabContents.push(results[0].result as TabContent);
          } catch (scriptError) {
            // Skip tabs that can't be accessed
            continue;
          }
        }
      }
      
      if (tabContents.length === 0) {
        setError('No accessible content found in the selected tabs. Try selecting different tabs or check if the pages are fully loaded.');
        setIsLoading(false);
        return;
      }
      
      const research = await api.research(query, tabContents);
      await tabState.saveResearch(research);
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to perform research';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };


  const handleSaveToNotion = async (content: any, type: string) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // ALWAYS fetch fresh content from current tab - don't trust cached state
      // This ensures we save content from the actual current page, not a previous page
      const response = await sendMessage({ type: 'GET_TAB_CONTENT' });
      if (!response.success) {
        throw new Error(response.error || 'Failed to get current page content');
      }

      const tabContent = response.data;

      // Use fresh content if type is 'content', otherwise use the passed content
      // This prevents saving stale cached data when navigating between pages
      const contentToSave = type === 'content' ? tabContent.content : content;

      await api.notionSave(
        contentToSave,
        type as 'summary' | 'highlight' | 'research' | 'content',
        tabContent?.title,
        tabContent?.url
      );

      setSuccess('✓ Saved to Notion successfully!');
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to save to Notion';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'summary', label: 'Summary', icon: Brain },
    { id: 'highlights', label: 'Highlights', icon: Lightbulb },
    { id: 'research', label: 'Research', icon: Search },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="flex flex-col h-screen bg-white m-0 p-0">
      {/* Toast Notifications */}
      {error && (
        <Toast
          message={error}
          type="error"
          onClose={() => setError(null)}
        />
      )}
      {success && (
        <Toast
          message={success}
          type="success"
          onClose={() => setSuccess(null)}
        />
      )}

      {/* Page Transition Indicator */}
      <PageTransitionIndicator
        isLoading={tabState.isLoading}
        currentUrl={tabState.currentUrl}
      />

      {/* Custom Header - Takes full control of the top area */}
      <div className="bg-gradient-to-r from-synthra-600 to-synthra-700 shadow-md">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2.5">
            <div className="bg-white/20 p-1.5 rounded-lg backdrop-blur-sm">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-lg font-bold text-white">Synthra</h1>
          </div>
          {currentTabContent && (
            <button
              onClick={() => handleSaveToNotion(null, 'content')}
              disabled={isLoading}
              className="flex items-center gap-2 px-3 py-1.5 bg-white text-synthra-700 text-sm font-medium rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              title="Save to Notion"
            >
              <Save className="w-4 h-4" />
              <span>Save</span>
            </button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex bg-white border-b border-gray-200">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ActiveTab)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-2 text-xs font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'text-synthra-600 border-b-2 border-synthra-600 bg-synthra-50/50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border-b-2 border-transparent'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden relative bg-gray-50">
        {(isLoading || tabState.isLoading) && (
          <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-10">
            <LoadingSpinner />
          </div>
        )}

        <div className="h-full overflow-y-auto bg-gray-50">
          {activeTab === 'summary' && (
            <SummarySection
              currentTab={currentTabContent}
              summary={tabState.currentState.summary}
              onSummarize={handleSummarize}
              isLoading={isLoading}
            />
          )}

          {activeTab === 'highlights' && (
            <HighlightSection
              highlights={tabState.currentState.highlights}
              onHighlight={handleHighlight}
              onClearHighlights={() => tabState.saveHighlights([])}
              isLoading={isLoading}
            />
          )}

          {activeTab === 'research' && (
            <ResearchSection
              research={tabState.currentState.research}
              onResearch={handleResearch}
              isLoading={isLoading}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsSection />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
