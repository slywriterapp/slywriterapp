# SlyWriter Authentication System - Deployment Guide

## Overview
The SlyWriter authentication system is production-ready with automatic environment detection. The frontend automatically uses the appropriate backend server based on the environment.

## Architecture

### Frontend (Next.js/React)
- **Location**: `/slywriter-ui`
- **Local URL**: http://localhost:3000
- **Production URL**: Deployed via your hosting service

### Backend (Flask/Python)
- **Location**: `/slywriter_server.py`
- **Local URL**: http://localhost:5000
- **Production URL**: https://slywriterapp.onrender.com


## Dynamic Server Selection

The system automatically detects the environment and uses the appropriate backend:

1. **Development (localhost)**: Frontend at localhost:3000 → Backend at localhost:5000
2. **Production**: Frontend at production domain → Backend at Render (slywriterapp.onrender.com)

### How It Works

```javascript
// Automatic detection in login/page.tsx and AuthContext.tsx
const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000' 
  : 'https://slywriterapp.onrender.com'
```

### Force Production Server (Testing)
Add `?server=render` to the URL to force using the Render backend from localhost:
```
http://localhost:3000/login?server=render
```

## Authentication Features

### 1. Email/Password Registration
- Sends verification email via SMTP
- Uses Webflow branded verification page
- Stores user data in JSON file (users.json)

### 2. Google Sign-In
- OAuth 2.0 with Google Identity Services
- Sends welcome email on first sign-in
- Automatic account creation for new Google users

### 3. Duplicate Email Handling
- Detects existing emails during registration
- Automatically switches to login mode
- Shows helpful toast notifications

## Environment Variables (Backend)

Required for the Flask server (`slywriter_server.py`):

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=support@slywriter.ai
SMTP_PASSWORD=icvvvhygzkccpuzg  # Google App Password
GOOGLE_CLIENT_ID=675434683795-shrls6suu68dj0cuvqct28gf3o6u3jav.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
```

**Note**: These are set automatically on Render. For local development, use `run_auth_server.py`.

## Deployment Steps

### Backend (Render)

1. **Already Deployed**: The backend is live at https://slywriterapp.onrender.com
2. **Auto-Deploy**: Pushes to GitHub automatically trigger Render deployment
3. **Environment Variables**: Already configured in Render dashboard

### Frontend

1. **Build the production app**:
```bash
cd slywriter-ui
npm run build
```

2. **Test production build locally**:
```bash
npm run start
```

3. **Deploy to your hosting service**:
   - The app will automatically use the Render backend when not on localhost
   - No configuration changes needed

## Key Files

### Authentication Flow
- `/slywriter-ui/app/login/page.tsx` - Login/Registration UI with dynamic server selection
- `/slywriter-ui/app/context/AuthContext.tsx` - Auth state management with dynamic API URL
- `/slywriter_server.py` - Flask backend with email and Google OAuth

### Configuration
- `/slywriter-ui/next.config.mjs` - COOP headers for Google OAuth popups
- `/run_auth_server.py` - Local development server launcher with environment variables

### Data Storage
- `/users.json` - User accounts and authentication data
- `/analytics.json` - User activity tracking
- `/word_data.json` - Usage statistics

## Testing Checklist

### Local Development
- [ ] Run backend: `python run_auth_server.py`
- [ ] Run frontend: `cd slywriter-ui && npm run dev`
- [ ] Test registration with email verification
- [ ] Test Google Sign-In
- [ ] Test duplicate email handling

### Production
- [ ] Frontend uses Render backend automatically
- [ ] Email verification links use Webflow domain
- [ ] Google Sign-In works with production OAuth
- [ ] Authentication persists across sessions

## Security Notes

1. **SMTP Password**: Uses Google App Password (not regular password)
2. **JWT Tokens**: Expire after 7 days
3. **CORS**: Configured for localhost:3000 and production domains
4. **OAuth**: Restricted to authorized JavaScript origins

## Troubleshooting

### Backend Not Responding
- Check Render dashboard for server status
- Verify environment variables are set
- Check `/analytics.json` for recent activity

### Google Sign-In Issues
- Ensure app runs on port 3000 (required for OAuth)
- Check JavaScript origins in Google Cloud Console
- Verify COOP headers in next.config.mjs

### Email Not Sending
- Verify SMTP credentials in environment
- Check spam folder for verification emails
- Ensure user email is valid

## Support

For issues with:
- **Authentication System**: Check `/slywriter_server.py` logs
- **Frontend**: Check browser console for errors
- **Deployment**: Monitor Render dashboard for build/deploy status

## Important URLs

- **Render Backend**: https://slywriterapp.onrender.com
- **Email Verification**: https://slywriter-site.webflow.io/verify-email
- **Google OAuth Console**: https://console.cloud.google.com/apis/credentials

---

*Last Updated: January 2025*
*System Status: Production Ready ✅*