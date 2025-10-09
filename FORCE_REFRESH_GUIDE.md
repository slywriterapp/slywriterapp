# Force Refresh Guide - Get Latest Code

## Method 1: Clear Cache via DevTools
1. Open DevTools (F12)
2. **Right-click the refresh button** (next to address bar)
3. Select **"Empty Cache and Hard Reload"**

## Method 2: Manual Cache Clear
1. Press **Ctrl + Shift + Delete**
2. Select "Cached images and files"
3. Click "Clear data"
4. Close and reopen browser tab

## Method 3: Incognito/Private Window
1. Press **Ctrl + Shift + N** (Chrome) or **Ctrl + Shift + P** (Firefox)
2. Go to https://slywriter-ui.onrender.com
3. Login and test

## Method 4: Different Browser
- Try Edge, Firefox, or Chrome (whichever you're NOT using)
- This guarantees no cache

## Method 5: Add Query Parameter
- Go to: `https://slywriter-ui.onrender.com/?v=2.5.3`
- The `?v=2.5.3` forces browser to treat it as new URL

## Stop Backend Typing Session

Your backend might still have a running typing session. Let's kill it:

**Windows PowerShell:**
```powershell
curl http://localhost:8000/api/typing/stop -Method POST
```

**OR use your web app:**
1. Click the STOP button
2. Wait 5 seconds
3. Refresh page

## Verify You Have Latest Code

After refreshing, check page source:
1. Right-click page → "View Page Source"
2. Search for "page-c2996e84835db5d3.js"
3. If you see a DIFFERENT hash (like "page-XXXXX.js"), you have new code!

## Test Checklist

Once you have fresh code:

1. ✅ Open Console (F12)
2. ✅ Clear console logs
3. ✅ Select a profile (Lightning or Custom 260)
4. ✅ Paste text
5. ✅ Click "Start Typing"
6. ✅ **LOOK FOR:** `========== TYPING START DEBUG ==========`

If you DON'T see that debug section, you're still on old code!
