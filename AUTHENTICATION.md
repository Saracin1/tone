# Tahlil One - Authentication System Documentation

## Overview
Tahlil One uses **Google OAuth** as the sole authentication method. No passwords are stored in the database.

---

## Authentication Flow

### 1. User Login Process
```
User clicks "Sign in with Google"
    ↓
Redirected to Google OAuth (handled by Emergent Auth)
    ↓
User authenticates with Google (Google handles password)
    ↓
Google returns user profile data
    ↓
Backend creates/updates user record
    ↓
Session token stored in secure httpOnly cookie
    ↓
User redirected to dashboard
```

### 2. What Happens on First Login

When a user logs in for the first time:

1. **User Record Created** in MongoDB with:
   - `user_id`: Unique internal ID (generated)
   - `google_user_id`: Unique Google user ID (from Google OAuth)
   - `email`: User's Google email
   - `name`: User's display name from Google
   - `picture`: User's Google profile picture URL
   - `access_level`: Default value = **"Limited"**
   - `created_at`: Timestamp of account creation

2. **Session Created**:
   - 7-day expiring session token
   - Stored in secure httpOnly cookie
   - Linked to user via `user_id`

---

## Access Levels

Users have an `access_level` field that determines their permissions:

| Access Level | Description | Permissions |
|--------------|-------------|-------------|
| **Limited** | Default for all new users | View markets, assets, and analysis only |
| **admin** | Administrative access | Full access: Create/edit markets, assets, and analysis |

### Upgrading User Access

To grant admin access to a user, update their record in MongoDB:

```javascript
db.users.updateOne(
  { email: "user@example.com" },
  { $set: { access_level: "admin" } }
)
```

---

## What is Stored in Database

### Users Collection
```json
{
  "user_id": "user_abc123def456",
  "google_user_id": "1234567890",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "access_level": "Limited",
  "created_at": "2026-01-07T10:30:00.000Z"
}
```

### User Sessions Collection
```json
{
  "user_id": "user_abc123def456",
  "session_token": "sess_xyz789...",
  "expires_at": "2026-01-14T10:30:00.000Z",
  "created_at": "2026-01-07T10:30:00.000Z"
}
```

---

## What is NOT Stored

❌ **No passwords** - Google OAuth handles all password management
❌ **No password hashes** - We never see or touch user passwords
❌ **No local authentication** - Only Google OAuth is supported

---

## Security Features

### 1. Secure Cookie Storage
- `httpOnly`: Cookie not accessible via JavaScript (XSS protection)
- `secure`: Cookie only sent over HTTPS
- `sameSite: "none"`: Required for cross-origin authentication
- `path: "/"`: Cookie valid for entire application
- `max_age: 7 days`: Automatic expiration

### 2. Session Management
- Sessions expire after 7 days
- Expired sessions are rejected automatically
- Users can logout to invalidate session immediately

### 3. Authorization Checks
- Every protected endpoint checks:
  1. Valid session token exists
  2. Session hasn't expired
  3. User has required access level

---

## API Endpoints

### Authentication Endpoints

#### POST `/api/auth/session`
Creates a new session after Google OAuth.

**Request:**
```json
{
  "session_id": "temp_session_id_from_google"
}
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "google_user_id": "1234567890",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://...",
  "access_level": "Limited",
  "created_at": "2026-01-07T10:30:00.000Z"
}
```

#### GET `/api/auth/me`
Returns current authenticated user.

**Response:** Same as above

#### POST `/api/auth/logout`
Invalidates current session and clears cookie.

---

## Protected Routes

### Admin-Only Endpoints
Require `access_level: "admin"`

- `POST /api/markets` - Create market
- `POST /api/assets` - Create asset
- `POST /api/analysis` - Create/update analysis

### User Endpoints
Require any authenticated user (Limited or admin)

- `GET /api/markets` - View all markets
- `GET /api/assets` - View all assets
- `GET /api/analysis/{asset_id}` - View analysis

---

## User Permissions & Subscriptions

All permissions and subscriptions are linked to the **Google user ID** (`google_user_id` field).

This ensures:
- Users keep their data even if they change their email in Google
- Unique identification across all services
- No duplicate accounts for the same Google user

### Example: Checking User Permissions
```python
user = await get_current_user(request)
if user.access_level != "admin":
    raise HTTPException(status_code=403, detail="Admin access required")
```

---

## Admin Account Management

### Creating First Admin
After first deployment, manually update a user to admin:

```javascript
// Connect to MongoDB
mongosh

// Switch to database
use('test_database');

// Make user admin
db.users.updateOne(
  { email: "your-email@gmail.com" },
  { $set: { access_level: "admin" } }
)
```

### Listing All Users
```javascript
db.users.find({}, { _id: 0, email: 1, access_level: 1, name: 1 }).pretty()
```

### Revoking Admin Access
```javascript
db.users.updateOne(
  { email: "user@example.com" },
  { $set: { access_level: "Limited" } }
)
```

---

## Development & Testing

### Creating Test User Session (for development)
```bash
mongosh --eval "
use('test_database');
var userId = 'test_user_' + Date.now();
var sessionToken = 'test_session_' + Date.now();

db.users.insertOne({
  user_id: userId,
  google_user_id: 'google_test_' + Date.now(),
  email: 'test@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  access_level: 'Limited',
  created_at: new Date().toISOString()
});

db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});

print('Session token: ' + sessionToken);
"
```

---

## Troubleshooting

### User can't access admin features
1. Check their access level:
```javascript
db.users.findOne({ email: "user@example.com" }, { _id: 0, access_level: 1 })
```

2. If access_level is "Limited", upgrade them:
```javascript
db.users.updateOne(
  { email: "user@example.com" },
  { $set: { access_level: "admin" } }
)
```

3. User must logout and login again for changes to take effect

### Session expired errors
- Sessions expire after 7 days
- User needs to login again via Google OAuth

### Multiple accounts for same user
- Should not happen if Google user ID is properly stored
- Check for duplicate `google_user_id` values
- Merge accounts if needed (keep the one with desired access_level)

---

## Security Best Practices

✅ **DO:**
- Always use HTTPS in production
- Keep session expiry reasonable (7 days default)
- Log authentication events
- Monitor for suspicious session activity

❌ **DON'T:**
- Never log session tokens
- Don't expose Google user IDs in public APIs
- Don't create backdoor authentication methods
- Don't store sensitive user data without encryption

---

## Future Enhancements

Potential features to add:
- Email notifications for admin actions
- Audit log for user access
- Rate limiting for API endpoints
- Two-factor authentication (via Google)
- Custom access levels beyond Limited/admin
