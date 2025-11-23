# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import from app package
from app.core.config import settings
from app.api.v1.router import api_router    

# Create the ASGI app object named exactly `app`
app = FastAPI(title=getattr(settings, "APP_NAME", "SchizoDot Backend"))

# Dev-friendly CORS for now; tighten later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "I love you baby", "env": getattr(settings, "ENV", "local")}

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "env": settings.ENV, "region": settings.AWS_REGION}
