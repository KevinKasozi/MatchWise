import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Club } from '../types/api';

export default function Clubs() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const itemsPerPage = 12;

  const { data: clubs = [], isLoading, isError } = useQuery<Club[]>({
    queryKey: ['clubs', search, page],
    queryFn: async () => {
      const res = await apiClient.get<Club[]>('/clubs', {
        params: {
          search,
          skip: (page - 1) * itemsPerPage,
          limit: itemsPerPage,
        },
      });
      console.log("Clubs response:", res.data);
      return res.data;
    },
  });

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value);
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="animate-pulse bg-slate-100 rounded-lg h-48" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 p-4 rounded-md border border-red-200 text-red-600">
        <p>Error loading clubs data. Please try again later.</p>
      </div>
    );
  }

  // For pagination
  const totalCount = Math.max(100, clubs.length); // Fallback to 100 if we don't have a real count
  const totalPages = Math.ceil(totalCount / itemsPerPage);

  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold mb-4">Football Clubs</h1>

      <input
        type="text"
        placeholder="Search clubs"
        value={search}
        onChange={handleSearchChange}
        className="w-full border border-gray-300 rounded px-4 py-2 mb-6 focus:outline-none focus:ring-2 focus:ring-blue-400"
      />

      {clubs.length === 0 ? (
        <div className="bg-white rounded shadow p-8 text-center border border-gray-100">
          <p className="text-gray-500">No clubs found. Try a different search term or check back later.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {clubs.map((club) => (
            <div key={club.id} className="bg-white rounded shadow p-4 border border-gray-100 hover:shadow-md transition-shadow">
              <h2 className="text-lg font-semibold mb-2">{club.name || "Unknown Club"}</h2>
              
              {club.country && (
                <div className="text-gray-600 text-sm">Country: {club.country}</div>
              )}
              
              {club.founded_year && (
                <div className="text-gray-600 text-sm">Founded: {club.founded_year}</div>
              )}
              
              {club.stadium_name && (
                <div className="text-gray-600 text-sm">Stadium: {club.stadium_name}</div>
              )}
              
              {club.city && (
                <div className="text-gray-600 text-sm">City: {club.city}</div>
              )}
              
              {/* If no details are available, show a placeholder message */}
              {!club.country && !club.founded_year && !club.stadium_name && !club.city && (
                <div className="text-gray-400 text-sm italic">No additional details available</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {clubs.length > 0 && (
        <div className="flex justify-center mt-8 space-x-2">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => handlePageChange(p)}
              className={`px-3 py-1 rounded border text-sm font-medium transition-colors ${
                p === page
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-blue-600 border-blue-300 hover:bg-blue-50'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      )}
    </div>
  );
} 