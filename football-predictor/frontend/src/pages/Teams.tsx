import { useState } from "react";

// Mock data for demo
const team = {
  name: "Arsenal",
  badge: "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
  stadium: "Emirates Stadium",
  coach: "Mikel Arteta",
  country: "England",
  form: ["W", "D", "L", "W", "W", "W", "L", "W", "D", "W"],
  fixtures: [
    { id: 1, opponent: "Chelsea", date: "2024-05-10", home: true },
    { id: 2, opponent: "Man Utd", date: "2024-05-17", home: false },
  ],
  results: [
    {
      id: 1,
      opponent: "Liverpool",
      date: "2024-05-03",
      score: "2-1",
      home: true,
      correct: true,
    },
    {
      id: 2,
      opponent: "Tottenham",
      date: "2024-04-27",
      score: "1-2",
      home: false,
      correct: false,
    },
  ],
  accuracy: 0.74,
};

const tabs = [
  { label: "Fixtures" },
  { label: "Results" },
  { label: "Prediction Accuracy" },
];

export default function Teams() {
  const [tab, setTab] = useState(0);
  const [follow, setFollow] = useState(false);

  return (
    <div className="w-full px-4 md:px-8 py-10 max-w-screen-lg mx-auto grid gap-10">
      {/* Header */}
      <div className="flex items-center gap-6 bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-2xl p-10 border-l-8 border-primary/80 hover:scale-[1.01] hover:shadow-2xl transition-transform duration-200">
        <img src={team.badge} alt={team.name} className="w-20 h-20" />
        <div className="flex-1">
          <div className="text-2xl font-bold text-primary mb-1">
            {team.name}
          </div>
          <div className="text-slate-700 text-sm mb-1">
            Stadium: <span className="font-semibold">{team.stadium}</span>
          </div>
          <div className="text-slate-700 text-sm mb-1">
            Coach: <span className="font-semibold">{team.coach}</span>
          </div>
          <div className="text-slate-700 text-sm">
            Country: <span className="font-semibold">{team.country}</span>
          </div>
        </div>
        <button
          className={`px-5 py-2 rounded-full font-semibold text-sm transition-colors border shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30 ${follow ? "bg-primary text-white border-primary shadow" : "text-text-secondary border-primary-light bg-white hover:bg-primary/5 hover:text-primary"}`}
          onClick={() => setFollow((f) => !f)}
        >
          {follow ? "Following" : "Follow"}
        </button>
      </div>
      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {tabs.map((t, i) => (
          <button
            key={i}
            className={`relative px-5 py-2 rounded-full font-semibold text-sm transition-colors border shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30
              ${
                tab === i
                  ? "bg-primary/10 text-primary border-primary shadow-sm"
                  : "text-text-secondary border-primary-light bg-white hover:bg-primary/5 hover:text-primary"
              }`}
            onClick={() => setTab(i)}
          >
            {t.label}
            {tab === i && (
              <span className="absolute left-1/2 -bottom-1 -translate-x-1/2 w-2/3 h-1 rounded-full bg-primary" />
            )}
          </button>
        ))}
      </div>
      {/* Tab Content */}
      {tab === 0 && (
        <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-lg p-8 border-l-4 border-accent/70 hover:shadow-2xl transition-shadow">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2 font-semibold">
            Upcoming Fixtures
          </div>
          <ul className="divide-y divide-slate-200">
            {team.fixtures.map((f) => (
              <li key={f.id} className="py-2 flex items-center gap-4">
                <span className="font-semibold text-slate-900">{f.date}</span>
                <span className="text-slate-700">{f.home ? "vs" : "@"}</span>
                <span className="font-semibold text-primary">{f.opponent}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {tab === 1 && (
        <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-lg p-8 border-l-4 border-secondary/70 hover:shadow-2xl transition-shadow">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2 font-semibold">
            Recent Results
          </div>
          <ul className="divide-y divide-slate-200">
            {team.results.map((r) => (
              <li key={r.id} className="py-2 flex items-center gap-4">
                <span className="font-semibold text-slate-900">{r.date}</span>
                <span className="text-slate-700">{r.home ? "vs" : "@"}</span>
                <span className="font-semibold text-primary">{r.opponent}</span>
                <span className="font-mono text-slate-900">{r.score}</span>
                {r.correct ? (
                  <span className="inline-flex items-center gap-1 text-success font-semibold">
                    ✅
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-error font-semibold">
                    ❌
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      {tab === 2 && (
        <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-lg p-8 border-l-4 border-success/70 hover:shadow-2xl transition-shadow">
          <div className="text-xs uppercase tracking-widest text-slate-700 mb-2 font-semibold">
            Prediction Accuracy
          </div>
          {/* Form Line Graph (mocked) */}
          <div className="w-full h-32 flex items-end gap-1 mb-4">
            {team.form.map((f, i) => (
              <div
                key={i}
                className={`flex-1 rounded-t ${f === "W" ? "bg-success" : f === "D" ? "bg-warning" : "bg-error"}`}
                style={{ height: `${30 + i * 5}px` }}
              />
            ))}
          </div>
          <div className="text-slate-700 text-sm mb-2">
            Last 10 matches:{" "}
            <span className="font-semibold">{team.form.join(" ")}</span>
          </div>
          <div className="text-slate-700 text-sm">
            Model accuracy:{" "}
            <span className="font-semibold text-primary">
              {Math.round(team.accuracy * 100)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
