import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from ..models.models import (
    Club, Team, Competition, Season, Fixture, MatchResult, Player, Ground, Group,
    TeamType, CompetitionType
)
from ..core.config import settings

class OpenFootballParser:
    def __init__(self, db: Session):
        self.db = db
        self.club_mapping: Dict[str, int] = {}
        self.team_mapping: Dict[str, int] = {}
        self.competition_mapping: Dict[str, int] = {}
        self.ground_mapping: Dict[str, int] = {}
        self.group_mapping: Dict[str, int] = {}

    def parse_clubs(self) -> None:
        """Parse club data from OpenFootball clubs directory."""
        clubs_path = os.path.join(settings.CLUBS_DATA_PATH)
        for country_dir in os.listdir(clubs_path):
            country_path = os.path.join(clubs_path, country_dir)
            if os.path.isdir(country_path):
                for club_file in os.listdir(country_path):
                    if club_file.endswith('.txt'):
                        self._parse_club_file(os.path.join(country_path, club_file), country_dir)

    def _parse_club_file(self, file_path: str, country: str) -> None:
        """Parse individual club file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        club_name = os.path.splitext(os.path.basename(file_path))[0]
        # Optionally parse stadium/ground info from club file
        stadium_name = None
        city = None
        for line in lines:
            if line.lower().startswith('stadium:'):
                stadium_name = line.split(':', 1)[1].strip()
            if line.lower().startswith('city:'):
                city = line.split(':', 1)[1].strip()
        club = Club(
            name=club_name,
            country=country,
            alternative_names=json.dumps([club_name]),
            stadium_name=stadium_name,
            city=city
        )
        self.db.add(club)
        self.db.flush()
        self.club_mapping[club_name] = club.id
        # Optionally create ground if stadium info is present
        if stadium_name:
            ground = self._get_or_create_ground(stadium_name, city, country)
            # Optionally link club to ground (not in schema, but can be used for mapping)

    def _get_or_create_ground(self, name: str, city: Optional[str], country: Optional[str]) -> int:
        if name in self.ground_mapping:
            return self.ground_mapping[name]
        ground = Ground(name=name, city=city, country=country)
        self.db.add(ground)
        self.db.flush()
        self.ground_mapping[name] = ground.id
        return ground.id

    def parse_groups(self, season_id: int, group_names: List[str]) -> Dict[str, int]:
        """Create groups for a season and return mapping."""
        mapping = {}
        for group_name in group_names:
            group = Group(season_id=season_id, name=group_name)
            self.db.add(group)
            self.db.flush()
            self.group_mapping[group_name] = group.id
            mapping[group_name] = group.id
        return mapping

    def parse_match(self, season_id: int, match_data: Dict) -> None:
        """Parse match data and create fixture with result."""
        home_team_id = self._get_or_create_team(match_data['home_team'])
        away_team_id = self._get_or_create_team(match_data['away_team'])
        # Ground
        ground_id = None
        if 'venue' in match_data and match_data['venue']:
            ground_id = self._get_or_create_ground(match_data['venue'], match_data.get('city'), match_data.get('country'))
        # Group
        group_id = None
        if 'group' in match_data and match_data['group']:
            group_id = self.group_mapping.get(match_data['group'])
        fixture = Fixture(
            season_id=season_id,
            match_date=datetime.strptime(match_data['date'], '%Y-%m-%d').date(),
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            stage=match_data.get('stage', 'Regular Season'),
            venue=match_data.get('venue'),
            is_completed=True,
            ground_id=ground_id,
            group_id=group_id
        )
        self.db.add(fixture)
        self.db.flush()
        if 'score' in match_data:
            home_score, away_score = map(int, match_data['score'].split('-'))
            result = MatchResult(
                fixture_id=fixture.id,
                home_score=home_score,
                away_score=away_score,
                extra_time=match_data.get('extra_time', False),
                penalties=match_data.get('penalties', False)
            )
            self.db.add(result)

    def _get_or_create_team(self, team_name: str) -> int:
        if team_name in self.team_mapping:
            return self.team_mapping[team_name]
        club_id = self.club_mapping.get(team_name)
        team_type = TeamType.CLUB if club_id else TeamType.NATIONAL
        team = Team(club_id=club_id, team_type=team_type)
        self.db.add(team)
        self.db.flush()
        self.team_mapping[team_name] = team.id
        return team.id

    def parse_players(self) -> None:
        players_path = os.path.join(settings.PLAYERS_DATA_PATH)
        for country_dir in os.listdir(players_path):
            country_path = os.path.join(players_path, country_dir)
            if os.path.isdir(country_path):
                for player_file in os.listdir(country_path):
                    if player_file.endswith('.txt'):
                        self._parse_player_file(os.path.join(country_path, player_file), country_dir)

    def _parse_player_file(self, file_path: str, country: Optional[str] = None) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        player_name = os.path.splitext(os.path.basename(file_path))[0]
        # Try to infer club from directory or file naming
        club_id = None
        if country:
            # If directory structure is .../clubs/<country>/<club>/<player>.txt
            club_name = os.path.basename(os.path.dirname(file_path))
            club_id = self.club_mapping.get(club_name)
        player = Player(
            name=player_name,
            nationality=lines[0].strip() if lines else None,
            position=lines[1].strip() if len(lines) > 1 else None,
            club_id=club_id
        )
        self.db.add(player) 