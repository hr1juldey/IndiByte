import type { UserProfile, LoginResponse, ProfileUpdateRequest, HealthCheckResponse, ScanRequest } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`API request failed: ${error.message}`);
      }
      throw error;
    }
  }

  // Health check
  async checkHealth(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>('/health');
  }

  // Profile endpoints
  profile = {
    get: async (name: string): Promise<{ profile: UserProfile }> => {
      return this.request<{ profile: UserProfile }>(`/api/profile/${name}`);
    },

    update: async (name: string, updates: Partial<ProfileUpdateRequest>): Promise<{ profile: UserProfile }> => {
      return this.request<{ profile: UserProfile }>(`/api/profile/${name}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
    },
  };

  // Auth endpoints
  auth = {
    login: async (name: string): Promise<LoginResponse> => {
      return this.request<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ name }),
      });
    },
  };

  // Scan endpoints
  scan = {
    start: async (scanRequest: ScanRequest): Promise<{ scan_id: string }> => {
      return this.request<{ scan_id: string }>('/api/scan', {
        method: 'POST',
        body: JSON.stringify(scanRequest),
      });
    },
  };
}

export const api = new APIClient();