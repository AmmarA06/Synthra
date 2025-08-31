import React from 'react';
import { Lightbulb, Trash2 } from 'lucide-react';
import { Highlight } from '@shared/types';

interface HighlightSectionProps {
  highlights: Highlight[];
  onHighlight: (text?: string) => void;
  onClearHighlights: () => void;
  isLoading: boolean;
}

const HighlightSection: React.FC<HighlightSectionProps> = ({
  highlights,
  onHighlight,
  onClearHighlights,
  isLoading
}) => {

  const clearHighlights = async () => {
    try {
      // Clear highlights from the page
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id!, {
          type: 'CLEAR_HIGHLIGHTS'
        });
      }
      // Clear highlights from application state
      onClearHighlights();
    } catch (error) {
      console.error('Failed to clear highlights:', error);
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Controls */}
      <div className="flex space-x-2">
        <button
          onClick={() => onHighlight()}
          disabled={isLoading}
          className="flex-1 btn-primary flex items-center justify-center space-x-2"
        >
          <Lightbulb className="w-4 h-4" />
          <span>Highlight Key Terms</span>
        </button>
        
        {highlights.length > 0 && (
          <button
            onClick={clearHighlights}
            className="btn-secondary flex items-center justify-center p-2 text-red-600 hover:text-red-700"
            title="Clear all highlights"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Highlights List */}
      {highlights.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">
              Key Terms ({highlights.length})
            </h3>
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {highlights.map((highlight, index) => (
              <div key={index} className="card animate-slide-up">
                <div className="space-y-2">
                  <div className="flex items-start justify-between">
                    <h4 className="text-sm font-medium text-gray-900">
                      {highlight.term}
                    </h4>
                    {highlight.importance && (
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        highlight.importance === 'high' 
                          ? 'bg-red-100 text-red-800'
                          : highlight.importance === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {highlight.importance}
                      </span>
                    )}
                  </div>
                  
                  {highlight.explanation && (
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {highlight.explanation}
                    </p>
                  )}
                  
                  {highlight.context && (
                    <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                      <span className="font-medium">Context:</span> "{highlight.context}"
                    </div>
                  )}
                  
                  {highlight.category && (
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">Category:</span>
                      <span className="px-2 py-1 bg-synthra-50 text-synthra-700 text-xs rounded">
                        {highlight.category}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <Lightbulb className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-gray-900 mb-2">No Highlights Yet</h3>
          <p className="text-xs text-gray-500 mb-4">
            Click "Highlight Key Terms" to automatically identify and explain important concepts on this page
          </p>
        </div>
      )}

      {/* Selection Highlight */}
      <div className="border-t pt-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Selected Text</h4>
        <p className="text-xs text-gray-500 mb-3">
          Select text on the page to get explanations for specific terms
        </p>
        <button
          onClick={() => {
            // Get selected text from content script
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
              if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id!, {
                  type: 'GET_SELECTED_TEXT'
                }, (response) => {
                  if (response?.success && response.data?.text) {
                    onHighlight(response.data.text);
                  }
                });
              }
            });
          }}
          disabled={isLoading}
          className="w-full btn-secondary flex items-center justify-center space-x-2"
        >
          <Lightbulb className="w-4 h-4" />
          <span>Explain Selection</span>
        </button>
      </div>
    </div>
  );
};

export default HighlightSection;
