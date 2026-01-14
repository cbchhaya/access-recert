/**
 * ReviewItemCard Component - Card display for review items
 * Author: Chiradeep Chhaya
 */

import { CheckCircle, ChevronRight } from 'lucide-react';
import type { ReviewItemSummary } from '../api/client';
import { ScoreBar, ClassificationBadge, SensitivityBadge, StatusBadge } from './ScoreBar';

interface ReviewItemCardProps {
  item: ReviewItemSummary;
  selected?: boolean;
  onSelect?: (id: string) => void;
  onClick?: (id: string) => void;
}

export function ReviewItemCard({ item, selected, onSelect, onClick }: ReviewItemCardProps) {
  return (
    <div
      className={`p-4 border rounded-lg transition-all cursor-pointer hover:shadow-md ${
        selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'
      }`}
      onClick={() => onClick?.(item.id)}
    >
      <div className="flex items-start gap-4">
        {onSelect && (
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => {
              e.stopPropagation();
              onSelect(item.id);
            }}
            className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600"
          />
        )}

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900 truncate">
                {item.employee_name}
              </span>
              {item.auto_certify_eligible && (
                <span className="text-xs text-green-600 flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Auto-eligible
                </span>
              )}
            </div>
            <StatusBadge status={item.status} />
          </div>

          {/* Employee info */}
          <p className="text-sm text-gray-500 mb-2">{item.employee_title}</p>

          {/* Resource */}
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm text-gray-700">{item.resource_name}</span>
            <SensitivityBadge sensitivity={item.resource_sensitivity} />
          </div>

          {/* Score */}
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <ScoreBar score={item.assurance_score} />
            </div>
            <ClassificationBadge classification={item.classification} />
          </div>

          {/* Explanations */}
          {item.explanations && item.explanations.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {item.explanations.slice(0, 2).map((exp, i) => (
                <span
                  key={i}
                  className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded"
                >
                  {exp}
                </span>
              ))}
              {item.explanations.length > 2 && (
                <span className="text-xs text-gray-400">
                  +{item.explanations.length - 2} more
                </span>
              )}
            </div>
          )}
        </div>

        <ChevronRight className="h-5 w-5 text-gray-400" />
      </div>
    </div>
  );
}

export function ReviewItemRow({ item, selected, onSelect, onClick }: ReviewItemCardProps) {
  return (
    <tr
      className={`cursor-pointer hover:bg-gray-50 ${selected ? 'bg-blue-50' : ''}`}
      onClick={() => onClick?.(item.id)}
    >
      {onSelect && (
        <td className="px-4 py-3">
          <input
            type="checkbox"
            checked={selected}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => {
              e.stopPropagation();
              onSelect(item.id);
            }}
            className="h-4 w-4 rounded border-gray-300 text-blue-600"
          />
        </td>
      )}
      <td className="px-4 py-3">
        <div className="font-medium text-gray-900">{item.employee_name}</div>
        <div className="text-sm text-gray-500">{item.employee_title}</div>
      </td>
      <td className="px-4 py-3">
        <div className="text-gray-900">{item.resource_name}</div>
        <SensitivityBadge sensitivity={item.resource_sensitivity} />
      </td>
      <td className="px-4 py-3 w-40">
        <ScoreBar score={item.assurance_score} size="sm" />
      </td>
      <td className="px-4 py-3">
        <ClassificationBadge classification={item.classification} />
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={item.status} />
      </td>
    </tr>
  );
}
