# Bytelense Frontend Architecture Plan
## Bulletproof Design for Zero JavaScript Debugging Skills

**Version:** 1.0  
**Created:** 2025-11-14  
**Target:** Developer with ZERO JS/TS debugging ability  
**Status:** Implementation Ready

---

## Executive Summary

**CRITICAL CONSTRAINT**: The user has ZERO JavaScript/TypeScript debugging skills. If it breaks, they cannot fix it. Therefore, this architecture prioritizes:

1. **Server-Side Control**: Backend dictates what to show; frontend just renders
2. **Type Safety**: TypeScript everywhere to catch errors at compile time
3. **Error Boundaries**: Every component wrapped in fallback UI
4. **Clear Error Messages**: Non-technical messages that tell user exactly what to do
5. **Minimal Client Logic**: No complex state management; backend is source of truth

**RECOMMENDATION**: React + Vite with Server-Driven UI (NOT Next.js SSR)

**Why NOT Next.js App Router?**
- Added complexity (RSC, server actions, routing conventions)
- Harder to debug for non-JS developers
- WebSocket integration more complex
- Camera API requires client components anyway
- Server components don't help with real-time updates

**Why React + Vite?**
- Simpler mental model: one codebase, clear boundaries
- Excellent TypeScript support out of the box
- Fast dev server, instant HMR
- WebSocket integration straightforward
- Camera API well-supported
- **Server still controls UI via JSON schema pattern**

---

## Table of Contents

1. [Architecture Decision](#1-architecture-decision)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Component Architecture](#4-component-architecture)
5. [Dynamic Rendering System](#5-dynamic-rendering-system)
6. [State Management Strategy](#6-state-management-strategy)
7. [WebSocket Integration](#7-websocket-integration)
8. [Camera/Image Capture](#8-camera-image-capture)
9. [Error Handling System](#9-error-handling-system)
10. [Type Safety](#10-type-safety)
11. [Step-by-Step Setup](#11-step-by-step-setup)
12. [Testing Strategy](#12-testing-strategy)
13. [Non-Technical Debug Guide](#13-non-technical-debug-guide)
14. [Potential Pitfalls](#14-potential-pitfalls)

---

## 1. Architecture Decision

### 1.1 Server-Driven UI Pattern

**Core Concept**: Backend sends JSON describing WHAT to render; frontend maps to components.

```bash
Backend Decision Logic:
  verdict = "avoid" → generate DetailedAssessment with allergen_alerts
  
Frontend Rendering Logic:
  if (assessment.allergen_alerts.length > 0):
    show AllergenAlert component with data
```

**Key Insight**: This IS server-side rendering logic, just with client-side components as the target. Backend controls:
- Which components to show
- Order of components
- Component configuration
- Themes and layouts

### 1.2 Why React + Vite (Not Next.js)

| Criteria | React + Vite | Next.js App Router |
|----------|--------------|-------------------|
| **Learning Curve** | Low (just React) | High (RSC, server actions, routing) |
| **TypeScript Setup** | Automatic | Manual configuration |
| **WebSocket Support** | Native, simple | Requires workarounds |
| **Camera API** | Direct access | Must use client components anyway |
| **Dev Experience** | Fast HMR | Slower, more complex |
| **Debugging** | Clear stack traces | Mixed server/client traces |
| **Error Messages** | Client-side, clear | Mixed context, confusing |
| **Build Output** | Single SPA | Multiple entry points |
| **Deployment** | Static files | Requires Node server |

**Decision**: React + Vite with **server-driven component selection**

### 1.3 How Server Controls UI

Backend returns `DetailedAssessment` JSON with all data needed:

```typescript
interface DetailedAssessment {
  scan_id: string;
  product_name: string;
  final_score: number;
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  verdict_emoji: string;
  
  // Data that determines which components to show
  allergen_alerts: string[];        // If present → AllergenAlert
  warnings: string[];                // If present → WarningsList
  highlights: string[];              // If present → HighlightsList
  moderation_message: string;        // If present → ModerationBanner
  
  reasoning_steps: string[];         // Always → ReasoningSection (collapsible)
  sources: CitationSource[];         // Always → CitationList
  nutrition_snapshot: object;        // Always → NutritionCard
  
  alternative_products: string[];    // If present → AlternativesSection
  timing_recommendation: string;     // If present → TimingCard
  portion_suggestion: string;        // If present → PortionCard
}
```

Frontend logic (simple, declarative):

```typescript
function VerdictScreen({ assessment }: { assessment: DetailedAssessment }) {
  return (
    <div className="verdict-screen">
      {/* Always show */}
      <VerdictBadge score={assessment.final_score} verdict={assessment.verdict} />
      
      {/* Conditionally show based on data presence */}
      {assessment.allergen_alerts.length > 0 && (
        <AllergenAlert alerts={assessment.allergen_alerts} />
      )}
      
      {assessment.moderation_message && (
        <ModerationBanner message={assessment.moderation_message} />
      )}
      
      {/* Always show with conditional content */}
      <InsightSection 
        warnings={assessment.warnings} 
        highlights={assessment.highlights} 
      />
      
      {/* ... more components */}
    </div>
  );
}
```

**Key Point**: No complex client-side logic. Just show/hide based on data presence.

---

## 2. Technology Stack

### 2.1 Core Framework

| Technology | Version | Purpose | Why |
|-----------|---------|---------|-----|
| **React** | 18+ | UI library | Industry standard, mature ecosystem |
| **TypeScript** | 5+ | Type safety | Catch errors at compile time |
| **Vite** | 5+ | Build tool | Fast dev server, excellent TS support |
| **pnpm** | 9+ | Package manager | Faster, more efficient than npm |

### 2.2 Styling

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Tailwind CSS** | 3+ | Utility-first CSS |
| **shadcn/ui** | Latest | Pre-built components |
| **class-variance-authority** | Latest | Component variants |
| **tailwind-merge** | Latest | Merge Tailwind classes |

**Why shadcn/ui?**
- Copy-paste components (you own the code)
- Built on Radix UI (accessible, battle-tested)
- Tailwind-based (consistent styling)
- TypeScript by default
- Customizable without complexity

### 2.3 Real-Time Communication

| Technology | Version | Purpose |
|-----------|---------|---------|
| **socket.io-client** | 4+ | WebSocket client |

**Why socket.io-client?**
- Auto-reconnection built-in
- Fallback to polling if WebSocket fails
- Event-based API (simple to use)
- Backend already uses python-socketio

### 2.4 Camera/Media

| Technology | Purpose |
|-----------|---------|
| **MediaDevices API** | Camera access (native browser API) |
| **canvas API** | Image capture and compression |

### 2.5 State Management

**Decision**: NO external state management library

**Why?**
- WebSocket is source of truth for scan state
- Profile data fetched once, stored in Context
- No complex client state to manage
- React's built-in useState + useContext sufficient

### 2.6 HTTP Client

**Decision**: Native `fetch` API

**Why?**
- Built into browsers
- Async/await syntax
- No additional dependencies
- TypeScript support with typed responses

---

## 3. Project Structure

### 3.1 Directory Layout

```
docs/UI/
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Root component with routing
│   │
│   ├── types/                      # TypeScript type definitions
│   │   ├── index.ts                # Re-exports all types
│   │   ├── assessment.ts           # DetailedAssessment, ShortAssessment
│   │   ├── profile.ts              # UserProfile, DailyTargets
│   │   ├── websocket.ts            # WebSocket event types
│   │   └── components.ts           # Component prop types
│   │
│   ├── components/
│   │   ├── ui/                     # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── alert.tsx
│   │   │   └── ...
│   │   │
│   │   ├── auth/                   # Authentication components
│   │   │   ├── LoginForm.tsx
│   │   │   └── OnboardingWizard.tsx
│   │   │
│   │   ├── scan/                   # Scanning components
│   │   │   ├── CameraCapture.tsx   # Camera interface
│   │   │   ├── ImageUpload.tsx     # File upload
│   │   │   └── ScanProgress.tsx    # Progress indicator
│   │   │
│   │   ├── verdict/                # Verdict display components
│   │   │   ├── VerdictBadge.tsx    # Score + emoji badge
│   │   │   ├── AllergenAlert.tsx   # Critical allergen warnings
│   │   │   ├── ModerationBanner.tsx # "You've had 25g sugar today"
│   │   │   ├── InsightSection.tsx   # Highlights + warnings
│   │   │   ├── NutritionCard.tsx    # Macro breakdown
│   │   │   ├── ReasoningSection.tsx # Collapsible reasoning
│   │   │   ├── CitationList.tsx     # Perplexity-style references
│   │   │   └── RecommendationSection.tsx # Alternatives, timing
│   │   │
│   │   ├── layout/                 # Layout components
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── ErrorBoundary.tsx   # Global error handler
│   │   │
│   │   └── screens/                # Full-page screens
│   │       ├── LoginScreen.tsx
│   │       ├── OnboardingScreen.tsx
│   │       ├── ScanScreen.tsx
│   │       └── VerdictScreen.tsx
│   │
│   ├── lib/                        # Utility libraries
│   │   ├── api.ts                  # HTTP client functions
│   │   ├── websocket.ts            # WebSocket client wrapper
│   │   ├── camera.ts               # Camera utility functions
│   │   └── utils.ts                # General utilities (cn, formatters)
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useWebSocket.ts         # WebSocket connection hook
│   │   ├── useCamera.ts            # Camera access hook
│   │   ├── useProfile.ts           # Profile context hook
│   │   └── useToast.ts             # Toast notifications hook
│   │
│   ├── context/                    # React Context providers
│   │   └── ProfileContext.tsx      # User profile global state
│   │
│   ├── config/                     # Configuration
│   │   └── constants.ts            # API URLs, timeouts, etc.
│   │
│   └── styles/                     # Global styles
│       └── globals.css             # Tailwind imports + custom CSS
│
├── public/                         # Static assets
│   ├── favicon.ico
│   └── images/
│
├── index.html                      # HTML entry point
├── package.json                    # Dependencies
├── tsconfig.json                   # TypeScript config
├── vite.config.ts                  # Vite config
├── tailwind.config.js              # Tailwind config
├── components.json                 # shadcn/ui config
└── .env.example                    # Environment variables template
```

### 3.2 File Naming Conventions

- **Components**: PascalCase with `.tsx` extension (e.g., `VerdictBadge.tsx`)
- **Utilities**: camelCase with `.ts` extension (e.g., `websocket.ts`)
- **Types**: camelCase with `.ts` extension (e.g., `assessment.ts`)
- **Hooks**: camelCase starting with `use` (e.g., `useWebSocket.ts`)
- **Constants**: camelCase (e.g., `constants.ts`)

### 3.3 Import Organization

```typescript
// 1. External dependencies
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

// 2. Internal utilities/config
import { API_BASE_URL } from '@/config/constants';
import { cn } from '@/lib/utils';

// 3. Types
import type { DetailedAssessment } from '@/types';

// 4. Components
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// 5. Hooks
import { useProfile } from '@/hooks/useProfile';
```

---

## 4. Component Architecture

### 4.1 Component Classification

#### 4.1.1 Base Components (shadcn/ui)

**Purpose**: Reusable, unstyled, accessible primitives

**Examples**: Button, Card, Badge, Alert, Dialog, Accordion

**Characteristics**:
- No business logic
- Pure presentation
- Highly configurable via props
- Accessible by default (Radix UI)

#### 4.1.2 Domain Components

**Purpose**: Business-specific components that use base components

**Examples**: VerdictBadge, AllergenAlert, NutritionCard

**Characteristics**:
- Specific to Bytelense domain
- Use base components for structure
- Accept typed data props
- Minimal logic (just presentation)

#### 4.1.3 Screen Components

**Purpose**: Full-page layouts that compose domain components

**Examples**: VerdictScreen, ScanScreen

**Characteristics**:
- Orchestrate multiple domain components
- Handle screen-level state
- Implement error boundaries
- Responsive layouts

### 4.2 Component Design Principles

#### Principle 1: Props-Only Data Flow

```typescript
// GOOD: All data via props
function VerdictBadge({ score, verdict, emoji }: VerdictBadgeProps) {
  return <Badge>{emoji} {verdict.toUpperCase()} - {score}/10</Badge>;
}

// BAD: Fetching data inside component
function VerdictBadge() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchData().then(setData); }, []);
  // ... DON'T DO THIS
}
```

#### Principle 2: No Complex Logic

```typescript
// GOOD: Simple conditional rendering
function AllergenAlert({ alerts }: { alerts: string[] }) {
  if (alerts.length === 0) return null;
  
  return (
    <Alert variant="destructive">
      <AlertTitle>⚠️ Allergen Alert</AlertTitle>
      <AlertDescription>
        {alerts.map(alert => <div key={alert}>{alert}</div>)}
      </AlertDescription>
    </Alert>
  );
}

// BAD: Complex filtering/transformation
function AllergenAlert({ rawData }: { rawData: any }) {
  const alerts = rawData.ingredients
    .filter(i => ALLERGENS.includes(i))
    .map(i => transformAllergen(i))
    .filter(a => a.severity > 2);
  // ... TOO MUCH LOGIC
}
```

#### Principle 3: Error Boundaries Everywhere

```typescript
function SafeComponent({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      fallback={<div>Something went wrong. Please refresh the page.</div>}
    >
      {children}
    </ErrorBoundary>
  );
}
```

### 4.3 Skeleton Component Library

#### 4.3.1 VerdictBadge

**Purpose**: Display overall score and verdict

**Props**:
```typescript
interface VerdictBadgeProps {
  score: number;           // 0-10
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  emoji: string;           // 🟢 🟡 🔴
}
```

**Visual**:
```
┌─────────────────────────────┐
│   🟢 GOOD - 7.5/10          │
└─────────────────────────────┘
```

**Implementation Notes**:
- Color based on verdict (green/yellow/red)
- Large font, prominent position
- Animated entrance

#### 4.3.2 AllergenAlert

**Purpose**: Critical allergen warnings

**Props**:
```typescript
interface AllergenAlertProps {
  alerts: string[];        // e.g., ["Contains milk", "May contain nuts"]
}
```

**Visual**:
```
┌─────────────────────────────────────────┐
│ ⚠️ ALLERGEN ALERT                       │
│                                         │
│ • Contains milk                         │
│ • May contain nuts                      │
└─────────────────────────────────────────┘
```

**Implementation Notes**:
- Red background, white text
- Always at top of verdict screen
- Pulsing animation for attention

#### 4.3.3 ModerationBanner

**Purpose**: Show daily consumption vs targets

**Props**:
```typescript
interface ModerationBannerProps {
  message: string;         // "You've had 25g sugar today (83% of limit)"
  level: "within" | "approaching" | "exceeding";
}
```

**Visual**:
```
┌─────────────────────────────────────────┐
│ 📊 You've had 25g sugar today (83%)    │
│ [████████░░] Approaching limit          │
└─────────────────────────────────────────┘
```

**Implementation Notes**:
- Color based on level (green/yellow/red)
- Progress bar visual
- Context-aware messaging

#### 4.3.4 InsightSection

**Purpose**: Display highlights and warnings

**Props**:
```typescript
interface InsightSectionProps {
  highlights: string[];    // Positive points
  warnings: string[];      // Concerns
}
```

**Visual**:
```
┌─────────────────────────────────────────┐
│ ✅ Highlights                           │
│ • High in fiber                         │
│ • Good protein source                   │
│                                         │
│ ⚠️ Warnings                             │
│ • High sodium for your blood pressure   │
└─────────────────────────────────────────┘
```

**Implementation Notes**:
- Two columns on desktop, stacked on mobile
- Icons for visual distinction
- Highlights first, warnings second

#### 4.3.5 NutritionCard

**Purpose**: Display macro breakdown

**Props**:
```typescript
interface NutritionCardProps {
  nutrition: {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    sugar_g: number;
    sodium_mg: number;
    fiber_g?: number;
  };
  targets?: {
    calories: number;
    protein_g: number;
    // ...
  };
}
```

**Visual**:
```
┌─────────────────────────────────────────┐
│ 📊 Nutrition Facts                      │
│                                         │
│ Calories:  250 / 2000  [████░░░░░░]    │
│ Protein:    15g / 80g  [███░░░░░░░]    │
│ Carbs:      30g / 250g [██░░░░░░░░]    │
│ Sugar:      25g / 25g  [██████████] ⚠️ │
└─────────────────────────────────────────┘
```

**Implementation Notes**:
- Progress bars for visual comparison
- Warning icon if exceeds target
- Tooltip with detailed info on hover

#### 4.3.6 ReasoningSection

**Purpose**: Show AI reasoning (collapsible)

**Props**:
```typescript
interface ReasoningSectionProps {
  steps: string[];         // Step-by-step reasoning
  confidence: number;      // 0-1
}
```

**Visual**:
```
┌─────────────────────────────────────────┐
│ 🤔 How we calculated this (85% confidence)
│ [Expand ▼]                              │
│                                         │
│ 1. Base nutritional analysis...         │
│ 2. Compared against your profile...     │
│ 3. Considered your sugar intake today..│
└─────────────────────────────────────────┘
```

**Implementation Notes**:
- Collapsed by default
- Numbered steps
- Confidence score at top

#### 4.3.7 CitationList

**Purpose**: Perplexity-style reference list

**Props**:
```typescript
interface CitationListProps {
  sources: CitationSource[];
}

interface CitationSource {
  citation_number: number;  // [1], [2]
  title: string;
  url?: string;
  snippet?: string;
  source_type: string;
}
```

**Visual**:
```
┌─────────────────────────────────────────┐
│ 📚 Sources                              │
│                                         │
│ [1] OpenFoodFacts - Product Database    │
│     "Contains 30g sugar per serving..." │
│     🔗 https://openfoodfacts.org/...    │
│                                         │
│ [2] WHO - Sugar Guidelines              │
│     "Adults should limit sugar to 25g..."
│     🔗 https://who.int/...              │
└─────────────────────────────────────────┘
```

**Implementation Notes**:
- Clickable links open in new tab
- Snippet truncated with "Read more"
- Source type badge (WHO = high authority)

#### 4.3.8 RecommendationSection

**Purpose**: Show alternatives and recommendations

**Props**:
```typescript
interface RecommendationSectionProps {
  alternatives: string[];
  timing: string;
  portion: string;
}
```

**Visual**:
```
┌─────────────────────────────────────────┐
│ 💡 Recommendations                      │
│                                         │
│ 🕐 Timing: Better for morning           │
│ 🍽️ Portion: Limit to 1 serving (25g)   │
│                                         │
│ Healthier alternatives:                 │
│ • Product A (8.5/10)                    │
│ • Product B (8.0/10)                    │
└─────────────────────────────────────────┘
```

**Implementation Notes**:
- Icons for visual clarity
- Alternatives clickable (future: search for them)
- Conditional rendering (only show if available)

---

## 5. Dynamic Rendering System

### 5.1 Core Concept

**Backend sends**: Complete `DetailedAssessment` JSON  
**Frontend renders**: Components based on data presence

**No separate UI schema needed** - the assessment structure IS the schema.

### 5.2 VerdictScreen Implementation

```typescript
// src/components/screens/VerdictScreen.tsx

import type { DetailedAssessment } from '@/types';
import { VerdictBadge } from '@/components/verdict/VerdictBadge';
import { AllergenAlert } from '@/components/verdict/AllergenAlert';
import { ModerationBanner } from '@/components/verdict/ModerationBanner';
// ... other imports

interface VerdictScreenProps {
  assessment: DetailedAssessment;
  onNewScan: () => void;
}

export function VerdictScreen({ assessment, onNewScan }: VerdictScreenProps) {
  return (
    <div className="container mx-auto p-4 space-y-6">
      {/* Header with score */}
      <VerdictBadge
        score={assessment.final_score}
        verdict={assessment.verdict}
        emoji={assessment.verdict_emoji}
      />

      {/* Critical alerts first */}
      {assessment.allergen_alerts.length > 0 && (
        <AllergenAlert alerts={assessment.allergen_alerts} />
      )}

      {/* Moderation context */}
      {assessment.moderation_message && (
        <ModerationBanner
          message={assessment.moderation_message}
          level="approaching" // Could be derived from message parsing
        />
      )}

      {/* Insights (always show, even if empty) */}
      <InsightSection
        highlights={assessment.highlights}
        warnings={assessment.warnings}
      />

      {/* Nutrition breakdown */}
      <NutritionCard nutrition={assessment.nutrition_snapshot} />

      {/* AI reasoning (collapsible) */}
      <ReasoningSection
        steps={assessment.reasoning_steps}
        confidence={assessment.confidence}
      />

      {/* Citations */}
      {assessment.sources.length > 0 && (
        <CitationList sources={assessment.sources} />
      )}

      {/* Recommendations */}
      {(assessment.alternative_products.length > 0 ||
        assessment.timing_recommendation ||
        assessment.portion_suggestion) && (
        <RecommendationSection
          alternatives={assessment.alternative_products}
          timing={assessment.timing_recommendation}
          portion={assessment.portion_suggestion}
        />
      )}

      {/* Action button */}
      <button onClick={onNewScan} className="w-full btn-primary">
        Scan Another Product
      </button>
    </div>
  );
}
```

### 5.3 No Component Registry Needed

**Why?** Because:
1. Components are directly imported and used
2. Conditional rendering is simple (`&&` operator)
3. No dynamic component resolution required
4. TypeScript validates all props at compile time

**Comparison**:

```typescript
// COMPLEX: Component registry pattern (NOT NEEDED)
const registry = {
  'verdict_badge': VerdictBadge,
  'allergen_alert': AllergenAlert,
  // ...
};

schema.components.map(spec => {
  const Component = registry[spec.type];
  return <Component {...spec.props} />;
});

// SIMPLE: Direct imports (RECOMMENDED)
return (
  <>
    <VerdictBadge {...assessment} />
    {assessment.allergen_alerts.length > 0 && (
      <AllergenAlert alerts={assessment.allergen_alerts} />
    )}
  </>
);
```

**Decision**: Use direct imports. Simpler, type-safe, easier to debug.

---

## 6. State Management Strategy

### 6.1 State Classification

| State Type | Storage | Lifetime | Example |
|-----------|---------|----------|---------|
| **Authentication** | Context + localStorage | Session | User profile |
| **Scan State** | WebSocket events | Single scan | Progress, result |
| **UI State** | Component state | Component lifetime | Modal open/closed |
| **Form State** | Component state | Form lifetime | Onboarding inputs |

### 6.2 ProfileContext (Global State)

```typescript
// src/context/ProfileContext.tsx

import { createContext, useContext, useState, useEffect } from 'react';
import type { UserProfile } from '@/types';

interface ProfileContextValue {
  profile: UserProfile | null;
  setProfile: (profile: UserProfile) => void;
  clearProfile: () => void;
  isAuthenticated: boolean;
}

const ProfileContext = createContext<ProfileContextValue | undefined>(undefined);

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfileState] = useState<UserProfile | null>(() => {
    // Load from localStorage on mount
    const stored = localStorage.getItem('bytelense_profile');
    return stored ? JSON.parse(stored) : null;
  });

  const setProfile = (newProfile: UserProfile) => {
    setProfileState(newProfile);
    localStorage.setItem('bytelense_profile', JSON.stringify(newProfile));
  };

  const clearProfile = () => {
    setProfileState(null);
    localStorage.removeItem('bytelense_profile');
  };

  return (
    <ProfileContext.Provider
      value={{
        profile,
        setProfile,
        clearProfile,
        isAuthenticated: profile !== null,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  const context = useContext(ProfileContext);
  if (!context) {
    throw new Error('useProfile must be used within ProfileProvider');
  }
  return context;
}
```

### 6.3 WebSocket State (Event-Driven)

```typescript
// src/hooks/useWebSocket.ts

import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import type { DetailedAssessment, ScanProgressEvent } from '@/types';

interface UseScanOptions {
  onProgress?: (progress: ScanProgressEvent) => void;
  onComplete?: (assessment: DetailedAssessment) => void;
  onError?: (error: { stage: string; error: string; retry_suggestion: string }) => void;
}

export function useScan(options: UseScanOptions) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    const newSocket = io('http://localhost:8000/scan');

    newSocket.on('connect', () => {
      setIsConnected(true);
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
    });

    newSocket.on('scan_progress', (data: ScanProgressEvent) => {
      options.onProgress?.(data);
    });

    newSocket.on('scan_complete', (data: { result: DetailedAssessment }) => {
      setIsScanning(false);
      options.onComplete?.(data.result);
    });

    newSocket.on('scan_error', (data) => {
      setIsScanning(false);
      options.onError?.(data);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const startScan = useCallback((imageData: string, userName: string) => {
    if (!socket || !isConnected) {
      throw new Error('WebSocket not connected');
    }

    setIsScanning(true);
    socket.emit('start_scan', {
      user: userName,
      image_data: imageData,
      source: 'camera',
      format: 'jpeg',
    });
  }, [socket, isConnected]);

  return {
    isConnected,
    isScanning,
    startScan,
  };
}
```

### 6.4 No Global State Library Needed

**Why Redux/Zustand/etc. NOT needed:**
- Profile: Simple Context (< 10 KB data)
- Scan: WebSocket events (ephemeral)
- UI: Component-local state
- No complex data transformations
- No shared mutations

**Keep it simple**: React's built-in primitives are sufficient.

---

## 7. WebSocket Integration

### 7.1 Connection Lifecycle

```typescript
// src/lib/websocket.ts

import { io, Socket } from 'socket.io-client';
import { WS_URL } from '@/config/constants';

export class WebSocketClient {
  private socket: Socket | null = null;

  connect(namespace: string = '/scan'): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(`${WS_URL}${namespace}`, {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 10000,
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });

    return this.socket;
  }

  disconnect() {
    this.socket?.close();
    this.socket = null;
  }

  emit(event: string, data: any) {
    if (!this.socket?.connected) {
      throw new Error('WebSocket not connected');
    }
    this.socket.emit(event, data);
  }

  on(event: string, callback: (...args: any[]) => void) {
    this.socket?.on(event, callback);
  }

  off(event: string, callback?: (...args: any[]) => void) {
    this.socket?.off(event, callback);
  }
}

export const wsClient = new WebSocketClient();
```

### 7.2 Event Types (TypeScript)

```typescript
// src/types/websocket.ts

export interface StartScanEvent {
  user: string;
  image_data: string;  // base64
  source: 'camera' | 'upload';
  format: 'jpeg' | 'png';
}

export interface ScanProgressEvent {
  stage: string;
  progress: number;  // 0-100
  message: string;
}

export interface ScanCompleteEvent {
  result: DetailedAssessment;
}

export interface ScanErrorEvent {
  stage: string;
  error: string;
  error_code: string;
  retry_suggestion?: string;
}
```

### 7.3 Usage in Component

```typescript
// src/components/screens/ScanScreen.tsx

import { useScan } from '@/hooks/useScan';

export function ScanScreen() {
  const [progress, setProgress] = useState<ScanProgressEvent | null>(null);
  const [result, setResult] = useState<DetailedAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { isConnected, isScanning, startScan } = useScan({
    onProgress: setProgress,
    onComplete: setResult,
    onError: (err) => setError(err.error),
  });

  const handleCapture = (imageData: string) => {
    try {
      startScan(imageData, profile.name);
    } catch (err) {
      setError('Failed to start scan. Please refresh and try again.');
    }
  };

  // ... render logic
}
```

---

## 8. Camera/Image Capture

### 8.1 Camera Access Hook

```typescript
// src/hooks/useCamera.ts

import { useState, useEffect, useRef } from 'react';

export function useCamera() {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',  // Rear camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });

      setStream(mediaStream);
      setHasPermission(true);
      setError(null);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      setHasPermission(false);
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError') {
          setError('Camera permission denied. Please allow camera access in browser settings.');
        } else if (err.name === 'NotFoundError') {
          setError('No camera found on this device.');
        } else {
          setError('Failed to access camera: ' + err.message);
        }
      }
    }
  };

  const stopCamera = () => {
    stream?.getTracks().forEach(track => track.stop());
    setStream(null);
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const captureImage = (): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (!videoRef.current || !stream) {
        reject(new Error('Camera not ready'));
        return;
      }

      const canvas = document.createElement('canvas');
      const video = videoRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas context not available'));
        return;
      }

      ctx.drawImage(video, 0, 0);

      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error('Failed to capture image'));
          return;
        }

        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result as string;
          resolve(base64.split(',')[1]);  // Remove data:image/jpeg;base64, prefix
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      }, 'image/jpeg', 0.8);  // 80% quality
    });
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return {
    videoRef,
    stream,
    error,
    hasPermission,
    startCamera,
    stopCamera,
    captureImage,
  };
}
```

### 8.2 CameraCapture Component

```typescript
// src/components/scan/CameraCapture.tsx

import { useCamera } from '@/hooks/useCamera';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface CameraCaptureProps {
  onCapture: (imageData: string) => void;
  isProcessing: boolean;
}

export function CameraCapture({ onCapture, isProcessing }: CameraCaptureProps) {
  const { videoRef, error, hasPermission, startCamera, captureImage } = useCamera();

  useEffect(() => {
    startCamera();
  }, []);

  const handleCapture = async () => {
    try {
      const imageData = await captureImage();
      onCapture(imageData);
    } catch (err) {
      console.error('Capture failed:', err);
    }
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
        <Button onClick={startCamera} className="mt-4">
          Try Again
        </Button>
      </Alert>
    );
  }

  if (hasPermission === false) {
    return (
      <Alert>
        <AlertDescription>
          Camera access is required to scan products.
          Please allow camera access and reload the page.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="w-full rounded-lg"
      />
      
      {/* Capture overlay */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-64 h-64 border-4 border-white rounded-lg" />
      </div>

      {/* Capture button */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
        <Button
          size="lg"
          onClick={handleCapture}
          disabled={isProcessing}
          className="rounded-full w-16 h-16"
        >
          📷
        </Button>
      </div>
    </div>
  );
}
```

---

## 9. Error Handling System

### 9.1 Error Boundary Component

```typescript
// src/components/layout/ErrorBoundary.tsx

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

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
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <Alert variant="destructive" className="max-w-md">
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription className="space-y-4">
              <p>
                The application encountered an error. Please try refreshing the page.
              </p>
              <p className="text-sm text-muted-foreground">
                Error: {this.state.error?.message}
              </p>
              <Button onClick={this.handleReset} className="w-full">
                Reload Application
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 9.2 Error Messages (User-Friendly)

```typescript
// src/lib/errorMessages.ts

export const ERROR_MESSAGES = {
  // Camera errors
  CAMERA_PERMISSION_DENIED: 'Please allow camera access in your browser settings and refresh the page.',
  CAMERA_NOT_FOUND: 'No camera detected. Please connect a camera or use the upload option.',
  CAMERA_IN_USE: 'Camera is being used by another application. Please close other apps and try again.',
  
  // WebSocket errors
  WEBSOCKET_DISCONNECTED: 'Connection lost. Please check your internet connection and refresh.',
  WEBSOCKET_TIMEOUT: 'Connection timed out. Please refresh and try again.',
  
  // API errors
  API_NETWORK_ERROR: 'Network error. Please check your internet connection.',
  API_SERVER_ERROR: 'Server error. Please try again in a few minutes.',
  
  // Scan errors
  SCAN_BARCODE_FAILED: 'Could not detect barcode. Try better lighting or angle.',
  SCAN_PRODUCT_NOT_FOUND: 'Product not found in database. Try manual entry (coming soon).',
  SCAN_IMAGE_TOO_DARK: 'Image too dark. Please use better lighting.',
  SCAN_IMAGE_TOO_BLURRY: 'Image too blurry. Please hold camera steady.',
  
  // Profile errors
  PROFILE_NOT_FOUND: 'Profile not found. Please log in again.',
  PROFILE_LOAD_FAILED: 'Failed to load profile. Please log in again.',
  
  // Generic
  UNKNOWN_ERROR: 'An unexpected error occurred. Please refresh and try again.',
} as const;

export function getErrorMessage(errorCode: string): string {
  return ERROR_MESSAGES[errorCode as keyof typeof ERROR_MESSAGES] || ERROR_MESSAGES.UNKNOWN_ERROR;
}
```

### 9.3 Toast Notifications

```typescript
// src/hooks/useToast.ts (using sonner library)

import { toast } from 'sonner';

export function useToast() {
  return {
    success: (message: string) => toast.success(message),
    error: (message: string) => toast.error(message),
    info: (message: string) => toast.info(message),
    loading: (message: string) => toast.loading(message),
  };
}

// Usage in component
const { error, success } = useToast();

try {
  await doSomething();
  success('Scan complete!');
} catch (err) {
  error(getErrorMessage('SCAN_FAILED'));
}
```

---

## 10. Type Safety

### 10.1 Backend Type Generation

**Goal**: Generate TypeScript types from backend Pydantic models

**Options**:
1. Manual typing (copy from `schemas.py`)
2. Generate from OpenAPI schema
3. Use shared schema generator

**Recommendation**: Manual typing for MVP (fastest)

```typescript
// src/types/assessment.ts

export interface DetailedAssessment {
  scan_id: string;
  timestamp: string;  // ISO date string
  product_name: string;
  brand: string | null;
  
  final_score: number;
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  verdict_emoji: string;
  
  base_score: number;
  context_adjustment: string;
  time_multiplier: number;
  final_calculation: string;
  
  highlights: string[];
  warnings: string[];
  allergen_alerts: string[];
  
  moderation_message: string;
  timing_recommendation: string;
  
  reasoning_steps: string[];
  confidence: number;
  
  sources: CitationSource[];
  inline_citations: Record<string, number>;
  
  alternative_products: string[];
  portion_suggestion: string | null;
  
  nutrition_snapshot: NutritionSnapshot;
}

export interface CitationSource {
  citation_number: number;
  source_type: "openfoodfacts" | "searxng_web" | "health_guideline" | "user_profile";
  title: string;
  url: string | null;
  authority_score: number;
  snippet: string | null;
  accessed_at: string;
}

export interface NutritionSnapshot {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g: number;
  sodium_mg: number;
  fiber_g: number | null;
  serving_size: string;
}
```

### 10.2 TypeScript Configuration

```json
// tsconfig.json

{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting - STRICT MODE */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictPropertyInitialization": true,

    /* Path aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 10.3 API Client Type Safety

```typescript
// src/lib/api.ts

import type { UserProfile, DetailedAssessment } from '@/types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  auth: {
    login: (name: string) =>
      fetchJSON<{ status: string; profile: UserProfile | null; requires_onboarding: boolean }>(
        '/api/auth/login',
        {
          method: 'POST',
          body: JSON.stringify({ name }),
        }
      ),
    
    onboard: (data: any) =>
      fetchJSON<{ profile: UserProfile }>('/api/auth/onboard', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  profile: {
    get: (name: string) =>
      fetchJSON<{ profile: UserProfile }>(`/api/profile/${name}`),
    
    update: (name: string, updates: Partial<UserProfile>) =>
      fetchJSON<{ profile: UserProfile }>(`/api/profile/${name}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      }),
  },

  health: () =>
    fetchJSON<{ status: string; services: any }>('/health'),
};
```

---

## 11. Step-by-Step Setup

### 11.1 Prerequisites

**Required**:
- Node.js 20+ (LTS)
- pnpm 9+ (`npm install -g pnpm`)
- Modern browser (Chrome/Firefox/Edge)

**Backend must be running**:
- FastAPI server on http://localhost:8000
- WebSocket server on ws://localhost:8000/scan
- Ollama running on http://localhost:11434

### 11.2 Initialize Project

```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/docs/UI

# 1. Create Vite + React + TypeScript project
pnpm create vite@latest . --template react-ts

# 2. Install dependencies
pnpm install

# 3. Install UI libraries
pnpm add tailwindcss postcss autoprefixer class-variance-authority clsx tailwind-merge lucide-react @radix-ui/react-slot

# 4. Initialize Tailwind
pnpm dlx tailwindcss init -p

# 5. Install shadcn/ui CLI
pnpm dlx shadcn@latest init

# 6. Install WebSocket client
pnpm add socket.io-client

# 7. Install toast library
pnpm add sonner

# 8. Install date utilities
pnpm add date-fns
```

### 11.3 Configure Tailwind

```javascript
// tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### 11.4 Install shadcn/ui Components

```bash
# Core UI components
pnpm dlx shadcn@latest add button
pnpm dlx shadcn@latest add card
pnpm dlx shadcn@latest add badge
pnpm dlx shadcn@latest add alert
pnpm dlx shadcn@latest add dialog
pnpm dlx shadcn@latest add input
pnpm dlx shadcn@latest add label
pnpm dlx shadcn@latest add select
pnpm dlx shadcn@latest add accordion
pnpm dlx shadcn@latest add progress
pnpm dlx shadcn@latest add separator
pnpm dlx shadcn@latest add tabs
```

### 11.5 Environment Variables

```bash
# .env.local

VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENV=development
```

### 11.6 Create Directory Structure

```bash
cd src

# Create directories
mkdir -p types/{assessment,profile,websocket,components}
mkdir -p components/{ui,auth,scan,verdict,layout,screens}
mkdir -p lib hooks context config styles

# Create placeholder files
touch types/index.ts
touch types/assessment.ts
touch types/profile.ts
touch types/websocket.ts
touch lib/api.ts
touch lib/websocket.ts
touch lib/camera.ts
touch lib/utils.ts
touch hooks/useWebSocket.ts
touch hooks/useCamera.ts
touch hooks/useProfile.ts
touch context/ProfileContext.tsx
touch config/constants.ts
```

### 11.7 Create Vite Config

```typescript
// vite.config.ts

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
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### 11.8 First Component Test

```typescript
// src/App.tsx

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

function App() {
  const [health, setHealth] = useState<any>(null)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error(err))
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card className="p-8 max-w-md">
        <h1 className="text-2xl font-bold mb-4">Bytelense</h1>
        
        {health ? (
          <div className="space-y-2">
            <p className="text-green-600">✅ Backend connected</p>
            <pre className="text-xs bg-gray-50 p-2 rounded">
              {JSON.stringify(health, null, 2)}
            </pre>
          </div>
        ) : (
          <p className="text-red-600">❌ Backend not connected</p>
        )}
        
        <Button className="w-full mt-4">
          Test Button
        </Button>
      </Card>
    </div>
  )
}

export default App
```

### 11.9 Run Development Server

```bash
pnpm run dev

# Open browser to http://localhost:5173
# You should see health check result if backend is running
```

---

## 12. Testing Strategy

### 12.1 Manual Testing Checklist

**Phase 1: Camera & Image Capture**
- [ ] Camera permission request works
- [ ] Video stream displays correctly
- [ ] Capture button creates image
- [ ] Image quality is sufficient (not too compressed)
- [ ] Error messages show for denied permission
- [ ] Error messages show for no camera
- [ ] Works on desktop (webcam)
- [ ] Works on mobile (front and rear camera)

**Phase 2: WebSocket Connection**
- [ ] Connection establishes on page load
- [ ] Reconnects if connection drops
- [ ] Shows "connecting" state appropriately
- [ ] Emits start_scan event correctly
- [ ] Receives progress events
- [ ] Receives complete event with assessment
- [ ] Receives error events
- [ ] Connection closes on page unload

**Phase 3: Verdict Display**
- [ ] All components render with sample data
- [ ] Conditional components show/hide correctly
- [ ] Allergen alerts are prominent (red)
- [ ] Citations are clickable
- [ ] Reasoning section collapses/expands
- [ ] Layout is responsive (mobile + desktop)
- [ ] Colors match verdict (green/yellow/red)

**Phase 4: End-to-End Flow**
- [ ] Login → Scan → Verdict flow works
- [ ] Profile data persists in localStorage
- [ ] Scan history is tracked (future)
- [ ] Error messages are clear and actionable
- [ ] No console errors
- [ ] TypeScript compilation has no errors

### 12.2 Automated Testing (Optional)

**For later** (not MVP):

```bash
# Install testing libraries
pnpm add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event

# Install Playwright for E2E
pnpm add -D @playwright/test
```

**Unit test example**:
```typescript
// src/components/verdict/VerdictBadge.test.tsx

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VerdictBadge } from './VerdictBadge';

describe('VerdictBadge', () => {
  it('renders score and verdict', () => {
    render(<VerdictBadge score={7.5} verdict="good" emoji="🟢" />);
    expect(screen.getByText(/7.5/)).toBeInTheDocument();
    expect(screen.getByText(/GOOD/)).toBeInTheDocument();
  });
});
```

**E2E test example**:
```typescript
// tests/scan-flow.spec.ts

import { test, expect } from '@playwright/test';

test('complete scan flow', async ({ page }) => {
  // Login
  await page.goto('http://localhost:5173');
  await page.fill('input[name="name"]', 'testuser');
  await page.click('button:has-text("Login")');

  // Wait for scan screen
  await expect(page.locator('h1')).toContainText('Scan Product');

  // Click capture (mock camera)
  await page.click('button:has-text("Capture")');

  // Wait for verdict
  await expect(page.locator('.verdict-badge')).toBeVisible({ timeout: 30000 });
});
```

---

## 13. Non-Technical Debug Guide

### 13.1 For User: "Nothing Happens When I Click"

**Diagnosis Steps**:
1. Open browser console (F12)
2. Look for red errors
3. Check network tab for failed requests

**Common Issues**:

| Error Message | Meaning | Fix |
|--------------|---------|-----|
| "WebSocket connection failed" | Backend not running | Start backend: `uvicorn app.main:app` |
| "Camera permission denied" | User denied camera | Allow camera in browser settings |
| "Failed to fetch" | API request failed | Check backend is on port 8000 |
| "Unexpected token" | JSON parse error | Backend returned invalid response |

**Instructions to User**:
1. Take screenshot of error (F12 → Console tab)
2. Note exact error message
3. Share with developer
4. Try refreshing page (Ctrl+R)

### 13.2 For User: "Camera Not Working"

**Checklist**:
- [ ] Camera permission allowed in browser
- [ ] Camera not used by another app (Zoom, Teams, etc.)
- [ ] Using HTTPS or localhost (required for camera API)
- [ ] Browser supports MediaDevices API (Chrome 53+, Firefox 36+)

**Instructions**:
1. Check browser permissions:
   - Chrome: Settings → Privacy → Site Settings → Camera
   - Firefox: Settings → Permissions → Camera
2. Close other apps using camera
3. Try different browser
4. Use upload option instead

### 13.3 For User: "Scan Takes Forever"

**Possible Causes**:
- Backend Ollama model loading (first request can take 30s)
- Network slow/interrupted
- Backend crashed

**Instructions**:
1. Check backend terminal for errors
2. Wait 60 seconds max
3. If no response, refresh page and try again
4. Check internet connection

### 13.4 Error Code Reference

```typescript
// src/lib/errorMessages.ts

export const USER_FACING_ERRORS = {
  'CAMERA_PERMISSION_DENIED': {
    title: 'Camera Access Blocked',
    message: 'Please allow camera access in your browser settings.',
    action: 'Open Settings',
    link: 'https://support.google.com/chrome/answer/2693767',
  },
  
  'WEBSOCKET_DISCONNECTED': {
    title: 'Connection Lost',
    message: 'Lost connection to server. Please refresh the page.',
    action: 'Refresh Page',
    link: null,
  },
  
  'SCAN_PRODUCT_NOT_FOUND': {
    title: 'Product Not Found',
    message: 'Could not find this product in our database.',
    action: 'Try Again',
    link: null,
  },
  
  // ... more errors
};
```

---

## 14. Potential Pitfalls & Solutions

### 14.1 Pitfall: Camera Permissions on Mobile

**Issue**: Mobile browsers handle camera permissions differently.

**Solutions**:
1. Always use HTTPS in production (localhost OK for dev)
2. Request permission only on user action (button click)
3. Provide clear instructions if denied
4. Offer upload alternative

**Code**:
```typescript
// Don't auto-start camera on mount
// Instead, wait for user click
const handleStartCamera = async () => {
  await startCamera();
};

<Button onClick={handleStartCamera}>
  Open Camera
</Button>
```

### 14.2 Pitfall: WebSocket Reconnection Loop

**Issue**: If backend restarts, client reconnects infinitely.

**Solution**: Limit reconnection attempts

```typescript
const socket = io(WS_URL, {
  reconnection: true,
  reconnectionAttempts: 5,  // Stop after 5 tries
  reconnectionDelay: 1000,
});

socket.on('reconnect_failed', () => {
  showError('Cannot connect to server. Please refresh the page.');
});
```

### 14.3 Pitfall: Large Image Size

**Issue**: Captured images too large for WebSocket transmission.

**Solution**: Compress before sending

```typescript
canvas.toBlob(
  (blob) => {
    // Process blob
  },
  'image/jpeg',
  0.7  // 70% quality (lower = smaller)
);
```

### 14.4 Pitfall: TypeScript Errors Hard to Debug

**Issue**: User sees "Type 'X' is not assignable to type 'Y'" and can't fix it.

**Solution**: Add clear type guards

```typescript
// Good: Type guard function
function isDetailedAssessment(data: any): data is DetailedAssessment {
  return (
    typeof data === 'object' &&
    'scan_id' in data &&
    'final_score' in data &&
    'verdict' in data
  );
}

// Usage
if (isDetailedAssessment(response)) {
  setAssessment(response);  // TypeScript knows it's safe
} else {
  throw new Error('Invalid assessment data received');
}
```

### 14.5 Pitfall: Component Renders Before Data Ready

**Issue**: Null pointer errors when data hasn't loaded yet.

**Solution**: Loading states everywhere

```typescript
function VerdictScreen({ assessment }: { assessment: DetailedAssessment | null }) {
  if (!assessment) {
    return <LoadingSpinner message="Analyzing product..." />;
  }

  return <div>{/* Render assessment */}</div>;
}
```

### 14.6 Pitfall: Error Messages Too Technical

**Issue**: User sees "ERR_CONNECTION_REFUSED" and doesn't know what to do.

**Solution**: Map technical errors to user-friendly messages

```typescript
function handleError(error: Error) {
  let userMessage = 'Something went wrong. Please try again.';
  
  if (error.message.includes('ERR_CONNECTION_REFUSED')) {
    userMessage = 'Cannot connect to server. Please check that the backend is running.';
  } else if (error.message.includes('timeout')) {
    userMessage = 'Request timed out. Please check your internet connection.';
  } else if (error.message.includes('NotAllowedError')) {
    userMessage = 'Camera access denied. Please allow camera in browser settings.';
  }
  
  showToast(userMessage, 'error');
}
```

### 14.7 Pitfall: LocalStorage Full

**Issue**: Storing too much data in localStorage (5MB limit).

**Solution**: Store only essential data

```typescript
// Good: Store only profile ID
localStorage.setItem('bytelense_user', profile.name);

// Bad: Store entire scan history
// localStorage.setItem('bytelense_history', JSON.stringify(allScans));
```

---

## 15. Implementation Roadmap

### Phase 1: Foundation (Hour 0-1)

**Goal**: Get dev environment running with health check

**Tasks**:
1. Initialize Vite project
2. Install dependencies
3. Configure Tailwind + shadcn/ui
4. Create directory structure
5. Test backend connection
6. Deploy first component

**Checkpoint**: Can see "Backend connected" on screen

### Phase 2: Type System (Hour 1-2)

**Goal**: Define all TypeScript types

**Tasks**:
1. Create `types/assessment.ts`
2. Create `types/profile.ts`
3. Create `types/websocket.ts`
4. Create `types/components.ts`
5. Verify TypeScript compilation

**Checkpoint**: `pnpm run build` succeeds with no errors

### Phase 3: Camera (Hour 2-3)

**Goal**: Camera capture works

**Tasks**:
1. Implement `useCamera` hook
2. Create `CameraCapture` component
3. Test on desktop (webcam)
4. Test on mobile (rear camera)
5. Add error handling

**Checkpoint**: Can capture image and log base64

### Phase 4: WebSocket (Hour 3-4)

**Goal**: Real-time communication works

**Tasks**:
1. Implement `websocket.ts` client
2. Create `useScan` hook
3. Test connection/disconnection
4. Test event emission/reception
5. Add reconnection logic

**Checkpoint**: Can send image and receive progress events

### Phase 5: Components (Hour 4-5)

**Goal**: All verdict components built

**Tasks**:
1. Implement `VerdictBadge`
2. Implement `AllergenAlert`
3. Implement `ModerationBanner`
4. Implement `InsightSection`
5. Implement `NutritionCard`
6. Implement `ReasoningSection`
7. Implement `CitationList`
8. Implement `RecommendationSection`

**Checkpoint**: Can render mock verdict screen

### Phase 6: Integration (Hour 5-6)

**Goal**: End-to-end flow works

**Tasks**:
1. Connect camera to WebSocket
2. Display verdict on scan complete
3. Handle errors gracefully
4. Add loading states
5. Test full flow

**Checkpoint**: Can scan product and see verdict

### Phase 7: Polish (Hour 6+)

**Goal**: Production-ready

**Tasks**:
1. Add animations
2. Improve error messages
3. Responsive design fixes
4. Performance optimization
5. Documentation

**Checkpoint**: Deployed and tested on multiple devices

---

## 16. Success Criteria

### 16.1 Technical Success

- [ ] Zero TypeScript errors on build
- [ ] All components render without errors
- [ ] WebSocket connects and reconnects
- [ ] Camera captures images successfully
- [ ] End-to-end flow completes under 30s
- [ ] Error boundaries catch all failures
- [ ] Mobile responsive (tested on 2 devices)

### 16.2 User Experience Success

- [ ] Non-technical user can complete scan without help
- [ ] Error messages are clear and actionable
- [ ] Loading states prevent confusion
- [ ] Verdict is easy to understand at a glance
- [ ] No "white screen of death"
- [ ] Works on Chrome, Firefox, Safari

### 16.3 Maintainability Success

- [ ] Code follows consistent structure
- [ ] Types are clearly defined
- [ ] Comments explain "why" not "what"
- [ ] README has clear setup instructions
- [ ] Environment variables documented
- [ ] Debug guide exists for common issues

---

## 17. Final Architecture Summary

**Decision**: React + Vite with Server-Driven UI

**Why It Works**:
1. Backend controls WHAT to show (via DetailedAssessment JSON)
2. Frontend renders HOW to show it (React components)
3. No complex client logic → harder to break
4. TypeScript catches errors at compile time
5. Error boundaries handle runtime failures
6. Clear error messages guide user
7. Minimal dependencies → fewer breaking changes

**Key Principles**:
- Server is source of truth
- Client only handles UI events + WebSocket
- No complex state management
- Types everywhere
- Fail gracefully
- Clear error messages

**This architecture is bulletproof because**:
- If component breaks → error boundary shows fallback
- If WebSocket fails → reconnects automatically
- If camera fails → shows clear instructions
- If backend returns bad data → type guards catch it
- If user is confused → error messages tell them what to do

**User with zero JS skills can**:
- Read error messages and know what to do
- Check browser console for specific errors
- Follow debug guide to fix common issues
- Ask for help with specific error codes

---

## Appendix A: Commands Reference

```bash
# Development
pnpm run dev              # Start dev server (port 5173)
pnpm run build            # Build for production
pnpm run preview          # Preview production build
pnpm run lint             # Check for errors (if configured)

# shadcn/ui
pnpm dlx shadcn@latest add <component>  # Add new component
pnpm dlx shadcn@latest                   # List available components

# Type checking
pnpm run type-check       # Run TypeScript compiler (no emit)

# Testing (optional)
pnpm run test             # Run unit tests
pnpm run test:e2e         # Run E2E tests
```

## Appendix B: File Templates

### B.1 Component Template

```typescript
// src/components/domain/MyComponent.tsx

import type { MyComponentProps } from '@/types';
import { Card } from '@/components/ui/card';

export function MyComponent({ prop1, prop2 }: MyComponentProps) {
  // Early return for loading/empty states
  if (!prop1) {
    return <div>Loading...</div>;
  }

  // Main render
  return (
    <Card className="p-4">
      <h2>{prop1}</h2>
      <p>{prop2}</p>
    </Card>
  );
}
```

### B.2 Hook Template

```typescript
// src/hooks/useMyHook.ts

import { useState, useEffect } from 'react';

export function useMyHook(param: string) {
  const [state, setState] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch data or setup subscriptions
    return () => {
      // Cleanup
    };
  }, [param]);

  return { state, error };
}
```

### B.3 Type Template

```typescript
// src/types/myType.ts

export interface MyType {
  id: string;
  name: string;
  optional?: string;
  nested: {
    field: number;
  };
}

export interface MyComponentProps {
  data: MyType;
  onAction: (id: string) => void;
}
```

---

## Conclusion

This architecture plan provides a comprehensive, bulletproof foundation for the Bytelense frontend. It prioritizes:

1. **Simplicity**: React + Vite, no unnecessary complexity
2. **Type Safety**: TypeScript everywhere, catch errors early
3. **Error Handling**: Boundaries, fallbacks, clear messages
4. **Server Control**: Backend decides UI, client just renders
5. **Debuggability**: Clear errors, debug guide, logging

**For a user with zero JavaScript debugging skills**, this plan ensures:
- Compile-time safety (TypeScript catches most errors)
- Runtime safety (error boundaries, type guards)
- Clear error messages (user knows what to do)
- Fallback UI (no white screens)
- Debug guide (step-by-step troubleshooting)

**The key insight**: By keeping client logic minimal and backend-driven, we minimize the surface area for bugs. The user doesn't need to debug complex state management or logic – they just need to ensure the backend is running and the connection works.

**Next step**: Execute the implementation roadmap, checkpoint by checkpoint.

---
