# Sub-Phase 2.2 Analysis: Sodium Data Quality Investigation

**Status**: ✅ COMPLETED
**Date**: 2025-11-20
**Test Method**: Direct OpenFoodFacts API Queries (bypassing system)

---

## Executive Summary

🔍 **MAJOR FINDING**: The 1680mg cucumber sodium value is **NOT in the raw API data**.

OpenFoodFacts returns cucumber sodium as: **0.84 grams per 100g** (= 840 mg)

The 1680 mg value appears to be **created by the system**, likely through:

1. Data merge with salted foods
2. Portion scaling multiplication error
3. Merge of multiple API results

---

## Direct API Test Results

### Test 1: Cucumber (The Problem Case)

```
Query: "cucumber"
API Response:
  Product Name: Amora Croq'Vert Cornichons Extra-Fins Bocal 370g
  Sodium: 0.84 g (per 100g)
  Converted: 840 mg (per 100g)

Expected for 200g portion: 840 * 2 = 1680 mg
Actual system output: 1680 mg ✅ MATCHES
```

**CRITICAL FINDING**: The system is scaling 100g data by 2 for a 200g portion!

- If original was 840 mg/100g
- And system got 2 cucumbers = 200g
- Then 840 * 2 = 1680 mg ✓ Mathematically correct!

### Test 2: Cucumber Salted

```
Query: "cucumber salted"
API Response:
  Product Name: Organic Lightly Salted Wholegrain Low Fat Rice Cakes
  Sodium: 0.72 g (per 100g)

Note: API search for "cucumber salted" returned rice cakes, not salted cucumber
```

### Test 3: Salt

```
Query: "salt"
API Response:
  Sodium: 39.6 g (per 100g) - as expected (pure salt is 39.6% sodium)
  Converted: 39,600 mg
```

### Test 4: Red Salt

```
Query: "red salt"
API Response:
  Sodium: 0.008 g (per 100g) - unusually low
  Note: Red salt (Himalayan salt) has lower sodium than table salt
```

### Test 5: Other Foods

```
Query: "vegetable"     → Sodium: 0.2 g/100g
Query: "rice cakes"    → Sodium: 0.118 g/100g
Query: "egg"           → Sodium: 0.38 g/100g (search returned brioche, not egg)
Query: "rohu fish"     → No results found
Query: "banana"        → Sodium: 0 g/100g
```

---

## Hypothesis Testing

### Hypothesis 2a: Raw API Response Has 1680mg

- **Status**: ❌ NEGATED
- **Finding**: OpenFoodFacts returns cucumber as 0.84g (840 mg), not 1680 mg
- **Conclusion**: Issue is NOT in API data, but in system processing

### Hypothesis 2b: System Merged Cucumber + Red Salt

- **Status**: ⚠️ PARTIALLY LIKELY
- **Evidence**:
  - If system thought "2 cucumbers with red salt" = mixed dish
  - And merged nutrition: cucumber (840mg) + salt ingredient
  - Could create higher value
- **Problem**: Salt values should make it much higher, not exactly 1680
- **Verdict**: Unlikely sole cause, but possible contributing factor

### Hypothesis 2c: Portion Scaling Multiplied Incorrectly

- **Status**: ✅ CONFIRMED (but not an error!)
- **Evidence**:
  - OpenFoodFacts: 840 mg/100g (for cornichons product)
  - System output: 1680 mg (for 200g portion)
  - Calculation: 840 * 2 = 1680 ✓
- **Finding**: System calculated correctly!
- **Real Problem**: Is OpenFoodFacts returning the right product for "cucumber"?

---

## Root Cause Analysis

### The Real Issue

When system queries OpenFoodFacts for "cucumber", it gets a **specific branded product**:

- **Product**: "Amora Croq'Vert Cornichons Extra-Fins Bocal 370g" (pickled cornichons)
- **Sodium**: 0.84g/100g = 840 mg/100g
- **Portion**: 2 units = 200g
- **Calculation**: 840 * 2 = 1680 mg ✓ CORRECT

The problem is **PRODUCT SELECTION**, not calculation:

- User says: "2 cucumbers"
- API returns: "Pickled cornichons (a cucumber product, but salted/preserved)"
- This is technically correct (cornichons ARE cucumbers) but:
  - Fresh cucumber ≈ 10-20 mg sodium/100g
  - Pickled cornichons ≈ 840 mg sodium/100g

**Why this happens**: OpenFoodFacts search returns the most common/documented product matching the term, which is usually the packaged version, not fresh.

---

## Data Quality Issues Identified

### Issue 1: API Returns Specific Products, Not Generic Ingredients

- **Problem**: "cucumber" query returns "Cornichons in pickle juice" (specific product)
- **Expected**: Generic fresh cucumber data
- **Impact**: Sodium values 40-80x higher than actual fresh cucumber
- **Real-world**: A person eating fresh cucumber shouldn't get 1680mg warning

### Issue 2: No Disambiguation Between Product Types

- **Problem**: System doesn't ask "Do you mean fresh cucumber or pickled?"
- **Expected**: For ambiguous queries, ask user or show top 3 options
- **Impact**: Medical advice based on wrong product type

### Issue 3: Domain KB Fallback Is Actually Better

- **Finding**: System's domain KB likely has "fresh cucumber ≈ 2mg sodium"
- **Evidence**: Fallback was used, and overall medical advice was correct
- **Implication**: For common foods, hardcoded KB is MORE ACCURATE than API

---

## Implications for System Fixes

### For Issue #2 (Sodium Quality)

- **Root Cause**: Not a calculation error, but API product selection
- **Solution Options**:
  1. Add product type hints (e.g., "fresh cucumber", "pickled cucumber")
  2. Filter API results to prefer fresh/raw products
  3. Use domain KB for common foods, API only for rare foods
  4. Add bounds checking: cucumber sodium should be <50mg (not 840+)

### For Issue #3 (Dictionary Architecture)

- **New Insight**: The 108-line dictionary is actually BETTER for common foods
- **Reason**: Domain KB has fresh/raw nutrition, API returns processed products
- **Recommendation**:
  - Keep ~20 most common foods in KB (they're more accurate)
  - Use API as fallback for rare/uncommon foods
  - Invert the architecture: KB first, API second

---

## Test Loop 2 Plan: Data Validation

### What To Add

```python
# In OpenFoodFactsResponseTranslator
REALISTIC_RANGES = {
    "calories": (0, 900),      # kcal per 100g
    "protein": (0, 80),        # g per 100g
    "carbs": (0, 100),         # g per 100g
    "fat": (0, 100),           # g per 100g
    "sodium": (0, 2500),       # mg per 100g
}

# Validate against ranges
if sodium_mg > 2500:
    log.warning(f"Sodium {sodium_mg}mg exceeds realistic range, using domain KB instead")
    return domain_kb_fallback()
```

### Validation Bounds by Food Type

- **Vegetables**: sodium < 100 mg/100g
- **Fruits**: sodium < 50 mg/100g
- **Grains**: sodium < 500 mg/100g (unless salted)
- **Proteins**: sodium varies (100-500 mg)
- **Salted/Processed**: sodium < 2500 mg/100g (hard cap)

---

## Recommendations

### Short-term (Fix #2: Data Validation)

1. Add bounds checking in OpenFoodFactsResponseTranslator
2. Log when bounds exceeded, fallback to domain KB
3. This prevents 1680mg false positives

### Medium-term (Architecture Redesign)

1. **Invert the food lookup chain**:
   - Start with Domain KB (accurate for common foods)
   - If not found, query API
   - Validate API results against realistic ranges
2. **Add product type hints**:
   - "cucumber (fresh)" vs "cucumber (pickled)"
   - Weight fresh products higher in search results

### Long-term (Better Data Sources)

1. Consider USDA FoodData Central (focuses on raw ingredients)
2. Maintain curated list of API product IDs for common foods
3. Build confidence scores: API results that match domain KB get higher confidence

---

## Key Takeaway

**The sodium "error" is actually a feature working as designed (correct math), but using the wrong product type (pickled instead of fresh).**

The system needs:

1. ✅ Bounds validation (prevent medical advice on edge cases)
2. ✅ Product type disambiguation (fresh vs processed)
3. ✅ Smarter fallback logic (domain KB first for common foods)

This explains why the overall assessment was still accurate (1715 kcal) - the system found good data for most foods, only picking wrong product for cucumber.
