# Tahlil One - Subscription System Documentation

## Overview
Tahlil One uses a subscription-based access system with three tiers. All subscriptions are linked to the user's Google user ID.

---

## Subscription Types

| Type | Level | Access |
|------|-------|--------|
| **Beginner** | 1 | Basic analysis access |
| **Advanced** | 2 | Enhanced analysis access |
| **Premium** | 3 | Full platform access |

### Subscription Hierarchy
Premium > Advanced > Beginner

Users with higher-tier subscriptions automatically have access to lower-tier features.

---

## User Subscription Fields

Each user has the following subscription-related fields:

```json
{
  "subscription_type": "Premium | Advanced | Beginner | null",
  "subscription_status": "active | expired | none",
  "subscription_start_date": "2026-01-07T10:30:00.000Z",
  "subscription_end_date": "2026-02-07T10:30:00.000Z"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `subscription_type` | string | Tier level (Premium, Advanced, Beginner, or null) |
| `subscription_status` | string | Current status (active, expired, none) |
| `subscription_start_date` | ISO datetime | When subscription started |
| `subscription_end_date` | ISO datetime | When subscription expires |

---

## Access Logic

### Rule 1: Check Subscription Status
```
IF subscription_status == "active" AND current_date <= subscription_end_date
  → Full platform access granted
ELSE
  → Limited access only
```

### Rule 2: Automatic Expiry Check
On every user authentication:
1. System checks if `current_date > subscription_end_date`
2. If expired, automatically updates `subscription_status` to "expired"
3. Access is immediately restricted

### Rule 3: Admin Override
Users with `access_level: "admin"` bypass all subscription checks and have full access regardless of subscription status.

---

## Access Enforcement Points

### 1. On Login
✅ Subscription status checked when user authenticates
✅ Expired subscriptions automatically updated

### 2. On Page Load
✅ Subscription banner displayed showing current status
✅ Access restrictions applied before content loads

### 3. On Every API Request
✅ Protected endpoints verify active subscription
✅ 403 error returned if subscription invalid

---

## API Endpoints

### GET `/api/subscriptions/status`
Returns current user's subscription status.

**Response:**
```json
{
  "subscription_type": "Premium",
  "subscription_status": "active",
  "has_access": true,
  "days_remaining": 25,
  "subscription_end_date": "2026-02-07T10:30:00.000Z"
}
```

### POST `/api/subscriptions/activate`
Activates a subscription for the current user.

**Request:**
```json
{
  "subscription_type": "Premium",
  "duration_days": 30
}
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "google_user_id": "1234567890",
  "email": "user@example.com",
  "subscription_type": "Premium",
  "subscription_status": "active",
  "subscription_start_date": "2026-01-07T10:30:00.000Z",
  "subscription_end_date": "2026-02-06T10:30:00.000Z"
}
```

### GET `/api/analysis/{asset_id}` (Protected)
Requires active subscription to access analysis data.

**Access Rules:**
- ❌ `subscription_status: "none"` → 403 Forbidden
- ❌ `subscription_status: "expired"` → 403 Forbidden  
- ✅ `subscription_status: "active"` → Analysis returned
- ✅ `access_level: "admin"` → Always allowed

---

## Frontend Implementation

### Subscription Context
Provides global subscription state management.

```jsx
import { useSubscription } from '@/contexts/SubscriptionContext';

function MyComponent() {
  const { subscriptionStatus, loading, checkSubscription } = useSubscription();
  
  if (subscriptionStatus?.has_access) {
    // Show premium content
  } else {
    // Show upgrade prompt
  }
}
```

### Subscription Banner
Visual indicator of subscription status displayed on dashboard.

**States:**
- 🟢 **Active**: Shows subscription type and days remaining
- 🔴 **Expired**: Warning message with limited access notice
- ⚪ **None**: Informational message about no subscription

### Access Denied Screen
Shown when user tries to view analysis without active subscription.

**Features:**
- Lock icon visual indicator
- Clear message about subscription requirement
- Current status display
- Bilingual support (Arabic/English)

---

## Subscription Management

### Activating a Subscription (via MongoDB)

```javascript
// Connect to database
mongosh

use('test_database');

// Activate 30-day Premium subscription
db.users.updateOne(
  { email: "user@example.com" },
  {
    $set: {
      subscription_type: "Premium",
      subscription_status: "active",
      subscription_start_date: new Date().toISOString(),
      subscription_end_date: new Date(Date.now() + 30*24*60*60*1000).toISOString()
    }
  }
)
```

### Extending a Subscription

```javascript
// Add 30 more days to existing subscription
var user = db.users.findOne({ email: "user@example.com" });
var currentEnd = new Date(user.subscription_end_date);
var newEnd = new Date(currentEnd.getTime() + 30*24*60*60*1000);

db.users.updateOne(
  { email: "user@example.com" },
  {
    $set: {
      subscription_end_date: newEnd.toISOString(),
      subscription_status: "active"
    }
  }
)
```

### Upgrading Subscription Type

```javascript
// Upgrade from Beginner to Premium
db.users.updateOne(
  { email: "user@example.com" },
  {
    $set: {
      subscription_type: "Premium"
    }
  }
)
```

### Canceling a Subscription

```javascript
// Immediate cancellation
db.users.updateOne(
  { email: "user@example.com" },
  {
    $set: {
      subscription_status: "expired",
      subscription_end_date: new Date().toISOString()
    }
  }
)
```

---

## Testing Subscriptions

### Create Test User with Active Subscription

```bash
mongosh --eval "
use('test_database');

var userId = 'test_user_' + Date.now();
var sessionToken = 'test_session_' + Date.now();

// Create user with Premium subscription
db.users.insertOne({
  user_id: userId,
  google_user_id: 'google_' + Date.now(),
  email: 'test@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  access_level: 'Limited',
  subscription_type: 'Premium',
  subscription_status: 'active',
  subscription_start_date: new Date().toISOString(),
  subscription_end_date: new Date(Date.now() + 30*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
});

// Create session
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});

print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

### Test API Access with curl

```bash
API_URL="https://your-app.com"
SESSION_TOKEN="your_session_token"

# Check subscription status
curl -X GET "$API_URL/api/subscriptions/status" \
  -H "Authorization: Bearer $SESSION_TOKEN"

# Try to access analysis (requires active subscription)
curl -X GET "$API_URL/api/analysis/asset_aramco" \
  -H "Authorization: Bearer $SESSION_TOKEN"
```

---

## Common Scenarios

### Scenario 1: New User Login
1. User signs in with Google OAuth
2. System creates user record with `subscription_status: "none"`
3. User can view markets/assets but cannot view analysis
4. Access denied screen shown when trying to view analysis

### Scenario 2: Activating Subscription
1. Admin activates subscription via database
2. User refreshes page or logs out/in
3. Subscription context automatically updates
4. User now has full access to analysis

### Scenario 3: Subscription Expiry
1. User has active subscription (ends 2026-02-01)
2. Current date becomes 2026-02-02
3. On next login/API call:
   - System detects `current_date > subscription_end_date`
   - Updates `subscription_status` to "expired"
   - Access immediately restricted
4. User sees expired subscription banner

### Scenario 4: Admin Access
1. User has `access_level: "admin"`
2. Even if `subscription_status: "none"`, admin can access everything
3. Subscription checks bypassed for admins

---

## Monitoring & Reporting

### List Users by Subscription Status

```javascript
// Active subscriptions
db.users.find(
  { subscription_status: "active" },
  { _id: 0, email: 1, subscription_type: 1, subscription_end_date: 1 }
).pretty()

// Expired subscriptions
db.users.find(
  { subscription_status: "expired" },
  { _id: 0, email: 1, subscription_type: 1, subscription_end_date: 1 }
).pretty()

// Users without subscription
db.users.find(
  { subscription_status: "none" },
  { _id: 0, email: 1, name: 1, created_at: 1 }
).pretty()
```

### Count Subscriptions by Type

```javascript
db.users.aggregate([
  { $match: { subscription_status: "active" } },
  { $group: { _id: "$subscription_type", count: { $sum: 1 } } }
])
```

### Find Expiring Subscriptions (Next 7 Days)

```javascript
var nextWeek = new Date(Date.now() + 7*24*60*60*1000);

db.users.find({
  subscription_status: "active",
  subscription_end_date: { 
    $gte: new Date().toISOString(),
    $lte: nextWeek.toISOString()
  }
}, {
  _id: 0,
  email: 1,
  subscription_type: 1,
  subscription_end_date: 1
}).pretty()
```

---

## Security Considerations

### ✅ Best Practices

1. **Server-Side Validation**: Never trust client-side subscription checks
2. **Automatic Expiry**: System automatically expires subscriptions on schedule
3. **Immutable Dates**: Subscription dates stored in UTC ISO format
4. **Session Verification**: Every protected endpoint verifies subscription status
5. **Audit Trail**: Track subscription changes with timestamps

### ⚠️ Important Notes

- Subscription checks happen on **every API request** to protected resources
- Frontend displays are informational only; backend enforces access
- Users cannot manipulate their subscription status via API
- Only database admin can manually modify subscriptions
- Google user ID ensures subscription follows user across devices

---

## Troubleshooting

### Issue: User has active subscription but cannot access analysis

**Check:**
1. Verify subscription_end_date hasn't passed
2. Ensure subscription_status is "active"
3. Check if user logged out and back in
4. Verify backend is enforcing correct logic

```javascript
// Debug user subscription
db.users.findOne(
  { email: "user@example.com" },
  { _id: 0, subscription_type: 1, subscription_status: 1, subscription_end_date: 1 }
)
```

### Issue: Subscription expired but user still has access

**Fix:**
1. User session might be cached
2. Force user to logout and login again
3. Check backend logs for subscription check execution

### Issue: Cannot activate subscription

**Verify:**
1. Subscription type is valid ("Beginner", "Advanced", or "Premium")
2. Duration_days is positive number
3. User is authenticated
4. Database connection is working

---

## Future Enhancements

Potential features for subscription system:
- Payment gateway integration (Stripe, PayPal)
- Automatic renewal options
- Subscription downgrade/upgrade flows
- Trial periods (7-day, 14-day, 30-day)
- Promo codes and discounts
- Email notifications for expiring subscriptions
- Usage analytics per subscription tier
- Grace period after expiration (3-7 days)
