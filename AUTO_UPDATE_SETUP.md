# SlyWriter Auto-Update Setup Guide

## Overview
SlyWriter now includes automatic update functionality that allows users to receive updates without re-downloading the entire application.

## How It Works

1. **Simple .exe Installer**: Users download and run a single .exe file that installs SlyWriter
2. **Automatic Update Checks**: The app checks for updates every 30 minutes and on startup
3. **Background Downloads**: Updates download in the background with progress notifications
4. **Install on Restart**: Updates are applied when the user restarts the application

## Setup Instructions

### 1. Configure GitHub Repository

1. Create a GitHub repository for your releases (if not already created)
2. Update `slywriter-electron/package.json` with your GitHub info:
   ```json
   "publish": {
     "provider": "github",
     "owner": "YOUR_GITHUB_USERNAME",
     "repo": "YOUR_REPO_NAME"
   }
   ```

### 2. Get GitHub Token

1. Go to GitHub Settings > Developer Settings > Personal Access Tokens
2. Generate a new token with `repo` scope
3. Save this token securely - you'll need it for publishing

### 3. Build and Publish

```bash
# Navigate to electron directory
cd slywriter-electron

# Set your GitHub token (Windows)
set GH_TOKEN=YOUR_GITHUB_TOKEN

# Build and publish to GitHub
npm run build

# Or to just build without publishing
npm run dist
```

### 4. Create a Release

Option A - Automatic (with GH_TOKEN):
- The build process will automatically create a draft release on GitHub

Option B - Manual:
1. Go to your GitHub repo > Releases
2. Create a new release
3. Upload these files from `slywriter-electron/dist/`:
   - `SlyWriter Setup 2.0.0.exe` (the installer)
   - `SlyWriter Setup 2.0.0.exe.blockmap`
   - `latest.yml` (update manifest)

### 5. Testing Updates

1. Install the app from the .exe
2. Update version in `package.json` (e.g., 2.0.0 -> 2.0.1)
3. Build and publish the new version
4. The installed app will detect and download the update

## Alternative: Custom Update Server

If you don't want to use GitHub, you can host updates on your own server:

1. Update `package.json`:
   ```json
   "publish": {
     "provider": "generic",
     "url": "https://your-server.com/updates/"
   }
   ```

2. Upload these files to your server:
   - The .exe installer
   - The .exe.blockmap file
   - The latest.yml file

3. Ensure your server supports:
   - HTTPS
   - Proper MIME types
   - CORS headers if needed

## Version Management

- Always increment version in `package.json` before building
- Use semantic versioning (MAJOR.MINOR.PATCH)
- The app compares versions to determine if an update is available

## Update Flow for Users

1. **Initial Install**: User downloads and runs the .exe installer once
2. **Automatic Checks**: App checks for updates periodically
3. **Notification**: User sees "Update Available" dialog
4. **Download**: User clicks "Download Now" - sees progress bar
5. **Install**: User clicks "Restart Now" when download completes
6. **Updated**: App restarts with new version installed

## Important Files

- `slywriter-electron/main.js` - Contains auto-updater logic
- `slywriter-ui/app/components/UpdateNotification.tsx` - UI for updates
- `slywriter-electron/package.json` - Version and publish configuration

## Troubleshooting

- **Updates not detected**: Check GitHub releases are published (not draft)
- **Download fails**: Ensure files are accessible and CORS is configured
- **Install fails**: User may need admin rights for some directories

## Security Notes

- Updates are signed with your GitHub/publisher certificate
- HTTPS is required for update downloads
- Users are always prompted before downloading/installing