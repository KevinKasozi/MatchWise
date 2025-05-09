import * as Tabs from '@radix-ui/react-tabs';

// Mock data
const favoriteTeams = [
  {
    name: 'Arsenal',
    crest: 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg',
    league: 'Premier League',
    position: 1,
    points: 82,
  },
  {
    name: 'Barcelona',
    crest: 'https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg',
    league: 'La Liga',
    position: 2,
    points: 78,
  },
];

const favoritePlayers = [
  {
    name: 'Erling Haaland',
    photo: 'https://upload.wikimedia.org/wikipedia/commons/5/5e/Erling_Haaland_2023.jpg',
    team: 'Man City',
    goals: 28,
    assists: 7,
  },
  {
    name: 'Bukayo Saka',
    photo: 'https://upload.wikimedia.org/wikipedia/commons/8/8e/Bukayo_Saka_2022.jpg',
    team: 'Arsenal',
    goals: 15,
    assists: 10,
  },
];

const favoriteCompetitions = [
  {
    name: 'Premier League',
    logo: 'https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg',
    country: 'England',
    teams: 20,
  },
  {
    name: 'Champions League',
    logo: 'https://upload.wikimedia.org/wikipedia/en/b/bf/UEFA_Champions_League_logo_2.svg',
    country: 'Europe',
    teams: 32,
  },
];

export default function Favorites() {
  return (
    <div className="w-full px-4 md:px-8 py-8 max-w-screen-lg mx-auto grid gap-8">
      <h1 className="text-2xl font-bold text-primary mb-4">My Favorites</h1>
      <Tabs.Root defaultValue="teams" className="w-full">
        <Tabs.List className="flex gap-2 mb-4">
          <Tabs.Trigger value="teams" className="px-5 py-2 rounded-lg font-semibold text-primary bg-white/90 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white data-[state=active]:shadow transition">Teams</Tabs.Trigger>
          <Tabs.Trigger value="players" className="px-5 py-2 rounded-lg font-semibold text-primary bg-white/90 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white data-[state=active]:shadow transition">Players</Tabs.Trigger>
          <Tabs.Trigger value="competitions" className="px-5 py-2 rounded-lg font-semibold text-primary bg-white/90 shadow border border-primary-light data-[state=active]:bg-primary data-[state=active]:text-white data-[state=active]:shadow transition">Competitions</Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="teams">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {favoriteTeams.map((team) => (
              <div key={team.name} className="bg-white/90 rounded-2xl shadow p-6 border border-slate-100 flex items-center gap-4 hover:shadow-lg transition-shadow">
                <img src={team.crest} alt={team.name} className="w-12 h-12" />
                <div>
                  <div className="font-bold text-lg text-slate-900">{team.name}</div>
                  <div className="text-sm text-slate-600">{team.league}</div>
                  <div className="text-xs mt-1 text-slate-500">Pos: <span className="font-semibold">{team.position}</span> | Pts: <span className="font-semibold">{team.points}</span></div>
                </div>
              </div>
            ))}
          </div>
        </Tabs.Content>
        <Tabs.Content value="players">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {favoritePlayers.map((player) => (
              <div key={player.name} className="bg-white/90 rounded-2xl shadow p-6 border border-slate-100 flex items-center gap-4 hover:shadow-lg transition-shadow">
                <img src={player.photo} alt={player.name} className="w-12 h-12 rounded-full object-cover" />
                <div>
                  <div className="font-bold text-lg text-slate-900">{player.name}</div>
                  <div className="text-sm text-slate-600">{player.team}</div>
                  <div className="text-xs mt-1 text-slate-500">Goals: <span className="font-semibold">{player.goals}</span> | Assists: <span className="font-semibold">{player.assists}</span></div>
                </div>
              </div>
            ))}
          </div>
        </Tabs.Content>
        <Tabs.Content value="competitions">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {favoriteCompetitions.map((comp) => (
              <div key={comp.name} className="bg-white/90 rounded-2xl shadow p-6 border border-slate-100 flex items-center gap-4 hover:shadow-lg transition-shadow">
                <img src={comp.logo} alt={comp.name} className="w-12 h-12" />
                <div>
                  <div className="font-bold text-lg text-slate-900">{comp.name}</div>
                  <div className="text-sm text-slate-600">{comp.country}</div>
                  <div className="text-xs mt-1 text-slate-500">Teams: <span className="font-semibold">{comp.teams}</span></div>
                </div>
              </div>
            ))}
          </div>
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
} 