# ElderCare System - Complete Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment Options](#cloud-deployment-options)
5. [Configuration & Environment](#configuration--environment)
6. [Database Setup](#database-setup)
7. [Docker Deployment](#docker-deployment)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL2
- **CPU**: 2+ cores minimum, 4+ cores recommended
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 20GB+ for development, 100GB+ for production

### Required Software
```bash
# Python 3.11+
python3 --version

# Node.js 18+
node --version

# Docker & Docker Compose
docker --version
docker-compose --version

# PostgreSQL client tools
psql --version

# Git
git --version
```

### Installation Commands

**Ubuntu/Debian:**
```bash
# Update package manager
sudo apt-get update && sudo apt-get upgrade -y

# Install runtime dependencies
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install PostgreSQL client
sudo apt-get install -y postgresql-client
```

**macOS (with Homebrew):**
```bash
brew install python@3.11 node postgresql docker
```

**Windows:**
- Download and install Docker Desktop from https://docker.com
- Install Python from https://python.org
- Install Node.js from https://nodejs.org
- Install PostgreSQL client from https://postgresql.org

---

## Local Development Setup

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd eldercare-system
```

### Step 2: Create Environment Files
```bash
# Copy example configuration
cp .env.example .env

# Edit with your configuration
nano .env  # or use your preferred editor
```

### Step 3: Backend Setup
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev  # Runs on http://localhost:5173
```

### Step 5: Database Setup
```bash
# Create database
createdb eldercare_dev

# Run seed data (optional)
psql eldercare_dev < database/schema.sql
```

### Step 6: Test the Setup
```bash
# Backend API
curl http://localhost:8000/api/v1/health

# Frontend
open http://localhost:5173

# API Documentation
open http://localhost:8000/api/v1/docs
```

---

## Production Deployment

### Pre-Deployment Checklist
- [ ] Security audit completed
- [ ] Environment variables configured
- [ ] Database backups tested
- [ ] SSL certificates obtained
- [ ] Domain configured
- [ ] Monitoring setup
- [ ] Error tracking setup (Sentry)
- [ ] Email service configured
- [ ] Payment gateway configured (if applicable)

### Deployment Steps

#### 1. Server Setup
```bash
# SSH into server
ssh admin@your-server.com

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y build-essential python3.11 python3-pip nodejs postgresql postgresql-contrib nginx

# Create application user
sudo useradd -m -s /bin/bash eldercare
sudo su - eldercare
```

#### 2. Clone Application
```bash
git clone <repository-url>
cd eldercare-system

# Create required directories
mkdir -p logs
mkdir -p data
```

#### 3. Backend Deployment
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
pip install gunicorn

# Create .env for production
nano .env
# Configure all environment variables

# Collect static files (if applicable)
# python manage.py collectstatic --noinput

# Test the application
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
```

#### 4. Frontend Deployment
```bash
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build

# Output is in dist/ directory
```

#### 5. Nginx Configuration
```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/eldercare

# Add configuration (see nginx.conf in project)

# Enable site
sudo ln -s /etc/nginx/sites-available/eldercare /etc/nginx/sites-enabled/

# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

#### 6. SSL Certificate Setup
```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

#### 7. Process Management (Systemd)
```bash
# Create systemd service file
sudo nano /etc/systemd/system/eldercare-api.service

# Add service configuration (example below)
# Enable and start service
sudo systemctl enable eldercare-api
sudo systemctl start eldercare-api
```

**Systemd Service File:**
```ini
[Unit]
Description=ElderCare API
After=network.target

[Service]
Type=notify
User=eldercare
WorkingDirectory=/home/eldercare/eldercare-system/backend
Environment="PATH=/home/eldercare/eldercare-system/backend/venv/bin"
ExecStart=/home/eldercare/eldercare-system/backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile - \
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Cloud Deployment Options

### AWS Deployment

#### Option 1: EC2 + RDS
```bash
# Launch EC2 instance
# - Instance type: t3.medium or larger
# - AMI: Ubuntu 22.04 LTS
# - Security Group: Allow ports 22, 80, 443

# Create RDS instance
# - Engine: PostgreSQL 14+
# - Instance class: db.t3.small or larger
# - Backup: Enable automatic backups

# Connection string
DATABASE_URL=postgresql://{user}:{password}@{rds-endpoint}:5432/{dbname}
```

#### Option 2: Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize Elastic Beanstalk
eb init -p python-3.11 eldercare-api

# Create environment
eb create eldercare-prod --instance-type t3.medium

# Deploy
eb deploy

# View logs
eb logs

# Monitor
eb health
```

### Google Cloud Deployment

#### Option 1: Cloud Run
```bash
# Build and push image
gcloud builds submit --tag gcr.io/{PROJECT_ID}/eldercare-api

# Deploy to Cloud Run
gcloud run deploy eldercare-api \
  --image gcr.io/{PROJECT_ID}/eldercare-api \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=postgresql://...

# Deploy frontend
gcloud run deploy eldercare-web \
  --image gcr.io/{PROJECT_ID}/eldercare-web \
  --platform managed \
  --region us-central1
```

#### Option 2: App Engine
```bash
# Deploy backend
gcloud app deploy app/app.yaml

# Deploy frontend
cd frontend
npm run build
gcloud app deploy web/app.yaml
```

### DigitalOcean Deployment

```bash
# Create Droplet (4GB RAM, 2 CPU)
doctl compute droplet create eldercare-api \
  --region nyc3 \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-4gb

# SSH into Droplet
ssh root@<droplet-ip>

# Follow self-hosted setup instructions above
```

---

## Configuration & Environment

### Environment Variables Template
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/eldercare
DATABASE_POOL_SIZE=10
DATABASE_POOL_TIMEOUT=30

# API Configuration
API_SECRET_KEY=your-secret-key-min-32-chars
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS Settings
CORS_ORIGINS=http://localhost:5173,https://your-domain.com

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Email Service (SendGrid)
SENDGRID_API_KEY=your-sendgrid-key
SENDER_EMAIL=noreply@eldercare.com

# SMS Service (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Payment Gateway (Stripe)
STRIPE_SECRET_KEY=your-stripe-secret
STRIPE_PUBLIC_KEY=your-stripe-public

# Logging Service (Sentry)
SENTRY_DSN=your-sentry-dsn

# Environment
ENVIRONMENT=production
DEBUG=False

# AWS (optional)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Frontend
VITE_API_URL=https://api.your-domain.com
VITE_APP_NAME=ElderCare
```

---

## Docker Deployment

### Using Docker Compose (Production)
```bash
# Pull latest images
docker-compose pull

# Start services
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f api web

# Stop services
docker-compose down
```

### Building Custom Images
```bash
# Build images
docker build -t eldercare-api:latest -f backend/Dockerfile.prod ./backend
docker build -t eldercare-web:latest -f frontend/Dockerfile.prod ./frontend

# Tag for registry
docker tag eldercare-api:latest your-registry/eldercare-api:latest
docker tag eldercare-web:latest your-registry/eldercare-web:latest

# Push to registry
docker push your-registry/eldercare-api:latest
docker push your-registry/eldercare-web:latest
```

---

## Monitoring & Logging

### Application Monitoring

#### Prometheus Metrics
```bash
# Install Prometheus
# Add to docker-compose.yml or install separately

# Configure Prometheus
nano prometheus.yml
```

#### Health Checks
```bash
# Check API health
curl https://your-domain.com/api/v1/health

# Response should be:
# {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

### Centralized Logging
```bash
# With ELK Stack (Docker Compose)
docker-compose -f docker-compose.logging.yml up -d

# Access Kibana
open http://localhost:5601

# With CloudWatch (AWS)
# Configure CloudWatch agent and logging driver
```

### Error Tracking
```bash
# With Sentry
# Set SENTRY_DSN in environment variables
# Errors will be automatically captured and reported
```

---

## Backup & Recovery

### Database Backups
```bash
# Manual backup
pg_dump -h {host} -U {user} eldercare > backup_$(date +%Y%m%d).sql

# Automated daily backups (crontab)
0 2 * * * pg_dump -h {host} -U {user} eldercare > /backups/backup_$(date +\%Y\%m\%d).sql

# S3 backup sync
0 3 * * * aws s3 sync /backups s3://your-backup-bucket/

# Restore from backup
psql -h {host} -U {user} eldercare < backup_20240101.sql
```

### Application Backups
```bash
# Backup uploaded files
tar -czf app_data_backup.tar.gz /path/to/uploads/

# Upload to S3
aws s3 cp app_data_backup.tar.gz s3://your-backup-bucket/
```

### Disaster Recovery
```bash
# Test restore procedure regularly
# 1. Restore database from backup
# 2. Deploy application code to new server
# 3. Verify all services are running
# 4. Run health checks
# 5. Monitor for errors
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
ERROR: could not connect to database
```
**Solution:**
```bash
# Check database is running
psql -h localhost -U user -d eldercare -c "\dt"

# Check connection string in .env
echo $DATABASE_URL

# Verify firewall rules
sudo ufw allow 5432
```

#### 2. Port Already in Use
```
ERROR: Address already in use: ('0.0.0.0', 8000)
```
**Solution:**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

#### 3. SSL Certificate Error
```
ERROR: certificate verification failed
```
**Solution:**
```bash
# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Check expiration
sudo certbot certificates
```

#### 4. Out of Memory
```
ERROR: Container killed due to memory limit
```
**Solution:**
```bash
# Increase container memory limits
# Edit docker-compose.yml:
services:
  api:
    mem_limit: 2g
    memswap_limit: 2g
```

#### 5. High CPU Usage
```
WARNING: CPU usage at 95%
```
**Solution:**
```bash
# Check running processes
top -p $(pgrep -f gunicorn)

# Increase workers
# Edit systemd service or docker-compose.yml
# Increase WORKERS or --workers value
```

### Performance Optimization

#### Database Optimization
```bash
# Analyze query performance
EXPLAIN ANALYZE SELECT * FROM tasks WHERE status = 'active';

# Add indexes
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_customer ON tasks(customer_id);

# Vacuum
VACUUM ANALYZE;
```

#### Application Tuning
```bash
# Increase gunicorn workers
gunicorn --workers 8 --worker-class uvicorn.workers.UvicornWorker

# Enable caching
# Add Redis to stack
# Configure cache headers

# Enable gzip compression
# Configure in nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

#### Frontend Optimization
```bash
# Enable caching
npm run build

# Minification is automatic with production build
```

---

## Post-Deployment Verification

### Checklist
- [ ] API responding on health endpoint
- [ ] Database migrations completed
- [ ] Frontend loads without errors
- [ ] User registration working
- [ ] Task creation working
- [ ] Email notifications sending
- [ ] SMS notifications working
- [ ] Payment processing working
- [ ] Admin dashboard accessible
- [ ] Monitoring/logging active
- [ ] SSL certificate valid
- [ ] Backups running
- [ ] Rate limiting active
- [ ] CORS configured correctly

### Monitoring Commands
```bash
# System status
systemctl status eldercare-api
systemctl status nginx

# Service logs
journalctl -u eldercare-api -f

# Docker status
docker-compose ps
docker-compose logs api

# Network
netstat -tlnp | grep 8000
curl -v https://your-domain.com/api/v1/health

# Database
psql -h localhost -U user -d eldercare -c "SELECT COUNT(*) FROM users;"
```

---

## Support & Maintenance

For questions or issues:
- Check logs: `/var/log/eldercare/` or `docker-compose logs`
- Review documentation: See other docs/ files
- API documentation: `/api/v1/docs`
- GitHub Issues: [Project Issues]

Regular maintenance tasks:
- Weekly: Check logs for errors
- Monthly: Review performance metrics
- Quarterly: Security updates
- Annually: Disaster recovery drill

---

**Last Updated**: January 2024
**Version**: 1.0.0
