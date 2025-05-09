import { useState, useEffect } from "react";
import predictionsMock from "../data/predictions.json";

// Type definitions for predictions
interface TeamInfo {
  name: string;
  crest: string;
  color: string;
}

interface FeatureInfo {
  label: string;
  value: string | number;
}

interface PredictionInfo {
  home: number;
  draw: number;
  away: number;
  winner: string;
  home_score: number;
  away_score: number;
}

interface MatchPrediction {
  id: number;
  home: TeamInfo;
  away: TeamInfo;
  kickoff: string;
  match_date: string;
  competition: string;
  features: FeatureInfo[];
  prediction: PredictionInfo;
}

export default function Predictions() {
  const [predictions, setPredictions] = useState<MatchPrediction[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load predictions
  useEffect(() => {
    try {
      // In a real app, we'd fetch this from an API
      // For now we use the JSON file
      setPredictions(predictionsMock as MatchPrediction[]);

      if (predictionsMock && predictionsMock.length > 0) {
        setSelectedId((predictionsMock as MatchPrediction[])[0].id);
      }
      setLoading(false);
    } catch {
      setError("Failed to load prediction data");
      setLoading(false);
    }
  }, []);

  // Find selected match
  const match = predictions.find((m) => m.id === selectedId);

  if (loading) {
    return (
      <div className="w-full p-4 space-y-4">
        <div className="animate-pulse bg-slate-100 rounded-2xl h-64 mb-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-4">
        <div className="bg-red-50 p-4 rounded-md border border-red-200 text-red-600">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!match || predictions.length === 0) {
    return (
      <div className="w-full p-4">
        <div className="bg-yellow-50 p-4 rounded-md border border-yellow-200 text-yellow-600">
          <p>No prediction data available. Please check back later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full p-4 space-y-8">
      <h1 className="text-2xl font-bold mb-4">Match Predictions</h1>
      <p className="text-gray-600 mb-6">
        Our AI model uses historical match data and team statistics to predict
        match outcomes.
      </p>

      <div className="bg-white/60 backdrop-blur-md shadow-glass rounded-2xl p-8 border border-primary-light">
        <div className="mb-4">
          <label className="block text-xs uppercase tracking-widest text-slate-700 mb-2">
            Select Match
          </label>
          <select
            className="w-full p-2 rounded border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-primary"
            value={selectedId || ""}
            onChange={(e) => setSelectedId(Number(e.target.value))}
          >
            {predictions.map((m) => (
              <option key={m.id} value={m.id}>
                {m.home.name} vs {m.away.name} ({m.kickoff}) - {m.competition}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4 mb-4">
          <img
            src={match.home.crest}
            alt={match.home.name}
            className="w-10 h-10 object-contain"
          />
          <span
            className="font-bold text-lg"
            style={{ color: match.home.color }}
          >
            {match.home.name}
          </span>
          <span className="text-slate-700 font-semibold">vs</span>
          <span
            className="font-bold text-lg"
            style={{ color: match.away.color }}
          >
            {match.away.name}
          </span>
          <img
            src={match.away.crest}
            alt={match.away.name}
            className="w-10 h-10 object-contain"
          />
        </div>

        <div className="text-sm text-slate-500 mb-4">
          {match.competition} •{" "}
          {new Date(match.match_date).toLocaleDateString()} • {match.kickoff}
        </div>

        {/* Predicted Score */}
        <div className="mb-4 text-center">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2">
            Predicted Score
          </div>
          <div className="flex items-center justify-center gap-2">
            <span
              className="font-bold text-2xl"
              style={{ color: match.home.color }}
            >
              {match.prediction.home_score}
            </span>
            <span className="text-slate-400">-</span>
            <span
              className="font-bold text-2xl"
              style={{ color: match.away.color }}
            >
              {match.prediction.away_score}
            </span>
          </div>
        </div>

        {/* Prediction Bar */}
        <div className="w-full max-w-xs mx-auto mb-2">
          <div className="flex justify-between text-xs mb-1">
            <span style={{ color: match.home.color }}>{match.home.name}</span>
            <span>Draw</span>
            <span style={{ color: match.away.color }}>{match.away.name}</span>
          </div>
          <div className="flex w-full h-6 rounded overflow-hidden border border-slate-200 bg-slate-100">
            <div
              className="h-full"
              style={{
                width: `${match.prediction.home * 100}%`,
                background: match.home.color,
                transition: "width 0.5s",
              }}
            />
            <div
              className="h-full bg-slate-400"
              style={{
                width: `${match.prediction.draw * 100}%`,
                transition: "width 0.5s",
              }}
            />
            <div
              className="h-full"
              style={{
                width: `${match.prediction.away * 100}%`,
                background: match.away.color,
                transition: "width 0.5s",
              }}
            />
          </div>
          <div className="flex justify-between text-xs mt-1">
            <span className="font-semibold" style={{ color: match.home.color }}>
              {Math.round(match.prediction.home * 100)}%
            </span>
            <span className="font-semibold text-slate-700">
              {Math.round(match.prediction.draw * 100)}%
            </span>
            <span className="font-semibold" style={{ color: match.away.color }}>
              {Math.round(match.prediction.away * 100)}%
            </span>
          </div>
        </div>

        <div className="text-sm text-slate-600 mb-4 text-center">
          Prediction:{" "}
          <span className="font-bold text-primary">
            {match.prediction.winner}
          </span>
        </div>

        {/* Features */}
        <div className="mt-6">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2">
            Key Factors
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {match.features.map((f, i) => (
              <span
                key={i}
                className="bg-primary-light text-primary px-2 py-1 rounded text-xs shadow-sm border border-primary/20"
                title={f.label}
              >
                {f.label}:{" "}
                <span className="font-semibold text-slate-900">{f.value}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
