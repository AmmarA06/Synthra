import React from 'react';
import { api, ApiError } from '../services/api';

const ApiDemo: React.FC = () => {
  const demoSummarize = async () => {
    try {
      const summary = await api.summarize(
        "This is a sample text about React. React is a JavaScript library for building user interfaces. It was developed by Facebook and is now widely used for web development.",
        "React Tutorial",
        "https://example.com/react-tutorial"
      );
      console.log('Summary result:', summary);
      alert(`✅ Summarize successful!\nSummary: ${summary.summary}\nKey Points: ${summary.keyPoints.length}`);
    } catch (error) {
      console.error('Summarize error:', error);
      alert(`❌ Summarize failed: ${error instanceof ApiError ? error.message : String(error)}`);
    }
  };

  const demoHighlight = async () => {
    try {
      const highlights = await api.highlight(
        "React is a JavaScript library for building user interfaces. Components are the building blocks of React applications.",
        "technical explanation"
      );
      console.log('Highlight result:', highlights);
      alert(`✅ Highlight successful!\nFound ${highlights.length} key terms`);
    } catch (error) {
      console.error('Highlight error:', error);
      alert(`❌ Highlight failed: ${error instanceof ApiError ? error.message : String(error)}`);
    }
  };

  const demoResearch = async () => {
    try {
      const tabs = [
        {
          title: "React Documentation",
          url: "https://reactjs.org",
          content: "React is a JavaScript library for building user interfaces",
          timestamp: Date.now()
        },
        {
          title: "Vue.js Guide",
          url: "https://vuejs.org",
          content: "Vue.js is a progressive framework for building user interfaces",
          timestamp: Date.now()
        }
      ];

      const research = await api.research("Compare React and Vue.js", tabs);
      console.log('Research result:', research);
      alert(`✅ Research successful!\nSummary: ${research.summary}\nFindings: ${research.keyFindings.length}`);
    } catch (error) {
      console.error('Research error:', error);
      alert(`❌ Research failed: ${error instanceof ApiError ? error.message : String(error)}`);
    }
  };

  const demoNotionSave = async () => {
    try {
      // Check if Notion is connected first
      const notionAuth = await chrome.storage.sync.get(['notionAuth', 'selectedDatabaseId']);
      if (!notionAuth.notionAuth?.isAuthenticated) {
        alert('❌ Notion not connected. Please connect to Notion first in the Settings tab.');
        return;
      }
      
      if (!notionAuth.selectedDatabaseId) {
        alert('❌ No database selected. Please select a database in the Settings tab.');
        return;
      }

      const result = await api.notionSave(
        { 
          summary: "This is a test summary from Synthra",
          keyPoints: ["Test point 1", "Test point 2"],
          keyConcepts: ["Testing", "Notion Integration"]
        },
        "summary",
        "Synthra Test Summary",
        "https://example.com/test"
      );
      console.log('Notion save result:', result);
      alert(`✅ Notion Save successful!\nPage ID: ${result.pageId || 'N/A'}\nYou can view it in your Notion database.`);
    } catch (error) {
      console.error('Notion save error:', error);
      const errorMessage = error instanceof ApiError ? error.message : String(error);
      alert(`❌ Notion Save failed: ${errorMessage}\n\nMake sure:\n1. Notion is connected\n2. A database is selected\n3. The database is shared with your integration`);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-lg font-semibold">API Demo</h3>
      <div className="grid grid-cols-1 gap-2">
        <button onClick={demoSummarize} className="btn-primary">
          Test Summarize
        </button>
        <button onClick={demoHighlight} className="btn-primary">
          Test Highlight
        </button>
        <button onClick={demoResearch} className="btn-primary">
          Test Research
        </button>
        <button onClick={demoNotionSave} className="btn-primary">
          Test Notion Save
        </button>
      </div>
    </div>
  );
};

export default ApiDemo;
