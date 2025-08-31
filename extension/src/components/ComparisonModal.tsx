import React from 'react';
import { X, ExternalLink } from 'lucide-react';
import { UrlResearchResponse } from '@shared/types';

interface ComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: UrlResearchResponse | null;
}

const ComparisonModal: React.FC<ComparisonModalProps> = ({ isOpen, onClose, data }) => {
  if (!isOpen || !data) return null;

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname + urlObj.pathname;
    } catch {
      return url;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Detailed Comparison Analysis</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          <div className="p-6 space-y-6">
            {/* Comparison Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Quick Summary</h3>
              <p className="text-gray-700">{data.comparison.summary}</p>
            </div>

            {/* Common Themes & Key Differences */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-green-900 mb-2">Common Themes</h3>
                <ul className="space-y-2">
                  {data.comparison.commonThemes.map((theme, index) => (
                    <li key={index} className="text-green-800 flex items-start space-x-2">
                      <span className="text-green-600 mt-1">•</span>
                      <span>{theme}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-blue-900 mb-2">Key Differences</h3>
                <ul className="space-y-2">
                  {data.comparison.keyDifferences.map((difference, index) => (
                    <li key={index} className="text-blue-800 flex items-start space-x-2">
                      <span className="text-blue-600 mt-1">→</span>
                      <span>{difference}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Full Comparison Table */}
            <div className="bg-white border rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b bg-gray-50">
                <h3 className="text-lg font-medium text-gray-900">Detailed Comparison Table</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Page
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Summary
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Key Points
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Pros
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cons
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.pages.filter(page => !page.error).map((page, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <a 
                              href={page.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-synthra-600 hover:text-synthra-700 font-medium flex items-center space-x-1"
                            >
                              <span className="truncate max-w-32">{formatUrl(page.url)}</span>
                              <ExternalLink className="w-4 h-4 flex-shrink-0" />
                            </a>
                          </div>
                          <p className="text-sm text-gray-500 mt-1">{page.title}</p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-gray-900">{page.summary}</p>
                        </td>
                        <td className="px-6 py-4">
                          <ul className="space-y-1">
                            {page.keyPoints.map((point, i) => (
                              <li key={i} className="text-sm text-gray-700">• {point}</li>
                            ))}
                          </ul>
                        </td>
                        <td className="px-6 py-4">
                          <ul className="space-y-1">
                            {page.pros.map((pro, i) => (
                              <li key={i} className="text-sm text-green-700">+ {pro}</li>
                            ))}
                          </ul>
                        </td>
                        <td className="px-6 py-4">
                          <ul className="space-y-1">
                            {page.cons.map((con, i) => (
                              <li key={i} className="text-sm text-red-700">- {con}</li>
                            ))}
                          </ul>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Individual Page Cards */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Individual Page Analysis</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {data.pages.map((page, index) => (
                  <PageCard key={index} page={page} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Individual Page Card Component
const PageCard: React.FC<{ page: any }> = ({ page }) => {
  if (page.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-red-500">⚠</span>
          <h4 className="text-sm font-medium text-red-700">{page.title}</h4>
        </div>
        <p className="text-sm text-red-600">{page.error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900">{page.title}</h4>
        <a 
          href={page.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-synthra-600 hover:text-synthra-700"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
      
      <p className="text-sm text-gray-600 mb-4">{page.summary}</p>
      
      <div className="grid grid-cols-1 gap-3">
        <div>
          <h5 className="text-xs font-medium text-gray-700 mb-1">Key Points</h5>
          <ul className="space-y-1">
            {page.keyPoints.map((point: string, index: number) => (
              <li key={index} className="text-xs text-gray-600">• {point}</li>
            ))}
          </ul>
        </div>
        
        <div>
          <h5 className="text-xs font-medium text-green-700 mb-1">Pros</h5>
          <ul className="space-y-1">
            {page.pros.map((pro: string, index: number) => (
              <li key={index} className="text-xs text-green-600">+ {pro}</li>
            ))}
          </ul>
        </div>
        
        <div>
          <h5 className="text-xs font-medium text-red-700 mb-1">Cons</h5>
          <ul className="space-y-1">
            {page.cons.map((con: string, index: number) => (
              <li key={index} className="text-xs text-red-600">- {con}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ComparisonModal;
