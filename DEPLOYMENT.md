# 🚀 Deployment Checklist

Use this checklist to deploy V1 to production.

---

## Pre-Deployment

### ✅ Code Preparation

- [ ] All tests passing (53/53)
  ```bash
  cd backend
  python test_database.py    # 33 tests
  python test_celery.py       # 5 tests
  python test_auth.py         # 15 tests
  ```

- [ ] No debug code in production
  - [ ] Remove `print()` statements
  - [ ] Remove `debug=True` from app.py
  - [ ] Review all TODO comments

- [ ] Environment variables documented
  - [ ] `JWT_SECRET_KEY` required
  - [ ] `REDIS_URL` optional
  - [ ] `DATABASE_URL` optional

### ✅ Security Configuration

- [ ] Generate secure JWT secret
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] Set JWT_SECRET_KEY in environment
  ```bash
  export JWT_SECRET_KEY='<generated-secret>'
  ```

- [ ] Review CORS settings in app.py
  - [ ] Restrict to your domain in production
  - [ ] Remove `*` if present

- [ ] Configure file upload limits
  - [ ] Max file size set appropriately
  - [ ] Allowed file types reviewed

- [ ] Database security
  - [ ] SQLite file permissions (600)
  - [ ] Regular backup schedule
  - [ ] Backup location secured

---

## Infrastructure Setup

### ✅ Server Preparation

- [ ] Server OS updated
  ```bash
  sudo apt-get update
  sudo apt-get upgrade
  ```

- [ ] Python 3.8+ installed
  ```bash
  python3 --version
  ```

- [ ] Tesseract OCR installed
  ```bash
  sudo apt-get install tesseract-ocr
  tesseract --version
  ```

- [ ] Redis installed and running
  ```bash
  sudo apt-get install redis-server
  sudo systemctl start redis
  sudo systemctl enable redis
  ```

- [ ] Redis authentication configured
  ```bash
  # Edit /etc/redis/redis.conf
  requirepass your-redis-password
  sudo systemctl restart redis
  ```

### ✅ Application Deployment

- [ ] Clone repository
  ```bash
  git clone <repository-url>
  cd Invoice-Receipt-Processor
  ```

- [ ] Create virtual environment
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Create required directories
  ```bash
  mkdir -p data uploads processed
  ```

- [ ] Set directory permissions
  ```bash
  chmod 755 data uploads processed
  ```

---

## Configuration

### ✅ Environment Variables

Create `.env` file:

```bash
# .env
JWT_SECRET_KEY=<your-secret-key>
REDIS_URL=redis://:your-redis-password@localhost:6379/0
DATABASE_URL=sqlite:///data/expenses.db
FLASK_ENV=production
```

Load environment:
```bash
export $(cat .env | xargs)
```

### ✅ Application Settings

- [ ] Disable Flask debug mode
  ```python
  # In app.py
  app.run(debug=False, host='0.0.0.0', port=5000)
  ```

- [ ] Configure logging
  ```python
  import logging
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s %(levelname)s: %(message)s',
      filename='app.log'
  )
  ```

- [ ] Set CORS for your domain
  ```python
  CORS(app, origins=['https://yourdomain.com'])
  ```

---

## Process Management

### ✅ Systemd Services

Create service files:

**Flask App:** `/etc/systemd/system/invoice-app.service`
```ini
[Unit]
Description=Invoice Processor Flask App
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Invoice-Receipt-Processor/backend
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/.env
ExecStart=/path/to/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Worker:** `/etc/systemd/system/celery-worker.service`
```ini
[Unit]
Description=Invoice Processor Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Invoice-Receipt-Processor/backend
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/.env
ExecStart=/path/to/venv/bin/celery -A celery_worker worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable invoice-app
sudo systemctl enable celery-worker
sudo systemctl start invoice-app
sudo systemctl start celery-worker
```

Check status:
```bash
sudo systemctl status invoice-app
sudo systemctl status celery-worker
```

---

## Reverse Proxy Setup

### ✅ Nginx Configuration

Install Nginx:
```bash
sudo apt-get install nginx
```

Create configuration: `/etc/nginx/sites-available/invoice-processor`
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Upload size limit
    client_max_body_size 50M;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout for long uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # Static files
    location /static/ {
        alias /path/to/Invoice-Receipt-Processor/frontend/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/invoice-processor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### ✅ SSL Certificate (Let's Encrypt)

Install Certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx
```

Obtain certificate:
```bash
sudo certbot --nginx -d yourdomain.com
```

Auto-renewal:
```bash
sudo systemctl enable certbot.timer
```

---

## Monitoring & Maintenance

### ✅ Log Files

- [ ] Application logs: `backend/app.log`
- [ ] Celery logs: `sudo journalctl -u celery-worker`
- [ ] Flask logs: `sudo journalctl -u invoice-app`
- [ ] Nginx logs: `/var/log/nginx/`

Monitor logs:
```bash
# Application logs
tail -f backend/app.log

# Service logs
sudo journalctl -u invoice-app -f
sudo journalctl -u celery-worker -f
```

### ✅ Database Backups

Create backup script: `backup-db.sh`
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/invoice-processor"
mkdir -p $BACKUP_DIR

# Backup SQLite database
cp /path/to/data/expenses.db $BACKUP_DIR/expenses_$DATE.db
cp /path/to/data/users.db $BACKUP_DIR/users_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

Schedule with cron:
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup-db.sh
```

### ✅ Health Checks

Create health check endpoint:
```python
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'redis': 'connected',
        'timestamp': datetime.now().isoformat()
    })
```

Monitor with uptime service (e.g., UptimeRobot)

---

## Testing in Production

### ✅ Smoke Tests

- [ ] Homepage loads
  ```bash
  curl https://yourdomain.com
  ```

- [ ] API responds
  ```bash
  curl https://yourdomain.com/health
  ```

- [ ] Register user
  ```bash
  curl -X POST https://yourdomain.com/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","username":"test","password":"test123"}'
  ```

- [ ] Login works
  ```bash
  curl -X POST https://yourdomain.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test123"}'
  ```

- [ ] Upload document
  ```bash
  curl -X POST https://yourdomain.com/api/upload \
    -F "file=@test-invoice.pdf"
  ```

- [ ] Async extraction works
  ```bash
  curl -X POST https://yourdomain.com/api/extract/{file_id} \
    -H "Content-Type: application/json" \
    -d '{"async":true}'
  ```

---

## Performance Optimization

### ✅ Redis Optimization

- [ ] Configure Redis persistence
  ```bash
  # In /etc/redis/redis.conf
  save 900 1
  save 300 10
  save 60 10000
  ```

- [ ] Set memory limit
  ```bash
  maxmemory 256mb
  maxmemory-policy allkeys-lru
  ```

### ✅ Celery Optimization

- [ ] Configure worker concurrency
  ```bash
  # In celery-worker.service
  --concurrency=4  # Adjust based on CPU cores
  ```

- [ ] Set task time limits
  ```python
  # In celery_worker.py
  task_time_limit = 300
  task_soft_time_limit = 240
  ```

### ✅ Application Optimization

- [ ] Enable gzip compression (Nginx)
  ```nginx
  gzip on;
  gzip_types text/plain text/css application/json application/javascript;
  ```

- [ ] Configure file upload limits
  ```python
  app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
  ```

---

## Security Hardening

### ✅ Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block Redis from external access
sudo ufw deny 6379/tcp

# Enable firewall
sudo ufw enable
```

### ✅ File Permissions

```bash
# Set ownership
sudo chown -R www-data:www-data /path/to/Invoice-Receipt-Processor

# Set directory permissions
find /path/to/Invoice-Receipt-Processor -type d -exec chmod 755 {} \;

# Set file permissions
find /path/to/Invoice-Receipt-Processor -type f -exec chmod 644 {} \;

# Protect database files
chmod 600 /path/to/data/*.db

# Make scripts executable
chmod +x /path/to/backup-db.sh
```

### ✅ Fail2Ban Configuration

Install and configure:
```bash
sudo apt-get install fail2ban

# Create jail for Flask app
sudo nano /etc/fail2ban/jail.d/invoice-app.conf
```

```ini
[invoice-app]
enabled = true
port = 80,443
filter = invoice-app
logpath = /path/to/backend/app.log
maxretry = 5
bantime = 3600
```

---

## Post-Deployment

### ✅ Monitoring

- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Configure email alerts for downtime
- [ ] Monitor disk space usage
- [ ] Monitor CPU and memory usage
- [ ] Track error rates in logs

### ✅ Documentation

- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document backup/restore procedure
- [ ] Create user guide for your team

### ✅ User Communication

- [ ] Announce launch to users
- [ ] Provide getting started guide
- [ ] Set up support channel
- [ ] Gather initial feedback

---

## Rollback Plan

If deployment fails:

```bash
# 1. Stop services
sudo systemctl stop invoice-app
sudo systemctl stop celery-worker

# 2. Restore database from backup
cp /var/backups/invoice-processor/expenses_YYYYMMDD.db /path/to/data/expenses.db

# 3. Revert code
git checkout <previous-commit>

# 4. Restart services
sudo systemctl start invoice-app
sudo systemctl start celery-worker
```

---

## Success Criteria

✅ Deployment is successful when:

- [ ] All services running (invoice-app, celery-worker, redis, nginx)
- [ ] HTTPS certificate valid
- [ ] Health check returns 200 OK
- [ ] Can register new user
- [ ] Can login and get JWT token
- [ ] Can upload and process document
- [ ] Async processing works
- [ ] Database queries < 100ms
- [ ] No errors in logs
- [ ] Backups running automatically

---

## Support

After deployment, monitor for:
- Error spikes in logs
- Performance degradation
- User feedback
- Security alerts

Keep this checklist for future deployments and updates.

---

**Last Updated:** 2025-11-06
**Status:** Ready for production deployment ✅
