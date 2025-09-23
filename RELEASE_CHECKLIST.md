# SlyWriter Release Checklist

## First-Time Setup ✅

### 1. GitHub Token
- [ ] Created at: https://github.com/settings/tokens/new
- [ ] Has `repo` scope
- [ ] Saved token starting with `ghp_`

### 2. Render Deployment
- [ ] Created service at: https://dashboard.render.com
- [ ] Service name: `slywriter-update-server`
- [ ] Root directory: `update-server`
- [ ] Environment variables added:
  - GITHUB_TOKEN = your token
  - REPO_OWNER = slywriterapp
  - REPO_NAME = slywriterapp
  - NODE_ENV = production

### 3. Test Update Server
```bash
# Should return JSON with status "healthy"
curl https://slywriter-update-server.onrender.com/health
```

## For Each Release 🚀

### 1. Update Version
Edit `slywriter-electron/package.json`:
```json
"version": "2.0.1"  // Increment this
```

### 2. Build Installer
```bash
cd slywriter-electron

# Set your GitHub token (Windows)
set GH_TOKEN=ghp_YOUR_TOKEN_HERE

# Build Squirrel installer
npm run dist:squirrel
```

### 3. Create GitHub Release
```bash
# The build process creates draft release automatically
# OR manually:

# Tag the version
git tag v2.0.1
git push origin v2.0.1

# Go to: https://github.com/slywriterapp/slywriterapp/releases/new
# Upload from dist/ folder:
- SlyWriter-2.0.1-Setup.exe
- RELEASES
- *.nupkg files (delta update packages)
```

### 4. Publish Release
- Change from "Draft" to "Published"
- Users will get automatic updates!

## Update Flow for Users

1. **Initial Install**: Download `SlyWriter-Setup.exe` once
2. **App checks**: `https://slywriter-update-server.onrender.com/updates/RELEASES`
3. **Proxy fetches**: From your private GitHub with token
4. **User downloads**: Update without any authentication
5. **Restart**: Update applied

## Troubleshooting

### "Update server not responding"
- Check Render dashboard for logs
- Verify GITHUB_TOKEN is set correctly
- Check GitHub API rate limits

### "No updates found"
- Ensure release is published (not draft)
- Version in package.json must be higher
- RELEASES file must be in GitHub release

### "Download failed"
- Check file names match exactly
- Ensure all .nupkg files are uploaded
- Verify proxy server has correct token