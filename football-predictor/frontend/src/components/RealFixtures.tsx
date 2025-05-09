import { useState, useEffect } from "react";
import { Tab } from "@headlessui/react";
import { apiClient } from "../api/client";
import type { Fixture } from "../types/api";

// Define types for our fixture display
interface FixtureDisplay {
  id: number;
  home_team: string;
  away_team: string;
  time: string;
  competition: string;
  country: string;
  date: Date;
}

interface FixturesByCompetition {
  [key: string]: FixtureDisplay[];
}

// Club badge mappings - teams to their respective badges
const CLUB_BADGES: { [key: string]: string } = {
  // Premier League
  "Arsenal FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t3.svg",
  "Aston Villa FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t7.svg",
  Bournemouth:
    "https://resources.premierleague.com/premierleague/badges/rb/t91.svg",
  "AFC Bournemouth":
    "https://resources.premierleague.com/premierleague/badges/rb/t91.svg",
  "Brentford FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t94.svg",
  Brighton:
    "https://resources.premierleague.com/premierleague/badges/rb/t36.svg",
  "Brighton & Hove Albion FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t36.svg",
  "Chelsea FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t8.svg",
  "Crystal Palace FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t31.svg",
  "Everton FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t11.svg",
  "Fulham FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t54.svg",
  "Ipswich Town FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t213.svg",
  "Leicester City FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t13.svg",
  "Liverpool FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t14.svg",
  "Manchester City FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t43.svg",
  "Manchester United FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t1.svg",
  "Newcastle United FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t4.svg",
  "Nottingham Forest FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t17.svg",
  "Southampton FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t20.svg",
  "Tottenham Hotspur FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t6.svg",
  "West Ham United FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t21.svg",
  "Wolverhampton Wanderers FC":
    "https://resources.premierleague.com/premierleague/badges/rb/t39.svg",

  // La Liga
  "Real Madrid":
    "https://assets.laliga.com/assets/2019/06/07/originals/2b14e21ea4db95ab2a6eeb6c1951c25e.png",
  "Real Madrid CF":
    "https://assets.laliga.com/assets/2019/06/07/originals/2b14e21ea4db95ab2a6eeb6c1951c25e.png",
  Barcelona:
    "https://assets.laliga.com/assets/2019/06/07/originals/7bb91585e0ec1a4d0403b4cdc55e4606.png",
  "FC Barcelona":
    "https://assets.laliga.com/assets/2019/06/07/originals/7bb91585e0ec1a4d0403b4cdc55e4606.png",
  "Atlético Madrid":
    "https://assets.laliga.com/assets/2019/06/07/originals/63288b6c6a6671f167a0fd48be1e4.png",
  "Club Atlético de Madrid":
    "https://assets.laliga.com/assets/2019/06/07/originals/63288b6c6a6671f167a0fd48be1e4.png",
  "Valencia CF":
    "https://assets.laliga.com/assets/2019/06/07/originals/e6a0ad5a7b4d1e2e99a84a7ef903dced.png",
  Sevilla:
    "https://assets.laliga.com/assets/2019/06/07/originals/b499b06a8517644ee077f84bb9f3702d.png",
  "Sevilla FC":
    "https://assets.laliga.com/assets/2019/06/07/originals/b499b06a8517644ee077f84bb9f3702d.png",
  "Villarreal CF":
    "https://assets.laliga.com/assets/2019/06/07/originals/eccbf3095b565f2abe4af3a882c2d5d5.png",
  "Real Sociedad":
    "https://assets.laliga.com/assets/2019/06/07/originals/b5f5c2fa7b2c5c2e97fa7392139b2ba8.png",
  "CA Osasuna":
    "https://assets.laliga.com/assets/2019/06/07/originals/6a079a94b646cfcd5581a22f7318f5bb.png",
  "Girona FC":
    "https://assets.laliga.com/assets/2021/06/18/thumbs/34d351688a6a6f22932d9d5e88c3169d.jpeg",
  "Getafe CF":
    "https://assets.laliga.com/assets/2019/06/07/originals/2b974a92a91c95d0cfe73d29b9cec26c.png",
  "Rayo Vallecano":
    "https://assets.laliga.com/assets/2019/06/07/originals/ac09f9da3a56ea276aaf37e76b36e989.png",
  "UD Las Palmas":
    "https://assets.laliga.com/assets/2023/08/15/medium/82acc96f0b50c3d25f55f87c32ef0f95.jpeg",
  "Cádiz CF":
    "https://assets.laliga.com/assets/2020/07/21/medium/c1feb3162fb3f931126dcad0f12d3314.jpeg",
  "UD Almería":
    "https://assets.laliga.com/assets/2022/06/19/medium/ea2a69a7ebc08218f996ff5cb188df04.jpeg",

  // Bundesliga
  "FC Bayern München":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/Bayern-Muenchen.png",
  "Borussia Dortmund":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/Borussia-Dortmund.png",
  "RB Leipzig":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/RB-Leipzig.png",
  "Borussia Mönchengladbach":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/Borussia-Moenchengladbach.png",
  "Bayer 04 Leverkusen":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/Bayer-04-Leverkusen.png",
  "SV Werder Bremen":
    "https://images.bundesliga.com/tachyon/sites/2/2022/01/Werder-Bremen-1.png",
  "VfB Stuttgart":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/VfB-Stuttgart.png",
  "Eintracht Frankfurt":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/Eintracht-Frankfurt.png",
  "VfL Wolfsburg":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/VfL-Wolfsburg.png",
  "TSG 1899 Hoffenheim":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/TSG-Hoffenheim.png",
  "FC Augsburg":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/FC-Augsburg.png",
  "1. FC Köln":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/1-FC-Koeln.png",
  "1. FC Nürnberg":
    "https://images.bundesliga.com/tachyon/sites/2/2019/11/1-FC-Nuernberg.png",
  "1. FC Heidenheim":
    "https://images.bundesliga.com/tachyon/sites/2/2023/06/1.-FC-Heidenheim.png",
  "Holstein Kiel":
    "https://images.bundesliga.com/tachyon/sites/2/2023/06/Holstein-Kiel.png",

  // Serie A
  "AC Milan": "https://img.legaseriea.it/vimages/629c0d58/milan.png",
  "Inter Milan": "https://img.legaseriea.it/vimages/62a0b75b/inter.png",
  "Juventus FC": "https://img.legaseriea.it/vimages/62a0b76a/juventus.png",
  "SS Lazio": "https://img.legaseriea.it/vimages/629c0d50/lazio.png",
  "AS Roma": "https://img.legaseriea.it/vimages/629c0d06/roma.png",
  Napoli: "https://img.legaseriea.it/vimages/62a0b768/napoli.png",
  "Cagliari Calcio": "https://img.legaseriea.it/vimages/629c0cf9/cagliari.png",
  "Como 1907": "https://img.legaseriea.it/vimages/64fd1b87/como.png",
  "Bologna FC": "https://img.legaseriea.it/vimages/629c0cf3/bologna.png",
  "Parma Calcio 1913": "https://img.legaseriea.it/vimages/64fd1b8b/parma.png",
  "Empoli FC": "https://img.legaseriea.it/vimages/629c0d00/empoli.png",
  "AS Cittadella": "https://img.legaseriea.it/vimages/629c0cf5/cittadella.png",
  "SSC Bari": "https://img.legaseriea.it/vimages/629c0cef/bari.png",

  // Ligue 1
  "Paris Saint-Germain":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/14.png",
  "Olympique Lyonnais":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/753.png",
  "Olympique de Marseille":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/19.png",
  "AS Monaco":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/415.png",
  "LOSC Lille":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/487.png",
  "Stade Rennais FC":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/16.png",
  "RC Strasbourg":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/20.png",
  "FC Nantes":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/12.png",
  "Olympique Marseille":
    "https://www.ligue1.com/-/media/Project/LFP/shared/Images/Clubs/2022-2023/Small/19.png",

  // Champions League
  Chelsea: "https://resources.premierleague.com/premierleague/badges/rb/t8.svg",
  "Manchester City":
    "https://resources.premierleague.com/premierleague/badges/rb/t43.svg",
};

export default function RealFixtures() {
  const [selectedTab, setSelectedTab] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [fixturesByDate, setFixturesByDate] = useState<{
    [key: string]: FixturesByCompetition;
  }>({});
  const [error, setError] = useState<string | null>(null);

  // Get fixtures from API
  useEffect(() => {
    const fetchFixtures = async () => {
      setLoading(true);
      try {
        const response = await apiClient.get<Fixture[]>("/fixtures", {
          params: {
            status: "upcoming",
            limit: 100,
          },
        });

        // Process the fixtures
        processFixtures(response.data);
      } catch (err) {
        console.error("Error fetching fixtures:", err);
        setError("Failed to load fixtures. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchFixtures();
  }, []);

  // Process fixtures into a more usable format
  const processFixtures = (fixtures: Fixture[]) => {
    // Group fixtures by date
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const dayAfterTomorrow = new Date(today);
    dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);

    // Initialize fixture groups for today and tomorrow
    const fixturesByDateResult: { [key: string]: FixturesByCompetition } = {
      today: {},
      tomorrow: {},
      future: {},
    };

    // Process each fixture
    fixtures.forEach((fixture) => {
      // Parse fixture date
      const fixtureDate = new Date(fixture.match_date);
      fixtureDate.setHours(0, 0, 0, 0);

      // Determine which group this fixture belongs to
      let dateKey: string;
      if (fixtureDate.getTime() === today.getTime()) {
        dateKey = "today";
      } else if (fixtureDate.getTime() === tomorrow.getTime()) {
        dateKey = "tomorrow";
      } else {
        dateKey = "future";
      }

      // Format the competition name with country for grouping
      const competitionKey = fixture.competition_name
        ? `${fixture.competition_country || "Unknown"} - ${fixture.competition_name}`
        : "Other Matches";

      // Initialize competition array if it doesn't exist
      if (!fixturesByDateResult[dateKey][competitionKey]) {
        fixturesByDateResult[dateKey][competitionKey] = [];
      }

      // Add fixture to the appropriate competition group
      fixturesByDateResult[dateKey][competitionKey].push({
        id: fixture.id,
        home_team: fixture.home_team_name,
        away_team: fixture.away_team_name,
        time: fixture.match_time || "15:00",
        competition: fixture.competition_name || "Unknown",
        country: fixture.competition_country || "Unknown",
        date: fixtureDate,
      });
    });

    // Sort fixtures by time within each competition
    for (const dateKey in fixturesByDateResult) {
      for (const compKey in fixturesByDateResult[dateKey]) {
        fixturesByDateResult[dateKey][compKey].sort((a, b) => {
          return a.time.localeCompare(b.time);
        });
      }
    }

    setFixturesByDate(fixturesByDateResult);
  };

  // Helper function to get team logo
  const getTeamLogo = (teamName: string) => {
    // First try to get the exact team name from our badge mapping
    if (CLUB_BADGES[teamName]) {
      return CLUB_BADGES[teamName];
    }

    // Try to find partial matches for teams with slight naming differences
    const partialMatch = Object.keys(CLUB_BADGES).find(
      (key) => teamName.includes(key) || key.includes(teamName),
    );

    if (partialMatch) {
      return CLUB_BADGES[partialMatch];
    }

    // As a fallback, use the first letter of the team name for a placeholder
    const initial = teamName.charAt(0).toUpperCase();
    const colorMap: { [key: string]: string } = {
      A: "1e40af",
      B: "1d4ed8",
      C: "2563eb",
      D: "3b82f6",
      E: "60a5fa",
      F: "93c5fd",
      G: "0f766e",
      H: "0d9488",
      I: "14b8a6",
      J: "06b6d4",
      K: "0ea5e9",
      L: "0284c7",
      M: "7e22ce",
      N: "6d28d9",
      O: "8b5cf6",
      P: "a855f7",
      Q: "c026d3",
      R: "d946ef",
      S: "e11d48",
      T: "be123c",
      U: "db2777",
      V: "ea580c",
      W: "c2410c",
      X: "a16207",
      Y: "65a30d",
      Z: "4d7c0f",
    };

    const bgColor = colorMap[initial] || "1e3a8a";
    return `https://placehold.co/100x100/${bgColor}/ffffff?text=${initial}`;
  };

  // Get color for competition badge
  const getCompetitionColor = (competition: string) => {
    if (competition.includes("Premier League")) {
      return "bg-blue-100 text-blue-800";
    } else if (competition.includes("La Liga")) {
      return "bg-red-100 text-red-800";
    } else if (competition.includes("Bundesliga")) {
      return "bg-amber-100 text-amber-800";
    } else if (competition.includes("Serie A")) {
      return "bg-indigo-100 text-indigo-800";
    } else if (competition.includes("Ligue 1")) {
      return "bg-green-100 text-green-800";
    } else if (competition.includes("Champions League")) {
      return "bg-purple-100 text-purple-800";
    } else if (competition.includes("Europa League")) {
      return "bg-orange-100 text-orange-800";
    } else {
      return "bg-gray-100 text-gray-800";
    }
  };

  const renderFixtures = (fixturesByCompetition: FixturesByCompetition) => {
    if (Object.keys(fixturesByCompetition).length === 0) {
      return (
        <div className="bg-white rounded shadow p-8 text-center border border-gray-100">
          <p className="text-gray-500">No fixtures found for this day.</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {Object.entries(fixturesByCompetition).map(
          ([competitionName, fixtures]) => (
            <div
              key={competitionName}
              className="bg-white rounded-lg shadow overflow-hidden"
            >
              <div className="flex justify-between items-center bg-gray-50 p-4 border-b">
                <h2 className="text-lg font-medium text-gray-800">
                  {competitionName}
                </h2>
                <span
                  className={`px-2 py-1 text-xs rounded-full font-medium ${getCompetitionColor(competitionName)}`}
                >
                  {fixtures.length} match{fixtures.length !== 1 ? "es" : ""}
                </span>
              </div>

              <div className="divide-y">
                {fixtures.map((fixture) => (
                  <div
                    key={fixture.id}
                    className="p-4 hover:bg-blue-50 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-4 flex-1">
                        <div className="flex items-center space-x-3 text-right flex-1">
                          <div className="text-right flex-1">
                            <span className="font-medium text-gray-800">
                              {fixture.home_team}
                            </span>
                          </div>
                          <img
                            src={getTeamLogo(fixture.home_team)}
                            alt={fixture.home_team}
                            className="w-10 h-10 object-contain"
                          />
                        </div>

                        <div className="flex flex-col items-center justify-center min-w-[60px]">
                          <div className="bg-gray-100 rounded-lg px-3 py-1 text-sm font-bold text-gray-800 min-w-[60px] text-center">
                            <span>vs</span>
                          </div>
                          <span className="text-xs text-gray-500 mt-1">
                            {fixture.time}
                          </span>
                        </div>

                        <div className="flex items-center space-x-3 flex-1">
                          <img
                            src={getTeamLogo(fixture.away_team)}
                            alt={fixture.away_team}
                            className="w-10 h-10 object-contain"
                          />
                          <div className="flex-1">
                            <span className="font-medium text-gray-800">
                              {fixture.away_team}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ),
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="w-full p-4 space-y-4">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="animate-pulse bg-slate-100 rounded-2xl h-24 mb-4"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md border border-red-200 text-red-600">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Real Upcoming Fixtures</h1>
      <p className="text-gray-600 mb-4">
        These are actual fixtures from major football leagues around the world.
      </p>

      <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
        <Tab.List className="flex space-x-2 mb-6">
          <Tab
            className={({ selected }) =>
              `px-4 py-2 rounded font-medium text-sm focus:outline-none transition-colors ${
                selected
                  ? "bg-blue-600 text-white"
                  : "bg-white text-blue-600 border border-blue-300 hover:bg-blue-50"
              }`
            }
          >
            Today
          </Tab>
          <Tab
            className={({ selected }) =>
              `px-4 py-2 rounded font-medium text-sm focus:outline-none transition-colors ${
                selected
                  ? "bg-blue-600 text-white"
                  : "bg-white text-blue-600 border border-blue-300 hover:bg-blue-50"
              }`
            }
          >
            Tomorrow
          </Tab>
          <Tab
            className={({ selected }) =>
              `px-4 py-2 rounded font-medium text-sm focus:outline-none transition-colors ${
                selected
                  ? "bg-blue-600 text-white"
                  : "bg-white text-blue-600 border border-blue-300 hover:bg-blue-50"
              }`
            }
          >
            Upcoming
          </Tab>
        </Tab.List>

        <Tab.Panels>
          <Tab.Panel>{renderFixtures(fixturesByDate["today"] || {})}</Tab.Panel>
          <Tab.Panel>
            {renderFixtures(fixturesByDate["tomorrow"] || {})}
          </Tab.Panel>
          <Tab.Panel>
            {renderFixtures(fixturesByDate["future"] || {})}
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}
