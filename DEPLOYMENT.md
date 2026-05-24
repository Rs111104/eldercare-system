# Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Supabase project created
- OpenAI API key
- WhatsApp Cloud API credentials

### Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd eldercare-system
```

2. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI
OPENAI_API_KEY=sk-...

# WhatsApp
WHATSAPP_API_TOKEN=your-token
WHATSAPP_PHONE_ID=your-phone-id
WHATSAPP_BUSINESS_ID=your-business-id

# Database (optional, uses Supabase by default)
DB_USER=postgres
DB_PASSWORD=secure-password
DB_NAME=eldercare

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

Services will be available at:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

4. **Verify setup**
```bash
# Check backend health
curl http://localhost:8000/

# Check frontend
open http://localhost:3000
```

## Manual Setup (Development)

### Backend Setup

1. **Create virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run migrations**
```bash
# Create Supabase tables (in SQL editor)
# Paste migrations from database/migrations/*.sql
```

4. **Start backend**
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Configure API URL** (in `.env`)
```
VITE_API_URL=http://localhost:8000/api/v1
```

3. **Start development server**
```bash
npm run dev
```

## Deployment to Cloud

### AWS EC2

1. **Launch EC2 instance**
   - Amazon Linux 2 or Ubuntu 20.04+
   - t2.medium or larger
   - 20GB storage minimum

2. **Install Docker**
```bash
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

3. **Clone and deploy**
```bash
git clone <repo-url> /app
cd /app
docker-compose up -d
```

4. **Configure Nginx** (reverse proxy)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

### Google Cloud Run

1. **Build and push Docker images**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/eldercare-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/eldercare-frontend frontend/
```

2. **Deploy backend**
```bash
gcloud run deploy eldercare-backend \
  --image gcr.io/PROJECT_ID/eldercare-backend \
  --set-env-vars SUPABASE_URL=...,OPENAI_API_KEY=... \
  --memory 1Gi \
  --region us-central1 \
  --allow-unauthenticated
```

3. **Deploy frontend**
```bash
gcloud run deploy eldercare-frontend \
  --image gcr.io/PROJECT_ID/eldercare-frontend \
  --set-env-vars VITE_API_URL=... \
  --region us-central1 \
  --allow-unauthenticated
```

### Heroku

1. **Create Procfile**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

2. **Deploy**
```bash
heroku login
heroku create eldercare-api
git push heroku main
```

## MongoDB for Scaling (Optional)

Replace PostgreSQL with MongoDB for document-based storage:

1. **Install MongoDB support**
```bash
pip install pymongo motor
```

2. **Configure connection**
```python
# app/core/database.py
from motor.motor_asyncio import AsyncClient
MONGODB_URL = "mongodb+srv://user:pass@cluster.mongodb.net/eldercare"
```

## Load Testing

Using Apache Bench:
```bash
ab -n 1000 -c 10 http://localhost:8000/docs
```

Using locust:
```bash
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8000
```

## Monitoring & Logging

### Application Monitoring
```bash
# Install Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Install Grafana
docker run -d -p 3001:3000 grafana/grafana
```

### Application Logs
```bash
# View Docker logs
docker-compose logs backend
docker-compose logs frontend

# Export logs
docker-compose logs > logs.txt
```

## Backup & Recovery

### Database Backup
```bash
# Supabase automatic backups
# Available in Supabase dashboard Settings → Backups

# Manual backup
pg_dump postgresql://user:pass@host/db > backup.sql

# Restore
psql postgresql://user:pass@host/db < backup.sql
```

## SSL/TLS Setup

Using Let's Encrypt with Certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
sudo nginx -s reload
```

## Performance Optimization

1. **Enable caching**
```python
@app.get("/tasks/{task_id}")
@cache(expire=300)  # 5 minutes
async def get_task(task_id: str):
    ...
```

2. **Database indexing** (see database/migrations/)

3. **CDN for static assets**
   - Configure CloudFront or Cloudflare

4. **Redis for sessions**
```bash
docker run -d -p 6379:6379 redis:latest
```

## Troubleshooting

**Port already in use**
```bash
lsof -i :8000
kill -9 <PID>
```

**Docker connection issues**
```bash
docker-compose down
docker-compose up -d --build
```

**Database connection errors**
- Verify SUPABASE_URL and SUPABASE_KEY
- Check network connectivity
- Review Supabase dashboard logs

**WhatsApp webhook not working**
- Verify WHATSAPP_API_TOKEN
- Check webhook URL is publicly accessible
- Verify HMAC signature verification

## Support

For issues, queries, or contributions:
- GitHub Issues: <repo-issues>
- Email: support@example.com
- Documentation: <docs-url>
