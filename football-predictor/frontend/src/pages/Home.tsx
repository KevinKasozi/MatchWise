import { useState, useEffect } from "react";
import RealFixtures from "../components/RealFixtures";

// Mock data for demo
const nextMatch = {
  home: {
    name: "Arsenal",
    crest: "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    color: "#EF0107",
  },
  away: {
    name: "Chelsea",
    crest: "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    color: "#034694",
  },
  kickoff: new Date(Date.now() + 1000 * 60 * 60 * 2), // 2 hours from now
  league: "Premier League",
  prediction: {
    home: 0.68,
    draw: 0.18,
    away: 0.14,
    winner: "Arsenal",
  },
  live: false,
};

const modelAccuracy = 0.72;
const todaysPicks = [
  {
    home: "Man Utd",
    away: "Liverpool",
    time: "21:00",
    homeCrest:
      "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    awayCrest:
      "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    prediction: "Draw",
    confidence: 0.41,
  },
  {
    home: "Real Madrid",
    away: "Barcelona",
    time: "19:30",
    homeCrest:
      "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg",
    awayCrest:
      "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg",
    prediction: "Real Madrid",
    confidence: 0.55,
  },
  {
    home: "PSG",
    away: "Marseille",
    time: "18:00",
    homeCrest:
      "https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg",
    awayCrest:
      "https://upload.wikimedia.org/wikipedia/en/6/6d/Olympique_Marseille_logo.svg",
    prediction: "PSG",
    confidence: 0.62,
  },
];

function useCountdown(target: Date) {
  const [time, setTime] = useState(target.getTime() - Date.now());
  useEffect(() => {
    const interval = setInterval(
      () => setTime(target.getTime() - Date.now()),
      1000,
    );
    return () => clearInterval(interval);
  }, [target]);
  const hours = Math.max(0, Math.floor(time / 1000 / 60 / 60));
  const minutes = Math.max(0, Math.floor((time / 1000 / 60) % 60));
  const seconds = Math.max(0, Math.floor((time / 1000) % 60));
  return `${hours.toString().padStart(2, "0")}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}

export default function Home() {
  const countdown = useCountdown(nextMatch.kickoff);

  return (
    <div className="w-full px-4 md:px-8 py-10 max-w-screen-2xl mx-auto grid gap-10">
      {/* Hero Card: Next Big Match */}
      <div className="relative bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-2xl p-10 flex flex-col md:flex-row items-center gap-10 border-l-8 border-primary/80 hover:scale-[1.01] hover:shadow-2xl transition-transform duration-200">
        <div className="flex flex-col items-center md:items-start flex-1">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2">
            Next Big Match
          </div>
          <div className="flex items-center gap-4 mb-2">
            <img
              src={nextMatch.home.crest}
              alt={nextMatch.home.name}
              className="w-14 h-14"
            />
            <span
              className="text-xl font-bold"
              style={{ color: nextMatch.home.color }}
            >
              {nextMatch.home.name}
            </span>
            <span className="text-lg font-semibold text-slate-700">vs</span>
            <span
              className="text-xl font-bold"
              style={{ color: nextMatch.away.color }}
            >
              {nextMatch.away.name}
            </span>
            <img
              src={nextMatch.away.crest}
              alt={nextMatch.away.name}
              className="w-14 h-14"
            />
          </div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-slate-500">{nextMatch.league}</span>
            {nextMatch.live && (
              <span className="bg-warning text-white px-2 py-1 rounded text-xs animate-pulse">
                LIVE
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span className="text-2xl font-mono font-semibold text-primary">
              {countdown}
            </span>
            <span className="text-xs text-slate-500">Kickoff</span>
          </div>
        </div>
        {/* Prediction Bar */}
        <div className="flex-1 flex flex-col items-center gap-4">
          <div className="w-full max-w-xs">
            <div className="flex justify-between text-xs mb-1">
              <span style={{ color: nextMatch.home.color }}>
                {nextMatch.home.name}
              </span>
              <span>Draw</span>
              <span style={{ color: nextMatch.away.color }}>
                {nextMatch.away.name}
              </span>
            </div>
            <div className="flex w-full h-6 rounded overflow-hidden border border-slate-200 bg-slate-100">
              <div
                className="h-full"
                style={{
                  width: `${nextMatch.prediction.home * 100}%`,
                  background: nextMatch.home.color,
                  transition: "width 0.5s",
                }}
              />
              <div
                className="h-full bg-slate-400"
                style={{
                  width: `${nextMatch.prediction.draw * 100}%`,
                  transition: "width 0.5s",
                }}
              />
              <div
                className="h-full"
                style={{
                  width: `${nextMatch.prediction.away * 100}%`,
                  background: nextMatch.away.color,
                  transition: "width 0.5s",
                }}
              />
            </div>
            <div className="flex justify-between text-xs mt-1">
              <span
                className="font-semibold"
                style={{ color: nextMatch.home.color }}
              >
                {Math.round(nextMatch.prediction.home * 100)}%
              </span>
              <span className="font-semibold text-slate-700">
                {Math.round(nextMatch.prediction.draw * 100)}%
              </span>
              <span
                className="font-semibold"
                style={{ color: nextMatch.away.color }}
              >
                {Math.round(nextMatch.prediction.away * 100)}%
              </span>
            </div>
          </div>
          <div className="text-sm text-slate-600 mt-2">
            Prediction:{" "}
            <span className="font-bold text-primary">
              {nextMatch.prediction.winner}
            </span>
          </div>
        </div>
      </div>

      {/* Real Fixtures Section */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <RealFixtures />
      </div>

      {/* Live Confidence & Model Accuracy */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-10 w-full">
        {/* Live Confidence Bar */}
        <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-lg p-8 flex flex-col items-center border-l-4 border-accent/70 hover:shadow-xl transition-shadow">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2">
            Live Confidence
          </div>
          <div className="w-full h-4 rounded bg-slate-200 overflow-hidden flex">
            <div
              className="bg-primary"
              style={{
                width: `${nextMatch.prediction.home * 100}%`,
                transition: "width 0.5s",
              }}
            />
            <div
              className="bg-slate-400"
              style={{
                width: `${nextMatch.prediction.draw * 100}%`,
                transition: "width 0.5s",
              }}
            />
            <div
              className="bg-error"
              style={{
                width: `${nextMatch.prediction.away * 100}%`,
                transition: "width 0.5s",
              }}
            />
          </div>
          <div className="flex justify-between w-full text-xs mt-1">
            <span className="font-semibold text-primary">
              {nextMatch.home.name}
            </span>
            <span className="font-semibold text-slate-700">Draw</span>
            <span className="font-semibold text-error">
              {nextMatch.away.name}
            </span>
          </div>
        </div>
        {/* Model Accuracy Widget */}
        <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-lg p-8 flex flex-col items-center border-l-4 border-success/70 hover:shadow-xl transition-shadow">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2">
            Model Accuracy
          </div>
          <div className="relative w-24 h-24 flex items-center justify-center">
            <svg
              className="absolute top-0 left-0 w-full h-full"
              viewBox="0 0 100 100"
            >
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="10"
              />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#2563eb"
                strokeWidth="10"
                strokeDasharray={282.6}
                strokeDashoffset={282.6 * (1 - modelAccuracy)}
                strokeLinecap="round"
              />
            </svg>
            <span className="text-2xl font-bold text-primary">
              {Math.round(modelAccuracy * 100)}%
            </span>
          </div>
          <div className="text-xs text-slate-500 mt-2">
            Overall model accuracy
          </div>
        </div>
      </div>

      {/* Today's Picks Carousel */}
      <div className="w-full">
        <div className="text-xs uppercase tracking-widest text-slate-700 mb-2 font-semibold">
          Today's Picks
        </div>
        <div className="flex gap-6 overflow-x-auto pb-2">
          {todaysPicks.map((pick, i) => (
            <div
              key={i}
              className="min-w-[220px] bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-lg p-5 flex flex-col items-center border-l-4 border-secondary/70 hover:scale-105 hover:shadow-2xl transition-transform duration-200"
            >
              <div className="flex items-center gap-2 mb-2">
                <img src={pick.homeCrest} alt={pick.home} className="w-8 h-8" />
                <span className="font-semibold text-slate-900">
                  {pick.home}
                </span>
                <span className="text-xs text-slate-500">vs</span>
                <span className="font-semibold text-slate-900">
                  {pick.away}
                </span>
                <img src={pick.awayCrest} alt={pick.away} className="w-8 h-8" />
              </div>
              <div className="text-xs text-slate-500 mb-1">{pick.time}</div>
              <div className="w-full h-3 rounded bg-slate-200 overflow-hidden mb-1">
                <div
                  className="h-full bg-primary"
                  style={{
                    width: `${pick.confidence * 100}%`,
                    transition: "width 0.5s",
                  }}
                />
              </div>
              <div className="text-xs text-slate-700">
                Prediction:{" "}
                <span className="font-bold text-primary">
                  {pick.prediction}
                </span>
              </div>
              <div className="text-xs text-slate-500">
                Confidence: {Math.round(pick.confidence * 100)}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
