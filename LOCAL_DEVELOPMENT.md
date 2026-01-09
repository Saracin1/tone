# Tahlil One - Local Development Setup

## Prerequisites

- Python 3.9+
- Node.js 18+
- Yarn package manager
- MongoDB (or MongoDB Atlas account)

## Configuration

### Backend Environment (`backend/.env`)

```env
MONGO_URL=mongodb+srv://fmukhlisov_db_user:Analiz75@cluster0.t3j6lmc.mongodb.net/?appName=Cluster0
DB_NAME=tahlil_one
CORS_ORIGINS=http://localhost:3000
GOOGLE_CLIENT_ID=962102164814-cktrna95l1j88n6bvp8emb59i4fulguj.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

### Frontend Environment (`frontend/.env`)

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

## Quick Start

### Option 1: Using the startup script

```bash
chmod +x start_local.sh
./start_local.sh
```

### Option 2: Manual startup

**Terminal 1 - Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn install
yarn start
```

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |

## Google OAuth Setup

The app uses Google OAuth for authentication. The callback URL is:
```
http://localhost:8000/api/auth/google/callback
```

Make sure this URL is added to your Google Cloud Console:
1. Go to https://console.cloud.google.com/
2. Navigate to APIs & Services > Credentials
3. Edit your OAuth 2.0 Client ID
4. Add `http://localhost:8000/api/auth/google/callback` to Authorized redirect URIs

## Database

The app connects to MongoDB Atlas. Collections:
- `users` - User accounts and subscriptions
- `user_sessions` - Authentication sessions
- `markets` - Market definitions
- `assets` - Tradeable instruments
- `analyses` - Asset analysis content
- `daily_analysis` - Google Sheets synced data
- `forecast_history` - History of Success records

## Troubleshooting

### CORS Errors
Make sure `CORS_ORIGINS` in `backend/.env` matches your frontend URL.

### Google OAuth Not Working
1. Verify `GOOGLE_REDIRECT_URI` matches exactly in both `.env` and Google Console
2. Check that the OAuth consent screen is configured
3. Ensure the app is in "Testing" mode with your email as a test user

### Database Connection Issues
1. Check MongoDB Atlas IP whitelist (add `0.0.0.0/0` for development)
2. Verify connection string is correct
3. Check database user permissions

## API Endpoints

### Authentication
- `GET /api/auth/google` - Initiate Google OAuth
- `GET /api/auth/google/callback` - OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Markets & Assets
- `GET /api/markets` - List markets
- `GET /api/assets` - List assets

### History of Success
- `GET /api/history/summary` - Performance summary
- `GET /api/history/forecasts` - Forecast list
- `GET /api/history/performance` - Bar chart data
- `GET /api/history/cumulative` - Line chart data

### Admin Endpoints (requires admin access)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users/subscription` - Manage subscriptions
- `POST /api/admin/history/forecast` - Create forecast
- `PUT /api/admin/history/forecast/{id}` - Update forecast
- `DELETE /api/admin/history/forecast/{id}` - Delete forecast
