#!/usr/bin/env python3
"""
Complete deployment script for Render
Combines all server functionality into one file
"""

import os
import shutil

def create_deployment():
    """Create a complete deployment package for Render"""
    
    # Create deployment directory
    deploy_dir = "render_deployment"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Files to include in deployment
    files_to_copy = [
        "slywriter_server.py",  # Main server
        "requirements_render.txt",  # Dependencies
        "telemetry_postgres.py",  # Telemetry handling
    ]
    
    # Copy files
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, deploy_dir)
            print(f"[OK] Copied {file}")
        else:
            print(f"[WARNING] Warning: {file} not found")
    
    # Create a combined server file that includes telemetry
    print("\n[PACKAGE] Creating combined server file...")
    
    # Read the main server
    with open("slywriter_server.py", "r") as f:
        server_content = f.read()
    
    # Check if telemetry is already imported
    if "from telemetry_postgres import" not in server_content:
        # Add import at the top
        import_line = "from telemetry_postgres import telemetry_db\n"
        lines = server_content.split("\n")
        
        # Find where to insert (after other imports)
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_index = i + 1
        
        lines.insert(insert_index, import_line)
        server_content = "\n".join(lines)
        
        # Save modified server
        with open(f"{deploy_dir}/slywriter_server.py", "w") as f:
            f.write(server_content)
        print("[OK] Added telemetry import to server")
    
    # Create requirements.txt if it doesn't exist
    if not os.path.exists("requirements_render.txt"):
        requirements = """Flask==2.3.2
flask-cors==4.0.0
psycopg==3.1.9
psycopg[binary]==3.1.9
bcrypt==4.0.1
PyJWT==2.8.0
openai==1.3.0
python-dotenv==1.0.0
gunicorn==21.2.0
"""
        with open(f"{deploy_dir}/requirements.txt", "w") as f:
            f.write(requirements)
        print("[OK] Created requirements.txt")
    else:
        shutil.copy("requirements_render.txt", f"{deploy_dir}/requirements.txt")
        print("[OK] Copied requirements.txt")
    
    # Create a Procfile for Render
    procfile = "web: gunicorn slywriter_server:app\n"
    with open(f"{deploy_dir}/Procfile", "w") as f:
        f.write(procfile)
    print("[OK] Created Procfile")
    
    # Create .env.example
    env_example = """# Required Environment Variables for Render

# OpenAI API Key (required for AI features)
OPENAI_API_KEY=your-openai-api-key-here

# Admin Password (required for admin endpoints)
ADMIN_PASSWORD=secure-random-password-here

# JWT Secret (required for authentication)
JWT_SECRET_KEY=secure-random-jwt-secret
SECRET_KEY=secure-random-secret-key

# Database URL (automatically set by Render)
# DATABASE_URL=postgresql://...

# Optional: Email configuration
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
"""
    with open(f"{deploy_dir}/.env.example", "w") as f:
        f.write(env_example)
    print("[OK] Created .env.example")
    
    # Create deployment instructions
    instructions = """# Render Deployment Instructions

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
"""
    with open(f"{deploy_dir}/DEPLOY_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    print("[OK] Created deployment instructions")
    
    print(f"\n[OK] Deployment package ready in '{deploy_dir}/' directory")
    print("[INFO] Follow DEPLOY_INSTRUCTIONS.md to complete deployment")
    
    return deploy_dir

if __name__ == "__main__":
    deploy_dir = create_deployment()
    print(f"\n[READY] Ready to deploy! Check the '{deploy_dir}' directory")