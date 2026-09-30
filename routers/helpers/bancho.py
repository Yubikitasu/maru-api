import os
from fastapi import HTTPException
import httpx
import country_converter as coco
from routers.helpers.calculation import calculate_accuracy, id_to_mods
from ossapi import Ossapi, GameMode, ScoreType

OSU_CLIENT_ID = int(os.getenv("OSU_CLIENT_ID", 0))
OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET", "")
OSU_API_KEY = os.getenv("OSU_API_KEY")

api = Ossapi(
    OSU_CLIENT_ID,
    OSU_CLIENT_SECRET,
    token_directory=os.getenv("OSSAPI_TOKEN_DIRECTORY", "/tmp"),
)

def mods_to_legacy_id(mods_list) -> int:
    """Chuyển đổi danh sách mods của API v2 thành số nguyên legacy bitwise"""
    if not mods_list:
        return 0
        
    # Phòng hờ trường hợp dùng bản ossapi cũ trả về Enum
    if hasattr(mods_list, 'value'):
        return mods_list.value

    # Bảng mapping chuẩn của osu! legacy bitwise mods
    MODS_MAP = {
        "NF": 1, "EZ": 2, "TD": 4, "HD": 8, "HR": 16, "SD": 32, "DT": 64,
        "RX": 128, "HT": 256, "NC": 512 | 64, "FL": 1024, "AT": 2048,
        "SO": 4096, "AP": 8192, "PF": 16384 | 32, "4K": 32768, "5K": 65536,
        "6K": 131072, "7K": 262144, "8K": 524288, "FI": 1048576, "RD": 2097152,
        "LM": 4194304, "9K": 16777216, "10K": 33554432, "1K": 67108864,
        "3K": 134217728, "2K": 268435456, "V2": 536870912, "MR": 1073741824
    }
    
    legacy_id = 0
    if isinstance(mods_list, list):
        for mod in mods_list:
            # ossapi mới trả về object có thuộc tính 'acronym'
            acronym = mod.acronym if hasattr(mod, 'acronym') else str(mod)
            legacy_id |= MODS_MAP.get(acronym.upper(), 0)
            
    return legacy_id

def getUserBancho(username: str, modeNum: int):
    try:
        mode = GameMode(modeNum)
    except ValueError:
        mode = GameMode.OSU

    try:
        user = api.user(username, mode=mode, key="username")
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = {
        "id": user.id,
        "userAvatar": user.avatar_url,
        "statistics": {
            "global_rank": user.statistics.global_rank if user.statistics else None,
            "pp": user.statistics.pp if user.statistics else None,
            "country_rank": user.statistics.country_rank if user.statistics else None,
        },
        "country_code": user.country.code,
        "country": {
            "code": user.country.code,
            "name": coco.convert(names=user.country.code, to='name'),
        }
    }
    return data

def getUserBestScoresBancho(user_id: str, modeNum: int):
    try:
        mode = GameMode(modeNum)
    except ValueError:
        mode = GameMode.OSU

    try:
        best_scores = api.user_scores(user_id, type=ScoreType.BEST, mode=mode, limit=5)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to connect to osu! API")

    if not best_scores:
        raise HTTPException(status_code=404, detail="User not found or no best scores available")

    result = []
    for play in best_scores:
        result.append({
            "pp": float(play.pp) if play.pp is not None else 0.0,
            "ended_at": play.ended_at.isoformat() if play.ended_at else "",
            "rank": play.rank.value if play.rank else "",
            "mods_id": mods_to_legacy_id(play.mods),
            "legacy_score_id": play.best_id or play.id,
            "beatmap": {
                "id": play.beatmap.id,
                "beatmapset_id": play.beatmap.beatmapset_id,
            },
            "beatmapset": {
                "title": play.beatmapset.title,
                "covers": {
                    "cover": play.beatmapset.covers.cover
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
                "name": score['username'],
                "userAvatar": f"https://a.ppy.sh/{score['user_id']}"
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