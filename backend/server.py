from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    google_user_id: str
    email: str
    name: str
    picture: str
    access_level: str = "Limited"
    created_at: str

class SessionData(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    session_token: str

class Market(BaseModel):
    model_config = ConfigDict(extra="ignore")
    market_id: str
    name_ar: str
    name_en: str
    region: str
    created_at: str

class MarketCreate(BaseModel):
    name_ar: str
    name_en: str
    region: str

class Asset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    asset_id: str
    market_id: str
    name_ar: str
    name_en: str
    type: str
    created_at: str

class AssetCreate(BaseModel):
    market_id: str
    name_ar: str
    name_en: str
    type: str

class Analysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    analysis_id: str
    asset_id: str
    market_id: str
    bias: str
    key_levels: str
    scenario_text: str
    insight_text: Optional[str] = None
    risk_note: Optional[str] = None
    confidence_level: str
    updated_at: str
    created_by: str

class AnalysisCreate(BaseModel):
    asset_id: str
    bias: str
    key_levels: str
    scenario_text: str
    insight_text: Optional[str] = None
    risk_note: Optional[str] = None
    confidence_level: str

async def get_current_user(request: Request) -> Optional[User]:
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session_id")
        
        session_data = SessionData(**resp.json())
    
    existing_user = await db.users.find_one({"google_user_id": session_data.id}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "email": session_data.email,
                "name": session_data.name,
                "picture": session_data.picture
            }}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "google_user_id": session_data.id,
            "email": session_data.email,
            "name": session_data.name,
            "picture": session_data.picture,
            "access_level": "Limited",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_data.session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    response.set_cookie(
        key="session_token",
        value=session_data.session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return User(**user)

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

@api_router.get("/markets", response_model=List[Market])
async def get_markets():
    markets = await db.markets.find({}, {"_id": 0}).to_list(100)
    return markets

@api_router.post("/markets", response_model=Market)
async def create_market(market: MarketCreate, request: Request):
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    market_id = f"market_{uuid.uuid4().hex[:12]}"
    market_doc = {
        "market_id": market_id,
        "name_ar": market.name_ar,
        "name_en": market.name_en,
        "region": market.region,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.markets.insert_one(market_doc)
    return Market(**market_doc)

@api_router.get("/assets", response_model=List[Asset])
async def get_assets(market_id: Optional[str] = None):
    query = {"market_id": market_id} if market_id else {}
    assets = await db.assets.find(query, {"_id": 0}).to_list(100)
    return assets

@api_router.post("/assets", response_model=Asset)
async def create_asset(asset: AssetCreate, request: Request):
    user = await get_current_user(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    asset_id = f"asset_{uuid.uuid4().hex[:12]}"
    asset_doc = {
        "asset_id": asset_id,
        "market_id": asset.market_id,
        "name_ar": asset.name_ar,
        "name_en": asset.name_en,
        "type": asset.type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.assets.insert_one(asset_doc)
    return Asset(**asset_doc)

@api_router.get("/analysis/{asset_id}")
async def get_analysis(asset_id: str):
    analysis = await db.analyses.find_one({"asset_id": asset_id}, {"_id": 0})
    if not analysis:
        return None
    return analysis

@api_router.post("/analysis", response_model=Analysis)
async def create_analysis(analysis: AnalysisCreate, request: Request):
    user = await get_current_user(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    asset = await db.assets.find_one({"asset_id": analysis.asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"
    analysis_doc = {
        "analysis_id": analysis_id,
        "asset_id": analysis.asset_id,
        "market_id": asset["market_id"],
        "bias": analysis.bias,
        "key_levels": analysis.key_levels,
        "scenario_text": analysis.scenario_text,
        "insight_text": analysis.insight_text,
        "risk_note": analysis.risk_note,
        "confidence_level": analysis.confidence_level,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.user_id
    }
    
    await db.analyses.update_one(
        {"asset_id": analysis.asset_id},
        {"$set": analysis_doc},
        upsert=True
    )
    
    return Analysis(**analysis_doc)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
