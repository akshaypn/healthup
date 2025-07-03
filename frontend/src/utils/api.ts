const API_BASE_URL = import.meta.env.VITE_API_URL;

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
}

class ApiClient {
  private async refreshTokenIfNeeded(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // Include cookies in the request
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const config: RequestInit = {
      ...options,
      credentials: 'include', // Include cookies in all requests
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      let response = await fetch(`${API_BASE_URL}${endpoint}`, config);

      // If token is expired, try to refresh and retry once
      if (response.status === 401) {
        const refreshed = await this.refreshTokenIfNeeded();
        if (refreshed) {
          response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        } else {
          // Refresh failed, redirect to login
          window.location.href = '/login';
          return { error: 'Authentication required' };
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return { error: errorData.detail || `HTTP ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('API request failed:', error);
      return { error: 'Network error' };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient(); 