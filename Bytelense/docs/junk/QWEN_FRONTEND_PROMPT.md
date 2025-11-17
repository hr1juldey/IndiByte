# Frontend Implementation Instructions for Qwen-Coder CLI

**READ THIS FIRST**: You will implement the Bytelense frontend one file at a time. After each file, STOP and wait for human verification before proceeding. Do NOT try to do multiple files at once.

## Your Available Resources

- **Documentation**: @Bytelense/docs/UI/FRONTEND_ARCHITECTURE_PLAN.md (full spec)
- **Quick Start**: @Bytelense/docs/UI/QUICK_START.md (setup steps)
- **LLD Reference**: @Bytelense/docs/LLD.md (data models, API contracts)
- **Tools**: tavily search (for looking up package docs), context7 MCP

## Critical Rules

1. **ONE FILE AT A TIME** - Implement exactly one file, then STOP
2. **HUMAN VERIFICATION** - Wait for approval before next file
3. **TYPE SAFETY** - All code must be TypeScript with strict types
4. **ERROR HANDLING** - Every async operation needs try/catch
5. **FOLLOW THE PLAN** - Reference @Bytelense/docs/UI/FRONTEND_ARCHITECTURE_PLAN.md Section 11 for exact specs

---

## PHASE 1: PROJECT INITIALIZATION (DO THIS FIRST)

### Task 1.1: Initialize Vite Project

**Location**: `/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/frontend/`

**Commands to run**:
```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense
mkdir -p frontend
cd frontend
pnpm create vite . --template react-ts
pnpm install
```

**After installation, create this file**:

**File**: `@frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**STOP HERE** - Wait for human to verify Vite is running with `pnpm run dev`

---

### Task 1.2: Install Dependencies

**Commands**:
```bash
cd frontend
pnpm add socket.io-client
pnpm add -D tailwindcss postcss autoprefixer
pnpm add -D @types/node
npx tailwindcss init -p
```

**File**: `@frontend/tailwind.config.js`

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
      },
    },
  },
  plugins: [],
}
```

**File**: `@frontend/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: 0 0% 100%;
  --foreground: 0 0% 3.9%;
  --border: 0 0% 89.8%;
}

.dark {
  --background: 0 0% 3.9%;
  --foreground: 0 0% 98%;
  --border: 0 0% 14.9%;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}
```

**STOP HERE** - Wait for human to verify Tailwind is working

---

## PHASE 2: TYPE DEFINITIONS (ONE FILE)

### Task 2.1: Create Type Definitions

**File**: `@frontend/src/types/index.ts`

**Instructions**:
1. Read @Bytelense/docs/LLD.md Section 2 (Data Models)
2. Read @Bytelense/docs/LLD.md Section 10.2 (WebSocket Events)
3. Create TypeScript interfaces matching EXACTLY the Pydantic models

**Required Interfaces** (copy structure from LLD):
- `UserProfile` (demographics, lifestyle, health_metrics, goals, food_preferences)
- `DetailedAssessment` (scan_id, product_name, final_score, verdict, etc.)
- `ShortAssessment` (condensed version)
- `CitationSource` (citation_number, title, url, authority_score)
- `ScanProgressEvent` (scan_id, stage, stage_number, message, progress)
- `OnboardingQuestionEvent` (question_number, category, question, response_type, choices, can_skip)

**Template to follow**:
```typescript
// From LLD Section 2.2.1
export interface UserProfile {
  name: string;
  demographics: {
    age: number;
    gender: "male" | "female" | "other";
    height_cm: number;
    weight_kg: number;
  };
  lifestyle_habits: {
    sleep_hours: number;
    work_style: "desk_job" | "light_activity" | "physical_job";
    exercise_frequency: "rarely" | "1-2_times_week" | "3-4_times_week" | "5_times_week" | "daily";
    commute_type: "car" | "public_transport" | "bike" | "walk";
    smoking: "yes" | "no" | "occasionally";
    alcohol: "none" | "light" | "moderate" | "heavy";
    stress_level: "low" | "moderate" | "high";
  };
  health_metrics: {
    bmi: number;
    bmi_category: "underweight" | "normal" | "overweight" | "obese";
    bmr: number;
    tdee: number;
    daily_energy_target: number;
    health_risks: string[];
  };
  goals: {
    primary_goal: "lose_weight" | "maintain_weight" | "gain_muscle";
    target_weight_kg: number | null;
    timeline_weeks: number | null;
  };
  food_preferences: {
    cuisine_preferences: string[];
    dietary_restrictions: string[];
    allergens: string[];
    disliked_ingredients: string[];
  };
  daily_targets: {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g: number;
    sugar_g: number;
    sodium_mg: number;
  };
  created_at: string;
  last_updated: string;
}

// Continue with other interfaces...
```

**Quality Checks**:
- [ ] All fields match LLD Section 2 exactly
- [ ] All string unions match backend Literal types
- [ ] No `any` types used
- [ ] Optional fields marked with `?`
- [ ] Export all interfaces

**STOP HERE** - Wait for human to verify types are correct

---

## PHASE 3: API CLIENT (ONE FILE)

### Task 3.1: Create API Client

**File**: `@frontend/src/lib/api.ts`

**Instructions**:
1. Read @Bytelense/docs/LLD.md Section 10.1 (REST API Endpoints)
2. Create typed fetch wrappers for each endpoint
3. Include error handling for every request

**Template**:
```typescript
import type { UserProfile } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`API request failed: ${error.message}`);
      }
      throw error;
    }
  }

  // Health check
  async checkHealth() {
    return this.request<{
      status: string;
      services: Record<string, { status: string }>;
    }>('/health');
  }

  // Profile endpoints
  profile = {
    get: async (name: string) => {
      return this.request<{ profile: UserProfile }>(`/api/profile/${name}`);
    },

    update: async (name: string, updates: Partial<UserProfile>) => {
      return this.request<{ profile: UserProfile }>(`/api/profile/${name}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
    },
  };

  // Auth endpoints
  auth = {
    login: async (name: string) => {
      return this.request<{
        status: string;
        user_exists: boolean;
        profile?: UserProfile;
      }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ name }),
      });
    },
  };
}

export const api = new APIClient();
```

**Quality Checks**:
- [ ] All endpoints from LLD Section 10.1 implemented
- [ ] Return types match LLD exactly
- [ ] Error handling on every request
- [ ] TypeScript strict mode passes
- [ ] Environment variable for API_BASE_URL

**STOP HERE** - Wait for human to test health check endpoint

---

## PHASE 4: WEBSOCKET CLIENT (ONE FILE)

### Task 4.1: Create WebSocket Manager

**File**: `@frontend/src/lib/socket.ts`

**Instructions**:
1. Read @Bytelense/docs/LLD.md Section 10.2 (WebSocket Events)
2. Create Socket.IO client with typed event handlers
3. Include reconnection logic and error handling

**Template**:
```typescript
import { io, Socket } from 'socket.io-client';
import type {
  ScanProgressEvent,
  DetailedAssessment,
  OnboardingQuestionEvent
} from '../types';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000';

class SocketManager {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect() {
    if (this.socket?.connected) {
      console.log('Socket already connected');
      return;
    }

    this.socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.socket.on('connect', () => {
      console.log('✓ Connected to server');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.warn('✗ Disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      this.reconnectAttempts++;
      console.error('Connection error:', error.message);

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        throw new Error('Cannot connect to server. Please check backend is running.');
      }
    });
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  // Scan events
  onScanStarted(callback: (data: { scan_id: string }) => void) {
    this.socket?.on('scan_started', callback);
  }

  onScanProgress(callback: (data: ScanProgressEvent) => void) {
    this.socket?.on('scan_progress', callback);
  }

  onScanComplete(callback: (data: { detailed_assessment: DetailedAssessment }) => void) {
    this.socket?.on('scan_complete', callback);
  }

  onScanError(callback: (data: { error: string; message: string }) => void) {
    this.socket?.on('scan_error', callback);
  }

  // Emit scan request
  startScan(userName: string, imageBase64: string) {
    if (!this.socket?.connected) {
      throw new Error('Not connected to server');
    }

    this.socket.emit('start_scan', {
      user_name: userName,
      image_base64: imageBase64,
      source: 'camera',
    });
  }

  // Onboarding events
  onOnboardingQuestion(callback: (data: OnboardingQuestionEvent) => void) {
    this.socket?.on('onboarding_question', callback);
  }

  startOnboarding(userName: string) {
    this.socket?.emit('start_onboarding', { user_name: userName });
  }

  sendOnboardingResponse(questionNumber: number, response: string) {
    this.socket?.emit('onboarding_response', {
      question_number: questionNumber,
      response,
    });
  }
}

export const socketManager = new SocketManager();
```

**Quality Checks**:
- [ ] All events from LLD Section 10.2 implemented
- [ ] Reconnection logic works
- [ ] Error handling for disconnection
- [ ] TypeScript types for all callbacks
- [ ] Singleton pattern (one instance)

**STOP HERE** - Wait for human to test WebSocket connection

---

## PHASE 5: BASE COMPONENTS (ONE AT A TIME)

### Task 5.1: Error Boundary Component

**File**: `@frontend/src/components/ErrorBoundary.tsx`

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md p-8 bg-white rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold text-red-600 mb-4">
                Something went wrong
              </h2>
              <p className="text-gray-700 mb-4">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Reload Page
              </button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
```

**STOP HERE** - Wait for human verification

---

### Task 5.2: Loading Component

**File**: `@frontend/src/components/Loading.tsx`

```typescript
export function Loading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
        <p className="mt-4 text-gray-600">{message}</p>
      </div>
    </div>
  );
}
```

**STOP HERE** - Wait for human verification

---

## PHASE 6: CAMERA CAPTURE (CRITICAL - TEST THOROUGHLY)

### Task 6.1: Camera Hook

**File**: `@frontend/src/hooks/useCamera.ts`

**Instructions**:
1. Use MediaDevices API for camera access
2. Handle permissions properly
3. Return base64 encoded image

```typescript
import { useState, useRef, useCallback } from 'react';

export function useCamera() {
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }, // Back camera on mobile
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsActive(true);
        setError(null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Camera access denied';
      setError(message);
      console.error('Camera error:', err);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  }, []);

  const captureImage = useCallback((): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (!videoRef.current) {
        reject(new Error('Video not ready'));
        return;
      }

      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas not supported'));
        return;
      }

      ctx.drawImage(videoRef.current, 0, 0);
      const base64 = canvas.toDataURL('image/jpeg', 0.8);
      resolve(base64);
    });
  }, []);

  return {
    videoRef,
    isActive,
    error,
    startCamera,
    stopCamera,
    captureImage,
  };
}
```

**STOP HERE** - Human MUST test camera on their machine before proceeding

---

## IMPORTANT: STOPPING POINT

**After Phase 6, STOP and report to human**:

1. What has been implemented
2. What tests passed
3. What tests failed (if any)
4. What should be done next

**DO NOT continue to Phase 7+ without explicit human approval**

The remaining phases are:
- Phase 7: Profile Context (src/context/ProfileContext.tsx)
- Phase 8: Scan Flow Components (ScanScreen.tsx, VerdictScreen.tsx)
- Phase 9: Verdict Components (8 components from LLD Section 9)
- Phase 10: Integration Testing

---

## Quality Standards (Check Every File)

- [ ] TypeScript strict mode passes (`pnpm run build` with zero errors)
- [ ] No `any` types used
- [ ] All async functions have try/catch
- [ ] All components have prop types defined
- [ ] Error messages are human-readable
- [ ] Code follows React best practices
- [ ] Comments explain WHY, not WHAT

## When You Get Stuck

1. Read the relevant section in @Bytelense/docs/UI/FRONTEND_ARCHITECTURE_PLAN.md
2. Search for examples using tavily (e.g., "socket.io-client TypeScript example")
3. Check @Bytelense/docs/LLD.md for data structure reference
4. Ask human for clarification (DO NOT guess)

## Success Criteria

- Code compiles without TypeScript errors
- Component renders without console errors
- Functionality works as specified
- Human can verify the feature works

---

**Remember**: ONE FILE AT A TIME. STOP after each task. Wait for human verification.
