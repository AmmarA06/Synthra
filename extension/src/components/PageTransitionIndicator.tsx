import React from 'react';
import { Loader2 } from 'lucide-react';

interface PageTransitionIndicatorProps {
  isLoading: boolean;
  currentUrl: string | null;
}

const PageTransitionIndicator: React.FC<PageTransitionIndicatorProps> = ({ isLoading, currentUrl }) => {
  if (!isLoading || !currentUrl) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 shadow-lg flex items-center space-x-3">
        <Loader2 className="w-5 h-5 text-synthra-600 animate-spin" />
        <div>
          <p className="text-sm font-medium text-gray-900">Switching to new page...</p>
          <p className="text-xs text-gray-500 mt-1">Loading your saved summaries and highlights</p>
        </div>
      </div>
    </div>
  );
};

export default PageTransitionIndicator;
