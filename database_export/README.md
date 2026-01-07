# Tahlil One - Database Export

## Contents

This folder contains all MongoDB collections exported from Tahlil One:

| File | Collection | Description |
|------|------------|-------------|
| `users.json` | users | User accounts, subscriptions, access levels |
| `user_sessions.json` | user_sessions | Active authentication sessions |
| `markets.json` | markets | Market definitions (GCC, Istanbul, Cairo) |
| `assets.json` | assets | Tradeable assets/instruments |
| `analyses.json` | analyses | Asset analysis content |
| `daily_analysis.json` | daily_analysis | Google Sheets synced data |
| `forecast_history.json` | forecast_history | History of Success records |

## How to Import to Your Server

### Option 1: Using the Import Script (Recommended)

```bash
# Install pymongo
pip install pymongo

# Run import script
python import_database.py --mongo-url "mongodb://your-server:27017" --db-name "tahlil_one"
```

### Option 2: Using mongoimport (CLI)

```bash
# For each collection:
mongoimport --uri "mongodb://your-server:27017/tahlil_one" --collection users --file users.json --jsonArray
mongoimport --uri "mongodb://your-server:27017/tahlil_one" --collection user_sessions --file user_sessions.json --jsonArray
mongoimport --uri "mongodb://your-server:27017/tahlil_one" --collection markets --file markets.json --jsonArray
mongoimport --uri "mongodb://your-server:27017/tahlil_one" --collection assets --file assets.json --jsonArray
mongoimport --uri "mongodb://your-server:27017/tahlil_one" --collection analyses --file analyses.json --jsonArray
mongoimport --uri "mongodb://your-server:27017/tahlil_one" --collection daily_analysis --file daily_analysis.json --jsonArray
mongoimport --uri "mongodb://your-server:27017/tahlil_one" --collection forecast_history --file forecast_history.json --jsonArray
```

### Option 3: Using MongoDB Compass (GUI)

1. Open MongoDB Compass
2. Connect to your MongoDB server
3. Create database `tahlil_one`
4. For each collection, click "Add Data" → "Import File" → Select JSON file

## After Import: Update Backend Configuration

Update `/app/backend/.env`:

```env
MONGO_URL="mongodb://your-server:27017"
DB_NAME="tahlil_one"
```

Then restart the backend service.

## Data Summary

- **Users**: 3 accounts (including admin)
- **Markets**: 7 market definitions
- **Assets**: 7 tradeable instruments
- **Daily Analysis**: 6 records (test data)
- **Forecast History**: 6 records (test data)
- **Sessions**: 3 active sessions

## Notes

- User sessions may expire - users will need to re-login
- Google OAuth will continue to work with the same Google credentials
- Subscription data is preserved in user records
