# Qwen-Coder Startup Prompt

Copy this entire message and paste it to qwen-coder CLI:

---

## Task: Build Bytelense Frontend

**Backend Status**: ✅ Running at http://localhost:8000

You will build the frontend for Bytelense, a food scanning app with generative UI. The backend is ready and provides:
- WebSocket endpoint for real-time scanning
- REST API for authentication and profiles
- Mock DetailedAssessment responses (perfect for UI development)

## Your Instructions

Follow **@QWEN_FRONTEND_PROMPT.md** exactly. This file contains step-by-step instructions for 6 phases.

## CRITICAL RULES (READ CAREFULLY)

1. **ONE FILE AT A TIME** - Implement exactly ONE file, then STOP
2. **WAIT FOR HUMAN** - After each file, wait for approval before proceeding
3. **NO SHORTCUTS** - Do not try to speed up by doing multiple files
4. **TYPE SAFETY** - All code must be TypeScript with strict types
5. **ERROR HANDLING** - Every async operation needs try/catch with user-friendly messages

## Backend Connection Details

### WebSocket (Socket.IO)
- **URL**: `http://localhost:8000`
- **Event to emit**: `start_scan`
- **Payload**:
  ```typescript
  {
    user_name: string;
    image_base64: string;  // Base64-encoded image from camera
    source: "camera" | "upload";
  }
  ```

### Events to listen for:
- `connected` - Connection established
- `scan_progress` - Progress updates (5 stages)
- `scan_complete` - Final assessment ready
- `scan_error` - Error occurred

### REST API
- `GET /health` - Health check
- `POST /api/auth/login` - Check if user exists
- `POST /api/auth/onboard` - Create new user profile

## Expected Data Structure (from backend)

When scan completes, you receive `DetailedAssessment`:

```typescript
interface DetailedAssessment {
  scan_id: string;
  timestamp: string;
  product_name: string;
  final_score: number;  // 0-10
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  verdict_emoji: string;  // 🟢 🟡 🔴 etc.
  base_score: number;
  context_adjustment: string;
  time_multiplier: number;
  highlights: string[];  // Good things
  warnings: string[];    // Bad things
  allergen_alerts: string[];
  moderation_message: string;
  timing_recommendation: string;
  reasoning_steps: string[];
  sources: CitationSource[];
  alternative_products: string[];
  nutrition_snapshot: {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g: number;
    sodium_mg: number;
    sugar_g: number;
    serving_size_g: number;
  };
}

interface CitationSource {
  url: string;
  title: string;
  snippet: string;
  source_type: "database" | "guidelines" | "research";
}
```

## Start Here

Begin with **PHASE 1: PROJECT INITIALIZATION** in @QWEN_FRONTEND_PROMPT.md

### First Task (Task 1.1)

Check if Vite is already initialized:
```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/frontend
ls -la
```

If you see `package.json` and `src/` directory, Vite is already initialized. **SKIP Task 1.1** and go to Task 1.2.

If NOT initialized, run:
```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense
mkdir -p frontend
cd frontend
pnpm create vite . --template react-ts
pnpm install
```

Then **STOP and wait for human verification**.

## Quality Checklist (for EVERY file you write)

Before marking a file as "complete", verify:
- [ ] TypeScript strict mode compliant (no `any` types)
- [ ] All imports have correct paths
- [ ] Error handling with try/catch for async operations
- [ ] User-friendly error messages (not technical jargon)
- [ ] Code is formatted and readable
- [ ] No console.log (use proper error handling)

## Remember

- The user (human) has ZERO JavaScript/TypeScript debugging skills
- If something breaks, they cannot fix it
- Your code MUST work perfectly the first time
- When in doubt, ASK before proceeding

## Questions to Ask Human (if needed)

- "The frontend directory already has files. Should I overwrite or skip initialization?"
- "I encountered an error in package installation. Here's the error: [error]. How should I proceed?"
- "Should I use pnpm, npm, or yarn for package management?"

---

**Now begin with Task 1.1 or 1.2 (depending on initialization status).**

**After completing the task, STOP and report back.**
