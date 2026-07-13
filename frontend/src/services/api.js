import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

const buildPalmFormData = (palmData) => {
  const formData = new FormData();
  Object.keys(palmData).forEach((key) => {
    if (key === 'images' && palmData[key]?.length) {
      palmData[key].forEach((image) => formData.append('images', image));
    } else if (palmData[key] !== undefined && palmData[key] !== null && palmData[key] !== '') {
      formData.append(key, palmData[key]);
    }
  });
  return formData;
};

export const fetchStatistics = async () => {
  const response = await api.get('/api/statistics');
  return response.data;
};

export const searchPalms = async (params) => {
  const response = await api.get('/api/search', { params });
  return response.data;
};

export const getPalmDetail = async (id) => {
  const response = await api.get(`/api/palms/${id}`);
  return response.data;
};

export const adminLogin = async (credentials) => {
  const response = await api.post('/api/admin/login', credentials);
  return response.data;
};

export const adminLogout = async () => {
  const response = await api.post('/api/admin/logout');
  return response.data;
};

export const requestPasswordReset = async (email) => {
  const response = await api.post('/api/admin/password-reset/request', { email });
  return response.data;
};

export const confirmPasswordReset = async (token, password) => {
  const response = await api.post('/api/admin/password-reset/confirm', { token, password });
  return response.data;
};

export const fetchAdminDashboard = async () => {
  const response = await api.get('/api/admin/dashboard');
  return response.data;
};

export const fetchAdminPalms = async (params = {}) => {
  const response = await api.get('/api/admin/palms', { params });
  return response.data;
};

export const adminAddPalm = async (palmData) => {
  const response = await api.post('/api/admin/palms', buildPalmFormData(palmData));
  return response.data;
};

export const adminUpdatePalm = async (id, data) => {
  const hasImages = data.images?.length > 0;
  if (hasImages) {
    const response = await api.post(`/api/admin/palms/${id}/update`, buildPalmFormData(data));
    return response.data;
  }
  const response = await api.put(`/api/admin/palms/${id}`, data);
  return response.data;
};

export const adminDeletePalm = async (id) => {
  const response = await api.delete(`/api/admin/palms/${id}`);
  return response.data;
};

export const fetchAdminReports = async (params = {}) => {
  const response = await api.get('/api/admin/reports', { params });
  return response.data;
};

export default api;
