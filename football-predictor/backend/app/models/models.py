from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from .base import Base
from datetime import datetime

class TeamType(str, enum.Enum):
    CLUB = "club"
    NATIONAL = "national"

class CompetitionType(str, enum.Enum):
    LEAGUE = "league"
    CUP = "cup"
    INTERNATIONAL = "international"

class Club(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    founded_year = Column(Integer)
    stadium_name = Column(String)
    city = Column(String)
    country = Column(String)
    alternative_names = Column(String)  # JSON string of alternative names

    teams = relationship("Team", back_populates="club")
    players = relationship("Player", back_populates="club")

class Player(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date_of_birth = Column(Date)
    nationality = Column(String)
    position = Column(String)
    team_id = Column(Integer, ForeignKey("team.id"), nullable=True)
    club_id = Column(Integer, ForeignKey("club.id"), nullable=True)

    team = relationship("Team", back_populates="players")
    club = relationship("Club", back_populates="players")

class Ground(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    city = Column(String)
    country = Column(String)
    capacity = Column(Integer)

    fixtures = relationship("Fixture", back_populates="ground")

class Group(Base):
    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("season.id"))
    name = Column(String)

    season = relationship("Season", back_populates="groups")
    fixtures = relationship("Fixture", back_populates="group")

class Team(Base):
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("club.id"), nullable=True)
    team_type = Column(Enum(TeamType))

    club = relationship("Club", back_populates="teams")
    home_fixtures = relationship("Fixture", foreign_keys="Fixture.home_team_id", back_populates="home_team")
    away_fixtures = relationship("Fixture", foreign_keys="Fixture.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")

class Competition(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    country = Column(String)
    competition_type = Column(Enum(CompetitionType))

    seasons = relationship("Season", back_populates="competition")

class Season(Base):
    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competition.id"))
    year_start = Column(Integer)
    year_end = Column(Integer)
    season_name = Column(String)

    competition = relationship("Competition", back_populates="seasons")
    fixtures = relationship("Fixture", back_populates="season")
    groups = relationship("Group", back_populates="season")

class Fixture(Base):
    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("season.id"))
    match_date = Column(Date)
    home_team_id = Column(Integer, ForeignKey("team.id"))
    away_team_id = Column(Integer, ForeignKey("team.id"))
    stage = Column(String)
    venue = Column(String)
    is_completed = Column(Boolean, default=False)
    ground_id = Column(Integer, ForeignKey("ground.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("group.id"), nullable=True)

    season = relationship("Season", back_populates="fixtures")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_fixtures")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_fixtures")
    result = relationship("MatchResult", back_populates="fixture", uselist=False)
    ground = relationship("Ground", back_populates="fixtures")
    group = relationship("Group", back_populates="fixtures")

class MatchResult(Base):
    fixture_id = Column(Integer, ForeignKey("fixture.id"), primary_key=True)
    home_score = Column(Integer)
    away_score = Column(Integer)
    extra_time = Column(Boolean, default=False)
    penalties = Column(Boolean, default=False)

    fixture = relationship("Fixture", back_populates="result")

class IngestionAudit(Base):
    __tablename__ = "ingestion_audit"
    id = Column(Integer, primary_key=True, index=True)
    repo = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    hash = Column(String, nullable=False) 