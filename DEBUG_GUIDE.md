# Debug Endpoints Guide

This document describes the debug endpoints added to the Nexus API to help diagnose deployment issues.

## Debug Endpoints

### 1. `/debug/summary` - **START HERE**
Comprehensive debug endpoint that checks everything at once.

```bash
curl https://nexus-4uxn.onrender.com/debug/summary
```

**Returns:**
- API status and environment
- Environment variable configuration
- Mini App static files check
- Mini App service availability
- Automated recommendations for fixing issues

### 2. `/debug/env`
Check environment variables without exposing sensitive values.

```bash
curl https://nexus-4uxn.onrender.com/debug/env
```

**Returns:**
- Which critical environment variables are set (boolean)
- Values of non-sensitive variables
- List of all environment variable keys

### 3. `/debug/mini-app-check`
Check if the Mini App service is reachable.

```bash
curl https://nexus-4uxn.onrender.com/debug/mini-app-check
```

**Returns:**
- DNS resolution status
- HTTP response from Mini App URL
- Response headers and content preview
- Any connection errors

### 4. `/debug/static-files`
Check if Mini App static files exist in the filesystem.

```bash
curl https://nexus-4uxn.onrender.com/debug/static-files
```

**Returns:**
- Current working directory
- Dist directory path and existence
- List of all files in dist/ with sizes
- Total file count

### 5. `/debug/serve-mini-app`
Fallback endpoint to serve Mini App HTML if static service fails.

```bash
curl https://nexus-4uxn.onrender.com/debug/serve-mini-app
```

**Returns:**
- Mini App HTML if files exist
- Error page if files don't exist

## How to Use

### Step 1: Check Summary
```bash
curl https://nexus-4uxn.onrender.com/debug/summary | jq
```

This will give you an overview of what's wrong and specific recommendations.

### Step 2: Check Environment
```bash
curl https://nexus-4uxn.onrender.com/debug/env | jq
```

Verify that MINI_APP_URL is set correctly.

### Step 3: Check Mini App Service
```bash
curl https://nexus-4uxn.onrender.com/debug/mini-app-check | jq
```

This will tell you if the Mini App service is reachable and what it's returning.

### Step 4: Check Static Files
```bash
curl https://nexus-4uxn.onrender.com/debug/static-files | jq
```

This will show you if the built files are present on the server.

## Common Issues and Solutions

### Issue: Mini App service returns 404
**Debug output:** `mini_app_service.http.status_code: 404`

**Possible causes:**
1. Static service not deployed on Render
2. staticPublishPath points to wrong directory
3. Build failed during deployment

**Solutions:**
- Check Render dashboard for nexus-mini-app service status
- Verify build logs ran successfully
- Confirm staticPublishPath is `./mini-app/dist`

### Issue: MINI_APP_URL not set
**Debug output:** `"MINI_APP_URL not set"`

**Solution:**
Add to render.yaml:
```yaml
envVars:
  - key: MINI_APP_URL
    value: https://nexus-mini-app.onrender.com
```

### Issue: Static files not found
**Debug output:** `mini_app_files.exists: false`

**Solution:**
Run the build locally or on Render:
```bash
cd mini-app && bun install && bun run build
```

### Issue: Mini App service unreachable
**Debug output:** `mini_app_service.http.error: timeout/connection error`

**Possible causes:**
1. Service not running
2. DNS propagation issue
3. Firewall/network restriction

**Solutions:**
- Check Render dashboard - service may be down
- Wait a few minutes for DNS to propagate
- Verify service is deployed to correct region

## Enhanced Logging

All incoming requests are now logged to help track what's happening. Check the API logs on Render to see:

```
Request: GET /debug/summary
Request: GET /api/v1/groups/my-groups
```

## Startup Logging

The API now logs detailed startup information:

```
==================================================
Nexus API Starting Up
==================================================
Python Version: 3.12.2
Working Directory: /opt/render/project
Environment: production
Initializing database...
Connecting to Redis...
Setting up middleware pipeline...
Loading bot modules...
Setting up Telegram webhook...
Mini App dist directory found at: /opt/render/project/mini-app/dist
Mini App contains 5 files
Startup complete!
==================================================
```

If Mini App files are missing, you'll see:
```
Mini App dist directory NOT found at: /opt/render/project/mini-app/dist
Mini App will not be available via /debug/serve-mini-app
```

## Testing Locally

To test these debug endpoints locally:

1. Start the API server:
```bash
cd /home/engine/project
python -m uvicorn api.main:app --reload
```

2. Test endpoints:
```bash
curl http://localhost:8000/debug/summary
curl http://localhost:8000/debug/mini-app-check
curl http://localhost:8000/debug/static-files
```

3. Access Swagger UI to see all endpoints:
```
http://localhost:8000/docs
```

## Production Testing

Test the deployed API:

```bash
# Check overall status
curl https://nexus-4uxn.onrender.com/debug/summary | jq

# Check environment
curl https://nexus-4uxn.onrender.com/debug/env | jq

# Check Mini App connectivity
curl https://nexus-4uxn.onrender.com/debug/mini-app-check | jq

# Check static files
curl https://nexus-4uxn.onrender.com/debug/static-files | jq
```

## Next Steps

After running these debug endpoints:

1. Review the output from `/debug/summary`
2. Follow the recommendations provided
3. Check the specific endpoint for more details
4. Consult Render logs for the nexus-mini-app service
5. If issues persist, the debug output provides detailed information for support
