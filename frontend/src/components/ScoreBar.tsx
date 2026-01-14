/**
 * ScoreBar Component - Visual representation of assurance score
 * Author: Chiradeep Chhaya
 */

interface ScoreBarProps {
  score: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function ScoreBar({ score, showLabel = true, size = 'md' }: ScoreBarProps) {
  const getColor = () => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getHeight = () => {
    switch (size) {
      case 'sm': return 'h-1';
      case 'lg': return 'h-3';
      default: return 'h-2';
    }
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 bg-gray-200 rounded-full ${getHeight()}`}>
        <div
          className={`${getColor()} ${getHeight()} rounded-full transition-all`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-gray-700 min-w-[3rem] text-right">
          {score.toFixed(0)}
        </span>
      )}
    </div>
  );
}

export function ClassificationBadge({ classification }: { classification: string }) {
  const getStyle = () => {
    switch (classification) {
      case 'high_assurance':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'medium_assurance':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low_assurance':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getLabel = () => {
    switch (classification) {
      case 'high_assurance': return 'High';
      case 'medium_assurance': return 'Medium';
      case 'low_assurance': return 'Low';
      default: return classification;
    }
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${getStyle()}`}>
      {getLabel()}
    </span>
  );
}

export function SensitivityBadge({ sensitivity }: { sensitivity: string }) {
  const getStyle = () => {
    switch (sensitivity) {
      case 'Critical':
        return 'bg-purple-100 text-purple-800';
      case 'Confidential':
        return 'bg-red-100 text-red-800';
      case 'Internal':
        return 'bg-blue-100 text-blue-800';
      case 'Public':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded ${getStyle()}`}>
      {sensitivity}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const getStyle = () => {
    switch (status) {
      case 'Auto-Approved':
        return 'bg-green-100 text-green-800';
      case 'Decided':
        return 'bg-blue-100 text-blue-800';
      case 'Needs-Review':
        return 'bg-orange-100 text-orange-800';
      case 'Pending':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded ${getStyle()}`}>
      {status}
    </span>
  );
}
