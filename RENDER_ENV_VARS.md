# Environment Variables for Render Deployment

Add these environment variables to your Render service:

## SMTP Configuration (Email Sending)
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=support@slywriter.ai
SMTP_PASSWORD=icvvvhygzkccpuzg
```

## Google OAuth Configuration
```
GOOGLE_CLIENT_ID=675434683795-shrls6suu68dj0cuvqct28gf3o6u3jav.apps.googleusercontent.com
```

## Flask Configuration
```
FLASK_ENV=production
```

## How to Add in Render:
1. Go to your Render dashboard
2. Select your `slywriterapp` service
3. Go to "Environment" tab
4. Add each variable above
5. Click "Save Changes"
6. The service will automatically redeploy

## Important Notes:
- The SMTP password is a Google App Password, not your regular Gmail password
- The Google Client ID must match what's configured in Google Cloud Console
- Make sure to add your production domain to Google OAuth authorized origins