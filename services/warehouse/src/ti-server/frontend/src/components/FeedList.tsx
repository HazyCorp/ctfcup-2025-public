import { useEffect, useState } from 'react';
import { Shield, Lock, Globe } from 'lucide-react';
import { tiService } from '../services/tiService';
import type { Feed } from '../types';

interface FeedListProps {
  onSelectFeed: (feed: Feed) => void;
}

export function FeedList({ onSelectFeed }: FeedListProps) {
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFeeds();
  }, []);

  const loadFeeds = async () => {
    try {
      setLoading(true);
      setError(null);
      const feeds = await tiService.getFeeds({ is_public: true });
      setFeeds(feeds);
    } catch (err) {
      setError('Failed to load feeds');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Threat Intelligence Feeds</h2>
        <Shield className="h-8 w-8 text-blue-600" />
      </div>

      {feeds.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No public feeds available</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {feeds.map((feed) => (
            <div
              key={feed.id}
              onClick={() => onSelectFeed(feed)}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                  {feed.name}
                </h3>
                {feed.is_public ? (
                  <Globe className="h-5 w-5 text-green-500 flex-shrink-0" />
                ) : (
                  <Lock className="h-5 w-5 text-gray-400 flex-shrink-0" />
                )}
              </div>
              <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                {feed.description || 'No description available'}
              </p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Created {new Date(feed.created_at).toLocaleDateString()}</span>
                <span className="text-blue-600 group-hover:text-blue-700 font-medium">
                  View details →
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
