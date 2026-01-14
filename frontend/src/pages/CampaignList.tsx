/**
 * CampaignList Page - List all campaigns
 * Author: Chiradeep Chhaya
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Play, Calendar, Clock, CheckCircle, AlertCircle, Archive, Pencil, MoreVertical, HelpCircle } from 'lucide-react';
import apiClient from '../api/client';
import type { Campaign } from '../api/client';

export function CampaignList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [renameModal, setRenameModal] = useState<{ id: string; name: string } | null>(null);

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns', showArchived],
    queryFn: () => apiClient.getCampaigns(showArchived).then(r => r.data),
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => apiClient.activateCampaign(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      navigate(`/campaigns/${id}`);
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => apiClient.archiveCampaign(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => apiClient.renameCampaign(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setRenameModal(null);
    },
  });

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="text-gray-500 mt-1">Manage access certification campaigns</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600"
            />
            Show archived
          </label>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Campaign
          </button>
        </div>
      </div>

      {/* Campaign List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-gray-200 animate-pulse rounded-lg" />
          ))}
        </div>
      ) : campaigns?.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-lg">
          <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No campaigns yet</h3>
          <p className="text-gray-500 mb-4">Create your first certification campaign</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Campaign
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {campaigns?.map(campaign => (
            <CampaignRow
              key={campaign.id}
              campaign={campaign}
              onActivate={() => {
                if (confirm('Activate this campaign? This will run analytics and generate review items.')) {
                  activateMutation.mutate(campaign.id);
                }
              }}
              onArchive={() => {
                if (confirm('Archive this campaign? It will be hidden from the default view.')) {
                  archiveMutation.mutate(campaign.id);
                }
              }}
              onRename={() => setRenameModal({ id: campaign.id, name: campaign.name })}
              activating={activateMutation.isPending && activateMutation.variables === campaign.id}
              archiving={archiveMutation.isPending && archiveMutation.variables === campaign.id}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateCampaignModal onClose={() => setShowCreateModal(false)} />
      )}

      {/* Rename Modal */}
      {renameModal && (
        <RenameCampaignModal
          name={renameModal.name}
          onClose={() => setRenameModal(null)}
          onSave={(newName) => renameMutation.mutate({ id: renameModal.id, name: newName })}
          saving={renameMutation.isPending}
        />
      )}
    </div>
  );
}

function CampaignRow({
  campaign,
  onActivate,
  onArchive,
  onRename,
  activating,
  archiving
}: {
  campaign: Campaign;
  onActivate: () => void;
  onArchive: () => void;
  onRename: () => void;
  activating: boolean;
  archiving: boolean;
}) {
  const [showMenu, setShowMenu] = useState(false);

  const getStatusIcon = () => {
    switch (campaign.status) {
      case 'Active': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'Draft': return <Clock className="h-5 w-5 text-gray-500" />;
      case 'Completed': return <CheckCircle className="h-5 w-5 text-blue-500" />;
      case 'Archived': return <Archive className="h-5 w-5 text-gray-400" />;
      default: return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const canArchive = campaign.status !== 'Archived';

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow ${campaign.status === 'Archived' ? 'opacity-60' : ''}`}>
      <div className="flex items-center justify-between">
        <Link to={`/campaigns/${campaign.id}`} className="flex-1">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <h3 className="font-medium text-gray-900">{campaign.name}</h3>
              <p className="text-sm text-gray-500">
                {campaign.scope_type} • Created {new Date(campaign.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </Link>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Due Date</p>
            <p className="font-medium text-gray-900">
              {new Date(campaign.due_date).toLocaleDateString()}
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            campaign.status === 'Active' ? 'bg-green-100 text-green-800' :
            campaign.status === 'Draft' ? 'bg-gray-100 text-gray-800' :
            campaign.status === 'Completed' ? 'bg-blue-100 text-blue-800' :
            campaign.status === 'Archived' ? 'bg-gray-100 text-gray-500' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {campaign.status}
          </span>
          {campaign.status === 'Draft' && (
            <button
              onClick={(e) => {
                e.preventDefault();
                onActivate();
              }}
              disabled={activating}
              className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {activating ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  Activating...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Activate
                </>
              )}
            </button>
          )}
          {/* Actions Menu */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.preventDefault();
                setShowMenu(!showMenu);
              }}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              <MoreVertical className="h-5 w-5 text-gray-500" />
            </button>
            {showMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    setShowMenu(false);
                    onRename();
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                >
                  <Pencil className="h-4 w-4" />
                  Rename
                </button>
                {canArchive && (
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      setShowMenu(false);
                      onArchive();
                    }}
                    disabled={archiving}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
                  >
                    <Archive className="h-4 w-4" />
                    {archiving ? 'Archiving...' : 'Archive'}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function CreateCampaignModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    scope_type: 'lob',
    lob: 'Technology',
    auto_approve_threshold: 80,
    review_threshold: 50,
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  });

  const createMutation = useMutation({
    mutationFn: () => apiClient.createCampaign({
      name: formData.name,
      scope_type: formData.scope_type,
      scope_filter: { lob: formData.lob },
      auto_approve_threshold: formData.auto_approve_threshold,
      review_threshold: formData.review_threshold,
      due_date: new Date(formData.due_date).toISOString(),
    }),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      navigate(`/campaigns/${response.data.id}`);
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Create New Campaign</h2>

        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Campaign Name
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Q1 2026 Access Review"
              />
            </div>

            <div>
              <FormLabel
                label="Scope Type"
                tooltip="Determines how access reviews are organized. LOB groups by business unit, Manager by reporting structure."
              />
              <select
                value={formData.scope_type}
                onChange={(e) => setFormData({ ...formData, scope_type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="lob">Line of Business</option>
                <option value="manager">Manager</option>
                <option value="resource_owner">Resource Owner</option>
                <option value="system">System</option>
              </select>
            </div>

            <div>
              <FormLabel
                label="Line of Business"
                tooltip="Select the business unit whose employee access will be reviewed in this campaign."
              />
              <select
                value={formData.lob}
                onChange={(e) => setFormData({ ...formData, lob: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="Technology">Technology</option>
                <option value="Retail Banking">Retail Banking</option>
                <option value="Commercial Banking">Commercial Banking</option>
                <option value="Wealth Management">Wealth Management</option>
                <option value="Investment Banking">Investment Banking</option>
                <option value="Operations & Risk">Operations & Risk</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <FormLabel
                  label="Auto-Approve Threshold"
                  tooltip="Access grants with assurance scores above this value will be automatically approved without manual review. Higher = fewer auto-approvals."
                />
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.auto_approve_threshold}
                  onChange={(e) => setFormData({ ...formData, auto_approve_threshold: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <FormLabel
                  label="Review Threshold"
                  tooltip="Access grants with scores below this value are flagged as 'Needs Review' for priority attention. Lower = fewer flagged items."
                />
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.review_threshold}
                  onChange={(e) => setFormData({ ...formData, review_threshold: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <FormLabel
                label="Due Date"
                tooltip="Deadline for completing all reviews in this campaign."
              />
              <input
                type="date"
                required
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function FormLabel({ label, tooltip }: { label: string; tooltip: string }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="flex items-center gap-1 mb-1">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <div className="relative">
        <button
          type="button"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          onClick={() => setShowTooltip(!showTooltip)}
          className="text-gray-400 hover:text-gray-600"
        >
          <HelpCircle className="h-4 w-4" />
        </button>
        {showTooltip && (
          <div className="absolute left-6 top-0 z-20 w-64 p-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
            {tooltip}
          </div>
        )}
      </div>
    </div>
  );
}

function RenameCampaignModal({
  name,
  onClose,
  onSave,
  saving
}: {
  name: string;
  onClose: () => void;
  onSave: (name: string) => void;
  saving: boolean;
}) {
  const [newName, setNewName] = useState(name);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Rename Campaign</h2>

        <form onSubmit={(e) => { e.preventDefault(); onSave(newName); }}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Campaign Name
            </label>
            <input
              type="text"
              required
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !newName.trim() || newName === name}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CampaignList;
