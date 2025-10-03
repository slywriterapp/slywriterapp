# SlyWriter Release Process

## Quick Release Guide

### 1. Update Version
Edit `package.json` and bump the version number:
```json
{
  "version": "2.1.9"
}
```

### 2. Update Release Notes
Edit `release-notes.txt` with your changes for this release.

### 3. Commit Changes
```bash
git add package.json
git commit -m "Bump version to 2.1.9"
git push origin main
```

### 4. Create Git Tag
```bash
git tag v2.1.9 -m "Release v2.1.9"
git push origin v2.1.9
```

### 5. Run Release Script
```bash
release.bat 2.1.9
```

This will:
- Build the NSIS installer
- Publish to **public** repository (slywriter-releases) for auto-updates
- Publish to **private** repository (slywriterapp) for tracking

## What Gets Published

### Public Repository (slywriter-releases)
- **Purpose**: Auto-update downloads
- **URL**: https://github.com/slywriterapp/slywriter-releases
- **Contains**: Only releases, no code
- **Visibility**: PUBLIC (required for auto-updates)

### Private Repository (slywriterapp)
- **Purpose**: Code tracking and team access
- **URL**: https://github.com/slywriterapp/slywriterapp
- **Contains**: Full source code + releases
- **Visibility**: PRIVATE

## Files Published

Each release includes:
- `SlyWriter-Setup-X.X.X.exe` - The installer
- `latest.yml` - Auto-update metadata

## Auto-Updater Configuration

The app checks for updates from the **public** repository:
- Repository: `slywriter-releases`
- Check interval: Every 30 minutes
- Download: Shows progress window
- License: Re-verified before checking updates

## Troubleshooting

### Build fails
- Ensure Node.js is installed
- Run `npm install` in slywriter-electron folder

### Release already exists
- Delete the tag: `git tag -d vX.X.X`
- Delete remote tag: `git push origin :refs/tags/vX.X.X`
- Try again

### Auto-update not working
- Verify `latest.yml` is accessible: https://github.com/slywriterapp/slywriter-releases/releases/latest
- Check that repository is PUBLIC
- Ensure version in package.json is higher than installed version
