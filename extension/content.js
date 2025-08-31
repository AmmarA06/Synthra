// Synthra Content Script

console.log('Synthra content script loaded');

// Highlight management
let activeHighlights = [];
let highlightIndex = 0;

// Initialize content script
function initialize() {
  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Content script received message:', message);
    
    switch (message.type) {
      case 'HIGHLIGHT_TERMS_ON_PAGE':
        highlightTermsOnPage(message.terms);
        sendResponse({ success: true });
        break;
        
      case 'CLEAR_HIGHLIGHTS':
        clearHighlights();
        sendResponse({ success: true });
        break;
        
      case 'GET_PAGE_CONTENT':
        const content = getPageContent();
        sendResponse({ success: true, data: content });
        break;
        
      case 'GET_SELECTED_TEXT':
        const selectedText = getSelectedText();
        sendResponse({ success: true, data: selectedText });
        break;
        
      case 'GET_PAGE_TITLE':
        const titleData = getPageTitle();
        sendResponse({ success: true, data: titleData });
        break;
        
      default:
        console.warn('Unknown message type in content script:', message.type);
    }
  });
  
  // Listen for text selection
  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('keyup', handleTextSelection);
}

// Get page content
function getPageContent() {
  return {
    title: document.title,
    url: window.location.href,
    content: document.body.innerText,
    html: document.documentElement.outerHTML,
    timestamp: Date.now()
  };
}

// Get just the page title for testing
function getPageTitle() {
  return {
    title: document.title,
    url: window.location.href,
    timestamp: Date.now()
  };
}

// Get currently selected text
function getSelectedText() {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  if (selectedText.length > 0) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    return {
      text: selectedText,
      position: {
        x: rect.left + window.scrollX,
        y: rect.top + window.scrollY,
        width: rect.width,
        height: rect.height
      },
      context: getTextContext(range, 100)
    };
  }
  
  return null;
}

// Get context around selected text
function getTextContext(range, contextLength) {
  const container = range.commonAncestorContainer;
  const fullText = container.textContent || '';
  const startOffset = range.startOffset;
  const endOffset = range.endOffset;
  
  const beforeStart = Math.max(0, startOffset - contextLength);
  const afterEnd = Math.min(fullText.length, endOffset + contextLength);
  
  return {
    before: fullText.substring(beforeStart, startOffset),
    selected: fullText.substring(startOffset, endOffset),
    after: fullText.substring(endOffset, afterEnd)
  };
}

// Handle text selection events
function handleTextSelection() {
  const selectedText = getSelectedText();
  
  if (selectedText && selectedText.text.length > 3) {
    // Notify background script about text selection
    chrome.runtime.sendMessage({
      type: 'TEXT_SELECTED',
      data: selectedText
    }).catch(error => {
      console.log('Background script not available:', error);
    });
  }
}

// Highlight terms on page
function highlightTermsOnPage(terms) {
  clearHighlights();
  
  terms.forEach(term => {
    const termData = typeof term === 'string' ? { text: term, explanation: '' } : term;
    highlightTerm(termData.text, termData.explanation);
  });
}

// Highlight a single term
function highlightTerm(termText, explanation = '') {
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        // Skip script and style elements
        const parent = node.parentElement;
        if (parent && (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE')) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );
  
  const textNodes = [];
  let node;
  while (node = walker.nextNode()) {
    textNodes.push(node);
  }
  
  textNodes.forEach(textNode => {
    const text = textNode.textContent;
    const regex = new RegExp(`\\b${escapeRegex(termText)}\\b`, 'gi');
    
    if (regex.test(text)) {
      const parent = textNode.parentNode;
      const wrapper = document.createElement('span');
      wrapper.innerHTML = text.replace(regex, (match) => {
        const highlightId = `synthra-highlight-${highlightIndex++}`;
        activeHighlights.push(highlightId);
        
        return `<mark class="synthra-highlight" id="${highlightId}" data-term="${escapeHtml(termText)}" data-explanation="${escapeHtml(explanation)}" title="${explanation}">${match}</mark>`;
      });
      
      parent.insertBefore(wrapper, textNode);
      parent.removeChild(textNode);
    }
  });
  
  // Add click listeners to highlights
  document.querySelectorAll('.synthra-highlight').forEach(highlight => {
    highlight.addEventListener('click', (e) => {
      e.preventDefault();
      showHighlightTooltip(e.target);
    });
  });
}

// Show tooltip for highlighted term
function showHighlightTooltip(element) {
  const term = element.getAttribute('data-term');
  const explanation = element.getAttribute('data-explanation');
  
  if (explanation) {
    // Remove existing tooltips
    document.querySelectorAll('.synthra-tooltip').forEach(tooltip => {
      tooltip.remove();
    });
    
    // Create new tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'synthra-tooltip';
    tooltip.innerHTML = `
      <div class="synthra-tooltip-content">
        <strong>${escapeHtml(term)}</strong>
        <p>${escapeHtml(explanation)}</p>
        <button class="synthra-tooltip-close">×</button>
      </div>
    `;
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.cssText = `
      position: fixed;
      top: ${rect.bottom + 5}px;
      left: ${rect.left}px;
      background: white;
      border: 1px solid #ccc;
      border-radius: 4px;
      padding: 10px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      z-index: 10000;
      max-width: 300px;
      font-size: 14px;
      line-height: 1.4;
    `;
    
    document.body.appendChild(tooltip);
    
    // Add close listener
    tooltip.querySelector('.synthra-tooltip-close').addEventListener('click', () => {
      tooltip.remove();
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (tooltip.parentNode) {
        tooltip.remove();
      }
    }, 5000);
  }
}

// Clear all highlights
function clearHighlights() {
  document.querySelectorAll('.synthra-highlight').forEach(highlight => {
    const parent = highlight.parentNode;
    parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
    parent.normalize();
  });
  
  // Remove tooltips
  document.querySelectorAll('.synthra-tooltip').forEach(tooltip => {
    tooltip.remove();
  });
  
  activeHighlights = [];
  highlightIndex = 0;
}

// Utility functions
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Add CSS for highlights and tooltips
function addStyles() {
  if (document.getElementById('synthra-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'synthra-styles';
  style.textContent = `
    .synthra-highlight {
      background-color: #fff3cd !important;
      border-bottom: 2px solid #ffc107 !important;
      cursor: pointer !important;
      transition: background-color 0.2s ease !important;
    }
    
    .synthra-highlight:hover {
      background-color: #fff3a0 !important;
    }
    
    .synthra-tooltip {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    .synthra-tooltip-content {
      position: relative;
    }
    
    .synthra-tooltip-close {
      position: absolute;
      top: -5px;
      right: -5px;
      background: #dc3545;
      color: white;
      border: none;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      cursor: pointer;
      font-size: 12px;
      line-height: 1;
    }
    
    .synthra-tooltip-close:hover {
      background: #c82333;
    }
  `;
  
  document.head.appendChild(style);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    addStyles();
    initialize();
  });
} else {
  addStyles();
  initialize();
}
