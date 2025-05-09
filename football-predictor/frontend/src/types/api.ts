export interface Club {
  id: number;
  name: string;
  founded_year?: number;
  stadium_name?: string;
  city?: string;
  country?: string;
  alternative_names?: string;
}

export interface Team {
  id: number;
  club_id?: number;
  team_type: 'club' | 'national';
}

export interface Competition {
  id: number;
  name: string;
  country: string;
  competition_type: 'league' | 'cup' | 'international';
}

export interface Season {
  id: number;
  competition_id: number;
  year_start: number;
  year_end: number;
  season_name: string;
}

export interface Fixture {
  id: number;
  season_id: number;
  match_date: string;
  match_time?: string;
  home_team_id: number;
  away_team_id: number;
  stage: string;
  venue?: string;
  is_completed: boolean;
  home_team_name: string;
  away_team_name: string;
  ground_id?: number;
  group_id?: number;
  competition_name?: string;
  competition_country?: string;
}

export interface MatchResult {
  fixture_id: number;
  home_score: number;
  away_score: number;
  extra_time: boolean;
  penalties: boolean;
}

export interface Player {
  id: number;
  name: string;
  date_of_birth?: string;
  nationality?: string;
  position?: string;
  team_id: number;
}

export interface Prediction {
  fixture_id: number;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  predicted_home_score?: number;
  predicted_away_score?: number;
} 