// Synthra Background Service Worker (Manifest V3)

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Install and startup
chrome.runtime.onInstalled.addListener(() => {
  console.log('Synthra extension installed');
  
  // Initialize storage with default settings
  chrome.storage.sync.set({
    apiBaseUrl: API_BASE_URL,
    autoSummarize: true,
    notionEnabled: false,
    highlightEnabled: true
  });
});

// Handle extension icon click - open side panel
chrome.action.onClicked.addListener(async (tab) => {
  try {
    await chrome.sidePanel.open({ tabId: tab.id });
  } catch (error) {
    console.error('Failed to open side panel:', error);
  }
});

// Message handling from content script and sidebar
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message);
  
  switch (message.type) {
    case 'GET_TAB_CONTENT':
      handleGetTabContent(message, sender, sendResponse);
      return true; // Keep message channel open for async response
      
    case 'SUMMARIZE_CONTENT':
      handleSummarizeContent(message, sendResponse);
      return true;
      
    case 'HIGHLIGHT_TERMS':
      handleHighlightTerms(message, sendResponse);
      return true;
      
    case 'MULTI_TAB_RESEARCH':
      handleMultiTabResearch(message, sendResponse);
      return true;
      
    case 'SUGGEST_NEXT_STEPS':
      handleSuggestNextSteps(message, sendResponse);
      return true;
      
    case 'SAVE_TO_NOTION':
      handleSaveToNotion(message, sendResponse);
      return true;
      
    case 'TEST_ECHO':
      handleTestEcho(message, sendResponse);
      return true;
      
    default:
      console.warn('Unknown message type:', message.type);
  }
});

// Get current tab content
async function handleGetTabContent(message, sender, sendResponse) {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Inject content script if not already injected
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: () => {
        return {
          title: document.title,
          url: window.location.href,
          content: document.body.innerText,
          html: document.documentElement.outerHTML
        };
      }
    });
    
    sendResponse({ success: true, data: results[0].result });
  } catch (error) {
    console.error('Error getting tab content:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// API call helper
async function makeAPICall(endpoint, data) {
  try {
    const settings = await chrome.storage.sync.get(['apiBaseUrl']);
    const baseUrl = settings.apiBaseUrl || API_BASE_URL;
    
    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`API call failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
}

// Handle summarize content
async function handleSummarizeContent(message, sendResponse) {
  try {
    const result = await makeAPICall('/summarize', {
      content: message.content,
      url: message.url,
      title: message.title
    });
    
    sendResponse({ success: true, data: result });
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
}

// Handle highlight terms
async function handleHighlightTerms(message, sendResponse) {
  try {
    const result = await makeAPICall('/highlight', {
      content: message.content,
      url: message.url,
      context: message.context
    });
    
    sendResponse({ success: true, data: result });
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
}

// Handle multi-tab research
async function handleMultiTabResearch(message, sendResponse) {
  try {
    // Get content from all specified tabs
    const tabs = await chrome.tabs.query({});
    const tabContents = [];
    
    for (const tabId of message.tabIds) {
      const tab = tabs.find(t => t.id === tabId);
      if (tab) {
        const results = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          function: () => ({
            title: document.title,
            url: window.location.href,
            content: document.body.innerText
          })
        });
        tabContents.push(results[0].result);
      }
    }
    
    const result = await makeAPICall('/multi-tab-research', {
      tabs: tabContents,
      query: message.query
    });
    
    sendResponse({ success: true, data: result });
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
}

// Handle suggest next steps
async function handleSuggestNextSteps(message, sendResponse) {
  try {
    const result = await makeAPICall('/suggest-next-steps', {
      content: message.content,
      summary: message.summary,
      userGoal: message.userGoal
    });
    
    sendResponse({ success: true, data: result });
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
}

// Handle save to Notion
async function handleSaveToNotion(message, sendResponse) {
  try {
    const result = await makeAPICall('/notion/save', {
      content: message.content,
      type: message.contentType,
      title: message.title,
      url: message.url
    });
    
    sendResponse({ success: true, data: result });
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
}

// Handle test echo - get title from current tab and send to backend
async function handleTestEcho(message, sendResponse) {
  try {
    // Get the current active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Get title from content script
    const titleResponse = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: () => {
        return {
          title: document.title,
          url: window.location.href
        };
      }
    });
    
    const titleData = titleResponse[0].result;
    
    // Send to backend echo endpoint
    const result = await makeAPICall('/echo', {
      title: titleData.title,
      url: titleData.url,
      source: 'extension-test'
    });
    
    sendResponse({ success: true, data: result });
  } catch (error) {
    console.error('Echo test error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Tab change detection for auto-summarize
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const settings = await chrome.storage.sync.get(['autoSummarize']);
  if (settings.autoSummarize) {
    // Notify sidebar about tab change
    chrome.runtime.sendMessage({
      type: 'TAB_CHANGED',
      tabId: activeInfo.tabId
    }).catch(() => {
      // Sidebar might not be open, ignore error
    });
  }
});

// Listen for tab updates (URL changes)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    const settings = await chrome.storage.sync.get(['autoSummarize']);
    if (settings.autoSummarize) {
      chrome.runtime.sendMessage({
        type: 'TAB_UPDATED',
        tabId: tabId,
        url: tab.url
      }).catch(() => {
        // Sidebar might not be open, ignore error
      });
    }
  }
});
