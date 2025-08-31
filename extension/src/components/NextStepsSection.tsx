import React, { useState } from 'react';
import { BookOpen, ArrowRight, ExternalLink, Target } from 'lucide-react';
import { NextStep } from '@shared/types';

interface NextStepsSectionProps {
  nextSteps: NextStep[];
  onGenerateSteps: (userGoal?: string) => void;
  isLoading: boolean;
}

const NextStepsSection: React.FC<NextStepsSectionProps> = ({
  nextSteps,
  onGenerateSteps,
  isLoading
}) => {
  const [userGoal, setUserGoal] = useState('');
  const [showGoalInput, setShowGoalInput] = useState(false);

  const handleGenerateSteps = () => {
    onGenerateSteps(userGoal.trim() || undefined);
    setShowGoalInput(false);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'read':
        return <BookOpen className="w-4 h-4" />;
      case 'action':
        return <Target className="w-4 h-4" />;
      case 'research':
        return <ExternalLink className="w-4 h-4" />;
      default:
        return <ArrowRight className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Goal Input Toggle */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowGoalInput(!showGoalInput)}
            className="text-sm text-synthra-600 hover:text-synthra-700 flex items-center space-x-1"
          >
            <Target className="w-4 h-4" />
            <span>Set Learning Goal</span>
          </button>
        </div>

        {showGoalInput && (
          <div className="animate-slide-up space-y-3">
            <textarea
              value={userGoal}
              onChange={(e) => setUserGoal(e.target.value)}
              placeholder="What would you like to learn or achieve? e.g., 'Understand React hooks', 'Prepare for job interview', 'Build a web app'"
              className="textarea-field h-20"
            />
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerateSteps}
        disabled={isLoading}
        className="w-full btn-primary flex items-center justify-center space-x-2"
      >
        <BookOpen className="w-4 h-4" />
        <span>Suggest Next Steps</span>
      </button>

      {/* Next Steps List */}
      {nextSteps.length > 0 ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">
              Recommended Next Steps ({nextSteps.length})
            </h3>
          </div>

          <div className="space-y-3">
            {nextSteps.map((step, index) => (
              <div key={index} className="card animate-slide-up">
                <div className="space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-2">
                      <div className="flex-shrink-0 mt-1 text-synthra-600">
                        {getTypeIcon(step.type)}
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">
                          {step.title}
                        </h4>
                        {step.description && (
                          <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                            {step.description}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {/* Priority Badge */}
                    {step.priority && (
                      <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(step.priority)}`}>
                        {step.priority}
                      </span>
                    )}
                  </div>

                  {/* Resources */}
                  {step.resources && step.resources.length > 0 && (
                    <div className="space-y-2">
                      <h5 className="text-xs font-medium text-gray-700">Resources</h5>
                      <div className="space-y-1">
                        {step.resources.map((resource, resourceIndex) => (
                          <a
                            key={resourceIndex}
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center space-x-2 text-sm text-synthra-600 hover:text-synthra-700 hover:underline"
                          >
                            <ExternalLink className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{resource.title}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Estimated Time */}
                  {step.estimatedTimeMinutes && (
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      <span>⏱️ Estimated time:</span>
                      <span>{step.estimatedTimeMinutes} minutes</span>
                    </div>
                  )}

                  {/* Tags */}
                  {step.tags && step.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {step.tags.map((tag, tagIndex) => (
                        <span
                          key={tagIndex}
                          className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="border-t pt-4">
            <div className="bg-synthra-50 p-3 rounded-lg">
              <h4 className="text-sm font-medium text-synthra-800 mb-1">
                Learning Path Summary
              </h4>
              <p className="text-sm text-synthra-600">
                Total steps: {nextSteps.length} • 
                Estimated time: {nextSteps.reduce((acc, step) => acc + (step.estimatedTimeMinutes || 0), 0)} minutes
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-gray-900 mb-2">Ready for Next Steps</h3>
          <p className="text-xs text-gray-500 mb-4">
            Get personalized learning recommendations based on the current page content
          </p>
        </div>
      )}
    </div>
  );
};

export default NextStepsSection;
