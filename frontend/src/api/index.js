import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

export const documentsApi = {
  getAll: () => api.get('/documents'),
  getById: (id) => api.get(`/documents/${id}`),
  getContent: (id) => api.get(`/documents/${id}/content`),
  upload: (files) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
  },
  delete: (id) => api.delete(`/documents/${id}`),
};

export const templatesApi = {
  getAll: () => api.get('/templates'),
  getById: (id) => api.get(`/templates/${id}`),
  create: (data) => api.post('/templates', data),
  update: (id, data) => api.put(`/templates/${id}`, data),
  delete: (id) => api.delete(`/templates/${id}`),
  addField: (templateId, data) => api.post(`/templates/${templateId}/fields`, data),
  updateField: (templateId, fieldId, data) => api.put(`/templates/${templateId}/fields/${fieldId}`, data),
  deleteField: (templateId, fieldId) => api.delete(`/templates/${templateId}/fields/${fieldId}`),
  reorderFields: (templateId, fieldIds) => api.post(`/templates/${templateId}/fields/reorder`, { field_ids: fieldIds }),
  exportTemplate: (templateId) => api.get(`/templates/${templateId}/export`),
  importTemplate: (data) => api.post('/templates/import', data),
};

export const projectsApi = {
  getAll: () => api.get('/projects'),
  getById: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  addDocuments: (projectId, documentIds) => api.post(`/projects/${projectId}/documents`, { document_ids: documentIds }),
  removeDocument: (projectId, documentId) => api.delete(`/projects/${projectId}/documents/${documentId}`),
  extract: (projectId) => api.post(`/projects/${projectId}/extract`),
  reExtract: (projectId) => api.post(`/projects/${projectId}/re-extract`),
  getValues: (projectId) => api.get(`/projects/${projectId}/values`),
  updateValue: (valueId, data) => api.put(`/projects/values/${valueId}`, data),
  approveValue: (valueId) => api.post(`/projects/values/${valueId}/approve`),
  rejectValue: (valueId) => api.post(`/projects/values/${valueId}/reject`),
  bulkApprove: (valueIds) => api.post('/projects/values/bulk/approve', { value_ids: valueIds }),
  bulkReject: (valueIds) => api.post('/projects/values/bulk/reject', { value_ids: valueIds }),
  exportCsv: (projectId) => api.get(`/projects/${projectId}/export/csv`, { responseType: 'blob' }),
  exportExcel: (projectId) => api.get(`/projects/${projectId}/export/excel`, { responseType: 'blob' }),
};

export const commentsApi = {
  getForValue: (valueId) => api.get(`/comments/values/${valueId}`),
  create: (valueId, content, author = 'user') => api.post(`/comments/values/${valueId}`, { content, author }),
  update: (commentId, content) => api.put(`/comments/${commentId}`, { content }),
  delete: (commentId) => api.delete(`/comments/${commentId}`),
};

export const auditApi = {
  getForProject: (projectId, limit = 100, offset = 0) => api.get(`/audit/projects/${projectId}`, { params: { limit, offset } }),
  getForValue: (valueId, limit = 50) => api.get(`/audit/values/${valueId}`, { params: { limit } }),
  getRecent: (limit = 50) => api.get('/audit/recent', { params: { limit } }),
};

export const settingsApi = {
  getProjectSettings: (projectId) => api.get(`/settings/projects/${projectId}`),
  updateProjectSettings: (projectId, data) => api.put(`/settings/projects/${projectId}`, data),
};

export const searchApi = {
  search: (query, options = {}) => api.get('/search', { 
    params: { 
      q: query, 
      ...options 
    } 
  }),
  getFieldTypes: () => api.get('/search/field-types'),
  getSuggestions: (query, limit = 10) => api.get('/search/suggestions', { 
    params: { q: query, limit } 
  }),
};

export const validationApi = {
  validateProject: (projectId) => api.post(`/validation/projects/${projectId}/validate`),
  getValidationSummary: (projectId) => api.get(`/validation/projects/${projectId}/summary`),
};

export default api;
