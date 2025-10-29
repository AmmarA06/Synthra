import { useState, useEffect, useCallback } from 'react';
import { Summary, Highlight, Research } from '@shared/types';

export interface TabState {
  summary: Summary | null;
  highlights: Highlight[];
  research: Research | null;
  lastUpdated: number;
}

export interface TabStateManager {
  currentUrl: string | null;
  currentState: TabState;
  isLoading: boolean;
  saveSummary: (summary: Summary) => Promise<void>;
  saveHighlights: (highlights: Highlight[]) => Promise<void>;
  saveResearch: (research: Research) => Promise<void>;
  clearCurrentTab: () => Promise<void>;
  getTabHistory: () => Promise<Array<{ url: string; title: string; lastUpdated: number }>>;
}

const DEFAULT_TAB_STATE: TabState = {
  summary: null,
  highlights: [],
  research: null,
  lastUpdated: Date.now()
};

export const useTabState = (): TabStateManager => {
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);
  const [currentState, setCurrentState] = useState<TabState>(DEFAULT_TAB_STATE);
  const [isLoading, setIsLoading] = useState(false);

  // Get current tab URL
  const getCurrentTabUrl = useCallback(async (): Promise<string | null> => {
    try {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]?.url) {
        // Normalize URL - keep query params but remove fragments for consistent storage
        // Query params are important for distinguishing different pages (e.g., ?id=1 vs ?id=2)
        const url = new URL(tabs[0].url);
        return `${url.protocol}//${url.host}${url.pathname}${url.search}`;
      }
      return null;
    } catch (error) {
      console.error('Error getting current tab URL:', error);
      return null;
    }
  }, []);

  // Load state for a specific URL
  const loadStateForUrl = useCallback(async (url: string): Promise<TabState> => {
    try {
      const result = await chrome.storage.local.get([`tabState_${url}`]);
      const storedState = result[`tabState_${url}`];
      
      if (storedState) {
        return {
          ...DEFAULT_TAB_STATE,
          ...storedState,
          lastUpdated: storedState.lastUpdated || Date.now()
        };
      }
      
      return { ...DEFAULT_TAB_STATE, lastUpdated: Date.now() };
    } catch (error) {
      console.error('Error loading state for URL:', error);
      return { ...DEFAULT_TAB_STATE, lastUpdated: Date.now() };
    }
  }, []);

  // Save state for current URL
  const saveStateForUrl = useCallback(async (url: string, newState: Partial<TabState>): Promise<void> => {
    try {
      const currentStoredState = await loadStateForUrl(url);
      const updatedState = {
        ...currentStoredState,
        ...newState,
        lastUpdated: Date.now()
      };
      
      await chrome.storage.local.set({
        [`tabState_${url}`]: updatedState
      });
      
      // Update current state if this is the active URL
      if (url === currentUrl) {
        setCurrentState(updatedState);
      }
    } catch (error) {
      console.error('Error saving state for URL:', error);
    }
  }, [currentUrl, loadStateForUrl]);

  // Check for tab changes
  const checkTabChange = useCallback(async () => {
    const newUrl = await getCurrentTabUrl();
    
    if (newUrl && newUrl !== currentUrl) {
      setIsLoading(true);
      setCurrentUrl(newUrl);
      
      const newState = await loadStateForUrl(newUrl);
      setCurrentState(newState);
      setIsLoading(false);
    }
  }, [currentUrl, getCurrentTabUrl, loadStateForUrl]);

  // Initialize and set up tab change listeners
  useEffect(() => {
    const initialize = async () => {
      const url = await getCurrentTabUrl();
      if (url) {
        setIsLoading(true);
        setCurrentUrl(url);
        const state = await loadStateForUrl(url);
        setCurrentState(state);
        setIsLoading(false);
      }
    };

    initialize();

    // Set up listeners for tab changes
    const handleTabActivated = () => {
      setTimeout(checkTabChange, 100); // Small delay to ensure tab is ready
    };

    const handleTabUpdated = (_tabId: number, changeInfo: chrome.tabs.TabChangeInfo, tab: chrome.tabs.Tab) => {
      if (changeInfo.status === 'complete' && tab.url) {
        setTimeout(checkTabChange, 100);
      }
    };

    chrome.tabs.onActivated.addListener(handleTabActivated);
    chrome.tabs.onUpdated.addListener(handleTabUpdated);

    return () => {
      chrome.tabs.onActivated.removeListener(handleTabActivated);
      chrome.tabs.onUpdated.removeListener(handleTabUpdated);
    };
  }, [getCurrentTabUrl, loadStateForUrl, checkTabChange]);

  // Public methods
  const saveSummary = useCallback(async (summary: Summary) => {
    if (currentUrl) {
      await saveStateForUrl(currentUrl, { summary });
    }
  }, [currentUrl, saveStateForUrl]);

  const saveHighlights = useCallback(async (highlights: Highlight[]) => {
    if (currentUrl) {
      await saveStateForUrl(currentUrl, { highlights });
    }
  }, [currentUrl, saveStateForUrl]);

  const saveResearch = useCallback(async (research: Research) => {
    if (currentUrl) {
      await saveStateForUrl(currentUrl, { research });
    }
  }, [currentUrl, saveStateForUrl]);

  const clearCurrentTab = useCallback(async () => {
    if (currentUrl) {
      const clearedState = { ...DEFAULT_TAB_STATE, lastUpdated: Date.now() };
      await saveStateForUrl(currentUrl, clearedState);
      setCurrentState(clearedState);
    }
  }, [currentUrl, saveStateForUrl]);

  const getTabHistory = useCallback(async (): Promise<Array<{ url: string; title: string; lastUpdated: number }>> => {
    try {
      const allData = await chrome.storage.local.get(null);
      const tabStates = Object.entries(allData)
        .filter(([key]) => key.startsWith('tabState_'))
        .map(([key, value]) => {
          const url = key.replace('tabState_', '');
          const state = value as TabState;
          return {
            url,
            title: state.summary?.title || url,
            lastUpdated: state.lastUpdated
          };
        })
        .sort((a, b) => b.lastUpdated - a.lastUpdated)
        .slice(0, 20); // Limit to last 20 pages
      
      return tabStates;
    } catch (error) {
      console.error('Error getting tab history:', error);
      return [];
    }
  }, []);

  return {
    currentUrl,
    currentState,
    isLoading,
    saveSummary,
    saveHighlights,
    saveResearch,
    clearCurrentTab,
    getTabHistory
  };
};
