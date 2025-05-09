// Mock data for demo
const standings = [
  {
    pos: 1,
    team: 'Arsenal',
    crest: 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg',
    played: 36,
    won: 25,
    drawn: 7,
    lost: 4,
    points: 82,
    form: ['W', 'W', 'D', 'W', 'W'],
  },
  {
    pos: 2,
    team: 'Man City',
    crest: 'https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg',
    played: 36,
    won: 24,
    drawn: 8,
    lost: 4,
    points: 80,
    form: ['W', 'D', 'W', 'W', 'W'],
  },
  {
    pos: 3,
    team: 'Liverpool',
    crest: 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg',
    played: 36,
    won: 22,
    drawn: 10,
    lost: 4,
    points: 76,
    form: ['L', 'W', 'D', 'W', 'W'],
  },
  {
    pos: 4,
    team: 'Chelsea',
    crest: 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg',
    played: 36,
    won: 20,
    drawn: 9,
    lost: 7,
    points: 69,
    form: ['W', 'L', 'W', 'D', 'W'],
  },
];

export default function Standings() {
  return (
    <div className="w-full px-4 md:px-8 py-10 max-w-screen-lg mx-auto grid gap-10">
      <h1 className="text-2xl font-bold text-primary mb-4">League Standings</h1>
      <div className="bg-gradient-to-br from-surface-alt to-surface/80 rounded-2xl shadow-2xl p-10 border-l-8 border-primary/80 hover:scale-[1.01] hover:shadow-2xl transition-transform duration-200">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-slate-700 border-b">
                <th className="p-2 text-left">#</th>
                <th className="p-2 text-left">Team</th>
                <th className="p-2 text-left">P</th>
                <th className="p-2 text-left">W</th>
                <th className="p-2 text-left">D</th>
                <th className="p-2 text-left">L</th>
                <th className="p-2 text-left">Pts</th>
                <th className="p-2 text-left">Form</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((t) => (
                <tr key={t.team} className={`border-b last:border-0 hover:bg-primary/10 transition duration-150 cursor-pointer ${t.pos === 1 ? 'bg-primary/10' : ''}`}>
                  <td className="p-2 font-bold text-slate-700">{t.pos}</td>
                  <td className="p-2 flex items-center gap-2">
                    <img src={t.crest} alt={t.team} className="w-6 h-6" />
                    <span className="font-semibold text-slate-900">{t.team}</span>
                  </td>
                  <td className="p-2">{t.played}</td>
                  <td className="p-2">{t.won}</td>
                  <td className="p-2">{t.drawn}</td>
                  <td className="p-2">{t.lost}</td>
                  <td className="p-2 font-bold text-primary">{t.points}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      {t.form.map((f, i) => (
                        <span key={i} className={`px-2 py-1 rounded text-xs font-bold shadow-sm transition-colors duration-150 ${f === 'W' ? 'bg-success/90 text-white hover:bg-success' : f === 'D' ? 'bg-warning/90 text-white hover:bg-warning' : 'bg-error/90 text-white hover:bg-error'}`}>{f}</span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 