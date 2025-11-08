import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Gamification Demo API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Demo-only data (in-memory)
# Note: This is read-only, non-persistent mock data for demo purposes.
# -----------------------------
class DemoUser(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None
    title: str = "Player"

class DemoBadge(BaseModel):
    id: str
    name: str
    description: str
    icon: str = "Star"
    color: str = "#6366F1"  # indigo-500

class DemoLeaderboardEntry(BaseModel):
    user: DemoUser
    points: int = Field(ge=0)
    level: int = Field(ge=1)
    rank: int = Field(ge=1)

class DemoUserSummary(BaseModel):
    user: DemoUser
    points: int
    level: int
    streak_days: int
    badges: List[DemoBadge] = []
    recent_actions: List[str] = []


# Sample demo dataset
_DEMO_USERS: List[DemoUser] = [
    DemoUser(id="u_001", name="Alex Morgan", avatar=None, title="Sales Captain"),
    DemoUser(id="u_002", name="Jamie Lee", avatar=None, title="Ops Strategist"),
    DemoUser(id="u_003", name="Riley Chen", avatar=None, title="Product Ace"),
    DemoUser(id="u_004", name="Jordan Patel", avatar=None, title="CX Pro"),
]

_DEMO_BADGES: List[DemoBadge] = [
    DemoBadge(id="b_hero", name="Hero", description="Top performer of the week", icon="Trophy", color="#F59E0B"),
    DemoBadge(id="b_streak", name="Streak", description="7-day activity streak", icon="Flame", color="#EF4444"),
    DemoBadge(id="b_helper", name="Mentor", description="Helped 5 teammates", icon="Handshake", color="#10B981"),
]

_DEMO_LEADERBOARD: List[DemoLeaderboardEntry] = [
    DemoLeaderboardEntry(user=_DEMO_USERS[0], points=18250, level=12, rank=1),
    DemoLeaderboardEntry(user=_DEMO_USERS[1], points=16940, level=11, rank=2),
    DemoLeaderboardEntry(user=_DEMO_USERS[2], points=15100, level=10, rank=3),
    DemoLeaderboardEntry(user=_DEMO_USERS[3], points=13320, level=9, rank=4),
]

_DEMO_USER_DETAILS = {
    "u_001": DemoUserSummary(
        user=_DEMO_USERS[0],
        points=18250,
        level=12,
        streak_days=8,
        badges=[_DEMO_BADGES[0], _DEMO_BADGES[1]],
        recent_actions=[
            "Closed enterprise deal (+2,000)",
            "Completed onboarding quest (+300)",
            "Shared playbook with team (+100)",
        ],
    ),
    "u_002": DemoUserSummary(
        user=_DEMO_USERS[1],
        points=16940,
        level=11,
        streak_days=6,
        badges=[_DEMO_BADGES[1]],
        recent_actions=[
            "Optimized ops workflow (+500)",
            "Daily check-in (+20)",
        ],
    ),
    "u_003": DemoUserSummary(
        user=_DEMO_USERS[2],
        points=15100,
        level=10,
        streak_days=4,
        badges=[],
        recent_actions=["Launched feature beta (+1,200)"],
    ),
    "u_004": DemoUserSummary(
        user=_DEMO_USERS[3],
        points=13320,
        level=9,
        streak_days=2,
        badges=[_DEMO_BADGES[2]],
        recent_actions=["Resolved 20+ support tickets (+800)"],
    ),
}


# -----------------------------
# Core + Demo Endpoints
# -----------------------------
@app.get("/")
def read_root():
    return {"message": "Gamification Demo API running"}

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "mode": "demo",
        "version": app.version,
    }

@app.get("/api/demo/leaderboard", response_model=List[DemoLeaderboardEntry])
def get_leaderboard():
    return _DEMO_LEADERBOARD

@app.get("/api/demo/badges", response_model=List[DemoBadge])
def get_badges():
    return _DEMO_BADGES

@app.get("/api/demo/users", response_model=List[DemoUser])
def list_users():
    return _DEMO_USERS

@app.get("/api/demo/user/{user_id}", response_model=DemoUserSummary)
def get_user_summary(user_id: str):
    summary = _DEMO_USER_DETAILS.get(user_id)
    if not summary:
        raise HTTPException(status_code=404, detail="User not found in demo dataset")
    return summary


# Write/Mutating endpoints return demo-mode notice
class DemoAction(BaseModel):
    action: str
    points: int = 0

@app.post("/api/demo/award")
def award_points(_: DemoAction):
    return {
        "mode": "demo",
        "message": "Read-only demo: no data was changed.",
    }


# -----------------------------
# Database connectivity test (optional utility)
# -----------------------------
@app.get("/test")
def test_database():
    """Check if database environment is configured (for future production use)."""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
