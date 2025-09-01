# 🧪 Testing Your Telemetry System After Deployment

## Quick Health Check
```bash
curl https://slywriterapp.onrender.com/api/admin/telemetry/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-XX-XX..."
}
```

## Test Telemetry Upload
Open browser console (F12) and run:
```javascript
fetch('https://slywriterapp.onrender.com/api/beta-telemetry', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    userId: 'test-user-001',
    sessionId: 'test-session-001',
    systemInfo: {
      platform: 'Windows',
      screenResolution: '1920x1080',
      browser: 'Chrome'
    },
    actions: [
      {action: 'app_start', timestamp: new Date().toISOString()},
      {action: 'typing_start', timestamp: new Date().toISOString()}
    ],
    errors: [],
    featureUsage: [
      {feature: 'ai_generation', usageCount: 1}
    ],
    performanceMetrics: [],
    sessionDuration: 120000,
    lastActivity: Date.now(),
    timestamp: new Date().toISOString()
  })
}).then(r => r.json()).then(console.log)
```

## Check Admin Stats
```bash
curl -H "X-Admin-Password: slywriter-admin-brice" \
  https://slywriterapp.onrender.com/api/admin/telemetry/stats
```

## View Recent Entries
```bash
curl -H "X-Admin-Password: slywriter-admin-brice" \
  https://slywriterapp.onrender.com/api/admin/telemetry?limit=10
```

## Export All Data
```bash
curl -H "X-Admin-Password: slywriter-admin-brice" \
  https://slywriterapp.onrender.com/api/admin/telemetry/export > telemetry_export.json
```

## PowerShell Test Commands (for Windows)
```powershell
# Health check
Invoke-RestMethod -Uri "https://slywriterapp.onrender.com/api/admin/telemetry/health"

# Get stats with auth
$headers = @{"X-Admin-Password" = "slywriter-admin-brice"}
Invoke-RestMethod -Uri "https://slywriterapp.onrender.com/api/admin/telemetry/stats" -Headers $headers

# Send test telemetry
$body = @{
    userId = "test-ps-user"
    sessionId = "test-ps-session"
    systemInfo = @{platform = "Windows"}
    actions = @()
    errors = @()
    featureUsage = @()
    performanceMetrics = @()
    sessionDuration = 0
    lastActivity = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ")
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "https://slywriterapp.onrender.com/api/beta-telemetry" `
    -ContentType "application/json" -Body $body
```

## Admin Dashboard Access
Your admin dashboard should work at:
- Local dev: http://localhost:3000/admin
- View it with password: slywriter-admin-brice

## Monitoring Checklist
After deployment, verify:
- [ ] Health endpoint returns "healthy"
- [ ] Test telemetry upload returns success
- [ ] Admin stats show the test data
- [ ] Admin dashboard displays data correctly
- [ ] Export endpoint returns JSON data

## Troubleshooting

### If health check fails:
1. Check Render logs for errors
2. Verify DATABASE_URL is set in environment variables
3. Check PostgreSQL is running on Render

### If telemetry upload fails:
1. Check CORS settings (should allow *)
2. Verify the server is running
3. Check Render logs for Python errors

### If admin endpoints return 401:
1. Verify ADMIN_PASSWORD environment variable is set
2. Check you're using correct password in header

## Database Direct Access
If needed, you can connect directly to PostgreSQL:
```bash
psql postgresql://slywriter_telemetry_user:lHG2FWdTSQIj3F9DtitvWzvO0MS6TjRM@dpg-d2psm2be5dus73be754g-a/slywriter_telemetry

# Check tables
\dt

# Count telemetry events
SELECT COUNT(*) FROM telemetry_events;

# View recent sessions
SELECT * FROM telemetry_sessions ORDER BY created_at DESC LIMIT 5;
```