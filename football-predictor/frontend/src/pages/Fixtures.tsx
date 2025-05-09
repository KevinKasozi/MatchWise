import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Fixture, MatchResult } from '../types/api';
import { Tab } from '@headlessui/react';
import RealFixtures from '../components/RealFixtures';

type FixtureStatus = 'upcoming' | 'completed' | 'all';

const tabOptions: { label: string; value: FixtureStatus }[] = [
  { label: 'Upcoming', value: 'upcoming' },
  { label: 'Completed', value: 'completed' },
  { label: 'All', value: 'all' },
];

export default function Fixtures() {
  const [status, setStatus] = useState<FixtureStatus>('upcoming');
  const [loading, setLoading] = useState(true);

  const { data: fixturesData = [], isError } = useQuery<(Fixture & { result?: MatchResult })[]>({
    queryKey: ['fixtures', status],
    queryFn: async () => {
      const res = await apiClient.get<(Fixture & { result?: MatchResult })[]>('/fixtures', {
        params: { status, limit: 50 },
      });
      console.log("Fixtures response:", res.data);
      return res.data;
    },
  });

  // Group fixtures by date
  const fixturesByDate: Record<string, (Fixture & { result?: MatchResult })[]> = {};
  
  fixturesData.forEach(fixture => {
    const dateKey = new Date(fixture.match_date).toLocaleDateString();
    if (!fixturesByDate[dateKey]) {
      fixturesByDate[dateKey] = [];
    }
    fixturesByDate[dateKey].push(fixture);
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

  if (isError) {
    return (
      <div className="bg-red-50 p-4 rounded-md border border-red-200 text-red-600">
        <p>Error loading fixtures data. Please try again later.</p>
      </div>
    );
  }

  // Helper function to get team logo
  const getTeamLogo = (teamName: string) => {
    // Basic function to generate a colored badge for teams - replace with actual logos in a real app
    const initial = teamName.charAt(0).toUpperCase();
    const colorMap: {[key: string]: string} = {
      'A': '1e40af', 'B': '1d4ed8', 'C': '2563eb', 
      'D': '3b82f6', 'E': '60a5fa', 'F': '93c5fd',
      'G': '0f766e', 'H': '0d9488', 'I': '14b8a6',
      'J': '06b6d4', 'K': '0ea5e9', 'L': '0284c7',
      'M': '7e22ce', 'N': '6d28d9', 'O': '8b5cf6',
      'P': 'a855f7', 'Q': 'c026d3', 'R': 'd946ef',
      'S': 'e11d48', 'T': 'be123c', 'U': 'db2777',
      'V': 'ea580c', 'W': 'c2410c', 'X': 'a16207',
      'Y': '65a30d', 'Z': '4d7c0f'
    };
    
    const bgColor = colorMap[initial] || '1e3a8a';
    return `https://placehold.co/100x100/${bgColor}/ffffff?text=${initial}`;
  };

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

        <Tab.Panels>
          {tabOptions.map((tab) => (
            <Tab.Panel key={tab.value}>
              {status === 'upcoming' ? (
                <RealFixtures />
              ) : (
                <div className="space-y-6">
                  {Object.keys(fixturesByDate).length === 0 ? (
                    <div className="bg-white rounded shadow p-8 text-center border border-gray-100">
                      <p className="text-gray-500">No fixtures found for this filter.</p>
                    </div>
                  ) : (
                    // Sort dates chronologically
                    Object.entries(fixturesByDate)
                      .sort(([dateA], [dateB]) => new Date(dateA).getTime() - new Date(dateB).getTime())
                      .map(([date, fixtures]) => {
                        // Group fixtures by competition
                        const fixturesByCompetition: Record<string, (Fixture & { result?: MatchResult })[]> = {};
                        fixtures.forEach(fixture => {
                          const competitionKey = fixture.competition_name || "Unknown Competition";
                          if (!fixturesByCompetition[competitionKey]) {
                            fixturesByCompetition[competitionKey] = [];
                          }
                          fixturesByCompetition[competitionKey].push(fixture);
                        });

                        return (
                          <div key={date} className="bg-white rounded-lg shadow overflow-hidden mb-8">
                            <div className="flex justify-between items-center bg-gray-50 p-4 border-b">
                              <h2 className="text-lg font-medium text-gray-800">
                                {new Date(date).toLocaleDateString('en-US', { 
                                  weekday: 'long', 
                                  month: 'long', 
                                  day: 'numeric' 
                                })}
                              </h2>
                              <span className="bg-blue-100 text-blue-800 rounded-full px-3 py-1 text-xs font-medium">
                                {fixtures.length} match{fixtures.length !== 1 ? 'es' : ''}
                              </span>
                            </div>
                            
                            {/* Display fixtures grouped by competition */}
                            {Object.entries(fixturesByCompetition).map(([competition, competitionFixtures]) => (
                              <div key={competition} className="mb-2">
                                <div className="bg-gray-50 px-4 py-2 border-b border-t">
                                  <h3 className="font-medium text-gray-700">{competition}</h3>
                                </div>
                                <div className="divide-y">
                                  {competitionFixtures.map((fixture) => (
                                    <div key={fixture.id} className="p-4 hover:bg-blue-50 transition-colors">
                                      <div className="flex justify-between items-center">
                                        <div className="flex items-center space-x-4 flex-1">
                                          <div className="flex items-center space-x-3 text-right flex-1">
                                            <div className="text-right flex-1">
                                              <span className="font-medium text-gray-800">{fixture.home_team_name}</span>
                                            </div>
                                            <img 
                                              src={getTeamLogo(fixture.home_team_name)} 
                                              alt={fixture.home_team_name} 
                                              className="w-10 h-10 object-contain"
                                            />
                                          </div>
                                          
                                          <div className="flex flex-col items-center justify-center min-w-[80px]">
                                            <div className="bg-gray-100 rounded-lg px-3 py-1 text-sm font-bold text-gray-800 min-w-[60px] text-center">
                                              {fixture.is_completed && fixture.result && typeof fixture.result.home_score === 'number' && typeof fixture.result.away_score === 'number' ? (
                                                <span>{fixture.result.home_score} - {fixture.result.away_score}</span>
                                              ) : (
                                                <span>vs</span>
                                              )}
                                            </div>
                                            {!fixture.is_completed && fixture.match_time && (
                                              <span className="text-xs text-gray-500 mt-1">
                                                {fixture.match_time}
                                              </span>
                                            )}
                                          </div>
                                          
                                          <div className="flex items-center space-x-3 flex-1">
                                            <img 
                                              src={getTeamLogo(fixture.away_team_name)} 
                                              alt={fixture.away_team_name} 
                                              className="w-10 h-10 object-contain"
                                            />
                                            <div className="flex-1">
                                              <span className="font-medium text-gray-800">{fixture.away_team_name}</span>
                                            </div>
                                          </div>
                                        </div>
                                        
                                        {fixture.venue && (
                                          <div className="text-gray-500 text-sm hidden md:block">
                                            {fixture.venue}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        );
                      })
                  )}
                </div>
              )}
            </Tab.Panel>
          ))}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
} 