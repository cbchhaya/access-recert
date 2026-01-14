/**
 * API Client for ARAS Backend
 * Author: Chiradeep Chhaya
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Campaign {
  id: string;
  name: string;
  scope_type: string;
  scope_filter: Record<string, unknown>;
  auto_approve_threshold: number;
  review_threshold: number;
  start_date: string;
  due_date: string;
  status: string;
  created_by: string;
  created_at: string;
}

export interface CampaignSummary {
  campaign: Campaign;
  total_items: number;
  pending_items: number;
  auto_approved_items: number;
  manually_reviewed_items: number;
  certified_items: number;
  revoked_items: number;
  completion_percentage: number;
  revocation_rate: number;
  score_distribution: Record<string, number>;
}

export interface ReviewItemSummary {
  id: string;
  employee_id: string;
  employee_name: string;
  employee_title: string;
  resource_id: string;
  resource_name: string;
  resource_sensitivity: string;
  assurance_score: number;
  classification: string;
  auto_certify_eligible: boolean;
  usage_pattern: string;
  peer_percentage: number;
  status: string;
  explanations: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Weights {
  structural: number;
  functional: number;
  behavioral: number;
  temporal: number;
  last_updated: string | null;
  updated_by: string | null;
}

export interface SystemStatus {
  status: string;
  database: string;
  statistics: {
    employees: number;
    resources: number;
    access_grants: number;
    campaigns: number;
  };
  timestamp: string;
}

// API Functions
export const apiClient = {
  // Health & Status
  getHealth: () => api.get('/health'),
  getStatus: () => api.get<SystemStatus>('/status'),

  // Campaigns
  getCampaigns: (includeArchived?: boolean) =>
    api.get<Campaign[]>('/campaigns', { params: { include_archived: includeArchived } }),
  getCampaign: (id: string) => api.get<CampaignSummary>(`/campaigns/${id}`),
  createCampaign: (data: {
    name: string;
    scope_type: string;
    scope_filter: Record<string, unknown>;
    auto_approve_threshold: number;
    review_threshold: number;
    due_date: string;
  }) => api.post<Campaign>('/campaigns', data),
  activateCampaign: (id: string) => api.post<CampaignSummary>(`/campaigns/${id}/activate`),
  archiveCampaign: (id: string) => api.post<Campaign>(`/campaigns/${id}/archive`),
  renameCampaign: (id: string, name: string) => api.patch<Campaign>(`/campaigns/${id}`, { name }),
  getCampaignProgress: (id: string) => api.get(`/campaigns/${id}/progress`),

  // Review Items
  getReviewItems: (
    campaignId: string,
    params: {
      status?: string;
      classification?: string;
      needs_review?: boolean;
      search?: string;
      sort_by?: string;
      sort_order?: string;
      page?: number;
      page_size?: number;
    }
  ) => api.get<PaginatedResponse<ReviewItemSummary>>(`/campaigns/${campaignId}/review-items`, { params }),

  getReviewItem: (id: string) => api.get(`/review-items/${id}`),

  submitDecision: (itemId: string, decision: {
    action: string;
    rationale?: string;
    modification_details?: string;
    delegated_to?: string;
  }) => api.post(`/review-items/${itemId}/decision`, decision),

  submitBulkDecisions: (campaignId: string, data: {
    review_item_ids: string[];
    action: string;
    rationale?: string;
  }) => api.post(`/campaigns/${campaignId}/bulk-decisions`, data),

  // Weights
  getWeights: () => api.get<Weights>('/weights'),
  updateWeights: (weights: {
    structural: number;
    functional: number;
    behavioral: number;
    temporal: number;
  }) => api.put<Weights>('/weights', weights),
  previewWeights: (weights: {
    structural: number;
    functional: number;
    behavioral: number;
    temporal: number;
  }) => api.post('/weights/preview', weights),

  // Analytics
  runAnalytics: (lob?: string) => api.post('/analytics/run', null, { params: { lob } }),

  // Employees
  getEmployee: (id: string) => api.get(`/employees/${id}`),
  getEmployeeAccessSummary: (id: string) => api.get(`/employees/${id}/access-summary`),

  // Audit
  getAuditRecords: (params?: {
    campaign_id?: string;
    action?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) => api.get('/audit', { params }),

  // Compliance
  createComplianceSample: (campaignId: string, sampleSize?: number) =>
    api.post(`/campaigns/${campaignId}/compliance-sample`, null, { params: { sample_size: sampleSize } }),

  // Graduation
  getGraduationStatus: () => api.get('/graduation-status'),
};

export default apiClient;
