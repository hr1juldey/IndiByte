# Bytelense Frontend Quick Start Guide

## Get Running in 30 Minutes

**Target**: Get development environment running with health check

---

## Prerequisites Checklist

- [ ] Node.js 20+ installed (`node --version`)
- [ ] pnpm installed (`npm install -g pnpm`)
- [ ] Backend running on <http://localhost:8000>
- [ ] Modern browser (Chrome/Firefox/Edge)

---

## Step 1: Create Project (5 minutes)

```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/docs/UI

# Create Vite project
pnpm create vite@latest . --template react-ts

# Install dependencies
pnpm install

# Install Tailwind
pnpm add -D tailwindcss postcss autoprefixer
pnpm dlx tailwindcss init -p

# Install shadcn/ui dependencies
pnpm add class-variance-authority clsx tailwind-merge lucide-react @radix-ui/react-slot

# Install WebSocket client
pnpm add socket.io-client

# Install toast library
pnpm add sonner

# Install date utilities
pnpm add date-fns
```

---

## Step 2: Configure Tailwind (2 minutes)

Replace `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Replace `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## Step 3: Initialize shadcn/ui (3 minutes)

```bash
# Initialize shadcn/ui
pnpm dlx shadcn@latest init

# When prompted:
# - Style: Default
# - Base color: Neutral or Slate
# - CSS variables: Yes

# Install base components
pnpm dlx shadcn@latest add button
pnpm dlx shadcn@latest add card
pnpm dlx shadcn@latest add badge
pnpm dlx shadcn@latest add alert
```

---

## Step 4: Configure Vite (2 minutes)

Update `vite.config.ts`:

```typescript
import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
```

Update `tsconfig.json` to add paths:

```json
{
  "compilerOptions": {
    // ... existing config
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

## Step 5: Create Environment File (1 minute)

Create `.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## Step 6: Test Health Check (2 minutes)

Replace `src/App.tsx`:

```typescript
import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'

function App() {
  const [health, setHealth] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const checkHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/health')
      if (!response.ok) throw new Error('Backend not responding')
      const data = await response.json()
      setHealth(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to backend')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkHealth()
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-3xl font-bold">Bytelense</CardTitle>
          <p className="text-muted-foreground">Frontend Health Check</p>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {loading && (
            <Alert>
              <AlertDescription>Connecting to backend...</AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>
                ❌ {error}
                <br />
                <span className="text-sm">
                  Make sure backend is running on http://localhost:8000
                </span>
              </AlertDescription>
            </Alert>
          )}

          {health && (
            <div className="space-y-4">
              <Alert>
                <AlertDescription className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-green-50">
                    ✅ Connected
                  </Badge>
                  Backend is running
                </AlertDescription>
              </Alert>

              {health.services && (
                <div className="space-y-2">
                  <h3 className="font-semibold">Services:</h3>
                  {Object.entries(health.services).map(([name, service]: [string, any]) => (
                    <div key={name} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="capitalize">{name}</span>
                      <Badge variant={service.status === 'connected' || service.status === 'ok' ? 'default' : 'destructive'}>
                        {service.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}

              <details className="text-xs">
                <summary className="cursor-pointer text-muted-foreground">
                  View raw response
                </summary>
                <pre className="mt-2 p-2 bg-gray-50 rounded overflow-auto">
                  {JSON.stringify(health, null, 2)}
                </pre>
              </details>
            </div>
          )}

          <Button onClick={checkHealth} className="w-full" disabled={loading}>
            {loading ? 'Checking...' : 'Refresh Health Check'}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

export default App
```

---

## Step 7: Run Dev Server (1 minute)

```bash
pnpm run dev
```

Open <http://localhost:5173>

**Expected Result**:

- You should see "✅ Connected" if backend is running
- You should see service statuses (ollama, searxng, etc.)
- If you see "❌ Failed to connect", check backend is running

---

## Step 8: Create Project Structure (5 minutes)

```bash
cd src

# Create directories
mkdir -p types/{assessment,profile,websocket,components}
mkdir -p components/{ui,auth,scan,verdict,layout,screens}
mkdir -p lib hooks context config

# Create initial files
cat > types/index.ts << 'EOF'
export * from './assessment';
export * from './profile';
export * from './websocket';
EOF

cat > lib/utils.ts << 'EOF'
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
EOF

cat > config/constants.ts << 'EOF'
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
export const WS_SCAN_NAMESPACE = '/scan';
EOF

echo "Project structure created!"
```

---

## Checkpoint: You Should Have

- [x] Dev server running on <http://localhost:5173>
- [x] Health check showing backend connection
- [x] No TypeScript errors
- [x] All dependencies installed
- [x] Project structure created

---

## Next Steps

Now you're ready to implement:

1. **Camera capture** (see `FRONTEND_ARCHITECTURE_PLAN.md` Section 8)
2. **WebSocket integration** (Section 7)
3. **Verdict components** (Section 4)

Refer to the main architecture document for detailed implementation.

---

## Troubleshooting

### "Cannot find module '@/components/ui/card'"

**Fix**: Make sure you ran `pnpm dlx shadcn@latest add card`

### "Failed to connect to backend"

**Fix**:

1. Check backend is running: `curl http://localhost:8000/health`
2. If not, start backend: `uvicorn app.main:app --reload`

### "Module not found: Error: Can't resolve 'path'"

**Fix**: Install path module: `pnpm add -D @types/node`

And update `vite.config.ts`:

```typescript
import path from "path"
// ... rest of config
```

### TypeScript errors about paths

**Fix**: Update `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Then restart TypeScript server in VS Code: `Ctrl+Shift+P` → "TypeScript: Restart TS Server"

---

## Health Check Validation

Your health check should show:

```json
{
  "status": "ok",
  "services": {
    "ollama": {
      "status": "connected",
      "model": "qwen3:30b"
    },
    "searxng": {
      "status": "connected"
    },
    "openfoodfacts": {
      "status": "connected"
    },
    "storage": {
      "status": "ok"
    }
  }
}
```

If any service shows "error", check:

- **ollama**: `ollama list` should show model
- **searxng**: <http://localhost:8888> should be accessible
- **openfoodfacts**: Internet connection required

---

## Success

If you see the health check page with backend connected, you're ready to continue with component implementation.

**Time taken**: ~30 minutes
**Next**: Read `FRONTEND_ARCHITECTURE_PLAN.md` for full implementation details
