# Nginx Configuration - SchizoDot AI

## Overview

Nginx acts as a reverse proxy and load balancer for the SchizoDot AI system, routing traffic to backend services.

## Architecture

```
Internet
    │
    ▼
┌─────────────────────┐
│   Nginx (Port 80)   │
│   Reverse Proxy     │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌─────────┐
│ FastAPI │  │   AI    │
│  :8000  │  │Pipeline │
└─────────┘  │  :8001  │
             └─────────┘
```

## Configuration Files

### 1. nginx.conf (Main Configuration)

**Location**: `infra/nginx/nginx.conf`

**Purpose**: Global Nginx settings

**Key Features**:
- Worker process optimization
- Gzip compression
- Security headers
- Rate limiting zones
- Upstream server definitions
- Logging configuration

**Upstreams Defined**:
- `fastapi_backend` → `fastapi-backend:8000`
- `ai_pipeline` → `ai-pipeline:8001`

---

### 2. default.conf (HTTP Configuration)

**Location**: `infra/nginx/conf.d/default.conf`

**Purpose**: HTTP routing rules

**Routes**:

| Path | Upstream | Purpose |
|------|----------|---------|
| `/api/*` | FastAPI | Main API endpoints |
| `/docs` | FastAPI | Swagger UI |
| `/openapi.json` | FastAPI | OpenAPI schema |
| `/ai/*` | AI Pipeline | AI service endpoints |
| `/health` | Nginx | Health check |
| `/` | Redirect | Redirect to health |

**Rate Limits**:
- API endpoints: 10 req/s (burst 20)
- Upload endpoints: 2 req/s (burst 5)

**Timeouts**:
- Standard: 60s
- AI endpoints: 120s (longer for processing)

**Max Upload Size**: 100MB (for video files)

---

### 3. ssl.conf.example (HTTPS Configuration)

**Location**: `infra/nginx/conf.d/ssl.conf.example`

**Purpose**: Production SSL/TLS setup

**Features**:
- HTTP to HTTPS redirect
- TLS 1.2 and 1.3
- OCSP stapling
- HSTS header
- Let's Encrypt support

**To Enable**:
```bash
# 1. Get SSL certificates
certbot certonly --webroot -w /var/www/certbot -d your-domain.com

# 2. Update domain in ssl.conf.example
sed -i 's/your-domain.com/actual-domain.com/g' ssl.conf.example

# 3. Rename to activate
mv ssl.conf.example ssl.conf

# 4. Reload Nginx
docker-compose exec nginx nginx -s reload
```

---

## Security Features

### 1. Rate Limiting

**API Endpoints**:
```nginx
limit_req zone=api_limit burst=20 nodelay;
```
- 10 requests/second baseline
- Burst up to 20 requests
- Prevents API abuse

**Upload Endpoints**:
```nginx
limit_req zone=upload_limit burst=5 nodelay;
```
- 2 requests/second baseline
- Burst up to 5 requests
- Prevents upload flooding

---

### 2. Security Headers

**X-Frame-Options**: Prevents clickjacking
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
```

**X-Content-Type-Options**: Prevents MIME sniffing
```nginx
add_header X-Content-Type-Options "nosniff" always;
```

**X-XSS-Protection**: XSS filter
```nginx
add_header X-XSS-Protection "1; mode=block" always;
```

**HSTS** (HTTPS only): Force HTTPS
```nginx
add_header Strict-Transport-Security "max-age=31536000" always;
```

---

### 3. Request Size Limits

```nginx
client_max_body_size 100M;
```
- Allows video uploads up to 100MB
- Prevents memory exhaustion attacks

---

## Performance Optimizations

### 1. Gzip Compression

Compresses responses for:
- JSON (API responses)
- JavaScript
- CSS
- XML
- Fonts

**Compression Level**: 6 (balanced)

**Benefit**: 60-80% size reduction

---

### 2. Keep-Alive Connections

```nginx
keepalive 32;  # FastAPI upstream
keepalive 16;  # AI Pipeline upstream
```
- Reuses TCP connections
- Reduces latency
- Improves throughput

---

### 3. Load Balancing

```nginx
upstream fastapi_backend {
    least_conn;  # Route to least busy server
    server fastapi-backend:8000;
}
```
- `least_conn` algorithm
- Health checks (max_fails=3)
- Automatic failover

---

## Monitoring & Logging

### Access Logs

**Location**: `/var/log/nginx/access.log`

**Format**:
```
IP - User [Time] "Request" Status Bytes "Referer" "User-Agent"
request_time upstream_connect_time upstream_response_time
```

**View logs**:
```bash
docker-compose logs -f nginx
# Or
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

---

### Error Logs

**Location**: `/var/log/nginx/error.log`

**Levels**: warn, error, crit

**View logs**:
```bash
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

---

### Health Checks

**Nginx Health**:
```bash
curl http://localhost/health
# Response: healthy
```

**Backend Health** (via Nginx):
```bash
curl http://localhost/api/v1/health
# Response: {"status":"ok"}
```

---

## Testing Configuration

### 1. Test Syntax

```bash
# Test configuration without reloading
docker-compose exec nginx nginx -t

# Expected output:
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

### 2. Reload Configuration

```bash
# Reload without downtime
docker-compose exec nginx nginx -s reload
```

---

### 3. Test Endpoints

```bash
# Health check
curl -I http://localhost/health

# API endpoint
curl http://localhost/api/v1/health

# Check headers
curl -I http://localhost/api/v1/health | grep -i "x-"

# Test rate limiting
for i in {1..15}; do curl http://localhost/api/v1/health; done
```

---

## Troubleshooting

### 502 Bad Gateway

**Cause**: Backend service not running

**Solution**:
```bash
# Check backend status
docker-compose ps fastapi-backend

# Check backend logs
docker-compose logs fastapi-backend

# Restart backend
docker-compose restart fastapi-backend
```

---

### 504 Gateway Timeout

**Cause**: Backend taking too long to respond

**Solution**:
```nginx
# Increase timeout in default.conf
proxy_read_timeout 120s;
```

Then reload:
```bash
docker-compose exec nginx nginx -s reload
```

---

### Rate Limit Errors (429)

**Cause**: Too many requests

**Response**:
```json
{
  "error": "Too Many Requests",
  "status": 429
}
```

**Solution**:
- Wait before retrying
- Implement exponential backoff
- Or increase rate limits (not recommended)

---

### SSL Certificate Issues

**Cause**: Expired or invalid certificates

**Solution**:
```bash
# Renew Let's Encrypt certificates
certbot renew

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

---

## Production Deployment

### 1. Enable SSL

```bash
# Install Certbot
apt-get install certbot

# Get certificates
certbot certonly --webroot \
  -w /var/www/certbot \
  -d your-domain.com \
  -d www.your-domain.com

# Enable SSL config
cd infra/nginx/conf.d
cp ssl.conf.example ssl.conf
nano ssl.conf  # Update domain names

# Reload
docker-compose exec nginx nginx -s reload
```

---

### 2. Auto-Renewal

Add to crontab:
```bash
0 0 * * * certbot renew --quiet && docker-compose exec nginx nginx -s reload
```

---

### 3. Security Hardening

**Disable server tokens**:
```nginx
server_tokens off;
```

**Restrict AI endpoints** (internal only):
```nginx
location /ai/ {
    allow 172.16.0.0/12;  # Docker network
    deny all;
    proxy_pass http://ai_pipeline/;
}
```

**Add CSP header**:
```nginx
add_header Content-Security-Policy "default-src 'self'" always;
```

---

## Custom Configuration

### Add New Route

Edit `infra/nginx/conf.d/default.conf`:

```nginx
location /custom/ {
    proxy_pass http://fastapi_backend;
    proxy_set_header Host $host;
    # ... other headers
}
```

Reload:
```bash
docker-compose exec nginx nginx -s reload
```

---

### Add New Upstream

Edit `infra/nginx/nginx.conf`:

```nginx
upstream new_service {
    server new-service:9000;
}
```

Then route to it in `default.conf`:
```nginx
location /new/ {
    proxy_pass http://new_service/;
}
```

---

## Performance Tuning

### Worker Processes

```nginx
worker_processes auto;  # Use all CPU cores
```

For specific count:
```nginx
worker_processes 4;  # 4 workers
```

---

### Worker Connections

```nginx
worker_connections 1024;  # Per worker
```

Total capacity: `workers × connections`

---

### Buffer Sizes

```nginx
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_busy_buffers_size 8k;
```

Increase for large responses:
```nginx
proxy_buffer_size 8k;
proxy_buffers 16 8k;
```

---

## Next Steps

After Nginx configuration:
1. ✅ Test configuration: `docker-compose exec nginx nginx -t`
2. ⏭️ Start full stack: `docker-compose up -d`
3. ⏭️ Verify all services healthy
4. ⏭️ Test end-to-end flow

---

## References

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [SSL Best Practices](https://ssl-config.mozilla.org/)
- [Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
