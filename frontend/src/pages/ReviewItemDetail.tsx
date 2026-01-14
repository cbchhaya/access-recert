/**
 * ReviewItemDetail Page - Single review item detail view
 * Author: Chiradeep Chhaya
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  User,
  Shield,
  Clock,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  MessageSquare
} from 'lucide-react';
import apiClient from '../api/client';
import { ScoreBar } from '../components/ScoreBar';

interface ReviewItemData {
  id: string;
  campaign_id: string;
  access_grant_id: string;
  employee: {
    id: string;
    employee_number: string;
    email: string;
    full_name: string;
    job_title: string;
    job_code: string;
    job_family: string;
    job_level: number;
    team_id: string | null;
    manager_id: string | null;
  };
  resource: {
    id: string;
    system_id: string;
    resource_type: string;
    name: string;
    description: string;
    sensitivity: string;
  };
  assurance_score: {
    overall_score: number;
    peer_typicality: number;
    sensitivity_ceiling: number;
    usage_factor: number;
    classification: string;
    auto_certify_eligible: boolean;
    peers_with_access: number;
    total_peers: number;
    peer_percentage: number;
    usage_pattern: string;
    days_since_last_use: number | null;
    explanations: string[];
  };
  status: string;
  clustering_consensus: number;
  needs_clustering_review: boolean;
  clustering_disagreement: string | null;
  system_recommendation: string | null;
  peer_group_size: number | null;
  human_review_reason: string | null;
  decision: {
    action: string;
    rationale: string;
    decision_by: string;
    decided_at: string;
  } | null;
  created_at: string;
  updated_at: string | null;
}

export function ReviewItemDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [showRationale, setShowRationale] = useState(false);
  const [rationale, setRationale] = useState('');
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  const { data: item, isLoading, error } = useQuery({
    queryKey: ['reviewItem', id],
    queryFn: () => apiClient.getReviewItem(id!).then(r => r.data as ReviewItemData),
    enabled: !!id,
  });

  const submitDecision = useMutation({
    mutationFn: (data: { action: string; rationale?: string }) =>
      apiClient.submitDecision(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewItem', id] });
      queryClient.invalidateQueries({ queryKey: ['reviewItems'] });
      queryClient.invalidateQueries({ queryKey: ['campaign'] });
      setShowRationale(false);
      setRationale('');
      setPendingAction(null);
    },
  });

  const handleAction = (action: string) => {
    if (action === 'Revoke') {
      setPendingAction(action);
      setShowRationale(true);
    } else {
      submitDecision.mutate({ action });
    }
  };

  const confirmAction = () => {
    if (pendingAction) {
      submitDecision.mutate({ action: pendingAction, rationale });
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-48 bg-gray-200 rounded" />
          <div className="h-32 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <Link
          to="/campaigns"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to campaigns
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700">Review item not found</p>
        </div>
      </div>
    );
  }

  const score = item.assurance_score;
  const sensitivityColors: Record<string, string> = {
    Critical: 'bg-red-100 text-red-800',
    Confidential: 'bg-orange-100 text-orange-800',
    Internal: 'bg-yellow-100 text-yellow-800',
    Public: 'bg-green-100 text-green-800',
  };

  const isDecided = item.status === 'Decided' || item.status === 'Auto-Approved';

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          to={`/campaigns/${item.campaign_id}`}
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to campaign
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Review Item</h1>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-gray-500">ID: {item.id}</p>
              <Link
                to={`/chat?explain=${item.id}`}
                className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors"
              >
                <MessageSquare className="h-4 w-4" />
                Ask AI to Explain
              </Link>
            </div>
          </div>
          <span className={`px-4 py-2 rounded-full text-sm font-medium ${
            item.status === 'Auto-Approved' ? 'bg-green-100 text-green-800' :
            item.status === 'Decided' ? 'bg-blue-100 text-blue-800' :
            item.status === 'Needs-Review' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {item.status}
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Employee Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Employee</h2>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-xl font-semibold text-gray-900">{item.employee.full_name}</p>
              <p className="text-gray-500">{item.employee.email}</p>
            </div>
            <div className="grid grid-cols-2 gap-4 pt-3 border-t border-gray-100">
              <div>
                <p className="text-sm text-gray-500">Job Title</p>
                <p className="font-medium text-gray-900">{item.employee.job_title}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Job Family</p>
                <p className="font-medium text-gray-900">{item.employee.job_family}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Job Code</p>
                <p className="font-medium text-gray-900">{item.employee.job_code}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Level</p>
                <p className="font-medium text-gray-900">{item.employee.job_level}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Resource Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Shield className="h-5 w-5 text-purple-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Resource</h2>
          </div>
          <div className="space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xl font-semibold text-gray-900">{item.resource.name}</p>
                <p className="text-gray-500">{item.resource.resource_type}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${sensitivityColors[item.resource.sensitivity] || 'bg-gray-100 text-gray-800'}`}>
                {item.resource.sensitivity}
              </span>
            </div>
            <p className="text-gray-600 pt-3 border-t border-gray-100">
              {item.resource.description || 'No description available'}
            </p>
          </div>
        </div>
      </div>

      {/* Assurance Score Card */}
      <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-amber-100 rounded-lg">
            <Info className="h-5 w-5 text-amber-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Assurance Score</h2>
        </div>

        {/* Score Display */}
        <div className="flex items-center gap-6 mb-6">
          <div className="text-center">
            <div className={`text-5xl font-bold ${
              score.overall_score >= 80 ? 'text-green-600' :
              score.overall_score >= 50 ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {score.overall_score.toFixed(0)}
            </div>
            <p className="text-sm text-gray-500 mt-1">Overall Score</p>
          </div>
          <div className="flex-1">
            <ScoreBar score={score.overall_score} showLabel={false} size="lg" />
            <div className="flex justify-between text-sm text-gray-500 mt-2">
              <span>Low Assurance</span>
              <span>High Assurance</span>
            </div>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <ScoreComponent
            label="Peer Typicality"
            value={score.peer_typicality}
            icon={<Users className="h-4 w-4" />}
          />
          <ScoreComponent
            label="Usage Factor"
            value={score.usage_factor}
            icon={<Clock className="h-4 w-4" />}
          />
          <ScoreComponent
            label="Sensitivity Ceiling"
            value={score.sensitivity_ceiling}
            icon={<Shield className="h-4 w-4" />}
          />
          <ScoreComponent
            label="Clustering Consensus"
            value={item.clustering_consensus}
            icon={<Users className="h-4 w-4" />}
          />
        </div>

        {/* Peer Context */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 bg-gray-50 rounded-lg mb-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{score.peers_with_access}</p>
            <p className="text-sm text-gray-500">Peers with Access</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{score.total_peers}</p>
            <p className="text-sm text-gray-500">Total Peers</p>
          </div>
          <div className="text-center">
            <p className={`text-2xl font-bold ${item.peer_group_size && item.peer_group_size < 5 ? 'text-amber-600' : 'text-gray-900'}`}>
              {item.peer_group_size ?? score.total_peers}
            </p>
            <p className="text-sm text-gray-500">Peer Group Size</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{score.peer_percentage.toFixed(0)}%</p>
            <p className="text-sm text-gray-500">Peer Percentage</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {score.days_since_last_use ?? 'N/A'}
            </p>
            <p className="text-sm text-gray-500">Days Since Use</p>
          </div>
        </div>

        {/* Usage Pattern */}
        <div className="flex items-center gap-4 mb-6">
          <span className="text-gray-600">Usage Pattern:</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            score.usage_pattern === 'active' ? 'bg-green-100 text-green-800' :
            score.usage_pattern === 'occasional' ? 'bg-yellow-100 text-yellow-800' :
            score.usage_pattern === 'stale' ? 'bg-orange-100 text-orange-800' :
            'bg-red-100 text-red-800'
          }`}>
            {score.usage_pattern}
          </span>
          {score.auto_certify_eligible && (
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              Auto-Certify Eligible
            </span>
          )}
        </div>

        {/* Explanations */}
        {score.explanations && score.explanations.length > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Score Explanations</h3>
            <ul className="space-y-1">
              {score.explanations.map((exp, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-gray-400">•</span>
                  {exp}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Human Review Required Warning */}
        {item.human_review_reason && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Human Review Required</p>
              <p className="text-sm text-amber-700 mt-1">{item.human_review_reason}</p>
              {item.system_recommendation && (
                <p className="text-sm text-amber-900 mt-2 font-medium">
                  System suggestion (if no flags): <span className={
                    item.system_recommendation === 'Certify' ? 'text-green-700' :
                    item.system_recommendation === 'Review Carefully' ? 'text-red-700' :
                    'text-blue-700'
                  }>{item.system_recommendation}</span>
                </p>
              )}
            </div>
          </div>
        )}

        {/* Clustering Warning (only show if no human_review_reason already covers it) */}
        {item.needs_clustering_review && !item.human_review_reason && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Clustering Disagreement Detected</p>
              <p className="text-sm text-amber-700 mt-1">
                {item.clustering_disagreement || 'Multiple clustering algorithms disagree on peer grouping for this employee.'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Decision Card */}
      <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Decision</h2>

        {item.decision ? (
          <div className="space-y-4">
            <div className={`p-4 rounded-lg ${
              item.decision.action === 'Certify' ? 'bg-green-50 border border-green-200' :
              item.decision.action === 'Revoke' ? 'bg-red-50 border border-red-200' :
              'bg-gray-50 border border-gray-200'
            }`}>
              <div className="flex items-center gap-3">
                {item.decision.action === 'Certify' ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-600" />
                )}
                <div>
                  <p className="font-semibold text-gray-900">{item.decision.action}</p>
                  <p className="text-sm text-gray-500">
                    by {item.decision.decision_by} on {new Date(item.decision.decided_at).toLocaleString()}
                  </p>
                </div>
              </div>
              {item.decision.rationale && (
                <p className="mt-3 text-gray-700 border-t border-gray-200 pt-3">
                  <span className="font-medium">Rationale:</span> {item.decision.rationale}
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {showRationale ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rationale for {pendingAction}
                  </label>
                  <textarea
                    value={rationale}
                    onChange={(e) => setRationale(e.target.value)}
                    placeholder="Enter your rationale..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 h-24"
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={confirmAction}
                    disabled={submitDecision.isPending || !rationale.trim()}
                    className={`flex-1 px-6 py-3 rounded-lg font-medium text-white disabled:opacity-50 ${
                      pendingAction === 'Revoke' ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {submitDecision.isPending ? 'Submitting...' : `Confirm ${pendingAction}`}
                  </button>
                  <button
                    onClick={() => {
                      setShowRationale(false);
                      setRationale('');
                      setPendingAction(null);
                    }}
                    className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex gap-3">
                <button
                  onClick={() => handleAction('Certify')}
                  disabled={submitDecision.isPending || isDecided}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
                >
                  <CheckCircle className="h-5 w-5" />
                  Certify
                </button>
                <button
                  onClick={() => handleAction('Revoke')}
                  disabled={submitDecision.isPending || isDecided}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50"
                >
                  <XCircle className="h-5 w-5" />
                  Revoke
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreComponent({
  label,
  value,
  icon
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
}) {
  const percentage = (value * 100).toFixed(0);
  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-2 text-gray-500 mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <div className="text-xl font-bold text-gray-900">{percentage}%</div>
    </div>
  );
}

export default ReviewItemDetail;
