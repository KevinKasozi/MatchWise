import { useState } from 'react';

// Mock data for demo
const results = [
  {
    id: 1,
    league: 'Premier League',
    date: '2024-05-09',
    home: {
      name: 'Arsenal',
      crest: 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg',
      color: '#EF0107',
    },
    away: {
      name: 'Chelsea',
      crest: 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg',
      color: '#034694',
    },
    score: '2-1',
    prediction: 'Arsenal',
    correct: true,
  },
  {
    id: 2,
    league: 'Premier League',
    date: '2024-05-09',
    home: {
      name: 'Man Utd',
      crest: 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg',
      color: '#DA291C',
    },
    away: {
      name: 'Liverpool',
      crest: 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg',
      color: '#C8102E',
    },
    score: '1-2',
    prediction: 'Man Utd',
    correct: false,
  },
  {
    id: 3,
    league: 'La Liga',
    date: '2024-05-09',
    home: {
      name: 'Real Madrid',
      crest: 'https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg',
      color: '#FEBE10',
    },
    away: {
      name: 'Barcelona',
      crest: 'https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg',
      color: '#A50044',
    },
    score: '1-1',
    prediction: 'Draw',
    correct: true,
  },
];

const accuracyByLeague = [
  { league: 'Premier League', accuracy: 0.71 },
  { league: 'La Liga', accuracy: 0.78 },
];

// Add a Result type for the filter functions
type Result = {
  correct: boolean;
  // add other fields as needed
};

const tabs = [
  { label: 'All', filter: () => true },
  { label: 'Model Wins', filter: (r: Result) => r.correct },
  { label: 'Model Losses', filter: (r: Result) => !r.correct },
];

export default function Results() {
  const [tab, setTab] = useState(0);
  const filtered = results.filter(tabs[tab].filter);

  return (
    <div className="w-full px-4 md:px-8 py-10 max-w-screen-lg mx-auto grid gap-10">
      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {tabs.map((t, i) => (
          <button
            key={i}
            className={`relative px-5 py-2 rounded-full font-semibold text-sm transition-colors border shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30
              ${tab === i
                ? 'bg-primary/10 text-primary border-primary shadow-sm after:absolute after:left-1/2 after:-bottom-1 after:-translate-x-1/2 after:w-2/3 after:h-1 after:rounded-full after:bg-primary after:content-[""]'
                : 'text-text-secondary border-primary-light bg-white hover:bg-primary/5 hover:text-primary'}`}
            onClick={() => setTab(i)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {/* Results Table */}
      <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-2xl p-10 border-l-8 border-primary/80 hover:scale-[1.01] hover:shadow-2xl transition-transform duration-200">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-slate-700 border-b">
                <th className="p-2 text-left">Date</th>
                <th className="p-2 text-left">Match</th>
                <th className="p-2 text-left">Score</th>
                <th className="p-2 text-left">Prediction</th>
                <th className="p-2 text-left">Model</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-b last:border-0 hover:bg-primary/10 transition duration-150 cursor-pointer">
                  <td className="p-2 whitespace-nowrap">{r.date}</td>
                  <td className="p-2 flex items-center gap-2 whitespace-nowrap">
                    <img src={r.home.crest} alt={r.home.name} className="w-6 h-6" />
                    <span className="font-semibold" style={{ color: r.home.color }}>{r.home.name}</span>
                    <span className="text-xs text-slate-500">vs</span>
                    <span className="font-semibold" style={{ color: r.away.color }}>{r.away.name}</span>
                    <img src={r.away.crest} alt={r.away.name} className="w-6 h-6" />
                  </td>
                  <td className="p-2 font-mono text-slate-900">{r.score}</td>
                  <td className="p-2">
                    <span className={`font-bold ${r.prediction === 'Draw' ? 'text-slate-700' : r.prediction === r.home.name ? 'text-primary' : 'text-error'}`}>{r.prediction}</span>
                  </td>
                  <td className="p-2">
                    {r.correct ? (
                      <span className="inline-flex items-center gap-1 text-success font-semibold">✅ Correct</span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-error font-semibold">❌ Incorrect</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {/* Accuracy by League Bar Chart */}
      <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-2xl p-10 border-l-8 border-accent/80 hover:scale-[1.01] hover:shadow-2xl transition-transform duration-200">
        <div className="text-xs uppercase tracking-widest text-slate-700 mb-2 font-semibold">Model Accuracy by League</div>
        <div className="space-y-2">
          {accuracyByLeague.map((l, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-32 text-slate-900 font-semibold">{l.league}</span>
              <div className="flex-1 h-4 bg-slate-200 rounded overflow-hidden">
                <div className="h-full bg-primary" style={{ width: `${l.accuracy * 100}%`, transition: 'width 0.5s' }} />
              </div>
              <span className="w-10 text-right font-mono text-primary">{Math.round(l.accuracy * 100)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 