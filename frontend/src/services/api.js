const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const getAccessToken = () => {
  return localStorage.getItem("access_token");
};
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem("refresh_token");

  if (!refreshToken) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      refresh_token: refreshToken,
    }),
  });

  if (!response.ok) {
    return null;
  }

  const data = await response.json();

  if (data.access_token) {
    localStorage.setItem("access_token", data.access_token);
  }

  if (data.refresh_token) {
    localStorage.setItem("refresh_token", data.refresh_token);
  }

  return data.access_token;
};

const api = {
  get: async (endpoint) => {
    let token = getAccessToken();

    let response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    });

    if (response.status === 401) {
      const newToken = await refreshAccessToken();

      if (newToken) {
        token = newToken;

        response = await fetch(`${API_BASE_URL}${endpoint}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    }

    if (!response.ok) {
      const error = new Error(`API Error: ${response.status}`);
      error.status = response.status;
      throw error;
    }

    return response.json();
  },

  post: async (endpoint, data = {}) => {
    const token = getAccessToken();

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token
          ? {
              Authorization: `Bearer ${token}`,
            }
          : {}),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = new Error(`API Error: ${response.status}`);
      error.status = response.status;
      throw error;
    }

    return response.json();
  },

  put: async (endpoint, data = {}) => {
    const token = getAccessToken();

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...(token
          ? {
              Authorization: `Bearer ${token}`,
            }
          : {}),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = new Error(`API Error: ${response.status}`);
      error.status = response.status;
      throw error;
    }

    return response.json();
  },

  delete: async (endpoint) => {
    const token = getAccessToken();

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    });

    if (!response.ok) {
      const error = new Error(`API Error: ${response.status}`);
      error.status = response.status;
      throw error;
    }

    return response.json();
  },
  uploadAvatar: async (file) => {
    const token = getAccessToken();

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/profile/avatar`, {
      method: "POST",
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
      body: formData,
    });

    if (!response.ok) {
      const error = new Error(`Avatar upload failed: ${response.status}`);
      error.status = response.status;
      throw error;
    }

    return response.json();
  },
};

export default api;
