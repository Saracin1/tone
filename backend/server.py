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
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
    subscription_type: Optional[str] = None
    subscription_status: str = "none"
    subscription_start_date: Optional[str] = None
    subscription_end_date: Optional[str] = None
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

class DailyAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    record_id: str
    market: str
    instrument_code: str
    insight_type: str
    analysis_datetime: str
    analysis_price: str
    target_price: str
    critical_level: str
    source: str = "google_sheets"
    created_at: str
    updated_at: str

class GoogleSheetsConfig(BaseModel):
    spreadsheet_id: str
    range_name: str = "Sheet1!A2:G"

class SyncResult(BaseModel):
    total_rows: int
    inserted: int
    updated: int
    skipped: int
    errors: List[str]

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
    
    user = User(**user_doc)
    
    if user.subscription_end_date:
        end_date = datetime.fromisoformat(user.subscription_end_date)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if now > end_date and user.subscription_status == "active":
            await db.users.update_one(
                {"user_id": user.user_id},
                {"$set": {"subscription_status": "expired"}}
            )
            user.subscription_status = "expired"
    
    return user

def check_subscription_access(user: User, required_access: str = "any") -> bool:
    if user.access_level == "admin":
        return True
    
    if user.subscription_status != "active":
        return False
    
    if user.subscription_end_date:
        end_date = datetime.fromisoformat(user.subscription_end_date)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > end_date:
            return False
    
    if required_access == "any":
        return True
    
    subscription_hierarchy = {"Beginner": 1, "Advanced": 2, "Premium": 3}
    user_level = subscription_hierarchy.get(user.subscription_type, 0)
    required_level = subscription_hierarchy.get(required_access, 0)
    
    return user_level >= required_level

def parse_datetime_string(date_str: str) -> str:
    try:
        parts = date_str.strip().replace('[', '').replace(']', '').split()
        if len(parts) >= 2:
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else "00:00:00"
        else:
            date_part = parts[0]
            time_part = "00:00:00"
        
        day, month, year = date_part.split('.')
        dt = datetime.strptime(f"{year}-{month}-{day} {time_part}", "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception as e:
        raise ValueError(f"Invalid datetime format: {date_str}. Expected DD.MM.YYYY [HH:MM:SS]")

def get_sheets_service():
    credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    if not credentials_json:
        raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not set")
    
    import json
    credentials_dict = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    
    return build('sheets', 'v4', credentials=credentials)

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
            "subscription_type": None,
            "subscription_status": "none",
            "subscription_start_date": None,
            "subscription_end_date": None,
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

class SubscriptionUpdate(BaseModel):
    subscription_type: str
    duration_days: int

@api_router.post("/subscriptions/activate")
async def activate_subscription(subscription: SubscriptionUpdate, request: Request):
    user = await get_current_user(request)
    
    if subscription.subscription_type not in ["Beginner", "Advanced", "Premium"]:
        raise HTTPException(status_code=400, detail="Invalid subscription type")
    
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=subscription.duration_days)
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "subscription_type": subscription.subscription_type,
            "subscription_status": "active",
            "subscription_start_date": start_date.isoformat(),
            "subscription_end_date": end_date.isoformat()
        }}
    )
    
    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return User(**updated_user)

@api_router.get("/subscriptions/status")
async def get_subscription_status(request: Request):
    user = await get_current_user(request)
    
    has_access = check_subscription_access(user)
    days_remaining = None
    
    if user.subscription_end_date and user.subscription_status == "active":
        end_date = datetime.fromisoformat(user.subscription_end_date)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        days_remaining = max(0, (end_date - datetime.now(timezone.utc)).days)
    
    return {
        "subscription_type": user.subscription_type,
        "subscription_status": user.subscription_status,
        "has_access": has_access,
        "days_remaining": days_remaining,
        "subscription_end_date": user.subscription_end_date
    }

class AdminSubscriptionControl(BaseModel):
    user_email: str
    subscription_type: str
    duration_days: int
    action: str

@api_router.get("/admin/users")
async def get_all_users(request: Request):
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return users

@api_router.post("/admin/users/subscription")
async def admin_manage_subscription(control: AdminSubscriptionControl, request: Request):
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if control.subscription_type not in ["Beginner", "Advanced", "Premium"]:
        raise HTTPException(status_code=400, detail="Invalid subscription type")
    
    target_user = await db.users.find_one({"email": control.user_email}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = datetime.now(timezone.utc)
    
    if control.action == "activate":
        end_date = now + timedelta(days=control.duration_days)
        await db.users.update_one(
            {"email": control.user_email},
            {"$set": {
                "subscription_type": control.subscription_type,
                "subscription_status": "active",
                "subscription_start_date": now.isoformat(),
                "subscription_end_date": end_date.isoformat()
            }}
        )
    
    elif control.action == "extend":
        current_end = target_user.get("subscription_end_date")
        if current_end:
            current_end_date = datetime.fromisoformat(current_end)
            if current_end_date.tzinfo is None:
                current_end_date = current_end_date.replace(tzinfo=timezone.utc)
            if current_end_date < now:
                new_end_date = now + timedelta(days=control.duration_days)
            else:
                new_end_date = current_end_date + timedelta(days=control.duration_days)
        else:
            new_end_date = now + timedelta(days=control.duration_days)
        
        await db.users.update_one(
            {"email": control.user_email},
            {"$set": {
                "subscription_type": control.subscription_type,
                "subscription_status": "active",
                "subscription_end_date": new_end_date.isoformat()
            }}
        )
    
    elif control.action == "deactivate":
        await db.users.update_one(
            {"email": control.user_email},
            {"$set": {
                "subscription_status": "expired",
                "subscription_end_date": now.isoformat()
            }}
        )
    
    elif control.action == "gift":
        end_date = now + timedelta(days=control.duration_days)
        await db.users.update_one(
            {"email": control.user_email},
            {"$set": {
                "subscription_type": control.subscription_type,
                "subscription_status": "active",
                "subscription_start_date": now.isoformat(),
                "subscription_end_date": end_date.isoformat()
            }}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    updated_user = await db.users.find_one({"email": control.user_email}, {"_id": 0})
    return User(**updated_user)

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
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
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
async def get_analysis(asset_id: str, request: Request):
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(
            status_code=403, 
            detail="Active subscription required to view analysis"
        )
    
    analysis = await db.analyses.find_one({"asset_id": asset_id}, {"_id": 0})
    if not analysis:
        return None
    return analysis

@api_router.post("/analysis", response_model=Analysis)
async def create_analysis(analysis: AnalysisCreate, request: Request):
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
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

@api_router.post("/admin/sheets/sync")
async def sync_from_google_sheets(config: GoogleSheetsConfig, request: Request):
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = get_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=config.spreadsheet_id,
            range=config.range_name
        ).execute()
        values = result.get('values', [])
        
        if not values:
            return SyncResult(
                total_rows=0,
                inserted=0,
                updated=0,
                skipped=0,
                errors=["No data found in sheet"]
            )
        
        total_rows = len(values)
        inserted = 0
        updated = 0
        skipped = 0
        errors = []
        
        for idx, row in enumerate(values, start=2):
            try:
                if len(row) < 7:
                    skipped += 1
                    errors.append(f"Row {idx}: Insufficient columns (expected 7, got {len(row)})")
                    continue
                
                market = row[0].strip()
                instrument_code = row[1].strip()
                insight_type = row[2].strip()
                date_time_str = row[3].strip()
                analysis_price = row[4].strip()
                target_price = row[5].strip()
                critical_level = row[6].strip()
                
                if not all([market, instrument_code, insight_type, date_time_str]):
                    skipped += 1
                    errors.append(f"Row {idx}: Missing required fields")
                    continue
                
                analysis_datetime = parse_datetime_string(date_time_str)
                
                unique_key = {
                    "market": market,
                    "instrument_code": instrument_code,
                    "analysis_datetime": analysis_datetime
                }
                
                now = datetime.now(timezone.utc).isoformat()
                record = {
                    "record_id": f"daily_{uuid.uuid4().hex[:12]}",
                    "market": market,
                    "instrument_code": instrument_code,
                    "insight_type": insight_type,
                    "analysis_datetime": analysis_datetime,
                    "analysis_price": analysis_price,
                    "target_price": target_price,
                    "critical_level": critical_level,
                    "source": "google_sheets",
                    "updated_at": now
                }
                
                existing = await db.daily_analysis.find_one(unique_key, {"_id": 0})
                
                if existing:
                    await db.daily_analysis.update_one(
                        unique_key,
                        {"$set": record}
                    )
                    updated += 1
                else:
                    record["created_at"] = now
                    await db.daily_analysis.insert_one(record)
                    inserted += 1
                
            except ValueError as e:
                skipped += 1
                errors.append(f"Row {idx}: {str(e)}")
            except Exception as e:
                skipped += 1
                errors.append(f"Row {idx}: Unexpected error - {str(e)}")
        
        return SyncResult(
            total_rows=total_rows,
            inserted=inserted,
            updated=updated,
            skipped=skipped,
            errors=errors
        )
    
    except HttpError as e:
        raise HTTPException(status_code=400, detail=f"Google Sheets API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@api_router.get("/daily-analysis")
async def get_daily_analysis(request: Request, market: Optional[str] = None, limit: int = 100):
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(
            status_code=403,
            detail="Active subscription required to view analysis"
        )
    
    query = {"market": market} if market else {}
    analyses = await db.daily_analysis.find(query, {"_id": 0}).sort("analysis_datetime", -1).limit(limit).to_list(limit)
    return analyses

@api_router.get("/daily-analysis/markets")
async def get_daily_analysis_markets():
    markets = await db.daily_analysis.distinct("market")
    return {"markets": markets}

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
