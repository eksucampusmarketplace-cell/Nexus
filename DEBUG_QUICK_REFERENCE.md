# Debug Quick Reference

## One Command to Diagnose Everything

```bash
curl https://nexus-4uxn.onrender.com/debug/summary | jq
```

This single command will:
- ✅ Check environment variables
- ✅ Verify Mini App files exist
- ✅ Test Mini App service connectivity
- ✅ Provide specific recommendations to fix issues

## All Debug Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/debug/summary` | Complete diagnosis with recommendations |
| `/debug/env` | Check environment variables |
| `/debug/mini-app-check` | Test Mini App connectivity |
| `/debug/static-files` | Check if Mini App files exist |
| `/debug/serve-mini-app` | Fallback: serve Mini App directly |

## Quick Testing Commands

```bash
# Complete diagnosis
curl https://nexus-4uxn.onrender.com/debug/summary | jq

# Check environment
curl https://nexus-4uxn.onrender.com/debug/env | jq

# Test Mini App service
curl https://nexus-4uxn.onrender.com/debug/mini-app-check | jq

# Check static files
curl https://nexus-4uxn.onrender.com/debug/static-files | jq

# Try fallback endpoint
curl https://nexus-4uxn.onrender.com/debug/serve-mini-app
```

## Common Fixes

### MINI_APP_URL not set
Add to `render.yaml`:
```yaml
envVars:
  - key: MINI_APP_URL
    value: https://nexus-mini-app.onrender.com
```

### Mini App returns 404
- Check Render dashboard for nexus-mini-app service
- View build logs
- Verify `staticPublishPath: ./mini-app/dist`

### Static files not found
Build the Mini App:
```bash
cd mini-app && bun run build
```

## Documentation

- `DEBUG_GUIDE.md` - Complete troubleshooting guide
- `DEBUG_SUMMARY.md` - Detailed explanation of all endpoints
- `DEBUG_QUICK_REFERENCE.md` - This quick reference card

## View in Swagger UI

```
https://nexus-4uxn.onrender.com/docs
```

Look for endpoints under the "debug" tag.
