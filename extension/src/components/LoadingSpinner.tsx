import React from 'react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center space-x-2">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-synthra-600"></div>
      <span className="text-gray-600 text-sm">Processing...</span>
    </div>
  );
};

export default LoadingSpinner;
