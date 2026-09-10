# modeNum = 0 for osu!, 3 for Mania
# Nếu player chơi Vanilla thì akatMode = 0, nếu chơi Relax thì akatMode = 1, nếu chơi AutoPilot thì akatMode = 2
# Rồi trọng số mode sẽ là mode = modeNum + akatMode * 4

import os
import httpx
from fastapi import HTTPException
import country_converter as coco

from routers.helpers.calculation import calculate_accuracy, id_to_mods

async def getUserAkatsuki(username: str, modeNum: int, akatMode: int):
    # 1. Lấy user_id người chơi
    url = "https://akatsuki.gg/api/v1/users"
    params = {
        "name": username,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to connect to osu! Akatsuki API")

    user_data = response.json()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user_data['id']
    country_code = user_data['country']

    print(f"User ID: {user_id}, Country Code: {country_code}")

    # 2. Lấy peak rank và peak pp của người chơi
    mode = modeNum + akatMode * 4
    url2 = f"https://akatsuki.gg/api/v1/profile-history/rank"

    params2 = {
        "user_id": user_id,
        "mode": mode
    }

    async with httpx.AsyncClient() as client:
        response2 = await client.get(url2, params=params2)
    if response2.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to connect to osu! Akatsuki API for peak rank")
    peak_data = response2.json()
    if not peak_data:
        raise HTTPException(status_code=404, detail="Peak rank data not found")
    print (f"Peak Data: {peak_data}")

    # If shows error: users.is_not_active:
    if peak_data.get('error') == 'users.is_not_active':
        raise HTTPException(status_code=404, detail="User is not active on current mode")
    else:
        global_rank = peak_data['data']['captures'][-1]['overall'] if peak_data['data']["captures"] else 0
        country_rank = peak_data['data']['captures'][-1]['country'] if peak_data['data']["captures"] else 0

    url3 = f"https://akatsuki.gg/api/v1/profile-history/pp?user_id={user_id}&mode={mode}"
    async with httpx.AsyncClient() as client:
        response3 = await client.get(url3)
    if response3.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to connect to osu! Akatsuki API for peak pp")
    peak_pp_data = response3.json()
    if not peak_pp_data:
        raise HTTPException(status_code=404, detail="Peak pp data not found")
    if peak_pp_data.get('error') == 'users.is_not_active':
        raise HTTPException(status_code=404, detail="User is not active on current mode")
    else:
        peak_pp = peak_pp_data['data']['captures'][-1]['pp'] if peak_pp_data['data']["captures"] else 0

    data = {
    "id": user_id,
    "userAvatar": f"https://a.akatsuki.gg/{user_id}",
        "statistics": {
        "global_rank": global_rank,
        "pp": peak_pp,
        "country_rank": country_rank,
        },
        "country_code": country_code,
        "country": {
            "code": country_code,
            "name": coco.convert(names=country_code, to='name'),
        }
    }
    return data

async def getUserBestScoresAkatsuki(user_id: str, modeNum: int, akatMode: int):
    url = "https://akatsuki.gg/api/v1/users/scores/best"
    params = {
        "mode": modeNum,
        "p": 1,
        "l": 10,
        "rx": akatMode,
        "id": user_id,
        "uid": user_id,
        "actual_id": 0
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    # Always check if the API actually responded successfully
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to connect to osu! API")
        
    bestPlaysData = response.json()

    scores = bestPlaysData.get('scores', [])

    # Check for empty data BEFORE trying to loop through it
    if not bestPlaysData:
        raise HTTPException(status_code=404, detail="User not found or no best scores available")


    result = []
    for play in scores:
        result.append({
            "pp": float(play['pp']),
            "ended_at": play['time'],
            "rank": play['rank'] or "",
            "mods_id": play.get('mods', ''),
            "legacy_score_id": play.get('id'),
            "beatmap": {
                "id": play['beatmap']['beatmap_id'],
                "beatmapset_id": play['beatmap']['beatmapset_id'],
            },
            "beatmapset": {
                "title": play['beatmap']['song_name'],
                "covers": {
                    "cover": f"https://assets.ppy.sh/beatmaps/{play['beatmap']['beatmapset_id']}/covers/cover.jpg"
                },
            },
        })

    return result


async def getBeatmapLeaderboardAkatsuki(beatmap_id: int, modeNum: int, akatMode: int):
    url = f"https://akatsuki.gg/api/v1/scores?sort=pp,desc&m={modeNum}&relax={akatMode}&b={beatmap_id}&p=1&l=50"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    # Always check if the API actually responded successfully
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to connect to Akatsuki API")

    if not response.json():
        raise HTTPException(status_code=404, detail="No scores found or beatmap does not exist")

    scoresData = response.json().get('scores', [])
    data = [
                {
                    "rank": score['rank'],
                    "pp": score['pp'],
                    "accuracy": score['accuracy'],
                    "score": {
                        "total": score['score'],
                    },
                    "combo": {
                        "max": score['max_combo'],
                    },
                    "user": {
                        "id": score['user_id'],
                        "name": score['user']['username']
                    },
                    "mods": {
                        "name": id_to_mods(int(score['mods'])),
                        "id":  score['mods'],
                    }
                }
                for score in scoresData
            ]

    return data