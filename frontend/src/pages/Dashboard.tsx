/**
 * Dashboard Page - Main overview page
 * Author: Chiradeep Chhaya
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Users,
  FileText,
  Shield,
  Activity,
  Clock,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';
import apiClient from '../api/client';
import type { Campaign } from '../api/client';

export function Dashboard() {
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['status'],
    queryFn: () => apiClient.getStatus().then(r => r.data),
  });

  const { data: campaigns, isLoading: campaignsLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: () => apiClient.getCampaigns().then(r => r.data),
  });

  const activeCampaigns = campaigns?.filter(c => c.status === 'Active') || [];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">ARAS Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Access Recertification Assurance System
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Employees"
          value={status?.statistics.employees.toLocaleString() ?? '-'}
          icon={Users}
          loading={statusLoading}
        />
        <StatCard
          title="Access Grants"
          value={status?.statistics.access_grants.toLocaleString() ?? '-'}
          icon={Shield}
          loading={statusLoading}
        />
        <StatCard
          title="Resources"
          value={status?.statistics.resources.toLocaleString() ?? '-'}
          icon={FileText}
          loading={statusLoading}
        />
        <StatCard
          title="Campaigns"
          value={status?.statistics.campaigns.toLocaleString() ?? '-'}
          icon={Activity}
          loading={statusLoading}
        />
      </div>

      {/* Active Campaigns */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Active Campaigns</h2>
          <Link
            to="/campaigns"
            className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
          >
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {campaignsLoading ? (
          <div className="animate-pulse space-y-4">
            {[1, 2].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg" />
            ))}
          </div>
        ) : activeCampaigns.length > 0 ? (
          <div className="space-y-4">
            {activeCampaigns.slice(0, 3).map(campaign => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No active campaigns
            </h3>
            <p className="text-gray-500 mb-4">
              Create a new campaign to start access reviews
            </p>
            <Link
              to="/campaigns/new"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              Create Campaign
            </Link>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ActionCard
            title="View Pending Reviews"
            description="Items needing your attention"
            icon={Clock}
            to="/reviews?status=Pending"
          />
          <ActionCard
            title="High Priority Items"
            description="Low assurance items requiring review"
            icon={AlertTriangle}
            to="/reviews?classification=low_assurance"
          />
          <ActionCard
            title="Analytics Settings"
            description="Configure proximity weights"
            icon={Activity}
            to="/settings/weights"
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  loading
}: {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  loading: boolean;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center">
        <div className="p-2 bg-blue-50 rounded-lg">
          <Icon className="h-6 w-6 text-blue-600" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          {loading ? (
            <div className="h-8 w-20 bg-gray-200 animate-pulse rounded mt-1" />
          ) : (
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function CampaignCard({ campaign }: { campaign: Campaign }) {
  return (
    <Link
      to={`/campaigns/${campaign.id}`}
      className="block bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">{campaign.name}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {campaign.scope_type} • Due {new Date(campaign.due_date).toLocaleDateString()}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          campaign.status === 'Active' ? 'bg-green-100 text-green-800' :
          campaign.status === 'Draft' ? 'bg-gray-100 text-gray-800' :
          'bg-blue-100 text-blue-800'
        }`}>
          {campaign.status}
        </span>
      </div>
    </Link>
  );
}

function ActionCard({
  title,
  description,
  icon: Icon,
  to
}: {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  to: string;
}) {
  return (
    <Link
      to={to}
      className="block bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
    >
      <Icon className="h-8 w-8 text-blue-600 mb-3" />
      <h3 className="font-medium text-gray-900">{title}</h3>
      <p className="text-sm text-gray-500 mt-1">{description}</p>
    </Link>
  );
}

export default Dashboard;
