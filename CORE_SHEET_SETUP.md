# Tahlil One - Core Google Sheet Integration Setup

## Spreadsheet Information

**Official Google Sheet:** https://docs.google.com/spreadsheets/d/1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4/edit?gid=1414441747

**Spreadsheet ID:** `1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4`

**Sheet Name/GID:** `1414441747`

**Default Range:** `Sheet1!A2:G`

---

## Setup Instructions

### Step 1: Create Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/Select project: `tahlil-one`
3. Enable **Google Sheets API**
4. Create Service Account:
   - Name: `tahlil-one-sheets-reader`
   - Role: None (read-only via sharing)
5. Generate JSON key

### Step 2: Share Sheet with Service Account

1. Open the official sheet: [Link](https://docs.google.com/spreadsheets/d/1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4/edit?gid=1414441747)
2. Click **Share** button
3. Add service account email (from JSON key):
   ```
   tahlil-one-sheets-reader@PROJECT-ID.iam.gserviceaccount.com
   ```
4. Permission: **Viewer**
5. Uncheck "Notify people"
6. Click **Share**

### Step 3: Configure Backend

Add to `/app/backend/.env`:

```bash
# Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account","project_id":"...FULL_JSON_HERE..."}'
```

**Important:** 
- Entire JSON on single line
- Enclosed in single quotes
- No line breaks

### Step 4: Restart Backend

```bash
sudo supervisorctl restart backend
```

### Step 5: Test Sync

1. Login as admin
2. Go to **Admin Dashboard** → **Daily Analysis** tab
3. Spreadsheet ID should be pre-filled: `1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4`
4. Range: `Sheet1!A2:G` (default)
5. Click **Sync Now**
6. Review sync results

---

## Expected Sheet Structure

| Column | Name | Example |
|--------|------|---------|
| A | Market | `NASDAQ`, `Tadawul KSA` |
| B | Stock Code | `$TSLA`, `8310` |
| C | Insight Type | `Bullish Strong` |
| D | Date & Time | `07.01.2026 [09:30:00]` |
| E | Analysis Price | `245.50` |
| F | Target | `275.00` |
| G | Critical Level | `230.00` |

---

## Verification

### Check Permissions

```bash
# Test API access
curl -X POST "https://your-app.com/api/admin/sheets/sync" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4",
    "range_name": "Sheet1!A2:G"
  }'
```

### Check Database

```javascript
// MongoDB
use test_database;

// Count synced records
db.daily_analysis.countDocuments()

// View latest
db.daily_analysis.find().sort({analysis_datetime: -1}).limit(5).pretty()

// Markets available
db.daily_analysis.distinct("market")
```

---

## Troubleshooting

### "Permission denied" error
- ✅ Service account email added to sheet with Viewer permission
- ✅ Sheet is not private/restricted

### "Invalid credentials" error
- ✅ `GOOGLE_SHEETS_CREDENTIALS` set in `.env`
- ✅ JSON is valid (no line breaks, proper escaping)
- ✅ Backend restarted after env change

### "No data found" error
- ✅ Sheet ID correct: `1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4`
- ✅ Range includes data: `Sheet1!A2:G`
- ✅ Sheet has data starting from row 2

### "Invalid datetime format" errors
- ✅ Date format: `DD.MM.YYYY [HH:MM:SS]`
- ✅ Example: `07.01.2026 [09:30:00]`
- ✅ Brackets around time are required

---

## Automation Options

### Option 1: Manual Sync (Current)
- Login as admin
- Navigate to Daily Analysis tab
- Click Sync Now
- Review results

### Option 2: Daily Cron Job

```bash
#!/bin/bash
# /app/scripts/daily-sync.sh

API_URL="https://your-app.com/api"
ADMIN_TOKEN="your_admin_session_token"

curl -X POST "$API_URL/admin/sheets/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4",
    "range_name": "Sheet1!A2:G"
  }' >> /var/log/daily-sync.log 2>&1
```

**Cron schedule (daily at 7 AM):**
```
0 7 * * * /app/scripts/daily-sync.sh
```

### Option 3: Real-time Webhook

**Google Apps Script** (add to sheet):

```javascript
function onEdit(e) {
  var url = 'https://your-app.com/api/admin/sheets/sync';
  
  var payload = {
    'spreadsheet_id': '1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4',
    'range_name': 'Sheet1!A2:G'
  };
  
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      'Authorization': 'Bearer YOUR_ADMIN_TOKEN'
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  
  UrlFetchApp.fetch(url, options);
}
```

---

## Data Flow

```
Google Sheet (Source of Truth)
    ↓
Admin triggers sync
    ↓
Backend reads all rows
    ↓
Validates each row
    ↓
Upserts into daily_analysis collection
    ↓
Data visible on platform
    ↓
Users view via subscription
```

---

## Important Notes

1. **Single Source of Truth:** This sheet controls ALL daily analysis data
2. **No Manual DB Edits:** Always update via Google Sheet
3. **Exact Values:** System preserves data exactly as provided
4. **Duplicate Prevention:** Unique key = market + instrument + datetime
5. **Error Isolation:** Bad rows skipped, good rows processed

---

## Support

If sync fails:
1. Check backend logs: `tail -f /var/log/supervisor/backend.*.log`
2. Verify service account has access
3. Test with minimal data first
4. Review error messages in sync results
5. Refer to `/app/GOOGLE_SHEETS_INTEGRATION.md` for detailed troubleshooting
