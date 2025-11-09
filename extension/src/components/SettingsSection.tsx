import React from 'react';
import { Settings } from 'lucide-react';
import NotionIntegration from './NotionIntegration';
import GeminiIntegration from './GeminiIntegration';

const SettingsSection: React.FC = () => {

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-2">
        <Settings className="w-5 h-5 text-synthra-600" />
        <h2 className="text-lg font-semibold text-gray-900">Settings</h2>
      </div>

      {/* Gemini AI Integration */}
      <GeminiIntegration />

      {/* Notion Integration */}
      <NotionIntegration />

      {/* Version Info */}
      <div className="border-t pt-4">
        <div className="text-xs text-gray-500 space-y-1">
          <div>Synthra Extension v1.0.0</div>
          <div>Manifest Version 3</div>
        </div>
      </div>
    </div>
  );
};

export default SettingsSection;
