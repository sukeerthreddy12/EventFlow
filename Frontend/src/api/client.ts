import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const access = localStorage.getItem("access");
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return null;

  try {
    const { data } = await axios.post(`${API_BASE}/accounts/token/refresh/`, {
      refresh,
    });
    localStorage.setItem("access", data.access);
    if (data.refresh) {
      localStorage.setItem("refresh", data.refresh);
    }
    return data.access as string;
  } catch {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    original._retry = true;
    refreshing ??= refreshAccessToken().finally(() => {
      refreshing = null;
    });

    const access = await refreshing;
    if (!access) {
      return Promise.reject(error);
    }

    original.headers.Authorization = `Bearer ${access}`;
    return api(original);
  },
);
