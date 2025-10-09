# SlyWriter Authentication Endpoints

**Base URL**: `https://slywriterapp.onrender.com`

## Summary of Available Authentication Endpoints

All authentication endpoints are now standardized and documented below.

---

## 1. Google OAuth Login (Web App)

**Endpoint**: `POST /auth/google/login`

**Purpose**: Authenticate users via Google Sign-In for the web application.

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "credential": "GOOGLE_ID_TOKEN_HERE"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "is_new_user": false,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "plan": "Free",
    "usage": 0,
    "humanizer_usage": 0,
    "ai_gen_usage": 0,
    "referrals": {
      "code": "ABC123XYZ",
      "count": 0,
      "tier_claimed": 0,
      "bonus_words": 0
    },
    "premium_until": null,
    "word_limit": 500,
    "humanizer_limit": 0,
    "ai_gen_limit": 0
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:
- `400 Bad Request`: No credential provided or invalid token
- `401 Unauthorized`: Invalid Google token
- `500 Internal Server Error`: Server error

---

## 2. Get User Profile (NEW!)

**Endpoint**: `GET /auth/profile`

**Purpose**: Get the current authenticated user's profile using their JWT token.

**Request Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN_HERE
```

**Response** (200 OK):
```json
{
  "id": 123,
  "email": "user@example.com",
  "plan": "Free",
  "usage": 150,
  "humanizer_usage": 0,
  "ai_gen_usage": 0,
  "profile_picture": "https://lh3.googleusercontent.com/a/...",
  "referrals": {
    "code": "ABC123XYZ",
    "count": 2,
    "tier_claimed": 1,
    "bonus_words": 1000
  },
  "premium_until": null,
  "word_limit": 500,
  "humanizer_limit": 0,
  "ai_gen_limit": 0
}
```

**Error Responses**:
- `401 Unauthorized`: Missing, invalid, or expired token
- `404 Not Found`: User not found
- `500 Internal Server Error`: Server error

---

## 3. Email Verification

**Endpoint**: `POST /auth/verify-email`

**Purpose**: Verify email token sent via magic link.

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "token": "JWT_EMAIL_TOKEN_HERE"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "plan": "Free",
    "usage": 0,
    "humanizer_usage": 0,
    "ai_gen_usage": 0,
    "referrals": {
      "code": "ABC123XYZ",
      "count": 0,
      "tier_claimed": 0,
      "bonus_words": 0
    },
    "premium_until": null,
    "word_limit": 500,
    "humanizer_limit": 0,
    "ai_gen_limit": 0
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:
- `400 Bad Request`: Token required or invalid
- `401 Unauthorized`: Token expired or invalid

---

## 4. Standard Login

**Endpoint**: `POST /api/auth/login`

**Purpose**: Login with email (password optional for legacy support).

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "optional_password"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "plan": "Free",
    "usage": 0,
    "humanizer_usage": 0,
    "ai_gen_usage": 0,
    "referrals": {
      "code": "ABC123XYZ",
      "count": 0,
      "tier_claimed": 0,
      "bonus_words": 0
    },
    "premium_until": null,
    "word_limit": 500,
    "humanizer_limit": 0,
    "ai_gen_limit": 0
  },
  "token": "token_123"
}
```

**Error Responses**:
- `400 Bad Request`: Email required

---

## 5. Register New User

**Endpoint**: `POST /api/auth/register`

**Purpose**: Register a new user account.

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "password": "optional_password"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "user": {
    "id": 456,
    "email": "newuser@example.com",
    "plan": "Free",
    "usage": 0,
    "referrals": {
      "code": "XYZ789ABC",
      "count": 0,
      "tier_claimed": 0,
      "bonus_words": 0
    },
    "word_limit": 500,
    "humanizer_limit": 0,
    "ai_gen_limit": 0
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:
- `400 Bad Request`: Email required or user already exists

---

## 6. Logout

**Endpoint**: `POST /api/auth/logout`

**Purpose**: Logout current user (client-side session clearing).

**Response** (200 OK):
```json
{
  "success": true
}
```

---

## 7. Get User by ID

**Endpoint**: `GET /api/auth/user/{user_id}`

**Purpose**: Get user information by user ID or email.

**Path Parameters**:
- `user_id`: Can be numeric ID or email with special encoding

**Response** (200 OK):
```json
{
  "id": 123,
  "email": "user@example.com",
  "plan": "Free",
  "usage": 150,
  "humanizer_usage": 0,
  "ai_gen_usage": 0,
  "referrals": {
    "code": "ABC123XYZ",
    "count": 0,
    "tier_claimed": 0,
    "bonus_words": 0
  },
  "premium_until": null,
  "word_limit": 500,
  "humanizer_limit": 0,
  "ai_gen_limit": 0
}
```

**Error Responses**:
- `404 Not Found`: User not found

---

## 8. Authentication Status

**Endpoint**: `GET /api/auth/status`

**Purpose**: Check authentication status (simplified for desktop app).

**Response** (200 OK):
```json
{
  "authenticated": false,
  "message": "Desktop app authentication status check"
}
```

---

## 9. Desktop Google OAuth

**Endpoint**: `POST /api/auth/google`

**Purpose**: Desktop app Google OAuth flow initiation.

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Desktop Google OAuth - handled by client",
  "auth_url": "https://accounts.google.com/o/oauth2/auth"
}
```

---

## Common HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication failed or missing token
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

---

## JWT Token Format

All JWT tokens use the following structure:

**Header**:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload**:
```json
{
  "sub": "user@example.com",
  "user_id": 123,
  "exp": 1234567890
}
```

**Usage**:
Include in Authorization header as: `Bearer YOUR_TOKEN_HERE`

---

## Important Notes

1. **CORS**: All endpoints support CORS with wildcard origins (`*`) and credentials.

2. **Token Expiration**: JWT tokens have an expiration time. Handle `401 Unauthorized` responses with token refresh logic.

3. **Google OAuth**: Use the official Google Sign-In library to obtain the credential token for `/auth/google/login`.

4. **Profile Picture**: Available in `/auth/profile` response after Google Sign-In.

5. **Endpoint Consistency**: 
   - Web app endpoints: `/auth/*` (e.g., `/auth/google/login`, `/auth/profile`)
   - Desktop/API endpoints: `/api/auth/*` (e.g., `/api/auth/register`, `/api/auth/login`)

---

## Testing Endpoints

A comprehensive test script is available at `test_critical_endpoints.bat` to verify all endpoints.

To test manually:

```bash
# Test profile endpoint with your token
curl -X GET https://slywriterapp.onrender.com/auth/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Test Google login
curl -X POST https://slywriterapp.onrender.com/auth/google/login \
  -H "Content-Type: application/json" \
  -d '{"credential": "GOOGLE_ID_TOKEN"}'
```

---

## Questions or Issues?

If you encounter any authentication issues:

1. Check that you're using the correct endpoint path
2. Verify the Authorization header format: `Bearer TOKEN`
3. Ensure tokens haven't expired
4. Check CORS headers if calling from browser
5. Review backend logs for detailed error messages

