# Debug Endpoints Added to Nexus API

## Summary

I've added comprehensive debug endpoints to the Nexus API to help diagnose the Mini App deployment issue on Render. These endpoints will help identify what's wrong without needing access to Render logs.

## New Debug Endpoints

### 1. `/debug/summary` - **START HERE**
Comprehensive overview of system state and issues.

```bash
curl https://nexus-4uxn.onrender.com/debug/summary | jq
```

**What it checks:**
- API service status and version
- Environment variables configuration
- Mini App static files existence
- Mini App service connectivity
- **Automatically provides recommendations** based on findings

### 2. `/debug/env`
Check which environment variables are set.

```bash
curl https://nexus-4uxn.onrender.com/debug/env | jq
```

**Use to verify:**
- MINI_APP_URL is set correctly
- Database and Redis are configured
- All required environment variables exist

### 3. `/debug/mini-app-check`
Test connectivity to Mini App service.

```bash
curl https://nexus-4uxn.onrender.com/debug/mini-app-check | jq
```

**Returns:**
- DNS resolution status
- HTTP response from Mini App URL
- Response headers and content preview
- Connection errors

### 4. `/debug/static-files`
Check if Mini App files exist on the server.

```bash
curl https://nexus-4uxn.onrender.com/debug/static-files | jq
```

**Shows:**
- Working directory path
- Whether `mini-app/dist/` exists
- List of all files with sizes
- Total file count

### 5. `/debug/serve-mini-app`
Fallback endpoint to serve Mini App HTML directly.

```bash
curl https://nexus-4uxn.onrender.com/debug/serve-mini-app
```

**Purpose:**
- Provides an alternative way to access the Mini App
- Useful if static service deployment fails
- Returns Mini App HTML or error page

## Enhanced Logging

### Request Logging
All incoming HTTP requests are now logged:
```
Request: GET /debug/summary
Request: POST /api/v1/groups/my-groups
```

### Startup Logging
Detailed startup information:
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

**Warnings you might see:**
```
Mini App dist directory NOT found at: /opt/render/project/mini-app/dist
Mini App will not be available via /debug/serve-mini-app
```

## How to Use on Production

### Quick Diagnosis
```bash
# Get complete picture of what's wrong
curl https://nexus-4uxn.onrender.com/debug/summary | jq
```

This single command will:
1. Check all environment variables
2. Verify Mini App static files exist
3. Test Mini App service connectivity
4. Provide specific recommendations for fixing issues

### Step-by-Step Diagnosis

If `/debug/summary` isn't clear enough:

```bash
# 1. Check environment
curl https://nexus-4uxn.onrender.com/debug/env | jq

# 2. Check Mini App connectivity
curl https://nexus-4uxn.onrender.com/debug/mini-app-check | jq

# 3. Check static files
curl https://nexus-4uxn.onrender.com/debug/static-files | jq
```

## Common Issues and Solutions

### Issue 1: MINI_APP_URL Not Set
**Debug Output:**
```json
{
  "mini_app_service": {
    "error": "MINI_APP_URL not set"
  }
}
```

**Solution:**
Add to `render.yaml` under the nexus-api service envVars:
```yaml
- key: MINI_APP_URL
  value: https://nexus-mini-app.onrender.com
```

### Issue 2: Mini App Returns 404
**Debug Output:**
```json
{
  "mini_app_service": {
    "http": {
      "status_code": 404,
      "success": false
    }
  }
}
```

**Possible Causes:**
1. Static service not deployed
2. Build failed during deployment
3. Wrong staticPublishPath

**Solutions:**
- Check Render dashboard for nexus-mini-app service status
- View build logs to see if `cd mini-app && bun install && bun run build` succeeded
- Verify `staticPublishPath: ./mini-app/dist` in render.yaml

### Issue 3: Static Files Not Found
**Debug Output:**
```json
{
  "mini_app_files": {
    "exists": false,
    "dist_path": "/opt/render/project/mini-app/dist"
  }
}
```

**Solution:**
The Mini App needs to be built. Either:
1. Build locally: `cd mini-app && bun run build`
2. Check why Render build failed (see build logs)
3. Ensure build command in render.yaml is correct: `cd mini-app && bun install && bun run build`

### Issue 4: Mini App Service Unreachable
**Debug Output:**
```json
{
  "mini_app_service": {
    "http": {
      "success": false,
      "error": "timeout"
    }
  }
}
```

**Solutions:**
- Wait a few minutes for DNS to propagate
- Check if nexus-mini-app service is running on Render
- Verify the service deployed to the correct region
- Try accessing directly: https://nexus-mini-app.onrender.com

## Testing Locally

Before deploying to Render, test debug endpoints locally:

```bash
# 1. Build the Mini App
cd mini-app && bun run build

# 2. Start API (with minimal env)
cd ..
export MINI_APP_URL=http://localhost:4173
.venv/bin/python -m uvicorn api.main:app --reload

# 3. In another terminal, test endpoints
curl http://localhost:8000/debug/summary
curl http://localhost:8000/debug/static-files
curl http://localhost:8000/debug/mini-app-check
```

## Viewing Debug Endpoints in Swagger UI

All debug endpoints are documented in Swagger UI:

```
https://nexus-4uxn.onrender.com/docs
```

Look for the "debug" tag to see all debug endpoints with examples.

## What These Endpoints Will Reveal

When you run these endpoints on your deployed API, you'll discover:

1. **Environment Configuration Issues**
   - Missing environment variables
   - Incorrect values (wrong URLs, etc.)

2. **File System Issues**
   - Mini App not built (no dist/ directory)
   - Wrong build output location
   - Build process errors

3. **Network/Service Issues**
   - Mini App service not running
   - DNS resolution problems
   - Connection timeouts
   - Wrong service URL

4. **Deployment Issues**
   - Static service not deployed
   - Build command failed
   - Wrong staticPublishPath

## Next Steps

1. **Deploy these changes** to Render (they're already committed)
2. **Wait for deployment** to complete
3. **Run the debug summary:**
   ```bash
   curl https://nexus-4uxn.onrender.com/debug/summary | jq
   ```
4. **Follow the recommendations** provided in the response
5. **Check specific endpoints** for more details if needed
6. **Review Render logs** for nexus-mini-app service if issues persist

## Documentation

See `DEBUG_GUIDE.md` for complete documentation of all debug endpoints and troubleshooting guide.

## Files Modified

- `api/main.py` - Added debug endpoints and enhanced logging
- `DEBUG_GUIDE.md` - Complete debugging guide
- `DEBUG_SUMMARY.md` - This summary document
