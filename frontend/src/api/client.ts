import axios, { AxiosError, AxiosResponse } from 'axios';

const getDefaultApiUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    const host = window.location.hostname;
    if (host.includes('.onrender.com')) {
      const prefix = host.split('.onrender.com')[0];
      const backendPrefix = prefix.replace('sentinel-frontend', 'sentinel-backend');
      return `https://${backendPrefix}.onrender.com/api/v1`;
    }
    return 'https://sentinel-backend.onrender.com/api/v1';
  }
  return 'http://127.0.0.1:8000/api/v1';
};

// Create an Axios instance with base configuration
const apiClient = axios.create({
  baseURL: getDefaultApiUrl(),
  timeout: 60000, // 60 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (e.g., for adding auth tokens in the future)
apiClient.interceptors.request.use(
  (config) => {
    // You can add headers here, e.g.:
    // const token = localStorage.getItem('token');
    // if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for global error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data;
  },
  (error: AxiosError) => {
    // Handle specific error cases globally
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('API Error Response:', error.response.data);
      if (error.response.status === 401) {
        // e.g., redirect to login or clear auth state
        console.warn('Unauthorized access - perhaps redirect to login?');
      }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('API Error No Response:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API Error Setup:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
