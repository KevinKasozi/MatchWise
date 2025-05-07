from fastapi import APIRouter
from .endpoints import clubs, teams, competitions, fixtures, predictions, grounds, groups, players

router = APIRouter()

router.include_router(clubs.router, prefix="/clubs", tags=["clubs"])
router.include_router(teams.router, prefix="/teams", tags=["teams"])
router.include_router(competitions.router, prefix="/competitions", tags=["competitions"])
router.include_router(fixtures.router, prefix="/fixtures", tags=["fixtures"])
router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
router.include_router(grounds.router, prefix="/grounds", tags=["grounds"])
router.include_router(groups.router, prefix="/groups", tags=["groups"])
router.include_router(players.router, prefix="/players", tags=["players"]) 