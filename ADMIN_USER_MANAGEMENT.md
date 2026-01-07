# Tahlil One - Admin User Management Guide

## Overview
Admin panel provides complete manual control over user subscriptions. This is designed for VIP clients, private agreements, and special cases that require manual intervention.

---

## Accessing Admin Panel

**URL:** `https://your-app.com/admin`

**Requirements:**
- User must have `access_level: "admin"` in database
- Authenticated via Google OAuth

**Navigation:**
1. Login with admin Google account
2. Navigate to Admin Dashboard
3. Click on **"Users"** tab

---

## Admin Capabilities

### 1. View All Users
See complete list of all registered users with their subscription details:
- Name and email
- Current subscription type (Premium/Advanced/Beginner)
- Subscription status (active/expired/none)
- Expiration date

### 2. Activate Subscription
**Use Case:** New subscription for a user

**What it does:**
- Sets subscription type (Beginner/Advanced/Premium)
- Activates subscription immediately
- Sets start date to now
- Sets end date to now + duration

**Example:** Give user 30-day Premium subscription

### 3. Extend Subscription
**Use Case:** Add more time to existing subscription without overwriting

**What it does:**
- Adds duration to existing end date
- If subscription already expired, adds to current date
- Preserves or updates subscription type
- Does NOT reset start date

**Example:** User has Premium until Jan 30, extend by 15 days → expires Feb 14

### 4. Gift Subscription
**Use Case:** VIP clients or promotional offers

**What it does:**
- Same as Activate, but semantically indicates it's a gift
- Starts immediately with specified duration
- Can override existing subscription

**Example:** Gift 60-day Premium to VIP client

### 5. Deactivate Subscription
**Use Case:** Immediate cancellation or refund

**What it does:**
- Changes status to "expired"
- Sets end date to current time
- User immediately loses access

**Example:** User requests refund, admin deactivates subscription

---

## Step-by-Step Instructions

### Activating a New Subscription

1. Go to Admin Dashboard → Users tab
2. In "Manage Subscription" form:
   - **Select User:** Choose user email from dropdown
   - **Subscription Type:** Select Beginner/Advanced/Premium
   - **Duration (Days):** Enter number (e.g., 30, 60, 90, 365)
   - **Action:** Select "Activate"
3. Click "Apply"
4. User list refreshes with updated status

**Result:** User receives immediate access for specified duration

---

### Extending Existing Subscription

**Scenario:** User has Premium subscription expiring on Feb 1. You want to add 30 more days.

1. Go to Admin Dashboard → Users tab
2. In "Manage Subscription" form:
   - **Select User:** User will show current expiry: Feb 1
   - **Subscription Type:** Premium (keep same or upgrade)
   - **Duration (Days):** 30
   - **Action:** Select "Extend"
3. Click "Apply"

**Result:** New expiry date = March 3 (Feb 1 + 30 days)

**Important:** Extend is **additive**, not replacement!

---

### Gifting a Subscription

**Scenario:** VIP client or promotional offer

1. Go to Admin Dashboard → Users tab
2. In "Manage Subscription" form:
   - **Select User:** Choose recipient
   - **Subscription Type:** Premium (typically highest for gifts)
   - **Duration (Days):** 60, 90, or 365 (common gift durations)
   - **Action:** Select "Gift"
3. Click "Apply"

**Result:** User receives subscription starting immediately

**Use Cases:**
- VIP client onboarding
- Partnership agreements
- Promotional campaigns
- Loyalty rewards
- Beta testers

---

### Deactivating a Subscription

**Scenario:** User requests cancellation or refund

1. Go to Admin Dashboard → Users tab
2. In "Manage Subscription" form:
   - **Select User:** Choose user to deactivate
   - **Action:** Select "Deactivate"
   - (Duration and Type are ignored for deactivation)
3. Click "Apply"

**Result:** Subscription immediately expires, user loses access

**Warning:** This is immediate! User cannot access analysis anymore.

---

## API Endpoints (Backend)

### GET `/api/admin/users`
Returns list of all users with subscription details.

**Authentication:** Admin only

**Response:**
```json
[
  {
    "user_id": "user_abc123",
    "google_user_id": "1234567890",
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://...",
    "access_level": "Limited",
    "subscription_type": "Premium",
    "subscription_status": "active",
    "subscription_start_date": "2026-01-07T10:00:00.000Z",
    "subscription_end_date": "2026-02-07T10:00:00.000Z",
    "created_at": "2026-01-01T08:30:00.000Z"
  }
]
```

### POST `/api/admin/users/subscription`
Manage user subscription (activate/extend/gift/deactivate).

**Authentication:** Admin only

**Request:**
```json
{
  "user_email": "user@example.com",
  "subscription_type": "Premium",
  "duration_days": 30,
  "action": "activate"
}
```

**Actions:**
- `activate`: New subscription (overwrites existing)
- `extend`: Add duration to existing subscription
- `gift`: Same as activate (semantic difference)
- `deactivate`: Cancel subscription immediately

**Response:**
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "subscription_type": "Premium",
  "subscription_status": "active",
  "subscription_end_date": "2026-02-07T10:00:00.000Z"
}
```

---

## Usage Examples

### Example 1: VIP Client Onboarding
**Scenario:** New VIP client signs exclusive 1-year agreement

```
Action: Gift
Type: Premium
Duration: 365 days
```

**Result:** User gets Premium for 1 year from today

---

### Example 2: Private Agreement Extension
**Scenario:** Existing Premium client (expires Jan 31) renews for 6 months

```
Action: Extend
Type: Premium
Duration: 180 days
```

**Result:** New expiry = July 30 (Jan 31 + 180 days)

---

### Example 3: Beta Tester Program
**Scenario:** Give 50 beta testers 2 months free Premium

**Process:**
1. Export user list
2. For each beta tester:
   - Action: Gift
   - Type: Premium
   - Duration: 60 days

---

### Example 4: Upgrade During Active Subscription
**Scenario:** User has Beginner (expires Feb 15), wants Premium

```
Action: Extend (to preserve remaining days)
Type: Premium (upgrade)
Duration: 0 days (keep same end date)
```

**Result:** Upgraded to Premium, still expires Feb 15

---

### Example 5: Refund Processing
**Scenario:** User paid but requests full refund

```
Action: Deactivate
```

**Result:** Subscription canceled immediately, process refund externally

---

## Business Use Cases

### 1. VIP Clients
- **Duration:** 1 year (365 days)
- **Type:** Premium
- **Action:** Gift or Activate
- **Renewal:** Extend before expiry

### 2. Private Agreements
- **Duration:** Custom (30, 90, 180, 365 days)
- **Type:** As negotiated
- **Action:** Activate initially, Extend on renewal
- **Documentation:** Keep agreement reference in external system

### 3. Promotional Campaigns
- **Duration:** 30-60 days
- **Type:** Usually Premium to showcase full platform
- **Action:** Gift
- **Tracking:** Note campaign name in external records

### 4. Partnership Deals
- **Duration:** As per contract
- **Type:** Typically Premium or Advanced
- **Action:** Gift for first term, Extend for renewals
- **Management:** Link to partnership agreement ID

### 5. Customer Service Recovery
- **Duration:** 7-30 days compensation
- **Type:** Match their paid tier
- **Action:** Extend (add free days)
- **Reason:** Document in support ticket

---

## Bulk Operations (via MongoDB)

For large-scale operations, use MongoDB directly:

### Bulk Activate Multiple Users

```javascript
// List of user emails
const users = [
  "user1@example.com",
  "user2@example.com",
  "user3@example.com"
];

// Subscription details
const endDate = new Date(Date.now() + 30*24*60*60*1000); // 30 days

users.forEach(email => {
  db.users.updateOne(
    { email: email },
    {
      $set: {
        subscription_type: "Premium",
        subscription_status: "active",
        subscription_start_date: new Date().toISOString(),
        subscription_end_date: endDate.toISOString()
      }
    }
  );
});
```

### Bulk Extend VIP Clients

```javascript
// Extend all Premium users by 30 days
const premiumUsers = db.users.find({ 
  subscription_type: "Premium", 
  subscription_status: "active" 
});

premiumUsers.forEach(user => {
  const currentEnd = new Date(user.subscription_end_date);
  const newEnd = new Date(currentEnd.getTime() + 30*24*60*60*1000);
  
  db.users.updateOne(
    { user_id: user.user_id },
    { $set: { subscription_end_date: newEnd.toISOString() } }
  );
});
```

---

## Reporting

### Active Subscriptions Report

```javascript
db.users.aggregate([
  { $match: { subscription_status: "active" } },
  {
    $project: {
      _id: 0,
      email: 1,
      name: 1,
      subscription_type: 1,
      subscription_end_date: 1,
      days_remaining: {
        $dateDiff: {
          startDate: new Date(),
          endDate: { $toDate: "$subscription_end_date" },
          unit: "day"
        }
      }
    }
  },
  { $sort: { days_remaining: 1 } }
])
```

### Revenue by Subscription Type

```javascript
db.users.aggregate([
  { $match: { subscription_status: "active" } },
  { $group: { _id: "$subscription_type", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

### Expiring Soon (Next 7 Days)

```javascript
const nextWeek = new Date(Date.now() + 7*24*60*60*1000);

db.users.find({
  subscription_status: "active",
  subscription_end_date: {
    $gte: new Date().toISOString(),
    $lte: nextWeek.toISOString()
  }
}, {
  _id: 0,
  email: 1,
  name: 1,
  subscription_type: 1,
  subscription_end_date: 1
}).sort({ subscription_end_date: 1 })
```

---

## Best Practices

### ✅ DO

1. **Document Special Cases:** Keep external records of VIP agreements
2. **Check Before Extending:** Verify current subscription details
3. **Use Extend for Renewals:** Preserves existing subscription time
4. **Gift for Promotions:** Clear distinction from regular activations
5. **Deactivate for Immediate Needs:** Refunds, violations, etc.

### ❌ DON'T

1. **Don't Activate Over Active Subscription:** Use Extend instead
2. **Don't Forget Duration:** Zero or negative days won't work
3. **Don't Mix Actions:** Each action has specific purpose
4. **Don't Bulk Deactivate:** Without proper authorization
5. **Don't Modify Admin Subscriptions:** Admins don't need subscriptions

---

## Troubleshooting

### User Not Showing in List
**Issue:** Cannot find user in admin panel

**Solutions:**
1. Verify user has logged in at least once
2. Check database for user record
3. Refresh the admin page

### Subscription Not Activating
**Issue:** User still can't access after activation

**Solutions:**
1. User must logout and login again
2. Check subscription_end_date is in future
3. Verify subscription_status is "active"
4. Check browser console for errors

### Extend Not Adding Time
**Issue:** Extension not working as expected

**Solutions:**
1. Verify current subscription_end_date
2. If already expired, extension adds to current time
3. Check if subscription_type was also changed
4. Refresh user list to see updates

---

## Security Notes

1. **Admin Access Only:** All user management endpoints require admin role
2. **Audit Trail:** Consider logging all subscription changes
3. **No Direct API Access:** Users cannot modify their own subscriptions
4. **Email-Based Lookup:** Uses email for security (not user_id)
5. **Immediate Effect:** Changes take effect on user's next request

---

## Support Workflow

### Customer Requests Extension

1. **Verify Identity:** Confirm user identity via email
2. **Check Current Status:** View subscription in admin panel
3. **Calculate Duration:** Determine days to add
4. **Apply Extension:** Use Extend action
5. **Confirm:** User sees updated expiry date
6. **Document:** Record transaction in support system

### VIP Agreement Activation

1. **Receive Contract:** Review VIP agreement terms
2. **Note Details:** Subscription type and duration
3. **Apply Gift:** Use Gift action for clarity
4. **Set Reminder:** Calendar reminder for renewal
5. **Document:** Link agreement in CRM
6. **Notify User:** Email confirmation with details

---

## Future Enhancements

Potential features for admin user management:
- Bulk CSV upload for user subscriptions
- Subscription history/audit log
- Automated renewal reminders
- Payment integration with subscription tracking
- Usage analytics per user
- Subscription templates (3-month VIP, 1-year Premium, etc.)
- Schedule future activations
- Refund tracking integration
