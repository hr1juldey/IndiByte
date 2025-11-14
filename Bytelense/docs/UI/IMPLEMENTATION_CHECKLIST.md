# Bytelense Frontend Implementation Checklist
## Verification & Testing Guide

Use this checklist to verify each implementation phase.

---

## Phase 1: Foundation ✅

### Environment Setup

- [ ] Node.js 20+ installed and verified
- [ ] pnpm installed globally
- [ ] Project created with Vite + React + TypeScript
- [ ] All dependencies installed successfully
- [ ] `pnpm run dev` starts without errors
- [ ] Browser opens to http://localhost:5173

### Tailwind Configuration

- [ ] `tailwind.config.js` configured correctly
- [ ] `postcss.config.js` exists
- [ ] `src/index.css` imports Tailwind directives
- [ ] Tailwind classes work in components (test with `className="bg-red-500"`)
- [ ] No CSS errors in console

### shadcn/ui Setup

- [ ] `components.json` exists
- [ ] `src/components/ui/` directory created
- [ ] Button component installed and imports correctly
- [ ] Card component installed and renders
- [ ] Badge component installed
- [ ] Alert component installed
- [ ] No import errors

### TypeScript Configuration

- [ ] `tsconfig.json` has `baseUrl` and `paths` configured
- [ ] `@/` import alias works
- [ ] No TypeScript errors on `pnpm run build`
- [ ] VS Code shows no red squiggles on imports

### Backend Connection

- [ ] `.env.local` file created with correct URLs
- [ ] Can fetch http://localhost:8000/health successfully
- [ ] Health check component displays backend status
- [ ] All services show "connected" or "ok"
- [ ] No CORS errors in console

### Checkpoint: Foundation Complete

```
✅ Dev server running
✅ Tailwind working
✅ shadcn/ui components render
✅ TypeScript compiles
✅ Backend health check passes
✅ No console errors
```

**Screenshot**: Save screenshot of health check page showing all green

---

## Phase 2: Type System ✅

### Type Files Created

- [ ] `src/types/index.ts` exists and exports all types
- [ ] `src/types/assessment.ts` defines DetailedAssessment
- [ ] `src/types/profile.ts` defines UserProfile
- [ ] `src/types/websocket.ts` defines event types
- [ ] `src/types/components.ts` defines component props

### Type Definitions

- [ ] DetailedAssessment interface matches backend schema
- [ ] All required fields defined
- [ ] Optional fields marked with `?`
- [ ] Union types for verdicts/stages correct
- [ ] CitationSource interface complete

### Type Validation

- [ ] Can import types: `import type { DetailedAssessment } from '@/types'`
- [ ] TypeScript shows autocomplete for type properties
- [ ] No "cannot find module" errors
- [ ] `pnpm run build` succeeds with no type errors

### API Client Types

- [ ] `src/lib/api.ts` exists
- [ ] All API functions have typed return values
- [ ] Request/response types defined
- [ ] Error handling typed

### Checkpoint: Type System Complete

```
✅ All type files created
✅ No TypeScript errors
✅ Types match backend schemas
✅ Autocomplete works in VS Code
✅ Build succeeds
```

**Test**: Create a test function using types and verify autocomplete

---

## Phase 3: Camera ✅

### Camera Hook

- [ ] `src/hooks/useCamera.ts` created
- [ ] Hook exports: videoRef, stream, error, hasPermission, startCamera, stopCamera, captureImage
- [ ] Can request camera permission
- [ ] Can start/stop camera stream
- [ ] Can capture image as base64
- [ ] Error handling for permission denied
- [ ] Error handling for no camera found
- [ ] Cleanup on unmount

### CameraCapture Component

- [ ] `src/components/scan/CameraCapture.tsx` created
- [ ] Video element displays stream
- [ ] Capture button visible and functional
- [ ] Shows error message if permission denied
- [ ] Shows error message if no camera
- [ ] Overlay guides user to center product
- [ ] Disabled state while processing

### Desktop Testing

- [ ] Webcam activates when component mounts
- [ ] Video stream shows in browser
- [ ] Click capture button creates image
- [ ] Base64 data logged to console
- [ ] Camera stops when component unmounts
- [ ] No memory leaks (test by mounting/unmounting multiple times)

### Mobile Testing

- [ ] Prompts for camera permission
- [ ] Rear camera selected by default
- [ ] Can switch to front camera
- [ ] Touch capture button works
- [ ] Image quality acceptable (not too compressed)
- [ ] Landscape orientation works

### Error Scenarios

- [ ] Denying permission shows clear error message
- [ ] Closing camera (another app) shows error
- [ ] No camera connected shows error
- [ ] Retry button works after error

### Checkpoint: Camera Complete

```
✅ Camera permission flow works
✅ Video stream displays
✅ Image capture works
✅ Base64 output correct
✅ Error messages clear
✅ Works on desktop (webcam)
✅ Works on mobile (rear camera)
```

**Screenshot**: Save photo captured from camera showing quality

---

## Phase 4: WebSocket ✅

### WebSocket Client

- [ ] `src/lib/websocket.ts` created
- [ ] WebSocketClient class implemented
- [ ] Can connect to ws://localhost:8000/scan
- [ ] Can emit events
- [ ] Can listen to events
- [ ] Auto-reconnection configured
- [ ] Connection timeout handling
- [ ] Disconnect cleanup

### Scan Hook

- [ ] `src/hooks/useScan.ts` created
- [ ] Hook exports: isConnected, isScanning, startScan
- [ ] Accepts callbacks: onProgress, onComplete, onError
- [ ] Calls callbacks on appropriate events
- [ ] Manages scanning state
- [ ] Cleans up on unmount

### Event Handling

- [ ] `start_scan` event emits correctly
- [ ] `scan_progress` events received
- [ ] `scan_complete` event received with assessment
- [ ] `scan_error` event received and handled
- [ ] TypeScript types for all events

### Connection States

- [ ] Shows "Connecting..." when establishing connection
- [ ] Shows "Connected" when ready
- [ ] Shows "Reconnecting..." if connection drops
- [ ] Shows error if connection fails after retries
- [ ] Prevents scan if not connected

### Backend Integration

- [ ] Backend receives start_scan event
- [ ] Backend sends progress updates
- [ ] Frontend displays progress (0-100%)
- [ ] Frontend receives complete assessment
- [ ] Data structure matches DetailedAssessment type

### Error Scenarios

- [ ] Backend not running → shows clear error
- [ ] Connection drops mid-scan → reconnects and continues
- [ ] Backend returns error → shows retry suggestion
- [ ] Timeout → shows timeout message

### Checkpoint: WebSocket Complete

```
✅ Connection establishes
✅ Can emit events
✅ Receives progress updates
✅ Receives assessment on complete
✅ Error handling works
✅ Reconnection works
✅ State management correct
```

**Test**: Start scan with mock image and verify progress events logged

---

## Phase 5: Components ✅

### VerdictBadge

- [ ] `src/components/verdict/VerdictBadge.tsx` created
- [ ] Props: score, verdict, emoji
- [ ] Displays score as "X/10"
- [ ] Shows verdict in uppercase
- [ ] Shows emoji
- [ ] Color based on verdict (green/yellow/red)
- [ ] Large, prominent styling
- [ ] Accessible (ARIA labels)

### AllergenAlert

- [ ] `src/components/verdict/AllergenAlert.tsx` created
- [ ] Props: alerts (string[])
- [ ] Red background, white text
- [ ] Warning icon (⚠️)
- [ ] Lists all allergens
- [ ] Only shows if alerts.length > 0
- [ ] Pulsing animation for attention

### ModerationBanner

- [ ] `src/components/verdict/ModerationBanner.tsx` created
- [ ] Props: message, level
- [ ] Shows consumption message
- [ ] Progress bar visual
- [ ] Color based on level (within/approaching/exceeding)
- [ ] Percentage calculation correct

### InsightSection

- [ ] `src/components/verdict/InsightSection.tsx` created
- [ ] Props: highlights, warnings
- [ ] Two sections: highlights and warnings
- [ ] Icons for visual distinction (✅/⚠️)
- [ ] Bullet list format
- [ ] Responsive layout (columns on desktop, stack on mobile)

### NutritionCard

- [ ] `src/components/verdict/NutritionCard.tsx` created
- [ ] Props: nutrition, targets (optional)
- [ ] Displays all macro nutrients
- [ ] Progress bars for comparison
- [ ] Warning icon if exceeds target
- [ ] Tooltip on hover with details
- [ ] Responsive grid layout

### ReasoningSection

- [ ] `src/components/verdict/ReasoningSection.tsx` created
- [ ] Props: steps, confidence
- [ ] Collapsible (closed by default)
- [ ] Numbered list of reasoning steps
- [ ] Shows confidence score
- [ ] Smooth expand/collapse animation

### CitationList

- [ ] `src/components/verdict/CitationList.tsx` created
- [ ] Props: sources
- [ ] Perplexity-style layout
- [ ] Citation numbers [1], [2]
- [ ] Clickable links open in new tab
- [ ] Snippet excerpt with "Read more"
- [ ] Source type badge (authority score)

### RecommendationSection

- [ ] `src/components/verdict/RecommendationSection.tsx` created
- [ ] Props: alternatives, timing, portion
- [ ] Shows timing recommendation with icon
- [ ] Shows portion suggestion with icon
- [ ] Lists healthier alternatives
- [ ] Only shows if data available

### Component Testing

**Each component**:
- [ ] Renders with mock data
- [ ] Handles empty/null data gracefully
- [ ] Responsive on mobile and desktop
- [ ] Accessible (keyboard navigation)
- [ ] No console errors
- [ ] No TypeScript errors

### Checkpoint: Components Complete

```
✅ All 8 components created
✅ Each component renders correctly
✅ Props typed correctly
✅ Conditional rendering works
✅ Styling matches design
✅ Responsive layout
✅ Accessible
```

**Screenshot**: Save screenshot of each component with sample data

---

## Phase 6: Integration ✅

### VerdictScreen

- [ ] `src/components/screens/VerdictScreen.tsx` created
- [ ] Accepts DetailedAssessment prop
- [ ] Renders all components in correct order
- [ ] Conditional rendering for optional sections
- [ ] Layout is responsive
- [ ] "Scan Another" button functional

### ScanScreen

- [ ] `src/components/screens/ScanScreen.tsx` created
- [ ] Integrates CameraCapture component
- [ ] Integrates useScan hook
- [ ] Shows progress during scan
- [ ] Navigates to VerdictScreen on complete
- [ ] Shows error on failure
- [ ] Retry button works

### App Routing

- [ ] `src/App.tsx` has routing logic
- [ ] Can navigate between screens
- [ ] Profile context wraps app
- [ ] Error boundary wraps entire app
- [ ] Loading states between transitions

### Profile Context

- [ ] `src/context/ProfileContext.tsx` created
- [ ] Provides profile, setProfile, clearProfile
- [ ] Persists to localStorage
- [ ] Loads from localStorage on mount
- [ ] useProfile hook works

### Full Flow Testing

**End-to-End Test**:
1. [ ] Open app → shows login screen
2. [ ] Enter name → loads/creates profile
3. [ ] Navigate to scan screen
4. [ ] Click camera → video stream starts
5. [ ] Capture image → WebSocket emits event
6. [ ] Progress bar updates (5 stages)
7. [ ] Verdict screen appears with assessment
8. [ ] All components display correctly
9. [ ] Click "Scan Another" → returns to scan screen
10. [ ] Profile persists on refresh

### Error Handling Integration

- [ ] Camera error → shows message, offers retry
- [ ] WebSocket error → shows message, suggests refresh
- [ ] Backend error → shows stage and retry suggestion
- [ ] Network error → shows offline message
- [ ] Unexpected error → error boundary catches

### Performance Testing

- [ ] Initial load < 2s
- [ ] Camera activation < 1s
- [ ] Image capture < 500ms
- [ ] Total scan time < 30s (first scan can be longer)
- [ ] Subsequent scans < 15s
- [ ] No memory leaks (check DevTools Memory tab)
- [ ] No excessive re-renders

### Checkpoint: Integration Complete

```
✅ Full flow works end-to-end
✅ All screens navigate correctly
✅ Profile persists
✅ WebSocket events trigger UI updates
✅ Error handling comprehensive
✅ Performance acceptable
✅ No console errors
```

**Video**: Record screen capture of full scan flow

---

## Phase 7: Polish ✅

### Visual Polish

- [ ] Colors match design (neutral theme)
- [ ] Consistent spacing (Tailwind spacing scale)
- [ ] Typography hierarchy clear
- [ ] Icons consistent (lucide-react)
- [ ] Animations smooth (60 FPS)
- [ ] Loading spinners not jarring
- [ ] Verdict colors intuitive (green=good, red=bad)

### Accessibility

- [ ] All buttons have aria-labels
- [ ] Images have alt text
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Color contrast passes WCAG AA
- [ ] Screen reader friendly (test with NVDA/VoiceOver)

### Responsive Design

- [ ] Mobile portrait (320px+) works
- [ ] Mobile landscape works
- [ ] Tablet (768px+) works
- [ ] Desktop (1024px+) works
- [ ] Large desktop (1920px+) works
- [ ] No horizontal scrollbars
- [ ] Touch targets ≥ 44px

### Error Messages

- [ ] All error messages user-friendly
- [ ] No technical jargon
- [ ] Action suggestions clear
- [ ] Contact info provided (if needed)
- [ ] Error codes human-readable

### Loading States

- [ ] Spinner shows during long operations
- [ ] Skeleton screens for content loading
- [ ] Progress bar for multi-step processes
- [ ] Disable buttons during loading
- [ ] No "flashing" content

### Toast Notifications

- [ ] Success messages green
- [ ] Error messages red
- [ ] Info messages blue
- [ ] Auto-dismiss after 5s
- [ ] Can manually dismiss
- [ ] Not too intrusive

### Documentation

- [ ] README.md with setup instructions
- [ ] TROUBLESHOOTING.md updated
- [ ] All environment variables documented
- [ ] API endpoints documented
- [ ] Component props documented (JSDoc comments)

### Checkpoint: Polish Complete

```
✅ Visual design consistent
✅ Accessible
✅ Responsive on all devices
✅ Error messages clear
✅ Loading states comprehensive
✅ Documentation complete
```

**Screenshots**: Save screenshots of all screens on mobile and desktop

---

## Final Verification

### Code Quality

- [ ] No TypeScript errors (`pnpm run build`)
- [ ] No ESLint errors (if configured)
- [ ] No console.log statements (remove debug logs)
- [ ] No commented-out code
- [ ] Consistent code formatting
- [ ] Meaningful variable names
- [ ] Functions < 50 lines
- [ ] Components < 200 lines

### Performance

- [ ] Lighthouse score > 90 (Performance)
- [ ] Lighthouse score > 90 (Accessibility)
- [ ] Lighthouse score > 90 (Best Practices)
- [ ] Bundle size < 500 KB (gzipped)
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s

### Security

- [ ] No secrets in code
- [ ] Environment variables used correctly
- [ ] No eval() or dangerouslySetInnerHTML
- [ ] XSS protection (React auto-escapes)
- [ ] Input validation where needed

### Browser Compatibility

- [ ] Works on Chrome 90+
- [ ] Works on Firefox 88+
- [ ] Works on Safari 14+
- [ ] Works on Edge 90+
- [ ] Works on Mobile Chrome
- [ ] Works on Mobile Safari (with HTTPS)

### Edge Cases

- [ ] No internet connection → shows offline message
- [ ] Backend down → shows clear error
- [ ] WebSocket timeout → reconnects
- [ ] Camera in use → shows error
- [ ] Very long product name → truncates nicely
- [ ] 100+ allergens → scrollable
- [ ] No nutrition data → shows "N/A"
- [ ] Zero score → displays correctly

### User Testing

- [ ] Non-technical user can complete scan
- [ ] User understands verdict
- [ ] User knows what to do on error
- [ ] User can retry failed scan
- [ ] User satisfied with speed
- [ ] User finds UI intuitive

---

## Deployment Readiness

### Pre-Deployment

- [ ] All tests pass
- [ ] No known bugs
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Environment variables set
- [ ] Error monitoring configured (Sentry, etc.)

### Build for Production

```bash
# 1. Install dependencies
pnpm install

# 2. Run type check
pnpm run type-check

# 3. Build
pnpm run build

# 4. Test build
pnpm run preview

# 5. Verify build output
ls -lh dist/
```

**Checklist**:
- [ ] Build completes without errors
- [ ] Build size < 500 KB gzipped
- [ ] Preview works on http://localhost:4173
- [ ] All assets bundled correctly
- [ ] Source maps generated (for debugging)

### Deployment Options

**Option 1: Static Hosting** (Vercel/Netlify):
- [ ] Connect GitHub repo
- [ ] Set build command: `pnpm run build`
- [ ] Set output directory: `dist`
- [ ] Set environment variables
- [ ] Deploy and test

**Option 2: Self-Hosted**:
- [ ] Copy `dist/` to server
- [ ] Configure nginx/Apache
- [ ] Set up HTTPS (required for camera)
- [ ] Point to backend API
- [ ] Test from external network

### Post-Deployment

- [ ] Verify health check page loads
- [ ] Test camera on production URL
- [ ] Test WebSocket connection
- [ ] Test full scan flow
- [ ] Monitor error logs
- [ ] Set up analytics (optional)

---

## Success Criteria

The frontend is **COMPLETE** and **PRODUCTION-READY** when:

### Technical Criteria

✅ Zero TypeScript errors
✅ Zero console errors in normal operation
✅ All components render correctly
✅ Camera capture works on desktop and mobile
✅ WebSocket real-time updates work
✅ End-to-end scan flow completes successfully
✅ Error handling comprehensive
✅ Performance metrics meet targets
✅ Responsive on all screen sizes
✅ Accessible (WCAG AA compliant)

### User Experience Criteria

✅ Non-technical user can scan product without help
✅ Error messages tell user exactly what to do
✅ Loading states prevent confusion
✅ Verdict is easy to understand at a glance
✅ Works on both desktop and mobile
✅ Intuitive navigation
✅ Fast enough (< 30s per scan)

### Maintainability Criteria

✅ Code is well-organized (follows structure)
✅ Types are clearly defined
✅ Components are reusable
✅ Documentation is complete
✅ Troubleshooting guide exists
✅ Developer can add new features easily

---

## Verification Sign-Off

**Developer**: _______________ Date: _______________

**Tester**: _______________ Date: _______________

**Product Owner**: _______________ Date: _______________

---

## Notes

Use this space to document any issues, workarounds, or future improvements:

```
Issue: Camera doesn't work on Safari < 14
Workaround: Show upload option
Future: Add polyfill or drop Safari 13 support

Issue: First scan takes 60s (Ollama loading)
Workaround: Show "First scan may take up to 1 minute" message
Future: Preload model on server startup

Issue: Large images (>10MB) cause WebSocket timeout
Workaround: Compress to 80% quality
Future: Implement progressive upload
```

---

## Testing Script

Run this script to verify all functionality:

```bash
#!/bin/bash
# test-frontend.sh

echo "🧪 Bytelense Frontend Test Suite"
echo "================================"

echo ""
echo "1. Type Check..."
pnpm run type-check
if [ $? -eq 0 ]; then
  echo "✅ Type check passed"
else
  echo "❌ Type check failed"
  exit 1
fi

echo ""
echo "2. Build..."
pnpm run build
if [ $? -eq 0 ]; then
  echo "✅ Build passed"
else
  echo "❌ Build failed"
  exit 1
fi

echo ""
echo "3. Check bundle size..."
BUILD_SIZE=$(du -sh dist | cut -f1)
echo "Bundle size: $BUILD_SIZE"

echo ""
echo "4. Start preview server..."
pnpm run preview &
PREVIEW_PID=$!
sleep 3

echo ""
echo "5. Health check..."
curl -f http://localhost:4173 > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✅ Preview server running"
else
  echo "❌ Preview server failed"
  kill $PREVIEW_PID
  exit 1
fi

kill $PREVIEW_PID

echo ""
echo "================================"
echo "✅ All tests passed!"
echo ""
echo "Manual testing required:"
echo "1. Camera capture"
echo "2. WebSocket connection"
echo "3. Full scan flow"
echo "4. Mobile responsiveness"
```

Save as `test-frontend.sh`, make executable: `chmod +x test-frontend.sh`

Run: `./test-frontend.sh`

---

**END OF CHECKLIST**

If all items checked, congratulations! Your frontend is bulletproof and ready for production. 🎉
