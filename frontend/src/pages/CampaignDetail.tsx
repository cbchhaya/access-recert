/**
 * CampaignDetail Page - Campaign overview and review items
 * Author: Chiradeep Chhaya
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Search,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import apiClient from '../api/client';
import { ReviewItemRow } from '../components/ReviewItemCard';
import { ScoreBar } from '../components/ScoreBar';

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  // State - initialize from URL params
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    classification: searchParams.get('classification') || '',
    search: searchParams.get('search') || '',
  });
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1'));
  const pageSize = 20;

  // Sync filters to URL
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.classification) params.set('classification', filters.classification);
    if (filters.search) params.set('search', filters.search);
    if (page > 1) params.set('page', page.toString());
    setSearchParams(params, { replace: true });
  }, [filters, page, setSearchParams]);

  // Queries
  const { data: campaignData, isLoading: campaignLoading } = useQuery({
    queryKey: ['campaign', id],
    queryFn: () => apiClient.getCampaign(id!).then(r => r.data),
    enabled: !!id,
  });

  const { data: reviewData, isLoading: reviewsLoading } = useQuery({
    queryKey: ['reviewItems', id, filters, page],
    queryFn: () => apiClient.getReviewItems(id!, {
      status: filters.status || undefined,
      classification: filters.classification || undefined,
      search: filters.search || undefined,
      page,
      page_size: pageSize,
    }).then(r => r.data),
    enabled: !!id,
  });

  // Mutations
  const bulkDecision = useMutation({
    mutationFn: (data: { action: string; rationale?: string }) =>
      apiClient.submitBulkDecisions(id!, {
        review_item_ids: Array.from(selectedItems),
        action: data.action,
        rationale: data.rationale,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign', id] });
      queryClient.invalidateQueries({ queryKey: ['reviewItems', id] });
      setSelectedItems(new Set());
    },
  });

  // Handlers
  const toggleSelect = (itemId: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const selectAll = () => {
    if (!reviewData?.items) return;
    const pendingItems = reviewData.items
      .filter(item => item.status !== 'Auto-Approved')
      .map(item => item.id);
    setSelectedItems(new Set(pendingItems));
  };

  const clearSelection = () => setSelectedItems(new Set());

  const handleBulkCertify = () => {
    if (selectedItems.size === 0) return;
    if (confirm(`Certify ${selectedItems.size} selected items?`)) {
      bulkDecision.mutate({ action: 'Certify', rationale: 'Bulk certification' });
    }
  };

  const handleBulkRevoke = () => {
    if (selectedItems.size === 0) return;
    const rationale = prompt('Enter revocation rationale:');
    if (rationale) {
      bulkDecision.mutate({ action: 'Revoke', rationale });
    }
  };

  if (campaignLoading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-32 bg-gray-200 rounded" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (!campaignData) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <p className="text-gray-500">Campaign not found</p>
      </div>
    );
  }

  const { campaign, total_items, pending_items, auto_approved_items, certified_items, revoked_items, completion_percentage, score_distribution } = campaignData;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/campaigns"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to campaigns
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
            <p className="text-gray-500 mt-1">
              {campaign.scope_type} • Due {new Date(campaign.due_date).toLocaleDateString()}
            </p>
          </div>
          <span className={`px-4 py-2 rounded-full text-sm font-medium ${
            campaign.status === 'Active' ? 'bg-green-100 text-green-800' :
            campaign.status === 'Draft' ? 'bg-gray-100 text-gray-800' :
            'bg-blue-100 text-blue-800'
          }`}>
            {campaign.status}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <StatBox label="Total Items" value={total_items} />
        <StatBox label="Auto-Approved" value={auto_approved_items} color="green" />
        <StatBox label="Pending" value={pending_items} color="yellow" />
        <StatBox label="Certified" value={certified_items} color="blue" />
        <StatBox label="Revoked" value={revoked_items} color="red" />
      </div>

      {/* Progress */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Completion Progress</h2>
          <span className="text-2xl font-bold text-blue-600">
            {completion_percentage.toFixed(1)}%
          </span>
        </div>
        <ScoreBar score={completion_percentage} showLabel={false} size="lg" />

        {/* Score Distribution */}
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {score_distribution?.high_assurance || 0}
            </div>
            <div className="text-sm text-gray-500">High Assurance</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {score_distribution?.medium_assurance || 0}
            </div>
            <div className="text-sm text-gray-500">Medium Assurance</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {score_distribution?.low_assurance || 0}
            </div>
            <div className="text-sm text-gray-500">Low Assurance</div>
          </div>
        </div>
      </div>

      {/* Filters & Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by employee or resource..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Needs-Review">Needs Review</option>
            <option value="Auto-Approved">Auto-Approved</option>
            <option value="Decided">Decided</option>
          </select>

          {/* Classification Filter */}
          <select
            value={filters.classification}
            onChange={(e) => setFilters({ ...filters, classification: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Classifications</option>
            <option value="high_assurance">High Assurance</option>
            <option value="medium_assurance">Medium Assurance</option>
            <option value="low_assurance">Low Assurance</option>
          </select>

          {/* Bulk Actions */}
          {selectedItems.size > 0 && (
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-sm text-gray-500">
                {selectedItems.size} selected
              </span>
              <button
                onClick={handleBulkCertify}
                disabled={bulkDecision.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Certify
              </button>
              <button
                onClick={handleBulkRevoke}
                disabled={bulkDecision.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Revoke
              </button>
              <button
                onClick={clearSelection}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Review Items Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  onChange={(e) => e.target.checked ? selectAll() : clearSelection()}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600"
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Employee</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Resource</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Score</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Classification</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {reviewsLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={6} className="px-4 py-6">
                    <div className="h-8 bg-gray-200 animate-pulse rounded" />
                  </td>
                </tr>
              ))
            ) : reviewData?.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-gray-500">
                  No review items found
                </td>
              </tr>
            ) : (
              reviewData?.items.map((item) => (
                <ReviewItemRow
                  key={item.id}
                  item={item}
                  selected={selectedItems.has(item.id)}
                  onSelect={toggleSelect}
                  onClick={(id) => window.location.href = `/review/${id}`}
                />
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {reviewData && reviewData.total_pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, reviewData.total)} of {reviewData.total} items
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="px-4 py-2 text-sm">
                Page {page} of {reviewData.total_pages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(reviewData.total_pages, p + 1))}
                disabled={page === reviewData.total_pages}
                className="p-2 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatBox({
  label,
  value,
  color = 'gray'
}: {
  label: string;
  value: number;
  color?: 'gray' | 'green' | 'yellow' | 'red' | 'blue';
}) {
  const colorClasses = {
    gray: 'bg-gray-50 text-gray-900',
    green: 'bg-green-50 text-green-900',
    yellow: 'bg-yellow-50 text-yellow-900',
    red: 'bg-red-50 text-red-900',
    blue: 'bg-blue-50 text-blue-900',
  };

  return (
    <div className={`rounded-lg p-4 ${colorClasses[color]}`}>
      <div className="text-2xl font-bold">{value.toLocaleString()}</div>
      <div className="text-sm opacity-75">{label}</div>
    </div>
  );
}

export default CampaignDetail;
