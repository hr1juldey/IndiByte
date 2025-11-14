# Bytelense Frontend Troubleshooting Guide
## For Users With Zero JavaScript Debugging Skills

This guide helps you fix common problems WITHOUT needing to understand JavaScript.

---

## How to Read Error Messages

When something breaks, you'll see error messages. Here's how to read them:

### 1. Open Browser Console

**Chrome/Edge**: Press `F12` or `Ctrl+Shift+I`
**Firefox**: Press `F12`
**Safari**: `Cmd+Option+I`

You'll see a panel at the bottom of your screen with tabs: "Console", "Network", "Sources", etc.

Click the **Console** tab. This is where errors appear.

### 2. Look for Red Text

Errors show up in red. They look like:

```
ERROR: WebSocket connection failed
ERROR: Camera permission denied
ERROR: Failed to fetch
```

Copy the EXACT error text and check this guide.

---

## Common Errors & Fixes

### ❌ "Backend not connected" or "Failed to fetch"

**What it means**: Your frontend can't talk to the backend server.

**Fix**:

1. **Check backend is running**:
   Open a terminal and run:
   ```bash
   curl http://localhost:8000/health
   ```
   
   If you see JSON response → Backend is running
   If you see "Connection refused" → Backend is NOT running

2. **Start backend**:
   ```bash
   cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Refresh browser**: Press `Ctrl+R`

---

### 📷 "Camera permission denied"

**What it means**: Browser blocked camera access.

**Fix**:

1. **Allow camera in browser settings**:
   
   **Chrome**:
   - Click lock icon 🔒 in address bar
   - Find "Camera" → Set to "Allow"
   - Refresh page (`Ctrl+R`)

   **Firefox**:
   - Click lock icon 🔒 in address bar
   - Click "More Information"
   - Go to "Permissions" tab
   - Uncheck "Use Default" for Camera
   - Select "Allow"
   - Refresh page

2. **Check camera not in use**:
   - Close Zoom, Teams, Skype, or any app using camera
   - Try again

3. **Try different browser**:
   - If still broken, try Chrome/Firefox/Edge

---

### 🔌 "WebSocket connection failed" or "WebSocket disconnected"

**What it means**: Real-time connection to backend is broken.

**Fix**:

1. **Check backend WebSocket is running**:
   ```bash
   curl http://localhost:8000/health
   ```
   Look for `"socketio": {"status": "ok"}` in response

2. **Restart backend**:
   - Stop backend (`Ctrl+C` in terminal)
   - Start again:
     ```bash
     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
     ```

3. **Refresh browser**: `Ctrl+R`

---

### ⏳ "Scan takes forever" (>60 seconds)

**What it means**: Backend is processing but taking too long.

**Possible causes**:
- Ollama model loading (first scan can take 30-60s)
- Network slow
- Backend crashed

**Fix**:

1. **Check backend terminal for errors**:
   Look for red text in terminal where backend is running
   Common errors:
   - "Ollama connection failed" → Start Ollama: `ollama serve`
   - "Out of memory" → Backend needs more RAM
   - "Connection timeout" → Internet slow/disconnected

2. **Wait 60 seconds**:
   First scan is always slow (loading AI model)
   Subsequent scans should be faster

3. **Refresh and try again**:
   If still stuck after 60s, refresh browser (`Ctrl+R`)

---

### 🖼️ "Image too dark" or "Image too blurry"

**What it means**: Camera image quality is poor.

**Fix**:

1. **Better lighting**:
   - Use bright overhead light
   - Avoid shadows on product
   - Natural light (near window) works best

2. **Hold camera steady**:
   - Rest phone/laptop on stable surface
   - Don't move while capturing
   - Get closer to product

3. **Clean camera lens**:
   - Wipe with soft cloth
   - Remove phone case if blocking lens

---

### 📦 "Product not found in database"

**What it means**: Backend couldn't find nutritional info for this product.

**Why**:
- Barcode not in OpenFoodFacts database
- OCR couldn't read label text clearly
- Product is regional/not indexed

**Fix**:

1. **Try better angle**:
   - Make sure barcode is visible
   - Avoid glare/reflections
   - Get closer to label

2. **Retry scan**:
   Sometimes second attempt works

3. **Use upload instead**:
   - Take photo with phone camera (better quality)
   - Upload that photo

4. **Manual entry** (coming soon):
   - Type product name manually

---

### 🚫 "TypeError: Cannot read property 'X' of undefined"

**What it means**: Frontend received unexpected data from backend.

**This is a BUG**. Do this:

1. **Take screenshot**:
   - Press `F12` to open console
   - Take screenshot of error message
   - Save screenshot

2. **Note what you did**:
   - What button did you click?
   - What product were you scanning?
   - Had you done anything before this?

3. **Report to developer**:
   - Share screenshot
   - Explain steps to reproduce

4. **Temporary fix**: Refresh page (`Ctrl+R`)

---

### ⚠️ White screen (nothing shows)

**What it means**: Frontend crashed completely.

**Fix**:

1. **Hard refresh**:
   - Press `Ctrl+Shift+R` (Windows/Linux)
   - Press `Cmd+Shift+R` (Mac)
   - This clears cache

2. **Clear localStorage**:
   - Press `F12` → Console tab
   - Type: `localStorage.clear()`
   - Press Enter
   - Refresh page (`Ctrl+R`)

3. **Check console**:
   - Press `F12` → Console tab
   - Take screenshot of errors
   - Report to developer

---

## Checking System Status

### Backend Health Check

Open this URL in browser: http://localhost:8000/health

**Good response** (everything working):
```json
{
  "status": "ok",
  "services": {
    "ollama": { "status": "connected" },
    "searxng": { "status": "connected" },
    "openfoodfacts": { "status": "connected" }
  }
}
```

**Bad response** (something broken):
```json
{
  "status": "degraded",
  "services": {
    "ollama": {
      "status": "error",
      "error": "Connection refused"
    }
  }
}
```

If you see "error" for any service:
- **ollama**: Run `ollama serve` in terminal
- **searxng**: Run `docker start searxng` (or restart Docker container)
- **openfoodfacts**: Check internet connection

### Frontend Health Check

Open http://localhost:5173 and you should see health check page.

If you see "Backend not connected", fix backend first (see above).

---

## When to Ask for Help

You should ask developer for help if:

1. **Error persists after following fixes above**
2. **You see "BUG" in error message**
3. **Application crashes repeatedly**
4. **Error message not in this guide**

**When asking for help, provide**:
- Screenshot of error (F12 → Console)
- What you were doing when error happened
- Browser you're using (Chrome/Firefox/Safari)
- Operating system (Windows/Mac/Linux)

---

## Prevention Tips

### Before Each Session

1. **Start backend first**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
   Wait for "Application startup complete"

2. **Check health**: http://localhost:8000/health

3. **Then start frontend**:
   ```bash
   cd docs/UI
   pnpm run dev
   ```

4. **Open browser**: http://localhost:5173

### During Use

- Don't close backend terminal
- Don't close too many browser tabs (memory)
- Refresh if page feels slow
- Clear localStorage if weird behavior

### After Session

- Stop frontend: `Ctrl+C` in terminal
- Stop backend: `Ctrl+C` in terminal
- Optional: Stop Ollama: `pkill ollama`

---

## Emergency Reset

If everything is broken and nothing works:

### Nuclear Option: Full Reset

```bash
# 1. Stop everything
pkill -f ollama
pkill -f uvicorn
pkill -f vite

# 2. Clear browser data
# In browser: Ctrl+Shift+Delete → Clear all data

# 3. Reinstall frontend dependencies
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/docs/UI
rm -rf node_modules
pnpm install

# 4. Restart backend
cd ../../backend
uvicorn app.main:app --reload

# 5. Restart frontend
cd ../docs/UI
pnpm run dev

# 6. Open fresh browser tab
# Go to http://localhost:5173
```

---

## Browser Compatibility

| Browser | Version | Camera | WebSocket | Status |
|---------|---------|--------|-----------|--------|
| Chrome | 90+ | ✅ | ✅ | Recommended |
| Firefox | 88+ | ✅ | ✅ | Works well |
| Edge | 90+ | ✅ | ✅ | Works well |
| Safari | 14+ | ⚠️ | ✅ | Camera may need permission |
| Mobile Chrome | Latest | ✅ | ✅ | Works |
| Mobile Safari | Latest | ⚠️ | ✅ | HTTPS required |

**Note**: Mobile browsers require HTTPS for camera (localhost is OK for dev).

---

## Performance Issues

### "Page is slow/laggy"

**Causes**:
- Too many browser tabs open
- Ollama using too much RAM
- Dev server memory leak

**Fixes**:
1. Close unused tabs
2. Restart backend/frontend
3. Check RAM usage: `htop` (Linux) or Task Manager (Windows)
4. Use smaller Ollama model (qwen3:8b instead of qwen3:30b)

### "Camera is laggy"

**Fixes**:
1. Close other apps
2. Lower camera resolution (edit camera hook to use 720p instead of 1080p)
3. Use better device

---

## Quick Diagnostics

Run these commands to check everything:

```bash
# Check Node.js
node --version  # Should be 20+

# Check pnpm
pnpm --version  # Should be 9+

# Check backend
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173

# Check Ollama
ollama list  # Should show models

# Check processes
ps aux | grep uvicorn  # Backend should be running
ps aux | grep vite     # Frontend should be running
```

---

## Error Code Reference

| Error Code | Meaning | Fix |
|-----------|---------|-----|
| `ERR_CONNECTION_REFUSED` | Backend not running | Start backend |
| `ERR_NAME_NOT_RESOLVED` | Wrong URL | Check localhost:8000 |
| `ERR_INTERNET_DISCONNECTED` | No internet | Check WiFi |
| `NotAllowedError` | Camera permission | Allow in browser settings |
| `NotFoundError` | No camera | Connect camera or use upload |
| `WebSocket connection failed` | Backend WebSocket broken | Restart backend |
| `TypeError: undefined` | Bug in code | Report to developer |
| `SyntaxError: JSON` | Backend sent bad data | Check backend logs |

---

## Logs Location

If developer asks for logs:

**Backend logs**: In terminal where you ran `uvicorn`

**Frontend logs**: 
1. Press F12 → Console tab
2. Right-click in console
3. Select "Save as..."
4. Save to file

**Browser console**: Copy all red errors and save to text file

---

## Final Checklist

Before reporting a bug, verify:

- [ ] Backend is running (`curl http://localhost:8000/health`)
- [ ] Frontend is running (http://localhost:5173 loads)
- [ ] Ollama is running (`ollama list` works)
- [ ] Camera permission is allowed (check browser settings)
- [ ] Tried refreshing browser (`Ctrl+R`)
- [ ] Tried hard refresh (`Ctrl+Shift+R`)
- [ ] Tried different browser
- [ ] Checked console for errors (`F12`)
- [ ] Took screenshot of error
- [ ] Can describe steps to reproduce

---

## Success!

If you can:
- See health check page with green checkmarks
- Click "Open Camera" and see video stream
- Capture an image
- See "Connecting..." message

Then your frontend is working correctly!

**Next**: Try a full scan to test end-to-end flow.
