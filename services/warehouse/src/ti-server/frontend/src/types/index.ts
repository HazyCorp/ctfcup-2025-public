// Feed represents a TI feed
export interface Feed {
  id: string;
  name: string;
  description: string;
  is_public: boolean;
  api_key?: string; // Only returned on creation
  created_at: string;
  updated_at: string;
}

// Indicator represents an IOC (Indicator of Compromise)
export interface Indicator {
  id: string;
  feed_id: string;
  type: string;
  value: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  created_at: string;
}

// API response wrapper for paginated lists
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// Request to create a new indicator
export interface CreateIndicatorRequest {
  feed_id: string;
  type: string;
  value: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description?: string;
}

// Request to create a new feed
export interface CreateFeedRequest {
  name: string;
  description?: string;
  is_public: boolean;
}

// Request to update a feed
export interface UpdateFeedRequest {
  name?: string;
  description?: string;
  is_public?: boolean;
}
