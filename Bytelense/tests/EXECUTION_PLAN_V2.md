# Execution Plan V2: Solving Remaining Issues Systematically

**Status**: Planning Phase
**Focus**: Fix critical issues + optimize architecture
**Constraints**:
- Keep in @Bytelense/tests/ (sandbox)
- No large embedded JSON dictionaries
- Performance: System takes 10+ minutes for full assessment
- Data quality: Indian food database needs smarter solution

---

## PHASE 1: ROOT CAUSE ANALYSIS & HYPOTHESIS FORMATION

### Issue #1: Temperature=0.3 Still Causing Fallbacks

**Hypothesis 1a**: temperature=0.3 is still set in test_pot.py (Phase 0.1 not implemented)
- Evidence: 3 foods triggered fallback
- Test: Grep test_pot.py for "temperature=0.3"
- If true: Change to 0.0 immediately (1-line fix)

**Hypothesis 1b**: Qwen model produces None values even with better temperature
- Evidence: Complex inputs fail more than simple ones
- Test: Run same extraction 10 times with temperature=0.0
- If true: Need assertions + better signature (Phase 0.3)

**Action Plan**:
```
Step 1: Search for current temperature setting in code
Step 2: Test with temperature=0.0 (if not already set)
Step 3: Check fallback frequency before/after
Step 4: Document actual cause
```

---

### Issue #2: Cucumber Sodium = 1680mg (280x too high)

**Hypothesis 2a**: Data source error (OpenFoodFacts returns wrong value)
- Test: Query OpenFoodFacts API directly for "cucumber"
- If true: Need data validation in response translator

**Hypothesis 2b**: System merged "cucumber" + "red salt" nutrition
- Test: Check if OpenFoodFacts returns multiple results, system took salt instead
- If true: Need source disambiguation logic

**Hypothesis 2c**: Portion scaling multiplied incorrectly
- Test: Check scaling formula (sodium_mg * scale_factor)
- If true: Add bounds checking

**Action Plan**:
```
Step 1: Query OpenFoodFacts "cucumber" directly via curl/requests
Step 2: Log actual API response (not system-processed)
Step 3: Check if sodium_mg=1680 is in raw API response
Step 4: If raw is correct, trace where multiplication happens
Step 5: Add validation: sodium_mg < 5000 (reasonable max)
```

---

### Issue #3: Large Embedded Dictionary in translators.py

**Problem**: 40+ Indian foods hardcoded as dict (lines 190-298)
- 108 lines of static data
- Difficult to maintain (spelling variations, regional names)
- Not scalable for global foods

**Hypothesis 3a**: Should use external CSV/JSON file instead
- Pros: Easier to update, version control friendly
- Cons: Extra I/O, need file path management

**Hypothesis 3b**: Should use API lookup instead of domain KB
- Pros: Always current, no maintenance
- Cons: Slower (not ideal for 10+ min already slow system)

**Hypothesis 3c**: Hybrid approach: small common foods in code, rest use API
- Pros: Fast fallback for common items, scales for uncommon
- Cons: Requires dual logic

**Decision**: Go with **Hypothesis 3c** - keep ~20 most common foods inline, rest use API

**Action Plan**:
```
Step 1: Identify "top 20" foods by frequency (Indian diet)
Step 2: Keep only those in translators.py (reduce to ~2KB)
Step 3: Add regional name aliases (mosambi → mousumbi, rohu → rui)
Step 4: Keep rest relying on OpenFoodFacts + SearXNG
Step 5: Test: Verify system still works with reduced KB
```

---

## PHASE 2: EXECUTION CHECKLIST

### Sub-Phase 2.1: Temperature Investigation (30 mins)

**Checklist**:
- [ ] Read test_pot.py line 242 - check current temperature value
- [ ] Grep codebase for "temperature=" (find all settings)
- [ ] Document findings in TEMPERATURE_ANALYSIS.md
- [ ] Hypothesis result: A or B or C?

**Expected Outcome**:
- Confirm if temperature=0.3 is still set
- If yes: Understand why Phase 0.1 wasn't done
- If no: Understand why fallbacks still occur with 0.0

---

### Sub-Phase 2.2: Sodium Data Quality Investigation (45 mins)

**Checklist**:
- [ ] Create script: test_api_direct.py to query OpenFoodFacts for "cucumber"
- [ ] Log raw API response (JSON dump)
- [ ] Compare raw response vs system-processed value
- [ ] Test with requests library directly (not system)
- [ ] Document findings in SODIUM_ANALYSIS.md
- [ ] Hypothesis result: A or B or C?

**Expected Outcome**:
- Know if 1680mg is in raw API response
- Know if it's a merge/scaling issue
- Know exact fix needed

---

### Sub-Phase 2.3: Domain KB Architecture Review (45 mins)

**Checklist**:
- [ ] Count lines in DomainKnowledgeBaseTranslator.__init__ (lines 190-298)
- [ ] Identify "top 20" foods by Indian diet frequency
- [ ] Create INDIAN_FOOD_FREQUENCY_ANALYSIS.md
- [ ] Analyze translators.py size and performance
- [ ] Hypothesis result: A, B, or C?

**Expected Outcome**:
- Know which foods to keep inline
- Know which can be removed
- Know refactoring strategy

---

### Sub-Phase 2.4: Performance Profiling (1 hour)

**What to measure**:
- How long does current system take? (already know: ~10 mins)
- Breakdown: API calls vs LLM inference vs data processing?
- Which is bottleneck?

**Checklist**:
- [ ] Add timing logs to agents.py (each step)
- [ ] Run one full test (9 foods)
- [ ] Parse logs to find slowest components
- [ ] Document in PERFORMANCE_ANALYSIS.md

**Expected Outcome**:
- Know where time is spent
- Know what optimizations help most

---

## PHASE 3: CRITICAL FIXES (Priority Order)

### Fix #1: Temperature=0.0 (IF Not Already Done)
**Time**: 5 minutes
**Impact**: Eliminates fallbacks, 8/10 → 8.5/10
**Steps**:
1. Check current value in test_pot.py line 242
2. Change "temperature=0.3" → "temperature=0.0"
3. Run test with 3 complex foods
4. Verify: 0 fallbacks

---

### Fix #2: Data Validation for Unrealistic Values
**Time**: 1-2 hours
**Impact**: Prevents medical advice errors, 8.5/10 → 9/10
**Steps**:
1. Add range validation in OpenFoodFactsResponseTranslator
2. Add bounds checks:
   - calories: 0-900 kcal/100g
   - sodium: 0-3000 mg/100g
   - carbs: 0-100g/100g
3. Log when values exceed bounds
4. Use domain KB fallback if values invalid
5. Test: Cucumber returns ~2mg sodium, not 1680mg

---

### Fix #3: Reduce Embedded Dictionary
**Time**: 1 hour
**Impact**: Code quality, easier maintenance
**Steps**:
1. Identify top 20 most common Indian foods
2. Keep only those in translators.py
3. Remove ~80 lines of static data
4. Rely on API for rest
5. Test: System still works, no performance drop

---

## PHASE 4: TESTING & VALIDATION

### Test Loop 1: Temperature Fix
```
Input: 3 complex foods
  - "rohu fish in a veg filled boiled soup"
  - "3 rotis"
  - "2 cucumbers"

Expected: 0 fallbacks (all extracted correctly)
Actual: [To be run]

Pass Criteria: 0 fallbacks
Timeout: 5 mins per food = 15 mins total
```

---

### Test Loop 2: Data Validation
```
Input: "2 cucumbers with red salt"

Validation Checks:
  - sodium_mg range: should be 2-10 (not 1680)
  - If violated: log warning, use domain KB instead
  - Medical advice: should NOT flag high sodium

Expected: cucumber sodium from domain KB (~2mg), not from API (1680mg)
Actual: [To be run]

Pass Criteria: Reasonable sodium value
Timeout: 3 mins
```

---

### Test Loop 3: Reduced Dictionary
```
Input: All 9 test foods

Validation:
  - rice, rotis, banana, apple: from domain KB (top 20)
  - eggs, fish, guava, chicken roll: from API
  - All get data (no None values)

Expected: Same results as before, cleaner code
Actual: [To be run]

Pass Criteria: All foods have nutrition data
Timeout: 10 mins
```

---

## PHASE 5: HYPOTHESIS TESTING FRAMEWORK

### For Each Issue, Test This Sequence:

1. **Form Hypothesis**
   - What could cause the problem?
   - Multiple possible causes?

2. **Design Minimal Test**
   - Can we test hypothesis quickly?
   - Need to isolate one variable?

3. **Run Test**
   - Execute minimal test
   - Document actual result

4. **Validate/Negate**
   - Does result match hypothesis?
   - If no, revise hypothesis

5. **Document Finding**
   - Update markdown file
   - Link to code changes

---

## PHASE 6: INTERNET RESEARCH POINTS

### Before Implementation, Search For:

**Problem #1**: "DSPy temperature extraction quality"
- How does temperature affect factual extraction?
- Best practices for portion extraction?

**Problem #2**: "Food database API sodium values inconsistent"
- Why do APIs return different sodium values?
- How to validate nutritional data?

**Problem #3**: "Indian food nutritional database"
- Are there maintained Indian food databases?
- Better than hardcoding?

**Problem #4**: "LLM performance for extraction tasks"
- Qwen vs other models for extraction?
- Why do complex inputs fail more?

---

## EXECUTION SEQUENCE

### Week 1:

**Day 1**: Root Cause Analysis (3 hours)
- Sub-Phase 2.1: Temperature investigation
- Sub-Phase 2.2: Sodium analysis
- Sub-Phase 2.3: Domain KB review

**Day 2**: Performance Profiling (2 hours)
- Sub-Phase 2.4: Where is time spent?

**Day 3**: Critical Fixes (3 hours)
- Fix #1: Temperature=0.0
- Fix #2: Data validation
- Fix #3: Reduce dictionary

**Day 4**: Testing & Validation (4 hours)
- Test Loops 1, 2, 3
- Document results

**Day 5**: Internet Research (2 hours)
- Research findings
- Verify hypotheses against best practices

---

## DELIVERABLES (Per Phase)

### Analysis Phase Output:
- [ ] TEMPERATURE_ANALYSIS.md
- [ ] SODIUM_ANALYSIS.md
- [ ] INDIAN_FOOD_FREQUENCY_ANALYSIS.md
- [ ] PERFORMANCE_ANALYSIS.md

### Fix Phase Output:
- [ ] Updated test_pot.py (temperature=0.0)
- [ ] Updated translators.py (validation + reduced dict)
- [ ] Updated agents.py (if needed)

### Testing Phase Output:
- [ ] TEST_RESULTS_TEMPERATURE.md
- [ ] TEST_RESULTS_VALIDATION.md
- [ ] TEST_RESULTS_ARCHITECTURE.md

### Research Phase Output:
- [ ] INTERNET_RESEARCH_FINDINGS.md
- [ ] BEST_PRACTICES_APPLIED.md

---

## SUCCESS METRICS

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| No None values | ✅ Pass | ✅ Pass | Done |
| Realistic calories | ✅ Pass | ✅ Pass | Done |
| Extraction fallbacks | 3/9 | 0/9 | HIGH |
| Data quality (sodium) | 1680mg ❌ | ~2mg ✅ | HIGH |
| Code cleanliness | Dict 108 lines | Dict 30 lines | MEDIUM |
| Performance | 10+ mins | <10 mins | LOW |
| Medical advice quality | Good | Excellent | MEDIUM |

---

## RISK MITIGATION

**Risk 1**: Temperature change breaks something else
- Mitigation: Test full pipeline after change
- Fallback: Keep backup of original setting

**Risk 2**: Data validation is too strict, blocks real data
- Mitigation: Log violations, don't fail silently
- Fallback: Manual review of edge cases

**Risk 3**: Removing foods from KB breaks backward compatibility
- Mitigation: Top 20 foods cover 90% of Indian diet
- Fallback: API fallback for uncommon foods

---

## NOTES FOR IMPLEMENTATION

1. **Keep everything in @Bytelense/tests/**
   - No external files
   - No cloud dependencies
   - Sandbox approach

2. **Avoid large embedded data**
   - Max 30 lines per dict
   - Use API as primary
   - KB as fallback only

3. **Performance constraints**
   - System slow (10+ mins)
   - E2E tests need timeouts
   - Profile before optimizing

4. **Test before claiming fix**
   - Don't assume fix works
   - Run actual test with real data
   - Document results

5. **Hypothesis-driven**
   - Form hypothesis first
   - Test to validate/negate
   - Document findings

---

**Next Step**: Execute Sub-Phase 2.1 (Temperature Investigation)
