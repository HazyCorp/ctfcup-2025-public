import type {
  Feed,
  Indicator,
  CreateIndicatorRequest,
  CreateFeedRequest,
  UpdateFeedRequest,
  PaginatedResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class TIService {
  // Normalizes feed responses so UI never receives unexpected payloads
  private extractFeedArray(payload: unknown): Feed[] {
    if (Array.isArray(payload)) {
      return payload as Feed[];
    }

    if (payload && typeof payload === 'object') {
      const { items, feeds, data } = payload as {
        items?: unknown;
        feeds?: unknown;
        data?: unknown;
      };

      if (Array.isArray(items)) {
        return items as Feed[];
      }

      if (Array.isArray(feeds)) {
        return feeds as Feed[];
      }

      if (Array.isArray(data)) {
        return data as Feed[];
      }

      if (data && typeof data === 'object') {
        const nestedItems = (data as { items?: unknown }).items;
        if (Array.isArray(nestedItems)) {
          return nestedItems as Feed[];
        }
      }
    }

    return [];
  }

  private async fetchWithAuth(url: string, options: RequestInit = {}, apiKey?: string): Promise<Response> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (apiKey) {
      headers['X-API-Key'] = apiKey;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    return response;
  }

  // Feeds API

  async getFeeds(params?: { is_public?: boolean; limit?: number; offset?: number }): Promise<Feed[]> {
    const queryParams = new URLSearchParams();
    if (params?.is_public !== undefined) queryParams.append('is_public', String(params.is_public));
    if (params?.limit) queryParams.append('limit', String(params.limit));
    if (params?.offset) queryParams.append('offset', String(params.offset));

    const url = `${API_BASE_URL}/feeds${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await this.fetchWithAuth(url);
    const data = await response.json();
    return this.extractFeedArray(data);
  }

  async getFeed(feedId: string): Promise<Feed> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/feeds/${feedId}`);
    return response.json();
  }

  async createFeed(request: CreateFeedRequest): Promise<Feed> {
    const response = await this.fetchWithAuth(
      `${API_BASE_URL}/feeds`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    return response.json();
  }

  async updateFeed(feedId: string, request: UpdateFeedRequest, apiKey: string): Promise<Feed> {
    const response = await this.fetchWithAuth(
      `${API_BASE_URL}/feeds/${feedId}`,
      {
        method: 'PUT',
        body: JSON.stringify(request),
      },
      apiKey
    );
    return response.json();
  }

  async deleteFeed(feedId: string, apiKey: string): Promise<void> {
    await this.fetchWithAuth(
      `${API_BASE_URL}/feeds/${feedId}`,
      { method: 'DELETE' },
      apiKey
    );
  }

  // Indicators API

  async getIndicators(params?: { feed_id?: string; type?: string; limit?: number; offset?: number }): Promise<PaginatedResponse<Indicator>> {
    const queryParams = new URLSearchParams();
    if (params?.feed_id) queryParams.append('feed_id', params.feed_id);
    if (params?.type) queryParams.append('type', params.type);
    if (params?.limit) queryParams.append('limit', String(params.limit));
    if (params?.offset) queryParams.append('offset', String(params.offset));

    const url = `${API_BASE_URL}/indicators${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await this.fetchWithAuth(url);
    return response.json();
  }

  async getFeedIndicators(feedId: string, params?: { type?: string; limit?: number; offset?: number }): Promise<Indicator[]> {
    const queryParams = new URLSearchParams();
    if (params?.type) queryParams.append('type', params.type);
    if (params?.limit) queryParams.append('limit', String(params.limit));
    if (params?.offset) queryParams.append('offset', String(params.offset));

    const url = `${API_BASE_URL}/feeds/${feedId}/iocs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await this.fetchWithAuth(url);
    return response.json();
  }

  async createIndicator(request: CreateIndicatorRequest, apiKey?: string): Promise<Indicator> {
    const response = await this.fetchWithAuth(
      `${API_BASE_URL}/feeds/${request.feed_id}/iocs`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      },
      apiKey
    );
    return response.json();
  }

  async deleteIndicator(indicatorId: string, apiKey: string): Promise<void> {
    await this.fetchWithAuth(
      `${API_BASE_URL}/indicators/${indicatorId}`,
      { method: 'DELETE' },
      apiKey
    );
  }

  async bulkCreateIndicators(feedId: string, indicators: Omit<CreateIndicatorRequest, 'feed_id'>[], apiKey: string): Promise<{ created: number; failed: number }> {
    const response = await this.fetchWithAuth(
      `${API_BASE_URL}/feeds/bulk-indicators`,
      {
        method: 'POST',
        body: JSON.stringify({
          feed_id: feedId,
          indicators,
        }),
      },
      apiKey
    );
    return response.json();
  }
}

export const tiService = new TIService();
