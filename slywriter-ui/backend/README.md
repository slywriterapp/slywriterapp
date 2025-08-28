# SlyWriter Backend API

## Overview
FastAPI backend for SlyWriter typing automation application with AI integration.

## Features
- ✅ Real-time typing automation with WebSocket updates
- ✅ AI text generation (ChatGPT integration)
- ✅ Google OAuth authentication
- ✅ Profile management
- ✅ Hotkey recording protection
- ✅ Typo correction
- ✅ Voice transcription
- ✅ Learning system with spaced repetition

## Quick Start

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. Clone the repository
2. Create and activate virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. Run startup checks:
```bash
python startup.py
```

6. Start the server:
```bash
python main_complete.py
```

The API will be available at http://localhost:8000

## Environment Variables

Required variables in `.env`:

```env
# OpenAI API Key (for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here

# Database
DATABASE_URL=sqlite:///./slywriter.db

# Server
HOST=0.0.0.0
PORT=8000
```

## Deployment

### Docker
```bash
docker-compose up -d
```

### Linux/Unix
```bash
chmod +x deploy.sh
./deploy.sh --service
```

### Windows
```batch
deploy.bat --service
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

### Typing Control
- `POST /api/typing/start` - Start typing session
- `POST /api/typing/stop` - Stop typing
- `POST /api/typing/pause` - Pause typing
- `POST /api/typing/resume` - Resume typing
- `GET /api/typing/status/{session_id}` - Get session status

### AI Generation
- `POST /api/ai/generate` - Generate text
- `POST /api/ai/essay` - Generate essay
- `POST /api/ai/humanize` - Humanize text
- `POST /api/ai/explain` - Explain topic
- `POST /api/ai/study-questions` - Generate study questions

### WebSocket
- `WS /ws/typing` - Real-time typing updates

### Authentication
- `POST /api/auth/google` - Google OAuth login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

## Testing

Run tests:
```bash
python test_all_features.py
```

## Logging

Logs are stored in:
- `logs/slywriter_YYYYMMDD.log` - Application logs
- `slywriter_backend.log` - Startup logs

## Troubleshooting

### AI features not working
- Ensure `OPENAI_API_KEY` is set in `.env`
- Check API key is valid at https://platform.openai.com/api-keys

### Google OAuth issues
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Add http://localhost:3000 to authorized origins in Google Console

### Database errors
- Run `python startup.py` to initialize database
- Check write permissions for SQLite file

## Support

For issues or questions:
- Check logs in `logs/` directory
- Run `python startup.py` for environment check
- Review test results with `python test_all_features.py`

## License

Copyright © 2025 SlyWriter. All rights reserved.