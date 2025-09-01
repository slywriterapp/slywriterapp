# Render Deployment Instructions

## 1. Push to GitHub
```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

## 2. Create New Web Service on Render
1. Go to https://dashboard.render.com/
2. Click "New +" -> "Web Service"
3. Connect your GitHub repository
4. Configure:
   - Name: slywriter-api
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn slywriter_server:app`

## 3. Set Environment Variables
In Render Dashboard -> Environment:

Required:
- `OPENAI_API_KEY` = Your OpenAI API key
- `ADMIN_PASSWORD` = Strong password for admin access
- `JWT_SECRET_KEY` = Random secret for JWT
- `SECRET_KEY` = Random secret for Flask

Optional:
- `SMTP_PASSWORD` = For email features
- `DATABASE_URL` = (Auto-set by Render if using PostgreSQL)

## 4. Add PostgreSQL Database
1. In Render Dashboard -> "New +" -> "PostgreSQL"
2. Create database
3. Copy Internal Database URL
4. Add as `DATABASE_URL` environment variable

## 5. Deploy
Click "Manual Deploy" -> "Deploy latest commit"

## 6. Test Endpoints
- Health check: `https://your-app.onrender.com/`
- AI generate: `https://your-app.onrender.com/api/ai/generate`
- Telemetry: `https://your-app.onrender.com/api/beta-telemetry`

## Important Notes
- First request may be slow (cold start)
- Free tier spins down after 15 minutes of inactivity
- Upgrade to paid tier for always-on service
