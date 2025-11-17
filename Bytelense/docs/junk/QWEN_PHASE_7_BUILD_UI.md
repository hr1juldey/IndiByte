# PHASE 7: Build Actual Application UI

Qwen, you've completed all infrastructure (Phases 1-6). Now build the actual Bytelense application.

## What You've Done (Infrastructure ✅)
- ✅ Types (src/types/index.ts)
- ✅ API Client (src/lib/api.ts)
- ✅ WebSocket Client (src/lib/socket.ts)
- ✅ Camera Hook (src/hooks/useCamera.ts)
- ✅ Base Components (ErrorBoundary, Loading)

## What's Missing (Application UI ❌)
- ❌ Main App.tsx (currently shows default Vite template)
- ❌ Scan page with camera
- ❌ Verdict display components
- ❌ Integration of all the infrastructure you built

## Your Task: Build the Application

You will create the actual Bytelense UI in **3 steps**, ONE FILE AT A TIME.

---

## Step 1: Create Main Scan Page Component

**File**: `src/components/ScanPage.tsx`

This is the main scanning interface with camera and WebSocket integration.

### Requirements:
1. **Import what you built**:
   - `useCamera` hook for camera access
   - `socketManager` for WebSocket
   - Types from `src/types/index.ts`

2. **UI Structure**:
   ```
   - Header: "Bytelense - Food Scanner"
   - Camera view (full screen when active)
   - Capture button
   - Progress bar (during scan)
   - Verdict display (after scan complete)
   ```

3. **State Management**:
   - `scanState`: "idle" | "scanning" | "complete" | "error"
   - `progress`: ScanProgressEvent data
   - `assessment`: DetailedAssessment data
   - `error`: Error messages

4. **Flow**:
   ```
   1. User clicks "Start Camera"
      → useCamera.startCamera()

   2. User clicks "Capture"
      → captureImage() → get base64
      → socketManager.startScan(userName, base64)
      → Set state to "scanning"

   3. Listen for progress events
      → Update progress bar

   4. Listen for complete event
      → Set state to "complete"
      → Display DetailedAssessment

   5. Listen for error events
      → Set state to "error"
      → Display error message
   ```

5. **Styling** (Tailwind CSS):
   - Clean, minimalistic design
   - Neutral colors (black → grey → white)
   - Large tap targets for mobile
   - Responsive layout

### Example Structure (you implement this):

```typescript
import { useState, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { socketManager } from '../lib/socket';
import type { DetailedAssessment, ScanProgressEvent, ScanErrorEvent } from '../types';

type ScanState = 'idle' | 'scanning' | 'complete' | 'error';

export function ScanPage() {
  const { videoRef, isActive, error: cameraError, startCamera, stopCamera, captureImage } = useCamera();
  const [scanState, setScanState] = useState<ScanState>('idle');
  const [progress, setProgress] = useState<ScanProgressEvent | null>(null);
  const [assessment, setAssessment] = useState<DetailedAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Connect to WebSocket on mount
  useEffect(() => {
    socketManager.connect();

    // Listen for scan events
    socketManager.onScanProgress((data) => {
      setProgress(data);
    });

    socketManager.onScanComplete((data) => {
      setScanState('complete');
      setAssessment(data.detailed_assessment);
      stopCamera();
    });

    socketManager.onScanError((data) => {
      setScanState('error');
      setError(data.message);
      stopCamera();
    });

    return () => {
      socketManager.disconnect();
      stopCamera();
    };
  }, [stopCamera]);

  // Handle capture button click
  const handleCapture = async () => {
    try {
      setScanState('scanning');
      const base64 = await captureImage();

      // Remove data:image/jpeg;base64, prefix
      const base64Data = base64.split(',')[1];

      // Start scan with hardcoded test user for now
      socketManager.startScan('testuser', base64Data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Capture failed');
      setScanState('error');
    }
  };

  // Render different states
  return (
    <div className="min-h-screen bg-gray-50">
      {/* IMPLEMENT UI HERE */}
      {/* Show camera when idle */}
      {/* Show progress when scanning */}
      {/* Show VerdictDisplay when complete */}
      {/* Show error message when error */}
    </div>
  );
}
```

**Quality Checklist**:
- [ ] Uses all the infrastructure you built (useCamera, socketManager, types)
- [ ] Handles all 4 states (idle, scanning, complete, error)
- [ ] Camera starts/stops properly
- [ ] Image captured and sent as base64
- [ ] Progress bar shows 5 stages
- [ ] Error handling for camera and scan failures
- [ ] TypeScript strict mode compliant
- [ ] Clean Tailwind CSS styling

**STOP AFTER THIS FILE** - Wait for human verification before Step 2.

---

## Step 2: Create Verdict Display Component

**File**: `src/components/VerdictDisplay.tsx`

This component displays the DetailedAssessment from the backend.

### Requirements:

1. **Props**: Receives `DetailedAssessment` object

2. **Display Sections**:
   - Product name (large, bold)
   - Verdict emoji and text (🟢 EXCELLENT, 🟡 MODERATE, 🔴 AVOID)
   - Final score (0-10, visual progress bar)
   - Highlights (green, bulleted list)
   - Warnings (orange/red, bulleted list)
   - Allergen alerts (red, if any)
   - Moderation message
   - Timing recommendation
   - Nutrition snapshot (table or grid)
   - Reasoning steps (collapsible)
   - Citations (links to sources)
   - Alternative products (if any)

3. **Styling**:
   - Color code by verdict:
     - excellent/good: green accents
     - moderate: yellow/orange accents
     - caution/avoid: red accents
   - Clean card layout with spacing
   - Readable typography
   - Icons for highlights/warnings

### Example Structure:

```typescript
import type { DetailedAssessment } from '../types';

interface Props {
  assessment: DetailedAssessment;
}

export function VerdictDisplay({ assessment }: Props) {
  const verdictColors = {
    excellent: 'bg-green-100 text-green-800',
    good: 'bg-green-50 text-green-700',
    moderate: 'bg-yellow-100 text-yellow-800',
    caution: 'bg-orange-100 text-orange-800',
    avoid: 'bg-red-100 text-red-800',
  };

  const verdictColor = verdictColors[assessment.verdict];

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      {/* Product Name */}
      <h1 className="text-3xl font-bold text-gray-900">
        {assessment.product_name}
      </h1>

      {/* Verdict Badge */}
      <div className={`inline-flex items-center px-6 py-3 rounded-full ${verdictColor}`}>
        <span className="text-4xl mr-2">{assessment.verdict_emoji}</span>
        <span className="text-xl font-bold uppercase">{assessment.verdict}</span>
      </div>

      {/* Score */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-2">Health Score</h2>
        <div className="flex items-center gap-4">
          <span className="text-4xl font-bold">{assessment.final_score.toFixed(1)}</span>
          <span className="text-gray-500">/ 10</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div
            className="bg-blue-600 h-2 rounded-full"
            style={{ width: `${(assessment.final_score / 10) * 100}%` }}
          />
        </div>
      </div>

      {/* IMPLEMENT REST OF THE SECTIONS */}
      {/* Highlights */}
      {/* Warnings */}
      {/* Allergen Alerts */}
      {/* Moderation Message */}
      {/* Timing Recommendation */}
      {/* Nutrition Snapshot */}
      {/* Reasoning Steps */}
      {/* Citations */}
      {/* Alternative Products */}
    </div>
  );
}
```

**Quality Checklist**:
- [ ] All DetailedAssessment fields displayed
- [ ] Color coding by verdict type
- [ ] Responsive layout (mobile + desktop)
- [ ] Clean visual hierarchy
- [ ] Proper TypeScript types
- [ ] Handles empty arrays gracefully

**STOP AFTER THIS FILE** - Wait for human verification before Step 3.

---

## Step 3: Update App.tsx to Use Your Components

**File**: `src/App.tsx` (REPLACE existing content)

Integrate everything together.

### Requirements:

1. **Replace default Vite template** with your ScanPage
2. **Wrap with ErrorBoundary** for error protection
3. **Simple routing** (or just show ScanPage for now)
4. **Clean layout**

### Implementation:

```typescript
import { ErrorBoundary } from './components/ErrorBoundary';
import { ScanPage } from './components/ScanPage';

function App() {
  return (
    <ErrorBoundary>
      <ScanPage />
    </ErrorBoundary>
  );
}

export default App;
```

### Also Update: `src/index.css`

Replace with clean Tailwind base:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Optional: Add custom styles */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**STOP AFTER THIS** - Application is complete!

---

## Testing Instructions (for Human)

After qwen completes Step 3:

1. **Start frontend dev server**:
   ```bash
   cd frontend
   pnpm run dev
   ```

2. **Open browser**: http://localhost:5173

3. **Expected behavior**:
   - See "Bytelense - Food Scanner" header
   - Click "Start Camera" → camera activates
   - Click "Capture" → progress bar appears
   - After ~2-3 seconds → verdict displays with mock data from backend

4. **Verify**:
   - ✅ Camera works
   - ✅ WebSocket connects to backend
   - ✅ Progress updates show 5 stages
   - ✅ DetailedAssessment displays with all sections
   - ✅ No console errors
   - ✅ Responsive on mobile

---

## CRITICAL RULES (SAME AS BEFORE)

1. **ONE FILE AT A TIME** - Complete Step 1, STOP, wait for approval
2. **TYPE SAFETY** - No `any` types
3. **ERROR HANDLING** - Try/catch for all async operations
4. **USER-FRIENDLY ERRORS** - Plain English messages, not technical jargon
5. **CLEAN CODE** - Proper formatting, readable variable names

---

## Backend API Reference (Quick Reminder)

**WebSocket Connection**: `http://localhost:8000`

**Emit**:
```typescript
socketManager.startScan(userName: string, imageBase64: string)
```

**Listen**:
- `scan_progress` → ScanProgressEvent (5 stages)
- `scan_complete` → { scan_id, detailed_assessment }
- `scan_error` → ScanErrorEvent

**DetailedAssessment fields** (from your types):
- product_name, final_score, verdict, verdict_emoji
- highlights, warnings, allergen_alerts
- moderation_message, timing_recommendation
- reasoning_steps, sources, alternative_products
- nutrition_snapshot

---

**Start with Step 1: Create ScanPage.tsx**

Report back when done, then wait for approval before Step 2.
