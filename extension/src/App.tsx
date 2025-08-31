import { useState, useEffect } from 'react';
import { Brain, Settings, BookOpen, Lightbulb, Search, Save } from 'lucide-react';
import { TabContent, Summary, Highlight, Research, NextStep } from '@shared/types';
import SummarySection from './components/SummarySection';
import HighlightSection from './components/HighlightSection';
import ResearchSection from './components/ResearchSection';
import NextStepsSection from './components/NextStepsSection';
import SettingsSection from './components/SettingsSection';
import LoadingSpinner from './components/LoadingSpinner';
import { useChrome } from './hooks/useChrome';
import { api, ApiError } from './services/api';

type ActiveTab = 'summary' | 'highlights' | 'research' | 'nextsteps' | 'settings';

function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('summary');
  const [currentTabContent, setCurrentTabContent] = useState<TabContent | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [research, setResearch] = useState<Research | null>(null);
  const [nextSteps, setNextSteps] = useState<NextStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { sendMessage, getStorage } = useChrome();

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
    if (!currentTabContent) return;

    setIsLoading(true);
    setError(null);

    try {
      const summary = await api.summarize(
        currentTabContent.content,
        currentTabContent.title,
        currentTabContent.url
      );
      setSummary(summary);
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to summarize content';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleHighlight = async (text?: string) => {
    if (!currentTabContent && !text) return;

    setIsLoading(true);
    setError(null);

    try {
      const newHighlights = await api.highlight(
        text || currentTabContent?.content || '',
        text ? 'selected' : 'full'
      );
      
      setHighlights(prev => [...prev, ...newHighlights]);
      
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
      console.log('Starting tab research with query:', query, 'and tab IDs:', tabIds);
      
      // Get content from all specified tabs
      const tabs = await chrome.tabs.query({});
      console.log('All available tabs:', tabs.map(t => ({ id: t.id, title: t.title, url: t.url })));
      
      const tabContents: TabContent[] = [];
      
      for (const tabId of tabIds) {
        const tab = tabs.find(t => t.id === tabId);
        console.log('Processing tab:', tab);
        
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
            console.log('Content extracted from tab:', results[0].result);
            
            if (results[0].result.error) {
              console.error('Content extraction error:', results[0].result.error);
              setError(`Failed to extract content from tab: ${results[0].result.error}`);
              setIsLoading(false);
              return;
            }
            
            tabContents.push(results[0].result as TabContent);
          } catch (scriptError) {
            console.error('Error extracting content from tab:', tabId, scriptError);
            setError(`Failed to extract content from tab: ${tab.title || tab.url}`);
            setIsLoading(false);
            return;
          }
        }
      }
      
      console.log('All tab contents extracted:', tabContents);
      
      if (tabContents.length === 0) {
        setError('No content could be extracted from the selected tabs');
        setIsLoading(false);
        return;
      }
      
      const research = await api.research(query, tabContents);
      console.log('Research result:', research);
      setResearch(research);
    } catch (err) {
      console.error('Research error:', err);
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to perform research';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNextSteps = async (userGoal?: string) => {
    if (!currentTabContent || !summary) return;

    setIsLoading(true);
    setError(null);

    try {
      const steps = await api.suggestNextSteps(
        currentTabContent.content,
        summary,
        userGoal
      );
      setNextSteps(steps);
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to suggest next steps';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveToNotion = async (content: any, type: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await api.notionSave(
        content,
        type as 'summary' | 'highlight' | 'research' | 'content',
        currentTabContent?.title,
        currentTabContent?.url
      );
      
      // Show success message
      console.log('Saved to Notion successfully:', result);
      // You could show a toast notification here instead of console.log
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
    { id: 'nextsteps', label: 'Next Steps', icon: BookOpen },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white border-b">
        <div className="flex items-center space-x-2">
          <Brain className="w-6 h-6 text-synthra-600" />
          <h1 className="text-lg font-semibold text-gray-900">Synthra</h1>
        </div>
        {currentTabContent && (
          <button
            onClick={() => handleSaveToNotion(summary || currentTabContent, 'content')}
            className="p-2 text-gray-500 hover:text-synthra-600 transition-colors"
            title="Save to Notion"
          >
            <Save className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b bg-white">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ActiveTab)}
              className={`flex-1 flex items-center justify-center space-x-1 py-3 px-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-synthra-600 border-b-2 border-synthra-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {error && (
          <div className="p-4 m-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-xs text-red-600 hover:text-red-800"
            >
              Dismiss
            </button>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center p-8">
            <LoadingSpinner />
          </div>
        )}

        <div className="h-full overflow-y-auto">
          {activeTab === 'summary' && (
            <SummarySection
              currentTab={currentTabContent}
              summary={summary}
              onSummarize={handleSummarize}
              isLoading={isLoading}
            />
          )}

          {activeTab === 'highlights' && (
            <HighlightSection
              highlights={highlights}
              onHighlight={handleHighlight}
              onClearHighlights={() => setHighlights([])}
              isLoading={isLoading}
            />
          )}

          {activeTab === 'research' && (
            <ResearchSection
              research={research}
              onResearch={handleResearch}
              isLoading={isLoading}
            />
          )}

          {activeTab === 'nextsteps' && (
            <NextStepsSection
              nextSteps={nextSteps}
              onGenerateSteps={handleNextSteps}
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
