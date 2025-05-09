import { useState } from "react";

// Mock data for demo
const competitions = [
  {
    id: 1,
    name: "Premier League",
    country: "England",
    logo: "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg",
    color: "#37003c",
  },
  {
    id: 2,
    name: "La Liga",
    country: "Spain",
    logo: "https://upload.wikimedia.org/wikipedia/en/7/79/LaLiga_Santander.svg",
    color: "#ff4c00",
  },
  {
    id: 3,
    name: "Serie A",
    country: "Italy",
    logo: "https://upload.wikimedia.org/wikipedia/en/e/e1/Serie_A_logo_%282019%29.svg",
    color: "#008fd7",
  },
  {
    id: 4,
    name: "Bundesliga",
    country: "Germany",
    logo: "https://upload.wikimedia.org/wikipedia/en/d/df/Bundesliga_logo_%282017%29.svg",
    color: "#e60026",
  },
  {
    id: 5,
    name: "Ligue 1",
    country: "France",
    logo: "https://upload.wikimedia.org/wikipedia/en/5/5e/Ligue1.svg",
    color: "#003366",
  },
];

export default function Competitions() {
  const [search, setSearch] = useState("");
  const filtered = competitions.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.country.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="w-full p-4 space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
        <h1 className="text-2xl font-bold text-primary">Competitions</h1>
        <input
          type="text"
          placeholder="Search leagues or countries..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full md:w-64 border border-slate-200 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {filtered.map((c) => (
          <div
            key={c.id}
            className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-6 flex flex-col items-center border border-primary-light hover:shadow-lg transition cursor-pointer"
            style={{ borderColor: c.color }}
          >
            <img src={c.logo} alt={c.name} className="w-16 h-16 mb-2" />
            <div className="text-lg font-bold mb-1" style={{ color: c.color }}>
              {c.name}
            </div>
            <div className="text-slate-700 text-sm mb-2">{c.country}</div>
            <div className="flex gap-2">
              <a href="#" className="text-xs text-primary hover:underline">
                Fixtures
              </a>
              <a href="#" className="text-xs text-primary hover:underline">
                Results
              </a>
              <a href="#" className="text-xs text-primary hover:underline">
                Standings
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
