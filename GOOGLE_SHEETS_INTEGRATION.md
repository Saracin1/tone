# Tahlil One - Google Sheets Integration Guide

## Overview
Automated daily market analysis ingestion system that reads data from Google Sheets and syncs it into the platform database. **Zero manual intervention required.**

---

## Philosophy

```
Data In → Data Stored → Data Displayed
```

**No AI generation. No price prediction. No interpretation.**

This is a **professional data pipeline**, not a trading signal generator.

---

## Google Sheet Structure

### Required Format

| Column | Name | Type | Description | Example |
|--------|------|------|-------------|---------|
| A | Market | string | Market name exactly as written | `NASDAQ`, `Tadawul KSA`, `NYSE` |
| B | Stock Code | string | Instrument identifier | `$TSLA`, `8310`, `AAPL` |
| C | Insight Type | string | Analysis bias | `Bullish Strong`, `Bearish Weak` |
| D | Date & Time | string | Format: `DD.MM.YYYY [HH:MM:SS]` | `07.01.2026 [09:30:00]` |
| E | Analysis Price | string | Entry/reference price | `245.50`, `87.25` |
| F | Target | string | Target price | `275.00`, `95.00` |
| G | Critical Level | string | Stop/support/resistance | `230.00`, `80.00` |

### Example Rows

```
NASDAQ          | $TSLA | Bullish Strong | 07.01.2026 [09:30:00] | 245.50 | 275.00 | 230.00
Tadawul KSA     | 8310  | Bearish Weak   | 07.01.2026 [14:00:00] | 87.25  | 80.00  | 92.50
NYSE            | AAPL  | Neutral        | 07.01.2026 [09:30:00] | 185.30 | 190.00 | 180.00
```

### Critical Rules

⚠️ **DO NOT:**
- Normalize market names
- Modify stock codes
- Auto-correct symbols
- Change formatting
- Add calculated fields

✅ **DO:**
- Keep data exactly as provided
- Preserve original formatting
- Maintain case sensitivity
- Use exact column order

---

## Setup Instructions

### 1. Create Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable **Google Sheets API**
4. Create Service Account:
   - Navigate to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name: `tahlil-one-sheets-reader`
   - Description: `Read-only access for daily analysis`
5. Create Key:
   - Click on created service account
   - **Keys** tab → **Add Key** → **Create new key**
   - Choose **JSON** format
   - Download the JSON file

### 2. Share Google Sheet with Service Account

1. Open your Google Sheet
2. Click **Share** button
3. Add service account email (from JSON file):
   ```
   tahlil-one-sheets-reader@project-id.iam.gserviceaccount.com
   ```
4. Set permission to **Viewer**
5. Click **Send**

### 3. Configure Environment Variable

Add the service account credentials to backend `.env`:

```bash
# Open the JSON file and copy its entire contents
cat /path/to/service-account-key.json

# Add to .env file (single line, no line breaks)
GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account","project_id":"...","private_key":"..."}'
```

**Important:** Ensure the entire JSON is on one line, enclosed in single quotes.

### 4. Get Spreadsheet ID

From your Google Sheets URL:
```
https://docs.google.com/spreadsheets/d/1A2B3C4D5E6F7G8H9I0J/edit

Spreadsheet ID: 1A2B3C4D5E6F7G8H9I0J
```

---

## API Usage

### Sync Data from Google Sheets

**Endpoint:** `POST /api/admin/sheets/sync`

**Authentication:** Admin only

**Request:**
```json
{
  "spreadsheet_id": "1A2B3C4D5E6F7G8H9I0J",
  "range_name": "Sheet1!A2:G"
}
```

**Response:**
```json
{
  "total_rows": 50,
  "inserted": 15,
  "updated": 30,
  "skipped": 5,
  "errors": [
    "Row 12: Missing required fields",
    "Row 25: Invalid datetime format: 07-01-2026"
  ]
}
```

### Get Daily Analysis

**Endpoint:** `GET /api/daily-analysis`

**Authentication:** Active subscription required

**Query Parameters:**
- `market` (optional): Filter by market name
- `limit` (optional): Max records (default: 100)

**Response:**
```json
[
  {
    "record_id": "daily_abc123def456",
    "market": "NASDAQ",
    "instrument_code": "$TSLA",
    "insight_type": "Bullish Strong",
    "analysis_datetime": "2026-01-07T09:30:00+00:00",
    "analysis_price": "245.50",
    "target_price": "275.00",
    "critical_level": "230.00",
    "source": "google_sheets",
    "created_at": "2026-01-07T10:15:00+00:00",
    "updated_at": "2026-01-07T10:15:00+00:00"
  }
]
```

### Get Available Markets

**Endpoint:** `GET /api/daily-analysis/markets`

**Response:**
```json
{
  "markets": ["NASDAQ", "NYSE", "Tadawul KSA", "DFM", "ADX"]
}
```

---

## Database Schema

### Collection: `daily_analysis`

```javascript
{
  record_id: "daily_abc123def456",           // Generated unique ID
  market: "NASDAQ",                          // Exact from sheet
  instrument_code: "$TSLA",                  // Exact from sheet
  insight_type: "Bullish Strong",            // Exact from sheet
  analysis_datetime: "2026-01-07T09:30:00Z", // Parsed ISO format
  analysis_price: "245.50",                  // Exact from sheet
  target_price: "275.00",                    // Exact from sheet
  critical_level: "230.00",                  // Exact from sheet
  source: "google_sheets",                   // Always this value
  created_at: "2026-01-07T10:15:00Z",       // First insertion
  updated_at: "2026-01-07T10:15:00Z"        // Last update
}
```

### Unique Key (Prevents Duplicates)

Combination of:
```
market + instrument_code + analysis_datetime
```

If record exists → **Update**
If record new → **Insert**

---

## Update Logic

### Scenario 1: New Analysis
```
Sheet: NASDAQ | $TSLA | Bullish Strong | 07.01.2026 [09:30:00] | ...
Database: (not found)
Action: INSERT new record
```

### Scenario 2: Updated Analysis
```
Sheet: NASDAQ | $TSLA | Bullish Strong | 07.01.2026 [09:30:00] | ...
Database: (exists with same market + instrument + datetime)
Action: UPDATE existing record
```

### Scenario 3: Same Instrument, Different Time
```
Sheet: NASDAQ | $TSLA | Bullish Strong | 07.01.2026 [14:30:00] | ...
Database: (NASDAQ | $TSLA | 09:30:00 exists)
Action: INSERT new record (different datetime)
```

---

## Automation Workflows

### Manual Sync (Admin Dashboard)

1. Login as admin
2. Navigate to **Admin Dashboard** → **Daily Analysis** tab
3. Enter Spreadsheet ID
4. Click "Sync Now"
5. View sync results

### Scheduled Sync (Cron Job)

Create a cron job to run daily:

```bash
#!/bin/bash
# /app/scripts/daily-sync.sh

API_URL="https://your-app.com/api"
ADMIN_TOKEN="your_admin_session_token"
SPREADSHEET_ID="1A2B3C4D5E6F7G8H9I0J"

curl -X POST "$API_URL/admin/sheets/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"spreadsheet_id\": \"$SPREADSHEET_ID\",
    \"range_name\": \"Sheet1!A2:G\"
  }"
```

**Cron Schedule (Daily at 7 AM):**
```cron
0 7 * * * /app/scripts/daily-sync.sh >> /var/log/daily-sync.log 2>&1
```

### Webhook Sync (Real-time)

Use Google Apps Script to trigger sync on sheet edit:

```javascript
// Google Apps Script
function onEdit(e) {
  var url = 'https://your-app.com/api/admin/sheets/sync';
  var spreadsheetId = SpreadsheetApp.getActive().getId();
  
  var payload = {
    'spreadsheet_id': spreadsheetId,
    'range_name': 'Sheet1!A2:G'
  };
  
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      'Authorization': 'Bearer YOUR_ADMIN_TOKEN'
    },
    'payload': JSON.stringify(payload)
  };
  
  UrlFetchApp.fetch(url, options);
}
```

---

## Error Handling

### Row Validation Errors

**Issue:** Row skipped during sync

**Common Causes:**
1. **Missing columns:** Row has < 7 columns
2. **Empty required fields:** Market, Stock Code, Insight Type, or Date/Time is blank
3. **Invalid datetime format:** Not in `DD.MM.YYYY [HH:MM:SS]` format

**Example Error:**
```
"Row 12: Insufficient columns (expected 7, got 5)"
"Row 18: Missing required fields"
"Row 23: Invalid datetime format: 2026-01-07"
```

**Solution:**
- Review sheet row by row
- Ensure all 7 columns present
- Fill required fields
- Use correct datetime format

### API Connection Errors

**Issue:** `Google Sheets API error`

**Causes:**
1. Invalid spreadsheet ID
2. Service account not shared with sheet
3. Credentials not configured
4. API not enabled

**Solution:**
1. Verify spreadsheet ID
2. Share sheet with service account email
3. Check `GOOGLE_SHEETS_CREDENTIALS` in .env
4. Enable Google Sheets API in Cloud Console

### Permission Errors

**Issue:** `Admin access required`

**Solution:**
- Verify user has `access_level: "admin"`
- Check authentication token validity

---

## Testing

### Test Sync Locally

```bash
# Set environment variables
export GOOGLE_SHEETS_CREDENTIALS='...'
export MONGO_URL='...'
export DB_NAME='test_database'

# Create test sheet with sample data
# Get spreadsheet ID: 1A2B3C4D5E6F7G8H9I0J

# Test sync via API
curl -X POST "http://localhost:8001/api/admin/sheets/sync" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "1A2B3C4D5E6F7G8H9I0J",
    "range_name": "Sheet1!A2:G"
  }'
```

### Verify Data in Database

```javascript
// MongoDB
use test_database;

// Count records
db.daily_analysis.countDocuments()

// View recent records
db.daily_analysis.find().sort({analysis_datetime: -1}).limit(10).pretty()

// Check for duplicates (should be 0)
db.daily_analysis.aggregate([
  {
    $group: {
      _id: {
        market: "$market",
        instrument_code: "$instrument_code",
        analysis_datetime: "$analysis_datetime"
      },
      count: { $sum: 1 }
    }
  },
  { $match: { count: { $gt: 1 } } }
])
```

---

## Best Practices

### Sheet Management

✅ **DO:**
1. Keep header row (A1:G1) intact
2. Start data from row 2
3. Use consistent datetime format
4. Fill all required columns
5. Test with small batch first

❌ **DON'T:**
1. Change column order
2. Merge cells
3. Use formulas in data columns
4. Leave gaps in rows
5. Modify historical records unnecessarily

### Data Quality

✅ **DO:**
1. Validate data before adding to sheet
2. Use consistent market names
3. Keep instrument codes standardized
4. Document unusual entries
5. Backup sheet regularly

❌ **DON'T:**
1. Use abbreviations inconsistently
2. Mix datetime formats
3. Leave required fields empty
4. Add extra columns in between
5. Delete historical data

### Security

✅ **DO:**
1. Keep service account credentials secure
2. Use read-only permissions for service account
3. Rotate credentials periodically
4. Monitor sync logs
5. Restrict sheet edit access

❌ **DON'T:**
1. Share service account key publicly
2. Grant unnecessary permissions
3. Use same credentials across environments
4. Ignore failed sync notifications
5. Allow public sheet access

---

## Monitoring & Maintenance

### Sync Logs

Check sync results after each run:

```bash
# View recent syncs
tail -f /var/log/daily-sync.log

# Count successful syncs today
grep "inserted" /var/log/daily-sync.log | grep "$(date +%Y-%m-%d)" | wc -l
```

### Database Health

```javascript
// Check last sync time
db.daily_analysis.find().sort({updated_at: -1}).limit(1)

// Records by market
db.daily_analysis.aggregate([
  { $group: { _id: "$market", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// Records by date
db.daily_analysis.aggregate([
  {
    $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: { $toDate: "$analysis_datetime" } } },
      count: { $sum: 1 }
    }
  },
  { $sort: { _id: -1 } },
  { $limit: 30 }
])
```

### Alerts

Set up monitoring for:
- Failed syncs (>10% error rate)
- No syncs in 24 hours
- Duplicate records detected
- API rate limit reached
- Invalid credentials

---

## Troubleshooting

### No Data Synced

**Symptoms:** `total_rows: 0`, no errors

**Checks:**
1. ✅ Spreadsheet ID correct?
2. ✅ Range includes data rows? (not just header)
3. ✅ Sheet name correct? (case-sensitive)
4. ✅ Service account has access?

### All Rows Skipped

**Symptoms:** `skipped: 50`, `inserted: 0`, `updated: 0`

**Checks:**
1. ✅ Date format correct: `DD.MM.YYYY [HH:MM:SS]`
2. ✅ All 7 columns present in each row?
3. ✅ Required fields not empty?
4. ✅ Review error messages in response

### Duplicates Created

**Symptoms:** Same analysis appearing multiple times

**Cause:** Unique key mismatch (market + instrument + datetime)

**Solution:**
1. Check if datetime format changes between syncs
2. Ensure market names exactly match
3. Verify instrument codes consistent
4. Clean duplicates:
   ```javascript
   // Find duplicates
   db.daily_analysis.aggregate([...])
   
   // Remove manually after verification
   ```

---

## Future Enhancements

Potential improvements:
- Multiple sheet support
- Column mapping configuration
- Data validation rules
- Conflict resolution strategies
- Historical data archival
- Performance analytics
- Multi-language market names
- Custom datetime formats
- Webhook notifications
- Rollback functionality

---

## Support

For issues or questions:
1. Review this documentation
2. Check sync logs
3. Verify Google Sheets setup
4. Test with minimal data set
5. Contact system administrator

**Remember:** This system is designed for accuracy and reliability. Take time to set it up correctly once, then enjoy automated daily updates.
