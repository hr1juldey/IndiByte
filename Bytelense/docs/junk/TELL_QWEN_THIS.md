# Message to Send to Qwen-Coder

Copy this **ENTIRE MESSAGE** and paste it to qwen-coder CLI:

---

## Task: Continue Building Bytelense Frontend

**Backend Status**: ✅ Running at http://localhost:8000
**Frontend Status**: ✅ Vite + React + TypeScript initialized, Tailwind configured, socket.io-client installed

## What You've Done So Far
Phase 1 (Project Initialization) is **COMPLETE**. The frontend has:
- ✅ Vite + React 19 + TypeScript
- ✅ Tailwind CSS 4.1 configured
- ✅ socket.io-client installed
- ✅ tsconfig.json setup
- ✅ All dependencies installed

## What You Need to Do Now

Continue with **PHASE 2: TYPE DEFINITIONS** from @QWEN_FRONTEND_PROMPT.md

### Your Next Task: Create Type Definitions

**File to create**: `@frontend/src/types/index.ts`

This file must define TypeScript interfaces matching the backend data structures.

### Backend Data Structures (Reference)

The backend sends this data when scan completes:

```typescript
// Main assessment response
interface DetailedAssessment {
  scan_id: string;
  timestamp: string;
  product_name: string;
  final_score: number;  // 0-10
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  verdict_emoji: string;
  base_score: number;
  context_adjustment: string;
  time_multiplier: number;
  highlights: string[];
  warnings: string[];
  allergen_alerts: string[];
  moderation_message: string;
  timing_recommendation: string;
  reasoning_steps: string[];
  sources: CitationSource[];
  alternative_products: string[];
  nutrition_snapshot: NutritionSnapshot;
}

interface CitationSource {
  url: string;
  title: string;
  snippet: string;
  source_type: "database" | "guidelines" | "research";
}

interface NutritionSnapshot {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sodium_mg: number;
  sugar_g: number;
  serving_size_g: number;
}

// WebSocket event types
interface ScanProgressEvent {
  scan_id: string;
  stage: "image_processing" | "nutrition_retrieval" | "profile_loading" | "scoring" | "assessment_generation";
  stage_number: number;  // 1-5
  total_stages: number;  // Always 5
  message: string;
  progress: number;  // 0-1
}

interface ScanErrorEvent {
  scan_id: string;
  error: string;
  message: string;
  stage: string;
  retry_suggestions: string[];
  recoverable: boolean;
}

interface ScanCompleteEvent {
  scan_id: string;
  detailed_assessment: DetailedAssessment;
}
```

### Backend WebSocket Connection

**URL**: `http://localhost:8000`

**Events to emit**:
- `start_scan` with payload:
  ```typescript
  {
    user_name: string;
    image_base64: string;  // Base64-encoded image
    source: "camera" | "upload";
  }
  ```

**Events to listen for**:
- `connected` - Connection established
- `scan_progress` - Progress update (ScanProgressEvent)
- `scan_complete` - Scan finished (ScanCompleteEvent)
- `scan_error` - Error occurred (ScanErrorEvent)

## CRITICAL RULES (MUST FOLLOW)

1. **ONE FILE AT A TIME** - Create `types/index.ts`, then STOP
2. **WAIT FOR HUMAN** - After creating the file, wait for approval
3. **TYPE SAFETY** - No `any` types, all interfaces must be fully typed
4. **MATCH BACKEND** - Types must exactly match the backend responses shown above
5. **EXPORT ALL** - Every interface must be exported

## Your Task RIGHT NOW

Create the file: `@frontend/src/types/index.ts`

Include these interfaces:
- `DetailedAssessment`
- `CitationSource`
- `NutritionSnapshot`
- `ScanProgressEvent`
- `ScanErrorEvent`
- `ScanCompleteEvent`
- `ScanRequest` (for start_scan payload)
- `VerdictType` (type alias for verdict values)

### Quality Checklist

Before submitting, verify:
- [ ] All interfaces exported
- [ ] No `any` types used
- [ ] Literal types used for enums (e.g., `"excellent" | "good"`)
- [ ] All fields have correct types (string, number, array, etc.)
- [ ] File location is `src/types/index.ts`
- [ ] No syntax errors

## After Completion

Report back with:
1. "✅ Created src/types/index.ts"
2. Show the file content
3. Wait for human verification before proceeding to next task

---

**Start now. Create `src/types/index.ts` with all required interfaces.**
