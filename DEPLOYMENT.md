# Production Deployment Guide

This guide covers deploying CaptPathfinder to production with best practices.

---

## 📋 Pre-Deployment Checklist

- [ ] Database backup created
- [ ] Environment variables documented
- [ ] Classification rules tested and validated
- [ ] AA bot endpoints configured and tested
- [ ] Monitoring/alerting configured
- [ ] Database connection pool sized appropriately
- [ ] SSL/TLS certificates ready (if self-hosting)

---

## Deployment Options

### Option 1: Railway (Recommended for Quick Deploy)

**Pros:** Simple, fast, automatic HTTPS, integrated database
**Cons:** Can be expensive at scale

#### Steps:

1. **Create Railway Project**
   ```bash
   npm i -g @railway/cli
   railway login
   railway init
   ```

2. **Add Postgres Database**
   - In Railway dashboard, add PostgreSQL service
   - Note the connection string

3. **Configure Environment Variables**
   - In Railway dashboard, add all variables from `.env`

4. **Deploy**
   ```bash
   railway up
   ```

5. **Run Migrations**
   ```bash
   railway run psql $DATABASE_URL -f migrations/001_initial_schema.sql
   railway run psql $DATABASE_URL -f scripts/create_functions.sql
   railway run psql $DATABASE_URL -f scripts/setup_pg_cron.sql
   ```

---

### Option 2: Render

**Pros:** Free tier available, simple setup
**Cons:** Cold starts on free tier

#### Steps:

1. **Create Web Service**
   - Connect GitHub repository
   - Select Python environment
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Add Supabase PostgreSQL**
   - Use existing Supabase or create new instance
   - Add `DATABASE_URL` environment variable

3. **Configure Environment Variables**
   - Add all from `.env` in Render dashboard

4. **Deploy**
   - Render auto-deploys on git push

---

### Option 3: AWS ECS (For Enterprise)

**Pros:** Full control, scalable, AWS ecosystem
**Cons:** More complex setup

#### Architecture:

```
Internet → ALB → ECS Fargate (FastAPI) → RDS PostgreSQL
                      ↓
                 CloudWatch Logs
```

#### Steps:

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name captpathfinder
   ```

2. **Build and Push Docker Image**
   ```dockerfile
   # Dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8000
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```
   
   ```bash
   docker build -t captpathfinder .
   docker tag captpathfinder:latest AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/captpathfinder:latest
   docker push AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/captpathfinder:latest
   ```

3. **Create RDS PostgreSQL Instance**
   - Enable pg_cron extension
   - Configure security groups

4. **Create ECS Cluster & Service**
   - Use Fargate launch type
   - Configure task definition with environment variables
   - Set up ALB for load balancing

5. **Setup CloudWatch Logs**
   - Configure log groups for application logs

6. **Run Database Migrations**
   ```bash
   # From bastion host or ECS Exec
   psql $DATABASE_URL -f migrations/001_initial_schema.sql
   ```

---

### Option 4: Google Cloud Run

**Pros:** Serverless, auto-scaling, pay per use
**Cons:** Cold starts, stateless

#### Steps:

1. **Create Container**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/captpathfinder
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy captpathfinder \
     --image gcr.io/PROJECT_ID/captpathfinder \
     --platform managed \
     --region us-east1 \
     --allow-unauthenticated \
     --set-env-vars SUPABASE_DB_URL=$DB_URL,...
   ```

3. **Setup Cloud SQL (or use Supabase)**
   - Configure Cloud SQL PostgreSQL
   - Enable pg_cron

---

## Database Considerations

### Supabase (Recommended)

**Pros:**
- Managed PostgreSQL with pg_cron built-in
- Automatic backups
- Built-in monitoring
- Storage integration

**Setup:**

1. **Enable pg_cron**
   ```sql
   -- In Supabase SQL Editor
   CREATE EXTENSION IF NOT EXISTS pg_cron;
   ```

2. **Configure Timezone**
   ```sql
   ALTER DATABASE postgres SET timezone TO 'America/New_York';
   ```

3. **Run Migrations**
   - Use Supabase SQL Editor or `psql`

### Self-Managed PostgreSQL

**Requirements:**
- PostgreSQL 13+
- pg_cron extension installed
- Timezone configured

**Installation:**

```bash
# Install pg_cron
# Ubuntu/Debian
apt install postgresql-14-cron

# CentOS/RHEL
yum install pg_cron_14

# Enable extension
psql -U postgres -c "CREATE EXTENSION pg_cron;"
```

---

## Worker Setup

For processing digests/reports independently from web requests:

### Option A: pg_cron + HTTP Calls

Configure pg_cron to call your API endpoints:

```sql
-- Call digest sender endpoint
SELECT cron.schedule(
    'send-digests',
    '*/10 * * * *',  -- Every 10 minutes
    $$
    SELECT net.http_post(
        url := 'https://your-app.com/admin/send-digests',
        headers := '{"Content-Type": "application/json"}'::jsonb
    );
    $$
);
```

### Option B: Separate Worker Process

Run `worker.py` as a scheduled job:

**Cron (Linux):**
```bash
# Edit crontab
crontab -e

# Add line (every 10 minutes)
*/10 * * * * cd /path/to/CaptPathfinder && /path/to/venv/bin/python worker.py >> /var/log/captpathfinder-worker.log 2>&1
```

**Systemd Timer (Linux):**

Create `/etc/systemd/system/captpathfinder-worker.service`:
```ini
[Unit]
Description=CaptPathfinder Worker
After=network.target

[Service]
Type=oneshot
User=captpathfinder
WorkingDirectory=/opt/captpathfinder
ExecStart=/opt/captpathfinder/venv/bin/python worker.py
Environment="PATH=/opt/captpathfinder/venv/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/captpathfinder-worker.timer`:
```ini
[Unit]
Description=Run CaptPathfinder Worker Every 10 Minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=10min

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl daemon-reload
systemctl enable captpathfinder-worker.timer
systemctl start captpathfinder-worker.timer
```

**Cloud Scheduler (GCP):**
```bash
gcloud scheduler jobs create http captpathfinder-worker \
  --schedule="*/10 * * * *" \
  --uri="https://your-app.com/admin/send-digests" \
  --http-method=POST
```

**AWS EventBridge:**
- Create EventBridge rule with rate expression
- Target: Lambda function that calls API or runs worker logic

---

## Environment Variables Management

### Development
Use `.env` file (never commit!)

### Production

**Option 1: Cloud Platform Secrets**
- Railway: Environment variables in dashboard
- Render: Environment variables in settings
- AWS: AWS Secrets Manager + ECS task definition
- GCP: Secret Manager + Cloud Run

**Example (AWS Secrets Manager):**
```bash
aws secretsmanager create-secret \
  --name captpathfinder/production \
  --secret-string file://secrets.json
```

**Option 2: Environment Variables in Container**
Set in your deployment configuration.

---

## Monitoring & Observability

### Application Logs

**Structured Logging:**

Edit `app/main.py` to use JSON logging:
```python
import logging
import json_log_formatter

formatter = json_log_formatter.JSONFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(handlers=[handler], level=logging.INFO)
```

### Metrics

**Key Metrics to Track:**
- Request rate (webhooks/sec)
- Processing latency
- Classification success rate
- Digest send success rate
- Database query performance

**Tools:**
- Prometheus + Grafana
- Datadog
- New Relic
- Cloud platform built-in (CloudWatch, Cloud Monitoring)

### Alerts

Set up alerts for:
- API response time > 2s
- Error rate > 1%
- Pending digests > 50
- Database connection failures
- AA bot call failures

---

## Scaling Considerations

### Horizontal Scaling

FastAPI service is stateless - scale by adding replicas:

**Railway/Render:**
- Use scale slider in dashboard

**AWS ECS:**
- Configure auto-scaling based on CPU/memory

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: captpathfinder
spec:
  replicas: 3
  selector:
    matchLabels:
      app: captpathfinder
  template:
    spec:
      containers:
      - name: captpathfinder
        image: captpathfinder:latest
        ports:
        - containerPort: 8000
```

### Database Scaling

**Read Replicas:**
- Use for analytics queries
- Keep writes on primary

**Connection Pooling:**
Update `app/database.py` to use pgbouncer or connection pool:

```python
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo=settings.supabase_db_url,
    min_size=2,
    max_size=10
)
```

---

## Security Best Practices

### 1. Secrets Management
- Never commit `.env` files
- Use secrets manager in production
- Rotate credentials regularly

### 2. API Security
Add authentication to admin endpoints:

```python
from fastapi import Header, HTTPException

async def verify_admin_token(x_admin_token: str = Header()):
    if x_admin_token != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Unauthorized")

@app.post("/admin/send-digests", dependencies=[Depends(verify_admin_token)])
async def send_digests():
    ...
```

### 3. Rate Limiting
Add rate limiting to webhook endpoint:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/webhooks/community")
@limiter.limit("100/minute")
async def receive_webhook(request: Request, event: WebhookEvent):
    ...
```

### 4. Database Security
- Use SSL/TLS for database connections
- Principle of least privilege for DB user
- Enable audit logging

---

## Backup & Disaster Recovery

### Database Backups

**Supabase:**
- Automatic daily backups on paid plans
- Point-in-time recovery available

**Self-Managed:**
```bash
# Daily backup cron
0 2 * * * pg_dump -U postgres captpathfinder > /backups/captpathfinder-$(date +\%Y\%m\%d).sql
```

### Application State

- Version control for code (Git)
- Document all configuration changes
- Keep classification rules in source control

### Recovery Procedures

1. **Database corruption:**
   - Restore from latest backup
   - Re-run migrations if needed

2. **Application failure:**
   - Roll back to previous deployment
   - Check logs for errors

---

## Cost Optimization

### Database
- Archive old `events_raw` (>14 days) - automatic via housekeeping
- Consider read replicas only if needed
- Monitor storage growth

### Compute
- Use auto-scaling to scale down during low traffic
- Consider serverless (Cloud Run) for variable workloads

### Monitoring
- Use free tiers where possible (Grafana Cloud, etc.)
- Sample logs rather than storing everything

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review error logs
- Check digest send success rate
- Monitor database size

**Monthly:**
- Review and update classification rules
- Check AA bot integration health
- Analyze performance metrics

**Quarterly:**
- Update dependencies (`pip list --outdated`)
- Review and optimize database indexes
- Load test the system

### Updating Dependencies

```bash
# Check for updates
pip list --outdated

# Update requirements.txt
pip freeze > requirements.txt

# Test thoroughly before deploying
```

---

## Rollback Procedures

### Application Rollback

**Railway/Render:**
- Use dashboard to rollback to previous deployment

**AWS ECS:**
```bash
aws ecs update-service \
  --cluster captpathfinder \
  --service captpathfinder \
  --task-definition captpathfinder:PREVIOUS_VERSION
```

### Database Rollback

```sql
-- Rollback migration (if needed)
DROP TABLE IF EXISTS new_table;
-- Restore from backup if major changes
```

---

## Support & Troubleshooting

### Common Issues

**Issue: High latency on webhook endpoint**
- Check database connection pool
- Monitor classification regex performance
- Add caching if needed

**Issue: Digests not sending**
- Verify AA bot credentials
- Check network connectivity
- Review retry logic in logs

**Issue: Memory leaks**
- Monitor application memory usage
- Check for unclosed database connections
- Review async task handling

---

**Ready for Production?**

Run through the checklist one more time, then deploy with confidence! 🚀

