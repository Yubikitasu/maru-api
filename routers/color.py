# routers/users.py
import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from routers.extract_color import extract_vibrant_colors

router = APIRouter(prefix="/color", tags=["Color Endpoints"])

OSU_API_KEY = os.getenv("OSU_API_KEY")

@router.get("/{user_id}")
async def get_user_color(user_id: str, server: str | None = None):
    # url = "https://osu.ppy.sh/api/get_user"
    # params = {"k": OSU_API_KEY, "u": user_id, "type": "id"}

    # async with httpx.AsyncClient() as client:
    #     response = await client.get(url, params=params)
    
    # if response.status_code != 200:
    #     raise HTTPException(status_code=500, detail="Failed to connect to osu! API")
    if server == "akatsuki":
        avatar_url = f"https://a.akatsuki.gg/{user_id}"  # URL avatar của người dùng
    else:
        avatar_url = f"https://a.ppy.sh/{user_id}"  # URL avatar của người dùng
    user_data = extract_vibrant_colors(avatar_url)
    print("user_data =", user_data)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return user_data
