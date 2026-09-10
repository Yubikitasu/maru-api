# routers/users.py
import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from routers.helpers.akatsuki import getUserAkatsuki, getUserBestScoresAkatsuki
from routers.helpers.bancho import getUserBancho, getUserBestScoresBancho

# Create the router instance
# prefix means all routes here will automatically start with /users
router = APIRouter(prefix="/users", tags=["User Endpoints"])

OSU_API_KEY = os.getenv("OSU_API_KEY")

MOD_BITS = {
    # For osu standard
    "NF": 1,
    "EZ": 2,
    "TD": 4,
    "HD": 8,
    "HR": 16,
    "SD": 32,
    "DT": 64,
    "RX": 128,
    "HT": 256,
    "NC": 512,
    "FL": 1024,
    "AT": 2048,
    "SO": 4096,
    "AP": 8192,
    "PF": 16384,
}


def mods_to_id(mods: str) -> int:
    return sum(MOD_BITS.get(mods[index:index + 2], 0) for index in range(0, len(mods), 2))

# This becomes a GET request at /users/{username}/osu
@router.get("/{username}/{gameMode}")
async def get_user_stats(username: str, gameMode: str, server: str | None = None, server_mods: str | None = None):
    modeNum = 0
    if gameMode == "mania":
        modeNum = 3
    
    if server == "akatsuki":
        akatModeNum = 0
        if server_mods == "relax":
            akatModeNum = 1
        elif server_mods == "autopilot":
            akatModeNum = 2
        user_data = await getUserAkatsuki(username, modeNum, akatModeNum)
    else:
        user_data = await getUserBancho(username, modeNum)
    return user_data

@router.get("/{user_id}/best/{gameMode}")
async def get_user_best_scores(user_id: str, gameMode: str, server: str | None = None, server_mods: str | None = None):
    modeNum = 0
    if gameMode == "mania":
        modeNum = 3
    if server == "akatsuki":
        akatModeNum = 0
        if server_mods == "relax":
            akatModeNum = 1
        elif server_mods == "autopilot":
            akatModeNum = 2
        result = await getUserBestScoresAkatsuki(user_id, modeNum, akatModeNum)
    else:
        result = await getUserBestScoresBancho(user_id, modeNum)
    return result

# Just an example Pydantic model for a POST request
class UserPreference(BaseModel):
    favorite_mode: int

# This becomes a POST request at /users/{user_id}/preferences
@router.post("/{user_id}/preferences")
async def save_preferences(user_id: str, pref: UserPreference):
    # Here you would typically save to a database
    return {"message": f"Saved mode {pref.favorite_mode} for {user_id}"}