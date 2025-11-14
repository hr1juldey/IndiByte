# Bytelense Frontend Documentation

## Overview

This directory contains the complete frontend architecture and implementation plan for **Bytelense**, a food scanning application with real-time AI-powered nutritional analysis.

**Key Design Principle**: Bulletproof architecture for developers with ZERO JavaScript/TypeScript debugging skills.

---

## Documentation Structure

### 📘 Core Documents

1. **[FRONTEND_ARCHITECTURE_PLAN.md](./FRONTEND_ARCHITECTURE_PLAN.md)** (PRIMARY)
   - Complete architectural specification
   - Technology stack decisions with justifications
   - Component architecture and design patterns
   - State management strategy
   - WebSocket and camera integration
   - Type safety system
   - Error handling strategy
   - 17 comprehensive sections covering every aspect

2. **[QUICK_START.md](./QUICK_START.md)**
   - Get running in 30 minutes
   - Step-by-step setup commands
   - Environment configuration
   - Health check verification
   - Troubleshooting common setup issues

3. **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)**
   - For users with ZERO JavaScript debugging skills
   - Common errors and fixes in plain English
   - Browser console basics
   - When to ask for help
   - Emergency reset procedures

4. **[IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)**
   - Verification checklist for each phase
   - Testing procedures
   - Performance validation
   - Deployment readiness
   - Success criteria

---

## Quick Navigation

### Need to...

**Get Started?**
→ Read [QUICK_START.md](./QUICK_START.md) first

**Understand Architecture?**
→ Read [FRONTEND_ARCHITECTURE_PLAN.md](./FRONTEND_ARCHITECTURE_PLAN.md) Section 1-6

**Implement Camera?**
→ Read [FRONTEND_ARCHITECTURE_PLAN.md](./FRONTEND_ARCHITECTURE_PLAN.md) Section 8

**Implement WebSocket?**
→ Read [FRONTEND_ARCHITECTURE_PLAN.md](./FRONTEND_ARCHITECTURE_PLAN.md) Section 7

**Build Components?**
→ Read [FRONTEND_ARCHITECTURE_PLAN.md](./FRONTEND_ARCHITECTURE_PLAN.md) Section 4

**Fix an Error?**
→ Read [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

**Verify Implementation?**
→ Use [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)

---

## Key Decisions Summary

### Architecture: React + Vite (NOT Next.js)

**Why?**
- Simpler for non-JS developers to debug
- Excellent TypeScript support
- Fast development experience
- Straightforward WebSocket integration
- Server-driven UI pattern still works

**Server-Driven UI Pattern**:
- Backend sends `DetailedAssessment` JSON
- Frontend maps data to components
- No complex client logic
- Backend controls WHAT to show, frontend controls HOW

### Technology Stack

| Category | Choice | Why |
|----------|--------|-----|
| Framework | React 18+ | Industry standard, mature |
| Build Tool | Vite 5+ | Fast, excellent TS support |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, copy-paste components |
| State | React Context + useState | No complex state management needed |
| WebSocket | socket.io-client | Auto-reconnection, fallback |
| Camera | MediaDevices API | Native browser support |
| HTTP | fetch API | Built-in, no dependencies |
| Package Manager | pnpm | Faster than npm |

### Component Architecture

**8 Core Components**:
1. VerdictBadge - Score display
2. AllergenAlert - Critical warnings
3. ModerationBanner - Daily consumption tracking
4. InsightSection - Highlights + warnings
5. NutritionCard - Macro breakdown
6. ReasoningSection - AI reasoning (collapsible)
7. CitationList - Perplexity-style references
8. RecommendationSection - Alternatives + timing

**Design Principles**:
- Props-only data flow (no internal fetching)
- No complex logic (keep it simple)
- Error boundaries everywhere
- Loading states for all async operations
- Clear, user-friendly error messages

---

## Implementation Roadmap

### Phase 1: Foundation (Hour 0-1)
- Set up Vite + React + TypeScript
- Configure Tailwind + shadcn/ui
- Test backend connection
- **Checkpoint**: Health check page shows backend connected

### Phase 2: Type System (Hour 1-2)
- Define all TypeScript types
- Match backend Pydantic models
- **Checkpoint**: Zero TypeScript errors on build

### Phase 3: Camera (Hour 2-3)
- Implement camera hook
- Build capture component
- **Checkpoint**: Can capture image, see base64 in console

### Phase 4: WebSocket (Hour 3-4)
- Implement WebSocket client
- Build scan hook with event handling
- **Checkpoint**: Can emit events, receive progress

### Phase 5: Components (Hour 4-5)
- Build all 8 verdict components
- **Checkpoint**: Can render mock verdict screen

### Phase 6: Integration (Hour 5-6)
- Connect camera → WebSocket → verdict display
- **Checkpoint**: Full end-to-end scan flow works

### Phase 7: Polish (Hour 6+)
- Animations, responsive design
- Error message improvements
- Documentation

---

## Project Structure

```
docs/UI/
├── src/
│   ├── types/              # TypeScript definitions
│   ├── components/
│   │   ├── ui/             # shadcn/ui base components
│   │   ├── auth/           # Login, onboarding
│   │   ├── scan/           # Camera, upload
│   │   ├── verdict/        # Verdict display components
│   │   ├── layout/         # Error boundary, navbar
│   │   └── screens/        # Full-page screens
│   ├── lib/                # API client, WebSocket, utils
│   ├── hooks/              # Custom React hooks
│   ├── context/            # Profile context
│   └── config/             # Constants, environment
├── public/                 # Static assets
├── FRONTEND_ARCHITECTURE_PLAN.md
├── QUICK_START.md
├── TROUBLESHOOTING.md
├── IMPLEMENTATION_CHECKLIST.md
└── README.md (this file)
```

---

## Critical Features

### 1. Server-Driven UI

Backend controls UI via DetailedAssessment JSON:

```typescript
interface DetailedAssessment {
  // Core verdict
  final_score: number;
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  verdict_emoji: string;
  
  // Conditional sections (show if present)
  allergen_alerts: string[];
  moderation_message: string;
  warnings: string[];
  highlights: string[];
  
  // Always show
  nutrition_snapshot: object;
  reasoning_steps: string[];
  sources: CitationSource[];
  
  // Optional recommendations
  alternative_products: string[];
  timing_recommendation: string;
  portion_suggestion: string;
}
```

Frontend logic (simple):
```typescript
{assessment.allergen_alerts.length > 0 && (
  <AllergenAlert alerts={assessment.allergen_alerts} />
)}
```

### 2. Error Handling

**Three Layers**:
1. **Type Guards**: Validate data structure at runtime
2. **Error Boundaries**: Catch React errors, show fallback UI
3. **User Messages**: Clear, actionable error messages

**Example**:
```typescript
// Type guard
if (!isDetailedAssessment(data)) {
  throw new Error('Invalid assessment data');
}

// Error boundary
<ErrorBoundary fallback={<ErrorScreen />}>
  <VerdictScreen assessment={data} />
</ErrorBoundary>

// User message
"Cannot connect to server. Please check that the backend is running."
```

### 3. Camera Integration

**Challenge**: Different browsers, permission flows, quality control

**Solution**:
- Request permission on user action (button click)
- Provide clear instructions if denied
- Offer upload alternative
- Compress images before sending (70% quality)
- Handle all error cases with user-friendly messages

### 4. WebSocket Real-Time

**Flow**:
1. Connect to ws://localhost:8000/scan
2. Emit `start_scan` with image data
3. Receive `scan_progress` events (5 stages)
4. Receive `scan_complete` with assessment
5. Display verdict screen

**Auto-Reconnection**:
- 5 retry attempts
- 1 second delay between attempts
- Show "Reconnecting..." to user
- Fail gracefully if can't reconnect

---

## Error Prevention Strategies

### 1. TypeScript Everywhere
- All components have typed props
- All API responses have types
- Catch type errors at compile time

### 2. Fallback UI
- Every component has loading state
- Every component handles null/undefined data
- Error boundaries catch runtime errors

### 3. Clear Error Messages
- No technical jargon
- Tell user WHAT went wrong
- Tell user HOW to fix it
- Provide retry buttons

### 4. Validation
- Type guards on API responses
- Input validation on forms
- Length limits on lists
- Image size limits

### 5. Logging
- Console.log progress for debugging
- Structured error objects
- Error codes for reference

---

## For Non-Technical Users

If you have **ZERO JavaScript debugging skills**, this architecture is designed for you:

### What You Can Do

1. **Read Error Messages**: All errors are in plain English
2. **Follow Troubleshooting Guide**: Step-by-step fixes
3. **Check Health Status**: Visit http://localhost:8000/health
4. **Refresh Page**: Fixes most issues (Ctrl+R)
5. **Ask for Help**: With screenshot + error message

### What You DON'T Need to Do

- ❌ Understand React internals
- ❌ Debug TypeScript errors
- ❌ Fix WebSocket code
- ❌ Modify component logic
- ❌ Deal with state management

### When Something Breaks

1. Open browser console (F12)
2. Take screenshot of error
3. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
4. If error not listed, ask developer with screenshot

---

## Testing Strategy

### Manual Testing (MVP)

**Essential Tests**:
- [ ] Camera opens and shows video stream
- [ ] Capture button creates image
- [ ] WebSocket connects and sends image
- [ ] Progress bar updates through 5 stages
- [ ] Verdict screen displays with all components
- [ ] Error messages appear on failures
- [ ] Works on Chrome desktop
- [ ] Works on mobile (Chrome/Safari)

### Automated Testing (Future)

**Unit Tests** (Vitest + React Testing Library):
- Component rendering
- Props validation
- State updates

**E2E Tests** (Playwright):
- Full scan flow
- Error scenarios
- Multi-device testing

---

## Performance Targets

| Metric | Target | How to Test |
|--------|--------|-------------|
| Initial Load | < 2s | Lighthouse |
| Camera Activation | < 1s | Manual timer |
| Image Capture | < 500ms | Manual timer |
| Total Scan Time | < 30s | WebSocket events |
| Bundle Size | < 500KB gzipped | `ls -lh dist/` |
| First Contentful Paint | < 1.5s | Lighthouse |
| Time to Interactive | < 3s | Lighthouse |

---

## Browser Compatibility

| Browser | Min Version | Camera | WebSocket | Status |
|---------|-------------|--------|-----------|--------|
| Chrome | 90+ | ✅ | ✅ | Recommended |
| Firefox | 88+ | ✅ | ✅ | Fully supported |
| Safari | 14+ | ⚠️ | ✅ | HTTPS required for camera |
| Edge | 90+ | ✅ | ✅ | Fully supported |
| Mobile Chrome | Latest | ✅ | ✅ | Fully supported |
| Mobile Safari | Latest | ⚠️ | ✅ | HTTPS required |

---

## Deployment

### Development

```bash
cd docs/UI
pnpm install
pnpm run dev
# Open http://localhost:5173
```

### Production Build

```bash
pnpm run build
# Output: dist/ directory
```

### Deploy Options

1. **Static Hosting** (Vercel/Netlify):
   - Connect GitHub repo
   - Set build: `pnpm run build`
   - Set output: `dist`
   - Deploy

2. **Self-Hosted**:
   - Copy `dist/` to server
   - Configure nginx/Apache
   - Enable HTTPS (required for camera)
   - Point to backend API

---

## Environment Variables

Create `.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENV=development
```

Production:

```bash
VITE_API_BASE_URL=https://api.bytelense.com
VITE_WS_URL=wss://api.bytelense.com
VITE_ENV=production
```

---

## Common Issues & Fixes

### Issue: "Backend not connected"
**Fix**: Start backend: `uvicorn app.main:app --reload`

### Issue: "Camera permission denied"
**Fix**: Allow camera in browser settings (click lock icon 🔒 in address bar)

### Issue: "WebSocket disconnected"
**Fix**: Backend WebSocket not running, restart backend

### Issue: TypeScript errors
**Fix**: Run `pnpm install` to ensure all types installed

For more, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## Security Considerations

### What's Protected

- ✅ XSS: React auto-escapes all content
- ✅ Input validation: All user inputs validated
- ✅ Environment variables: Secrets in .env, not code
- ✅ HTTPS: Required for camera in production

### What's NOT in MVP

- ❌ Authentication (name-only login)
- ❌ Authorization (no user permissions)
- ❌ Rate limiting (no API limits)
- ❌ Encryption (local development only)

**Note**: This is MVP/demo. Add proper security for production.

---

## Future Enhancements

### V0.2
- Manual product entry (if barcode fails)
- Scan history view
- Profile editing UI
- Dark mode

### V0.3
- Offline support (PWA)
- Better animations
- Voice output (text-to-speech)
- Multiple camera angles

### V1.0
- Mobile native apps (React Native)
- Social features (share scans)
- Meal planning
- Advanced analytics

---

## Contributing

### Code Style

- Use TypeScript (strict mode)
- Use Tailwind for styling (no custom CSS)
- Use shadcn/ui components (don't reinvent)
- Keep components < 200 lines
- Add JSDoc comments for complex logic

### Naming Conventions

- Components: PascalCase (`VerdictBadge.tsx`)
- Hooks: camelCase with `use` prefix (`useCamera.ts`)
- Utilities: camelCase (`api.ts`)
- Types: PascalCase (`DetailedAssessment`)

### Git Workflow

- Feature branches: `feature/camera-capture`
- Bug fixes: `fix/camera-permission`
- Commit format: `feat: add camera capture`

---

## Resources

### Official Documentation

- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)

### Helpful Guides

- [MediaDevices API](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)

---

## Support

### For Users

- Read [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Check browser console (F12)
- Take screenshot of error
- Open GitHub issue with:
  - Screenshot
  - Steps to reproduce
  - Browser + OS version

### For Developers

- Read [FRONTEND_ARCHITECTURE_PLAN.md](./FRONTEND_ARCHITECTURE_PLAN.md)
- Check [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)
- Review TypeScript errors
- Check backend logs
- Open GitHub issue with:
  - Error message
  - Code context
  - Expected vs actual behavior

---

## License

[Add license information]

---

## Contact

[Add contact information]

---

## Changelog

### 2025-11-14 - v1.0 (Initial Design)

**Created**:
- Complete frontend architecture plan
- Quick start guide
- Troubleshooting guide
- Implementation checklist
- README (this file)

**Decisions**:
- React + Vite (not Next.js)
- Server-driven UI pattern
- Zero client-side state management
- TypeScript strict mode
- Error-first design

**Next**: Begin implementation Phase 1

---

**Last Updated**: 2025-11-14
**Status**: Design Complete, Ready for Implementation
**Version**: 1.0

---
