import os
import httpx
from fastapi import HTTPException
import country_converter as coco
from routers.helpers.calculation import calculate_accuracy, id_to_mods

OSU_API_KEY = os.getenv("OSU_API_KEY")

async def getUserBancho(username: str, modeNum: int):
    url = "https://osu.ppy.sh/api/get_user"
    params = {
        "k": OSU_API_KEY,
        "u": username,
        "type": "id" if username.isdigit() else "string",
        "m": modeNum 
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to connect to osu! API")

    user_data = response.json()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    # Default to osu! mode
    data = {
    "id": user_data[0]['user_id'],
    "userAvatar": f"https://a.ppy.sh/{user_data[0]['user_id']}",
        "statistics": {
        "global_rank": user_data[0]['pp_rank'],
        "pp": user_data[0]['pp_raw'],
        "country_rank": user_data[0]['pp_country_rank'],
        },
        "country_code": user_data[0]['country'],
        "country": {
            "code": user_data[0]['country'],
            "name": coco.convert(names=user_data[0]['country'], to='name'),
        }
    }
    return data

async def getUserBestScoresBancho(user_id: str, modeNum: int):
    url = "https://osu.ppy.sh/api/get_user_best"
    # Note: "type": "id" means user_id must be their number ID, not their username text
    params = {"k": OSU_API_KEY, "u": user_id, "type": "id", "limit": 5, "m": modeNum}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    # Always check if the API actually responded successfully
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to connect to osu! API")
        
    bestPlaysData = response.json()

    # Check for empty data BEFORE trying to loop through it
    if not bestPlaysData:
        raise HTTPException(status_code=404, detail="User not found or no best scores available")


    result = []
    # Fetch beatmap metadata and return the nested shape expected by index.js.
    async with httpx.AsyncClient() as client:
        for play in bestPlaysData:
            beatmap_url = "https://osu.ppy.sh/api/get_beatmaps"
            beatmap_params = {"k": OSU_API_KEY, "b": play['beatmap_id']}
            beatmap_response = await client.get(beatmap_url, params=beatmap_params)
            beatmap_data = beatmap_response.json()

            if not beatmap_data:
                continue

            beatmap = beatmap_data[0]
            beatmapset_id = beatmap['beatmapset_id']
            result.append({
                "pp": float(play['pp']),
                "ended_at": play['date'],
                "rank": play['rank'] or "",
                "mods_id": play.get('enabled_mods', ''),
                "legacy_score_id": play.get('score_id'),
                "beatmap": {
                    "id": beatmap['beatmap_id'],
                    "beatmapset_id": beatmapset_id,
                },
                "beatmapset": {
                    "title": beatmap['title'],
                    "covers": {
                        "cover": f"https://assets.ppy.sh/beatmaps/{beatmapset_id}/covers/cover.jpg"
                    },
                },
            })

    return result


async def getBeatmapLeaderboardBancho(beatmap_id: int, mode: str):
    if mode == "mania":
        modeNum = 3
    else:
        modeNum = 0  # Default to osu! standard

    url = "https://osu.ppy.sh/api/get_scores"
    params = {
        "k": OSU_API_KEY,
        "b": beatmap_id, # The beatmap ID (not the beatmapset ID)
        "m": modeNum,       # Game mode
        "limit": 50      # Request exactly 50 scores
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error communicating with osu! API")

    scoreData = response.json()
    data = [
            {
                "rank": score['rank'],
                "pp": score['pp'],
                "accuracy": calculate_accuracy(int(score['count300']), int(score['count100']), int(score['count50']), int(score['countmiss'])),
                "score": {
                "total": score['score'],
                },
                "combo": {
                "max": score['maxcombo'],
                },
                "user": {
                "id": score['user_id'],
                "name": score['username']
                },
                "mods": {
                "name": id_to_mods(int(score['enabled_mods'])),
                "id":  score['enabled_mods'],
                }
            }
            for score in scoreData
        ]
    
    # If the beatmap doesn't exist or has no scores, APIv1 returns an empty list
    if not data:
        raise HTTPException(status_code=404, detail="No scores found or beatmap does not exist")

    return data