from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date, datetime, timedelta
from ...core.database import get_db
from ...models.models import Fixture, Club, Team, Season, Competition
from ...schemas.fixture import FixtureRead, FixtureWithTeamNamesRead

router = APIRouter()

@router.get("/", response_model=List[FixtureWithTeamNamesRead])
def get_fixtures(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="upcoming, completed, or all"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    team_id: Optional[int] = Query(None),
    competition_id: Optional[int] = Query(None)
):
    # Default from_date to today if not provided for upcoming fixtures
    if from_date is None and status == "upcoming":
        from_date = date.today()
    
    # Default to_date to 14 days from from_date if not provided for upcoming fixtures
    if to_date is None and status == "upcoming" and from_date:
        to_date = from_date + timedelta(days=14)
    
    # Build the base query with joins for team and club information
    query = db.query(Fixture)
    
    # Apply status filter
    if status == "upcoming":
        # Get upcoming fixtures from the database
        query = query.filter(Fixture.is_completed == False)
        
        # Only include fixtures from today onward
        if from_date:
            query = query.filter(Fixture.match_date >= from_date)
        else:
            query = query.filter(Fixture.match_date >= date.today())
            
        if to_date:
            query = query.filter(Fixture.match_date <= to_date)
        
        # Apply competition filter if provided
        if competition_id:
            # Join Season to filter by competition_id
            query = query.join(Season).filter(Season.competition_id == competition_id)
        
        # Join related tables and load them eagerly for better performance
        query = query.options(
            joinedload(Fixture.season).joinedload(Season.competition),
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        )
        
        # Order by match date and time
        query = query.order_by(Fixture.match_date, Fixture.match_time)
        
        # Get fixtures with pagination
        fixtures = query.offset(skip).limit(limit).all()
        
        # Create result list with complete team and competition information
        result = []
        for fixture in fixtures:
            # Get team and competition names from the loaded relationships
            home_team_name = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else f"Team {fixture.home_team_id}"
            away_team_name = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else f"Team {fixture.away_team_id}"
            
            competition_name = None
            competition_country = None
            if fixture.season and fixture.season.competition:
                competition_name = fixture.season.competition.name
                competition_country = fixture.season.competition.country
            
            # Create fixture with team names
            fixture_dict = {
                "id": fixture.id,
                "season_id": fixture.season_id,
                "match_date": fixture.match_date,
                "match_time": fixture.match_time or "15:00",
                "home_team_id": fixture.home_team_id,
                "away_team_id": fixture.away_team_id,
                "stage": fixture.stage or "Regular Season",
                "venue": fixture.venue,
                "is_completed": fixture.is_completed,
                "ground_id": fixture.ground_id,
                "group_id": fixture.group_id,
                "home_team_name": home_team_name,
                "away_team_name": away_team_name,
                # Add additional info for frontend display
                "competition_name": competition_name,
                "competition_country": competition_country
            }
            
            result.append(fixture_dict)
        
        return result
    
    elif status == "completed":
        query = query.filter(Fixture.is_completed == True)
    
    # Apply date filters
    if from_date:
        query = query.filter(Fixture.match_date >= from_date)
    if to_date:
        query = query.filter(Fixture.match_date <= to_date)
    
    # Apply team filter
    if team_id:
        query = query.filter((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
    
    # Apply competition filter
    if competition_id:
        query = query.join(Season).filter(Season.competition_id == competition_id)
    
    # Join related tables for better performance
    query = query.options(
        joinedload(Fixture.season).joinedload(Season.competition),
        joinedload(Fixture.home_team).joinedload(Team.club),
        joinedload(Fixture.away_team).joinedload(Team.club)
    )
    
    # Order by match date
    query = query.order_by(Fixture.match_date)
    
    # Get fixtures
    fixtures = query.offset(skip).limit(limit).all()
    
    # Create result list
    result = []
    
    # Process each fixture
    for fixture in fixtures:
        # Get team and competition names from the loaded relationships
        home_team_name = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else f"Team {fixture.home_team_id}"
        away_team_name = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else f"Team {fixture.away_team_id}"
        
        competition_name = None
        competition_country = None
        if fixture.season and fixture.season.competition:
            competition_name = fixture.season.competition.name
            competition_country = fixture.season.competition.country
        
        # Create fixture with team names
        fixture_dict = {
            "id": fixture.id,
            "season_id": fixture.season_id,
            "match_date": fixture.match_date,
            "home_team_id": fixture.home_team_id,
            "away_team_id": fixture.away_team_id,
            "stage": fixture.stage or "Regular Season",
            "venue": fixture.venue,
            "is_completed": fixture.is_completed,
            "ground_id": fixture.ground_id,
            "group_id": fixture.group_id,
            "home_team_name": home_team_name,
            "away_team_name": away_team_name,
            "match_time": fixture.match_time or "15:00",
            "competition_name": competition_name,
            "competition_country": competition_country
        }
        
        result.append(fixture_dict)
    
    return result

@router.get("/competitions", response_model=List[dict])
def get_fixture_competitions(db: Session = Depends(get_db)):
    """Get all competitions that have fixtures"""
    # Query competitions that have seasons with fixtures
    competitions = (
        db.query(Competition)
        .join(Season)
        .join(Fixture)
        .distinct()
        .all()
    )
    
    return [
        {
            "id": comp.id,
            "name": comp.name,
            "country": comp.country,
            "competition_type": comp.competition_type
        }
        for comp in competitions
    ]

# Add fixtures endpoints here 