import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getDashboardStats = async () => {
  const response = await apiClient.get('/analytics/dashboard');
  return response.data;
};

export const getIssues = async () => {
  const response = await apiClient.get('/issues/');
  return response.data;
};

export const acknowledgeIssue = async (issueId: string) => {
  const response = await apiClient.post(`/issues/${issueId}/acknowledge`);
  return response.data;
};

export const markInProgress = async (issueId: string) => {
  const response = await apiClient.post(`/issues/${issueId}/in_progress`);
  return response.data;
};

export const resolveIssue = async (issueId: string, status: string, resolution?: string, user_typing?: string) => {
  const response = await apiClient.post(`/issues/${issueId}/resolve`, {
    status,
    resolution,
    user_typing,
  });
  return response.data;
};

export const getBaselines = async () => {
  const response = await apiClient.get('/analytics/baselines');
  return response.data;
};

export const getFeedbackLogs = async () => {
  const response = await apiClient.get('/feedback/');
  return response.data;
};

export const ingestTransactions = async (transactions: any[]) => {
  const response = await apiClient.post('/transactions/bulk', transactions);
  return response.data;
};

