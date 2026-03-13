"""Community leaderboard endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.community import LeaderboardEntry, LeaderboardOut, MyRank
from app.api.deps import get_current_user
from app.services.leaderboard_service import get_leaderboard, get_my_rank, update_leaderboard

router = APIRouter(prefix="/community", tags=["Community"])


@router.get("/leaderboard", response_model=LeaderboardOut)
def leaderboard(top_n: int = 20, db: Session = Depends(get_db)):
    entries = get_leaderboard(db, top_n)
    return LeaderboardOut(
        entries=[LeaderboardEntry(**e) for e in entries],
        total=len(entries),
    )


@router.get("/my-rank", response_model=MyRank)
def my_rank(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Update first, then fetch
    update_leaderboard(user, db)
    result = get_my_rank(user.id, db)
    return MyRank(**result)
