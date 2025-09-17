# How to Enable Google Sign-In in the Electron App

## The Problem
Google Sign-In doesn't work in Electron apps by default because:
1. Electron apps use `file://` protocol which Google doesn't allow
2. Even when loading from `localhost`, Google needs that origin to be whitelisted

## Solution 1: Add localhost to Google Console (EASIEST)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one)
3. Go to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID (or create one)
5. Under **Authorized JavaScript origins**, add:
   ```
   http://localhost:3000
   http://localhost:3001
   http://localhost:3002
   ```
6. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:3000/auth/callback
   http://localhost:3001/auth/callback
   http://localhost:3002/auth/callback
   ```
7. Click **Save**
8. Wait 5 minutes for changes to propagate

Now Google Sign-In will work in your Electron app since it's loading from `http://localhost:3000`!

## Solution 2: Use a Custom Protocol (Advanced)

If you want your app to work with a custom protocol like `slywriter://`:

1. Register the protocol in Electron's main.js:
```javascript
// At the top of main.js
const { protocol } = require('electron')

// In app.whenReady()
protocol.registerHttpProtocol('slywriter', (request, callback) => {
  const url = request.url.replace('slywriter://', 'http://localhost:3000/')
  callback({ url })
})
```

2. Update BrowserWindow to load from custom protocol:
```javascript
mainWindow.loadURL('slywriter://login')
```

3. Add `slywriter://` to Google Console's authorized origins

## Solution 3: External Browser OAuth (Already Implemented)

The app now has a fallback that opens Google Sign-In in your default browser.
This works but is less seamless than in-app authentication.

## Current Status

- ✅ Email/password login works
- ⚠️ Google Sign-In requires adding `http://localhost:3000` to Google Console
- ✅ External browser fallback available

## Quick Fix

For immediate results, just add `http://localhost:3000` to your Google OAuth client's authorized origins. This is the standard approach used by most Electron apps during development.