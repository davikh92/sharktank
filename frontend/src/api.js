import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

let authToken = localStorage.getItem('auth_token');

export const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

export const getAuthToken = () => authToken;

const apiClient = axios.create({
  baseURL: API,
});

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (email, password) => 
  apiClient.post('/auth/register', { email, password });

export const login = (email, password) => 
  apiClient.post('/auth/login', { email, password });

export const getMe = () => 
  apiClient.get('/auth/me');

// Sharks
export const getSharks = () => 
  apiClient.get('/sharks');

// Sessions
export const createSession = (sessionData) => 
  apiClient.post('/sessions', sessionData);

export const listSessions = () => 
  apiClient.get('/sessions');

export const getSession = (sessionId) => 
  apiClient.get(`/sessions/${sessionId}`);

export const startSession = (sessionId) => 
  apiClient.post(`/sessions/${sessionId}/start`);

export const respondToSession = (sessionId, content) => 
  apiClient.post(`/sessions/${sessionId}/respond`, { content });

export const getSessionMessages = (sessionId) => 
  apiClient.get(`/sessions/${sessionId}/messages`);

export const getSessionEvents = (sessionId) => 
  apiClient.get(`/sessions/${sessionId}/events`);

// Reports
export const generateReport = (sessionId) => 
  apiClient.post(`/sessions/${sessionId}/report`);

export const getReport = (sessionId) => 
  apiClient.get(`/sessions/${sessionId}/report`);

export default apiClient;