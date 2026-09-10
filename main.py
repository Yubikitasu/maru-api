# main.py
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load env variables before importing routers that read them at module load time
load_dotenv()

# fix the cors policy
from fastapi.middleware.cors import CORSMiddleware

# Import the router files we just created
from routers import color, users, beatmaps

app = FastAPI(title="osu! APIv1 Modular Integration")

configured_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        ""
    ).split(",")
    if origin.strip()
]
frontend_origins = list(dict.fromkeys([
    *configured_origins,
    "http://127.0.0.1:24050",
    "http://localhost:24050",
]))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Plug the routers into the main app
app.include_router(users.router)
app.include_router(beatmaps.router)
app.include_router(color.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the osu! API"}