# Caddy HTTPS Setup for Bytelense

## Architecture

Caddy acts as a reverse proxy providing HTTPS for all services using self-signed certificates from Caddy's internal CA.

```
Browser (HTTPS)
    ↓
Caddy (Docker) - Provides HTTPS Layer
    ↓
Local Services (HTTP)
    ├── Frontend: http://localhost:5173
    ├── Backend: http://localhost:8000
    └── SearXNG: http://localhost:8080
```

## Service URLs

**With Caddy HTTPS:**
- Frontend: https://192.168.1.4:443 (or just https://192.168.1.4)
- Backend: https://192.168.1.4:8443
- SearXNG: https://192.168.1.4:8444

**Original HTTP Services (still running locally):**
- Frontend: http://192.168.1.4:5173
- Backend: http://192.168.1.4:8000
- SearXNG: http://192.168.1.4:8080

## Setup Steps

### 1. Start Caddy

```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense
docker compose -f docker-compose.caddy.yml up -d
```

### 2. Check Caddy Logs

```bash
docker logs bytelense-caddy -f
```

You should see Caddy generating certificates and starting successfully.

### 3. Export Root CA Certificate (for mobile)

```bash
# Extract the root CA from Caddy's data volume
docker cp bytelense-caddy:/data/caddy/pki/authorities/local/root.crt ~/Downloads/caddy-root-ca.crt
```

### 4. Install CA Certificate

**Desktop (Pop!_OS/Ubuntu):**
```bash
# Copy to system trust store
sudo cp ~/Downloads/caddy-root-ca.crt /usr/local/share/ca-certificates/caddy-local-ca.crt
sudo update-ca-certificates

# For Firefox specifically (uses its own trust store)
# Import manually: Settings → Privacy & Security → View Certificates → Authorities → Import
```

**Mobile (Android/Firefox Mobile):**
1. Transfer `caddy-root-ca.crt` to your mobile device
2. Settings → Security → Install certificates → CA certificate
3. Select the `caddy-root-ca.crt` file
4. Restart Firefox mobile

### 5. Test HTTPS Access

**Desktop:**
```bash
# Test frontend
curl -I https://192.168.1.4

# Test backend
curl -I https://192.168.1.4:8443

# Test SearXNG
curl -I https://192.168.1.4:8444
```

**Browser:**
- Open Firefox
- Navigate to https://192.168.1.4
- Camera should work without errors

### 6. Restart Frontend (if needed)

The frontend .env.local has been updated to use HTTPS backend. Restart frontend:

```bash
# In your frontend terminal, stop current process (Ctrl+C) and restart:
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/frontend
pnpm run dev
```

## Troubleshooting

### Certificate Not Trusted

If browser shows "Not Secure":
1. Check CA certificate is installed correctly
2. For Firefox, import certificate manually in Settings
3. Restart browser after installing certificate

### Connection Refused

If Caddy can't connect to services:
1. Ensure all services are running (frontend, backend, SearXNG)
2. Check `host.docker.internal` is resolving correctly
3. Check Caddy logs: `docker logs bytelense-caddy`

### SearXNG Connection Issues

SearXNG is in its own Docker setup at `/home/riju279/Documents/Tools/SearchXNG/searxng-docker/`
Ensure it's running on port 8080:
```bash
docker ps | grep searxng
```

## Commands Reference

**Start Caddy:**
```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense
docker compose -f docker-compose.caddy.yml up -d
```

**Stop Caddy:**
```bash
docker compose -f docker-compose.caddy.yml down
```

**View Logs:**
```bash
docker logs bytelense-caddy -f
```

**Restart Caddy:**
```bash
docker compose -f docker-compose.caddy.yml restart
```

**Export CA Certificate:**
```bash
docker cp bytelense-caddy:/data/caddy/pki/authorities/local/root.crt ~/Downloads/caddy-root-ca.crt
```

## Success Criteria

- ✅ Frontend accessible at https://192.168.1.4
- ✅ Backend accessible at https://192.168.1.4:8443
- ✅ SearXNG accessible at https://192.168.1.4:8444
- ✅ No certificate warnings (after CA installation)
- ✅ Camera works on desktop Firefox
- ✅ Camera works on mobile Firefox
- ✅ Images are sharp and clear
- ✅ OCR can read captured images
