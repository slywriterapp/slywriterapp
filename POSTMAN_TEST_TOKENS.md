# Postman Testing Tokens for SlyWriter API

## Test User Account

**Email**: `postman.test@slywriter.ai`
**User ID**: `11`
**Password**: Not required (passwordless login)

---

## Working JWT Token (Valid for ~30 minutes)

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwb3N0bWFuLnRlc3RAc2x5d3JpdGVyLmFpIiwidXNlcl9pZCI6MTEsImV4cCI6MTc1OTk3MjU3OCwidHlwZSI6ImFjY2VzcyJ9.Zb-gFeL9inI3JzVxKP2xkNA4yPcHN1dzKPCHgqchcug
```

**How to Use in Postman**:
1. Open the request in Postman
2. Go to the "Headers" tab
3. Add a header:
   - **Key**: `Authorization`
   - **Value**: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwb3N0bWFuLnRlc3RAc2x5d3JpdGVyLmFpIiwidXNlcl9pZCI6MTEsImV4cCI6MTc1OTk3MjU3OCwidHlwZSI6ImFjY2VzcyJ9.Zb-gFeL9inI3JzVxKP2xkNA4yPcHN1dzKPCHgqchcug`

---

## How to Get a Fresh Token (When Expired)

### Method 1: Login (Recommended)
```bash
POST https://slywriterapp.onrender.com/api/auth/login
Content-Type: application/json

{
  "email": "postman.test@slywriter.ai"
}
```

### Method 2: Register New User
```bash
POST https://slywriterapp.onrender.com/api/auth/register
Content-Type: application/json

{
  "email": "your-test-email@example.com"
}
```

Both will return a response like:
```json
{
  "status": "success",
  "user": { ... },
  "token": "YOUR_NEW_JWT_TOKEN",
  "access_token": "YOUR_NEW_JWT_TOKEN"
}
```

Copy the `access_token` value and use it in your Authorization header.

---

## Endpoints That Require JWT Token

1. **GET /auth/profile** - Get current user profile
2. **GET /api/user-dashboard** - Get user dashboard data

### Example Postman Request:

**URL**: `https://slywriterapp.onrender.com/auth/profile`
**Method**: `GET`
**Headers**:
- Key: `Authorization`
- Value: `Bearer <YOUR_JWT_TOKEN>`

---

## Endpoints That DON'T Require Token

1. **POST /auth/google/login** - Google OAuth login
2. **POST /auth/verify-email** - Email verification
3. **POST /api/auth/login** - Standard login
4. **POST /api/auth/register** - Register new user
5. **POST /api/auth/logout** - Logout
6. **GET /api/auth/user/{user_id}** - Get user by ID
7. **GET /api/auth/status** - Auth status
8. **POST /api/auth/google** - Desktop Google OAuth

---

## Testing Tips

1. **Token Expiration**: JWT tokens expire after 30 minutes. If you get `401 Unauthorized`, get a fresh token using the login endpoint.

2. **Bearer Prefix**: Always include `Bearer ` (with space) before the token in the Authorization header.

3. **Quick Token Refresh**: Save the login request in Postman and run it whenever you need a new token.

4. **Environment Variables**: Set up a Postman environment variable called `jwt_token` and use `{{jwt_token}}` in your requests for easy token management.

---

## Verified Working (Tested 2025-10-08)

✅ Login endpoint returns valid JWT token
✅ Profile endpoint accepts JWT token
✅ Token format is correct (HS256 algorithm)
✅ All authentication endpoints working

---

## Support

If tokens stop working or you encounter authentication issues:
1. Try getting a fresh token via login
2. Check that you're using `Bearer ` prefix
3. Verify the token hasn't expired (30 min limit)
4. Make sure there are no extra spaces in the Authorization header
