import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("indusvision_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear session and bounce to login (simple approach; upgrade to silent refresh later)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("indusvision_access_token");
      localStorage.removeItem("indusvision_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
