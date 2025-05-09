import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Fixture, MatchResult } from '../types/api';
import { Tab } from '@headlessui/react';

type FixtureStatus = 'upcoming' | 'completed' | 'all';

const tabOptions: { label: string; value: FixtureStatus }[] = [
  { label: 'Upcoming', value: 'upcoming' },
  { label: 'Completed', value: 'completed' },
  { label: 'All', value: 'all' },
];

export default function Fixtures() {
  const [status, setStatus] = useState<FixtureStatus>('upcoming');
  const [loading, setLoading] = useState(true);

  const { data: fixturesData = [] } = useQuery<(Fixture & { result?: MatchResult })[]>({
    queryKey: ['fixtures', status],
    queryFn: async () => {
      const res = await apiClient.get<(Fixture & { result?: MatchResult })[]>('/fixtures', {
        params: { status },
      });
      return res.data;
    },
  });

  useEffect(() => {
    // Simulate loading shimmer
    const timer = setTimeout(() => setLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="w-full p-4 space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="animate-pulse bg-slate-100 rounded-2xl h-24 mb-4" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Football Fixtures</h1>

      <Tab.Group selectedIndex={tabOptions.findIndex(t => t.value === status)} onChange={i => setStatus(tabOptions[i].value)}>
        <Tab.List className="flex space-x-2 mb-6">
          {tabOptions.map((tab) => (
            <Tab
              key={tab.value}
              className={({ selected }) =>
                `px-4 py-2 rounded font-medium text-sm focus:outline-none transition-colors ${
                  selected
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-blue-600 border border-blue-300 hover:bg-blue-50'
                }`
              }
            >
              {tab.label}
            </Tab>
          ))}
        </Tab.List>
      </Tab.Group>

      <div className="space-y-4">
        {fixturesData.map((fixture: Fixture & { result?: MatchResult }) => (
          <div key={fixture.id} className="bg-white rounded shadow p-4 border border-gray-100">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold">{fixture.home_team_id} vs {fixture.away_team_id}</h2>
                <div className="text-gray-500 text-sm">{new Date(fixture.match_date).toLocaleDateString()}</div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">{fixture.stage}</span>
                {fixture.result && (
                  <span className="text-lg font-bold">{fixture.result.home_score} - {fixture.result.away_score}</span>
                )}
              </div>
            </div>
            {fixture.venue && (
              <div className="text-gray-500 text-sm mt-2">Venue: {fixture.venue}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
} 