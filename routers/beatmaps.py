# routers/beatmaps.py
import os
import httpx
from fastapi import APIRouter, HTTPException
from routers.helpers.akatsuki import getBeatmapLeaderboardAkatsuki
from routers.helpers.bancho import getBeatmapLeaderboardBancho
# from routers.helpers.calculation import calculate_accuracy, id_to_mods

router = APIRouter(prefix="/beatmaps", tags=["Beatmap Endpoints"])
OSU_API_KEY = os.getenv("OSU_API_KEY")

# Function này Maru Overlay ko cần nên nếu uncomment thì cx chả có tác dụng gì
@router.get("/{beatmap_id}")
async def get_beatmap_info(beatmap_id: int):
    url = "https://osu.ppy.sh/api/get_beatmaps"
    params = {"k": OSU_API_KEY, "b": beatmap_id}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error communicating with osu! API")
        
    data = response.json()
    
    # If the beatmap doesn't exist, APIv1 returns an empty list
    if not data:
        raise HTTPException(status_code=404, detail="Beatmap not found")
        
    return data[0]  # Return the first (and only) beatmap info

# Lấy leaderboard bên osu! standard và mania
# Mẫu: https://{BASEURL}/beatmaps/12059810/mania
# Mẫu: https://{BASEURL}/beatmaps/12059810/global
@router.get("/{beatmap_id}/{mode}")
async def get_beatmap_scores(beatmap_id: int, mode: str, server: str | None = None, server_mods: str | None = None):
    if server == "akatsuki":
        modeNum = 0
        if mode == "mania":
            modeNum = 3
        akatMode = 0
        if server_mods == "relax":
            akatMode = 1
        elif server_mods == "autopilot":
            akatMode = 2
        data = await getBeatmapLeaderboardAkatsuki(beatmap_id, modeNum, akatMode)
    else:
        data = await getBeatmapLeaderboardBancho(beatmap_id, mode)
    return data
