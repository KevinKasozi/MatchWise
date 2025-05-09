import { useState } from 'react';

// Mock data for demo
const matches = [
  {
    id: 1,
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
    kickoff: '19:00',
    features: [
      { label: 'Home Win Streak', value: 3 },
      { label: 'xG Diff', value: '+0.7' },
      { label: 'Home Form', value: 'W W D' },
    ],
    prediction: {
      home: 0.68,
      draw: 0.18,
      away: 0.14,
      winner: 'Arsenal',
    },
  },
  {
    id: 2,
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
    kickoff: '21:00',
    features: [
      { label: 'Away Win Streak', value: 2 },
      { label: 'xG Diff', value: '-0.2' },
      { label: 'Away Form', value: 'W D W' },
    ],
    prediction: {
      home: 0.32,
      draw: 0.41,
      away: 0.27,
      winner: 'Draw',
    },
  },
];

export default function Predictions() {
  const [selectedId, setSelectedId] = useState(matches[0].id);
  const match = matches.find((m) => m.id === selectedId)!;

  return (
    <div className="w-full p-4 space-y-8">
      <div className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-8 border border-primary-light">
        <div className="mb-4">
          <label className="block text-xs uppercase tracking-widest text-slate-700 mb-2">Select Match</label>
          <select
            className="w-full p-2 rounded border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-primary"
            value={selectedId}
            onChange={(e) => setSelectedId(Number(e.target.value))}
          >
            {matches.map((m) => (
              <option key={m.id} value={m.id}>
                {m.home.name} vs {m.away.name} ({m.kickoff})
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-4 mb-4">
          <img src={match.home.crest} alt={match.home.name} className="w-10 h-10" />
          <span className="font-bold text-lg" style={{ color: match.home.color }}>{match.home.name}</span>
          <span className="text-slate-700 font-semibold">vs</span>
          <span className="font-bold text-lg" style={{ color: match.away.color }}>{match.away.name}</span>
          <img src={match.away.crest} alt={match.away.name} className="w-10 h-10" />
        </div>
        {/* Prediction Bar */}
        <div className="w-full max-w-xs mx-auto mb-2">
          <div className="flex justify-between text-xs mb-1">
            <span style={{ color: match.home.color }}>{match.home.name}</span>
            <span>Draw</span>
            <span style={{ color: match.away.color }}>{match.away.name}</span>
          </div>
          <div className="flex w-full h-6 rounded overflow-hidden border border-slate-200 bg-slate-100">
            <div className="h-full" style={{ width: `${match.prediction.home * 100}%`, background: match.home.color, transition: 'width 0.5s' }} />
            <div className="h-full bg-slate-400" style={{ width: `${match.prediction.draw * 100}%`, transition: 'width 0.5s' }} />
            <div className="h-full" style={{ width: `${match.prediction.away * 100}%`, background: match.away.color, transition: 'width 0.5s' }} />
          </div>
          <div className="flex justify-between text-xs mt-1">
            <span className="font-semibold" style={{ color: match.home.color }}>{Math.round(match.prediction.home * 100)}%</span>
            <span className="font-semibold text-slate-700">{Math.round(match.prediction.draw * 100)}%</span>
            <span className="font-semibold" style={{ color: match.away.color }}>{Math.round(match.prediction.away * 100)}%</span>
          </div>
        </div>
        <div className="text-sm text-slate-600 mb-2">Prediction: <span className="font-bold text-primary">{match.prediction.winner}</span></div>
        {/* Features Tooltip */}
        <div className="flex flex-wrap gap-2 mt-2">
          {match.features.map((f, i) => (
            <span key={i} className="bg-primary-light text-primary px-2 py-1 rounded text-xs shadow-sm border border-primary/20" title={f.label}>
              {f.label}: <span className="font-semibold text-slate-900">{f.value}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
} 