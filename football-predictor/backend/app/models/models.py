from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum, DateTime, Float, Text, Table, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()

class TeamType(str, enum.Enum):
    CLUB = "club"
    NATIONAL = "national"

class CompetitionType(str, enum.Enum):
    LEAGUE = "league"
    CUP = "cup"
    INTERNATIONAL = "international"

class Club(Base):
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    founded_year = Column(Integer, nullable=True)
    stadium_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    alternative_names = Column(String, nullable=True)

    teams = relationship("Team", back_populates="club")
    players = relationship("Player", back_populates="club")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date_of_birth = Column(Date, nullable=True)
    nationality = Column(String, nullable=True)
    position = Column(String, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)

    team = relationship("Team", back_populates="players")
    club = relationship("Club", back_populates="players")

class Ground(Base):
    __tablename__ = "grounds"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    city = Column(String, nullable=True)

    fixtures = relationship("Fixture", back_populates="ground")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"))
    name = Column(String)

    season = relationship("Season", back_populates="groups")
    fixtures = relationship("Fixture", back_populates="group")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    team_type = Column(String)

    club = relationship("Club", back_populates="teams")
    home_fixtures = relationship("Fixture", foreign_keys="Fixture.home_team_id", back_populates="home_team")
    away_fixtures = relationship("Fixture", foreign_keys="Fixture.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")

class Competition(Base):
    __tablename__ = "competitions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    country = Column(String)
    competition_type = Column(String)

    seasons = relationship("Season", back_populates="competition")

class Season(Base):
    __tablename__ = "seasons"
    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"))
    year_start = Column(Integer)
    year_end = Column(Integer, nullable=True)
    season_name = Column(String)

    competition = relationship("Competition", back_populates="seasons")
    fixtures = relationship("Fixture", back_populates="season")
    groups = relationship("Group", back_populates="season")

class Fixture(Base):
    __tablename__ = "fixtures"
    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"))
    match_date = Column(Date)
    match_time = Column(String, nullable=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    stage = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)
    ground_id = Column(Integer, ForeignKey("grounds.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    season = relationship("Season", back_populates="fixtures")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_fixtures")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_fixtures")
    result = relationship("MatchResult", back_populates="fixture", uselist=False)
    ground = relationship("Ground", back_populates="fixtures")
    group = relationship("Group", back_populates="fixtures")
    predictions = relationship("Prediction", back_populates="fixture")

class MatchResult(Base):
    __tablename__ = "match_results"
    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), unique=True)
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

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    home_win_probability = Column(Float)
    draw_probability = Column(Float)
    away_win_probability = Column(Float)
    predicted_home_score = Column(Float, nullable=True)
    predicted_away_score = Column(Float, nullable=True)
    created_at = Column(DateTime)
    actual_home_score = Column(Integer, nullable=True)
    actual_away_score = Column(Integer, nullable=True)

    fixture = relationship("Fixture", back_populates="predictions") 