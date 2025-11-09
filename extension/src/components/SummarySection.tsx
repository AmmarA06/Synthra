import React from 'react';
import { Brain, ExternalLink } from 'lucide-react';
import { TabContent, Summary } from '@shared/types';

interface SummarySectionProps {
  currentTab: TabContent | null;
  summary: Summary | null;
  onSummarize: () => void;
  isLoading: boolean;
}

const SummarySection: React.FC<SummarySectionProps> = ({
  currentTab,
  summary,
  onSummarize,
  isLoading
}) => {

  return (
    <div className="p-4 space-y-4">

      {/* Generate Summary Button */}
      <button
        onClick={onSummarize}
        disabled={!currentTab || isLoading}
        className="w-full btn-primary flex items-center justify-center space-x-2"
      >
        <Brain className="w-4 h-4" />
        <span>{summary ? 'Re-summarize' : 'Summarize Page'}</span>
      </button>

      {/* Summary Display */}
      {summary && (
        <div className="card animate-fade-in">
          <div className="flex items-center space-x-2 mb-3">
            <Brain className="w-4 h-4 text-synthra-600" />
            <h3 className="text-sm font-medium text-gray-900">Summary</h3>
          </div>

          {/* Key Points */}
          {summary.keyPoints && summary.keyPoints.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-gray-700 mb-2">Key Points</h4>
              <ul className="space-y-1">
                {summary.keyPoints.map((point, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                    <span className="text-synthra-500 mt-1">•</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Main Summary */}
          {summary.summary && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-gray-700 mb-2">Summary</h4>
              <p className="text-sm text-gray-600 leading-relaxed">{summary.summary}</p>
            </div>
          )}

          {/* Key Concepts */}
          {summary.keyConcepts && summary.keyConcepts.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-gray-700 mb-2">Key Concepts</h4>
              <div className="flex flex-wrap gap-2">
                {summary.keyConcepts.map((concept, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-synthra-50 text-synthra-700 text-xs rounded-full"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Reading Time */}
          {summary.readingTimeMinutes && (
            <div className="text-xs text-gray-500 border-t pt-3">
              Estimated reading time: {summary.readingTimeMinutes} minute{summary.readingTimeMinutes !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!summary && !isLoading && currentTab && (
        <div className="text-center py-8">
          <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-gray-900 mb-2">Ready to Summarize</h3>
          <p className="text-xs text-gray-500 mb-4">
            Click the button above to generate an AI summary of this page
          </p>
        </div>
      )}

      {/* No Tab State */}
      {!currentTab && !isLoading && (
        <div className="text-center py-8">
          <ExternalLink className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-gray-900 mb-2">No Page Loaded</h3>
          <p className="text-xs text-gray-500">
            Navigate to a webpage to get started with summarization
          </p>
        </div>
      )}
    </div>
  );
};

export default SummarySection;
