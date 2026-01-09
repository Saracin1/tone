from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
import secrets
from datetime import datetime, timezone, timedelta
import httpx
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from urllib.parse import urlencode

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

# History of Success Models
class ForecastHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    record_id: str
    instrument_code: str
    market: str
    forecast_date: str
    forecast_direction: str  # "Bullish" or "Bearish"
    entry_price: float
    forecast_target_price: float
    actual_result_price: Optional[float] = None
    result_date: Optional[str] = None
    calculated_pl_percent: Optional[float] = None
    status: str = "pending"  # "success", "failed", "pending"
    notes: Optional[str] = None
    created_at: str
    updated_at: str

class ForecastCreate(BaseModel):
    instrument_code: str
    market: str
    forecast_date: str
    forecast_direction: str
    entry_price: float
    forecast_target_price: float
    actual_result_price: Optional[float] = None
    result_date: Optional[str] = None
    notes: Optional[str] = None

class ForecastUpdate(BaseModel):
    actual_result_price: float
    result_date: str
    notes: Optional[str] = None

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

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback')
FRONTEND_URL = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')[0]

@api_router.get("/auth/google")
async def google_login():
    """Redirect to Google OAuth consent screen"""
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=google_auth_url)

@api_router.get("/auth/google/callback")
async def google_callback(code: str, response: Response):
    """Handle Google OAuth callback"""
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': GOOGLE_REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        
        # Get user info from Google
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = userinfo_response.json()
    
    google_user_id = user_info.get('id')
    email = user_info.get('email')
    name = user_info.get('name')
    picture = user_info.get('picture', '')
    
    # Check if user exists
    existing_user = await db.users.find_one({"google_user_id": google_user_id}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "email": email,
                "name": name,
                "picture": picture
            }}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "google_user_id": google_user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "access_level": "Limited",
            "subscription_type": None,
            "subscription_status": "none",
            "subscription_start_date": None,
            "subscription_end_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create session
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Create redirect response with cookie
    redirect_response = RedirectResponse(url=f"{FRONTEND_URL}/dashboard", status_code=302)
    redirect_response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to False for localhost
        samesite="lax",
        path="/",
        max_age=7*24*60*60
    )
    
    return redirect_response

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Legacy endpoint - kept for compatibility"""
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # For local development, this endpoint is not used
    # Google OAuth flow handles authentication directly
    raise HTTPException(status_code=400, detail="Use /api/auth/google for authentication")

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

@api_router.get("/daily-analysis/chart-data")
async def get_analysis_price_chart_data(request: Request):
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(
            status_code=403,
            detail="Active subscription required"
        )
    
    pipeline = [
        {
            "$group": {
                "_id": {
                    "market": "$market",
                    "instrument": "$instrument_code"
                },
                "latest_price": {"$last": "$analysis_price"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "market": "$_id.market",
                "instrument": "$_id.instrument",
                "analysis_price": "$latest_price"
            }
        }
    ]
    
    results = await db.daily_analysis.aggregate(pipeline).to_list(1000)
    
    chart_data = []
    for item in results:
        try:
            price_value = float(item["analysis_price"].replace(",", ""))
            chart_data.append({
                "market": item["market"],
                "instrument": item["instrument"],
                "value": price_value
            })
        except (ValueError, AttributeError):
            continue
    
    return chart_data

@api_router.get("/daily-analysis/line-chart-data")
async def get_line_chart_data(request: Request):
    """
    Returns analysis price vs target price data for all instruments.
    Used for the dual-line comparison chart.
    """
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(
            status_code=403,
            detail="Active subscription required"
        )
    
    # Get the latest record for each instrument
    pipeline = [
        {"$sort": {"analysis_datetime": -1}},
        {
            "$group": {
                "_id": {
                    "market": "$market",
                    "instrument": "$instrument_code"
                },
                "analysis_price": {"$first": "$analysis_price"},
                "target_price": {"$first": "$target_price"},
                "analysis_datetime": {"$first": "$analysis_datetime"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "market": "$_id.market",
                "instrument_code": "$_id.instrument",
                "analysis_price": 1,
                "target_price": 1,
                "analysis_datetime": 1
            }
        },
        {"$sort": {"market": 1, "instrument_code": 1}}
    ]
    
    results = await db.daily_analysis.aggregate(pipeline).to_list(1000)
    
    chart_data = []
    for item in results:
        try:
            analysis_price = float(item["analysis_price"].replace(",", "")) if item.get("analysis_price") else 0
            target_price = float(item["target_price"].replace(",", "")) if item.get("target_price") else 0
            
            chart_data.append({
                "market": item["market"],
                "instrument_code": item["instrument_code"],
                "analysis_price": analysis_price,
                "target_price": target_price,
                "analysis_datetime": item.get("analysis_datetime", "")
            })
        except (ValueError, AttributeError) as e:
            continue
    
    return chart_data

@api_router.get("/daily-analysis/last-sync")
async def get_last_sync_time(request: Request):
    """
    Returns the last sync timestamp to enable auto-refresh detection.
    """
    user = await get_current_user(request)
    
    # Get the most recent updated_at from daily_analysis
    latest = await db.daily_analysis.find_one(
        {},
        {"_id": 0, "updated_at": 1},
        sort=[("updated_at", -1)]
    )
    
    return {
        "last_sync": latest.get("updated_at") if latest else None
    }

# ==================== HISTORY OF SUCCESS ENDPOINTS ====================

@api_router.get("/history/forecasts")
async def get_forecast_history(
    request: Request, 
    market: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """
    Get all forecast history records. Read-only for credibility display.
    """
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    query = {}
    if market:
        query["market"] = market
    if status:
        query["status"] = status
    
    forecasts = await db.forecast_history.find(
        query, 
        {"_id": 0}
    ).sort("forecast_date", -1).limit(limit).to_list(limit)
    
    return forecasts

@api_router.get("/history/performance")
async def get_performance_data(request: Request):
    """
    Get aggregated performance data for bar charts.
    Returns P/L percentage per instrument.
    """
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    # Aggregate performance by instrument
    pipeline = [
        {"$match": {"status": {"$in": ["success", "failed"]}}},
        {
            "$group": {
                "_id": {
                    "market": "$market",
                    "instrument": "$instrument_code"
                },
                "total_forecasts": {"$sum": 1},
                "successful_forecasts": {
                    "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                },
                "total_pl_percent": {"$sum": "$calculated_pl_percent"},
                "avg_pl_percent": {"$avg": "$calculated_pl_percent"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "market": "$_id.market",
                "instrument_code": "$_id.instrument",
                "total_forecasts": 1,
                "successful_forecasts": 1,
                "win_rate": {
                    "$multiply": [
                        {"$divide": ["$successful_forecasts", "$total_forecasts"]},
                        100
                    ]
                },
                "total_pl_percent": {"$round": ["$total_pl_percent", 2]},
                "avg_pl_percent": {"$round": ["$avg_pl_percent", 2]}
            }
        },
        {"$sort": {"total_pl_percent": -1}}
    ]
    
    results = await db.forecast_history.aggregate(pipeline).to_list(1000)
    return results

@api_router.get("/history/cumulative")
async def get_cumulative_performance(request: Request):
    """
    Get cumulative performance over time for line chart.
    """
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    # Get all completed forecasts sorted by date
    pipeline = [
        {"$match": {"status": {"$in": ["success", "failed"]}, "result_date": {"$ne": None}}},
        {"$sort": {"result_date": 1}},
        {
            "$project": {
                "_id": 0,
                "result_date": 1,
                "instrument_code": 1,
                "market": 1,
                "calculated_pl_percent": 1,
                "status": 1
            }
        }
    ]
    
    forecasts = await db.forecast_history.aggregate(pipeline).to_list(1000)
    
    # Calculate cumulative return
    cumulative_data = []
    cumulative_return = 0
    total_trades = 0
    winning_trades = 0
    
    for forecast in forecasts:
        total_trades += 1
        if forecast.get("status") == "success":
            winning_trades += 1
        
        pl = forecast.get("calculated_pl_percent", 0) or 0
        cumulative_return += pl
        
        cumulative_data.append({
            "date": forecast.get("result_date", ""),
            "instrument": forecast.get("instrument_code", ""),
            "market": forecast.get("market", ""),
            "pl_percent": round(pl, 2),
            "cumulative_return": round(cumulative_return, 2),
            "total_trades": total_trades,
            "win_rate": round((winning_trades / total_trades) * 100, 2) if total_trades > 0 else 0
        })
    
    return cumulative_data

@api_router.get("/history/summary")
async def get_history_summary(request: Request):
    """
    Get overall summary statistics for History of Success section.
    """
    user = await get_current_user(request)
    
    if not check_subscription_access(user):
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    # Get total counts
    total_forecasts = await db.forecast_history.count_documents({})
    completed_forecasts = await db.forecast_history.count_documents({"status": {"$in": ["success", "failed"]}})
    successful_forecasts = await db.forecast_history.count_documents({"status": "success"})
    pending_forecasts = await db.forecast_history.count_documents({"status": "pending"})
    
    # Calculate total and average P/L
    pipeline = [
        {"$match": {"status": {"$in": ["success", "failed"]}}},
        {
            "$group": {
                "_id": None,
                "total_pl": {"$sum": "$calculated_pl_percent"},
                "avg_pl": {"$avg": "$calculated_pl_percent"},
                "max_gain": {"$max": "$calculated_pl_percent"},
                "max_loss": {"$min": "$calculated_pl_percent"}
            }
        }
    ]
    
    stats = await db.forecast_history.aggregate(pipeline).to_list(1)
    
    summary = {
        "total_forecasts": total_forecasts,
        "completed_forecasts": completed_forecasts,
        "successful_forecasts": successful_forecasts,
        "pending_forecasts": pending_forecasts,
        "win_rate": round((successful_forecasts / completed_forecasts) * 100, 2) if completed_forecasts > 0 else 0,
        "total_return_percent": round(stats[0]["total_pl"], 2) if stats else 0,
        "avg_return_percent": round(stats[0]["avg_pl"], 2) if stats else 0,
        "best_trade_percent": round(stats[0]["max_gain"], 2) if stats and stats[0].get("max_gain") else 0,
        "worst_trade_percent": round(stats[0]["max_loss"], 2) if stats and stats[0].get("max_loss") else 0
    }
    
    return summary

@api_router.get("/history/markets")
async def get_history_markets(request: Request):
    """
    Get list of markets with forecast history.
    """
    user = await get_current_user(request)
    
    markets = await db.forecast_history.distinct("market")
    return {"markets": markets}

# Admin endpoints for managing forecast history
@api_router.post("/admin/history/forecast")
async def create_forecast(forecast: ForecastCreate, request: Request):
    """
    Admin: Create a new forecast record.
    """
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Calculate P/L if actual result is provided
    calculated_pl = None
    status = "pending"
    
    if forecast.actual_result_price is not None and forecast.result_date:
        if forecast.forecast_direction == "Bullish":
            calculated_pl = ((forecast.actual_result_price - forecast.entry_price) / forecast.entry_price) * 100
            status = "success" if forecast.actual_result_price >= forecast.forecast_target_price else "failed"
        else:  # Bearish
            calculated_pl = ((forecast.entry_price - forecast.actual_result_price) / forecast.entry_price) * 100
            status = "success" if forecast.actual_result_price <= forecast.forecast_target_price else "failed"
    
    forecast_doc = {
        "record_id": f"forecast_{uuid.uuid4().hex[:12]}",
        "instrument_code": forecast.instrument_code,
        "market": forecast.market,
        "forecast_date": forecast.forecast_date,
        "forecast_direction": forecast.forecast_direction,
        "entry_price": forecast.entry_price,
        "forecast_target_price": forecast.forecast_target_price,
        "actual_result_price": forecast.actual_result_price,
        "result_date": forecast.result_date,
        "calculated_pl_percent": round(calculated_pl, 2) if calculated_pl is not None else None,
        "status": status,
        "notes": forecast.notes,
        "created_at": now,
        "updated_at": now
    }
    
    await db.forecast_history.insert_one(forecast_doc)
    return ForecastHistory(**forecast_doc)

@api_router.put("/admin/history/forecast/{record_id}")
async def update_forecast_result(record_id: str, update: ForecastUpdate, request: Request):
    """
    Admin: Update forecast with actual result.
    """
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = await db.forecast_history.find_one({"record_id": record_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    # Calculate P/L based on direction
    entry_price = existing["entry_price"]
    target_price = existing["forecast_target_price"]
    direction = existing["forecast_direction"]
    
    if direction == "Bullish":
        calculated_pl = ((update.actual_result_price - entry_price) / entry_price) * 100
        status = "success" if update.actual_result_price >= target_price else "failed"
    else:  # Bearish
        calculated_pl = ((entry_price - update.actual_result_price) / entry_price) * 100
        status = "success" if update.actual_result_price <= target_price else "failed"
    
    update_doc = {
        "actual_result_price": update.actual_result_price,
        "result_date": update.result_date,
        "calculated_pl_percent": round(calculated_pl, 2),
        "status": status,
        "notes": update.notes if update.notes else existing.get("notes"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.forecast_history.update_one(
        {"record_id": record_id},
        {"$set": update_doc}
    )
    
    updated = await db.forecast_history.find_one({"record_id": record_id}, {"_id": 0})
    return ForecastHistory(**updated)

@api_router.delete("/admin/history/forecast/{record_id}")
async def delete_forecast(record_id: str, request: Request):
    """
    Admin: Delete a forecast record.
    """
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.forecast_history.delete_one({"record_id": record_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    return {"message": "Forecast deleted successfully"}

@api_router.get("/admin/history/forecasts")
async def admin_get_all_forecasts(request: Request, limit: int = 500):
    """
    Admin: Get all forecasts for management.
    """
    user = await get_current_user(request)
    if user.access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    forecasts = await db.forecast_history.find(
        {}, 
        {"_id": 0}
    ).sort("forecast_date", -1).limit(limit).to_list(limit)
    
    return forecasts

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
