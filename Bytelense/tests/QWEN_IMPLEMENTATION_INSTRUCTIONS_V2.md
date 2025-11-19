# Instructions for Qwen V2: Implement Medical Nutrition Agentic System
## Critical Fixes for Production Readiness

**Document Version**: V2.0 (2025-11-20)
**Previous Version**: [QWEN_IMPLEMENTATION_INSTRUCTIONS.md](./QWEN_IMPLEMENTATION_INSTRUCTIONS.md)
**Design Reference**: [HLD_MEDICAL_NUTRITION_AGENT.md](./HLD_MEDICAL_NUTRITION_AGENT.md)

---

## EXECUTIVE SUMMARY: WHAT WENT WRONG IN V1

### V1 Implementation Status
✅ Translation layers created
✅ Agent modules implemented
✅ Integration with test_pot.py completed
❌ **CRITICAL FAILURE**: System returns empty/None nutrition data
❌ **CRITICAL FAILURE**: Portion extraction randomly returns None
❌ **CRITICAL FAILURE**: No actual API retrieval happening

### Real-World Test Results
```
Input: "rohu fish 60 gram piece with vegetable soup"
Output: Food name: None, Portion: None → CRASH

Input: "80 to 100 gram rice"
Output: nutrition: {all fields are None} → USELESS

Total Calories Calculated: 1 (should be ~1500)
```

### Root Causes Identified (From DSPy Research + Code Analysis)

1. **Module Calling Anti-Pattern** (CRITICAL)
   - V1 uses `agent.forward()` directly
   - DSPy documentation: "Calling module.forward(...) directly is discouraged"
   - Should use `agent()` instead to enable callbacks/tracking

2. **No Output Validation** (CRITICAL)
   - OutputFields can return None
   - No dspy.Assert or dspy.Suggest to enforce non-None
   - DSPy Guidance: "Use assertions to validate outputs and retry on failure"

3. **Mock API Implementations** (CRITICAL)
   - agents.py lines 188-202 return empty `{}`
   - No actual HTTP calls to OpenFoodFacts
   - No actual calls to SearXNG
   - Only Domain KB works (3 foods: tea, chips, pav bhaji)

4. **Temperature-Induced Non-Determinism** (HIGH)
   - temperature=0.3 causes different outputs per run
   - DSPy Best Practice: Use temperature=0.0 for routing/extraction
   - Use temperature > 0 only for creative generation

5. **No Fallback Chain** (HIGH)
   - When API returns empty → propagates None
   - Should fallback: OpenFoodFacts → SearXNG → DomainKB → ReasonedEstimate
   - Missing: LLM-based inference when all sources fail

---

## CRITICAL RESEARCH FINDINGS FROM DSPY.AI

### Finding 1: Module Invocation Pattern
**Source**: https://dspy.ai/api/modules/Module/

```python
# ❌ WRONG (V1 pattern - causes warning)
result = agent.forward(input=data)

# ✅ CORRECT (V2 pattern - enables full DSPy infrastructure)
result = agent(input=data)
```

**Why it matters**: Direct `.forward()` bypasses:
- Callback execution
- Usage tracking
- Module context management
- Compilation infrastructure

### Finding 2: Assertions for Output Validation
**Source**: https://dspy.ai/learn/programming/7-assertions/

```python
# Add to signatures that must not return None
def forward(self, food_description: str):
    result = self.extractor(food_description=food_description)

    # ✅ NEW: Assert non-None outputs
    dspy.Suggest(
        result.food_name is not None and len(result.food_name) > 0,
        "Food name must be extracted from description. Cannot be None or empty.",
        target_module=self.extractor
    )

    return result
```

**Activation Required**: Must call `program.activate_assertions()` or wrap with `assert_transform_module`

### Finding 3: Temperature Strategy
**Source**: https://dspy.ai/cheatsheet/

- **temperature=0.0**: Deterministic routing, extraction, classification
- **temperature > 0**: Creative generation, reasoning, inference
- **Cache bypass**: Use unique `rollout_id` with non-zero temperature

**V2 Strategy**:
- PortionExtractor: temperature=0.0 (extraction task)
- DataQualityAssessment: temperature=0.0 (routing task)
- DeepInferenceAgent: temperature=0.5 (creative reasoning)
- MedicalAdapter: temperature=0.3 (balanced medical advice)

### Finding 4: Prediction Access Patterns
**Source**: https://dspy.ai/api/primitives/Prediction/

```python
# ✅ SAFE: Use .get() with defaults
food_name = result.get('food_name', 'unknown')

# ❌ UNSAFE: Direct attribute access (crashes if None)
food_name = result.food_name  # Fails if LLM didn't generate field
```

### Finding 5: Tool Design for ReAct
**Source**: https://dspy.ai/api/modules/ReAct/

**NOT NEEDED FOR THIS PROJECT**. The V1 design attempted to use ReAct with tools, but:
- OpenFoodFacts is not a "tool" - it's a data source
- SearXNG is not a "tool" - it's a retrieval system
- ReAct is for *agent decision-making* with tools
- Our use case needs *multi-source data aggregation*

**V2 Change**: Remove ReAct, use direct API calls + fallback logic

---

## V2 IMPLEMENTATION ROADMAP (FIXES FOR V1 FAILURES)

### PHASE 0: Pre-Implementation Fixes (NEW)

**Purpose**: Fix critical anti-patterns before building

**Step 0.1: Set Temperature Correctly**

Location: test_pot.py line 242 and agents.py (all module init)

```python
# In test_pot.py main()
llm = dspy.LM(
    f'ollama/{ollama_model}',
    api_base=ollama_url,
    api_key="",
    temperature=0.0,  # ← CHANGE FROM 0.3 to 0.0 for determinism
    max_tokens=2000   # ← INCREASE from 1000 to 2000 for complex outputs
)
```

**Step 0.2: Fix Module Calling Pattern**

Location: test_pot.py line 133

```python
# ❌ V1 (causes warning)
nutrition_result = self.nutrition_agent.forward(
    food_name=food_name,
    portion=portion_size,
    medical_condition=medical_condition
)

# ✅ V2 (correct pattern)
nutrition_result = self.nutrition_agent(
    food_name=food_name,
    portion=portion_size,
    medical_condition=medical_condition
)
```

**Step 0.3: Add Assertions to PortionExtractor**

Location: test_pot.py (new wrapper class)

```python
class SafePortionExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extractor = dspy.Predict(PortionExtractor)

    def forward(self, food_description: str):
        result = self.extractor(food_description=food_description)

        # Validate extraction succeeded
        dspy.Suggest(
            result.food_name is not None and len(result.food_name.strip()) > 0,
            f"Must extract food name from: '{food_description}'. Cannot return None.",
            target_module=self.extractor
        )

        dspy.Suggest(
            result.portion_size is not None and len(result.portion_size.strip()) > 0,
            f"Must extract portion size from: '{food_description}'. Cannot return None.",
            target_module=self.extractor
        )

        return result
```

Then activate:
```python
# In CalorieQualityProgram.__init__()
self.portion_extractor = SafePortionExtractor()
self.portion_extractor.activate_assertions()  # CRITICAL
```

---

### PHASE 1: Fix Data Retrieval (CRITICAL FIX)

**Purpose**: V1 returns empty data because API calls are mocked

**Problem in V1**:
```python
# agents.py line 188-202
def _query_openfoodfacts(self, food_name: str, portion: str):
    # Mock implementation - returns empty
    return {}

def _query_searxng(self, food_name: str, num_results: int = 3):
    # Mock implementation - returns empty
    return []
```

**V2 Fix: Implement Real OpenFoodFacts API**

```python
import requests
from typing import Optional

def _query_openfoodfacts(self, food_name: str, portion: str) -> dict:
    """
    Query OpenFoodFacts API for nutritional data.
    API Docs: https://world.openfoodfacts.org/data
    """
    try:
        # Search endpoint
        search_url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": food_name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("products"):
            return {}

        # Get first product
        product = data["products"][0]

        # Return in expected format
        return {
            "product_name": product.get("product_name", ""),
            "energy_kcal_100g": product.get("nutriments", {}).get("energy-kcal_100g"),
            "carbohydrates_100g": product.get("nutriments", {}).get("carbohydrates_100g"),
            "proteins_100g": product.get("nutriments", {}).get("proteins_100g"),
            "fat_100g": product.get("nutriments", {}).get("fat_100g"),
            "fiber_100g": product.get("nutriments", {}).get("fiber_100g"),
            "sodium_100g": product.get("nutriments", {}).get("sodium_100g"),
            "sugars_100g": product.get("nutriments", {}).get("sugars_100g")
        }

    except requests.Timeout:
        print(f"  WARNING: OpenFoodFacts timeout for '{food_name}'")
        return {}
    except Exception as e:
        print(f"  WARNING: OpenFoodFacts error: {str(e)}")
        return {}
```

**V2 Fix: Implement Real SearXNG Integration**

```python
def _query_searxng(self, food_name: str, num_results: int = 3) -> list:
    """
    Query SearXNG for nutritional information from web.
    Uses existing searxng_search_func from test_pot.py
    """
    try:
        # Import the existing search function
        from test_pot import searxng_search_func

        # Construct nutrition-focused query
        query = f"{food_name} nutrition facts calories protein carbs"

        # Get results
        results_json = searxng_search_func(query, num_results)
        results = json.loads(results_json)

        return results

    except Exception as e:
        print(f"  WARNING: SearXNG error: {str(e)}")
        return []
```

**Why This Fixes the Problem**:
- V1: No data retrieval → all nutrition fields None
- V2: Real API calls → actual nutrition data returned
- Fallback: If APIs fail, Domain KB provides estimates

---

### PHASE 2: Expand Domain Knowledge Base (CRITICAL FIX)

**Problem in V1**: Only 3 foods in domain KB (tea, chips, pav bhaji)

**V2 Fix**: Add comprehensive Indian food database

Location: translators.py lines 189-253

```python
class DomainKnowledgeBaseTranslator:
    def __init__(self):
        self.food_knowledge_base = {
            # === BEVERAGES ===
            "tea": {"calories": 1, "carbs_g": 0.3, "protein_g": 0, "fat_g": 0, "fiber_g": 0, "sodium_mg": 2, "sugars_g": 0.3},
            "black tea": {"calories": 1, "carbs_g": 0.3, "protein_g": 0, "fat_g": 0, "fiber_g": 0, "sodium_mg": 2, "sugars_g": 0.3},
            "green tea": {"calories": 1, "carbs_g": 0.3, "protein_g": 0, "fat_g": 0, "fiber_g": 0, "sodium_mg": 2, "sugars_g": 0.3},
            "coffee": {"calories": 1, "carbs_g": 0, "protein_g": 0.1, "fat_g": 0, "fiber_g": 0, "sodium_mg": 5, "sugars_g": 0},

            # === INDIAN STAPLES ===
            "rice": {"calories": 130, "carbs_g": 28, "protein_g": 2.7, "fat_g": 0.3, "fiber_g": 0.4, "sodium_mg": 1, "sugars_g": 0.1},
            "white rice": {"calories": 130, "carbs_g": 28, "protein_g": 2.7, "fat_g": 0.3, "fiber_g": 0.4, "sodium_mg": 1, "sugars_g": 0.1},
            "brown rice": {"calories": 112, "carbs_g": 24, "protein_g": 2.6, "fat_g": 0.9, "fiber_g": 1.8, "sodium_mg": 5, "sugars_g": 0.4},
            "roti": {"calories": 71, "carbs_g": 15, "protein_g": 3, "fat_g": 0.4, "fiber_g": 2.7, "sodium_mg": 119, "sugars_g": 0.4},
            "chapati": {"calories": 71, "carbs_g": 15, "protein_g": 3, "fat_g": 0.4, "fiber_g": 2.7, "sodium_mg": 119, "sugars_g": 0.4},
            "naan": {"calories": 262, "carbs_g": 45, "protein_g": 9, "fat_g": 5, "fiber_g": 2, "sodium_mg": 419, "sugars_g": 3.5},
            "paratha": {"calories": 290, "carbs_g": 36, "protein_g": 6, "fat_g": 13, "fiber_g": 2, "sodium_mg": 400, "sugars_g": 1.5},

            # === FISH & SEAFOOD ===
            "rohu fish": {"calories": 97, "carbs_g": 0, "protein_g": 19, "fat_g": 2, "fiber_g": 0, "sodium_mg": 55, "sugars_g": 0},
            "rohu": {"calories": 97, "carbs_g": 0, "protein_g": 19, "fat_g": 2, "fiber_g": 0, "sodium_mg": 55, "sugars_g": 0},
            "katla fish": {"calories": 96, "carbs_g": 0, "protein_g": 17.5, "fat_g": 2.7, "fiber_g": 0, "sodium_mg": 59, "sugars_g": 0},
            "hilsa fish": {"calories": 310, "carbs_g": 0, "protein_g": 18, "fat_g": 25, "fiber_g": 0, "sodium_mg": 65, "sugars_g": 0},

            # === EGGS ===
            "egg": {"calories": 155, "carbs_g": 1.1, "protein_g": 13, "fat_g": 11, "fiber_g": 0, "sodium_mg": 124, "sugars_g": 1.1},
            "boiled egg": {"calories": 155, "carbs_g": 1.1, "protein_g": 13, "fat_g": 11, "fiber_g": 0, "sodium_mg": 124, "sugars_g": 1.1},
            "chicken eggs": {"calories": 155, "carbs_g": 1.1, "protein_g": 13, "fat_g": 11, "fiber_g": 0, "sodium_mg": 124, "sugars_g": 1.1},
            "fried egg": {"calories": 196, "carbs_g": 0.8, "protein_g": 13.6, "fat_g": 15, "fiber_g": 0, "sodium_mg": 207, "sugars_g": 0.4},

            # === VEGETABLES ===
            "cucumber": {"calories": 16, "carbs_g": 3.6, "protein_g": 0.7, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 1.7},
            "cucumbers": {"calories": 16, "carbs_g": 3.6, "protein_g": 0.7, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 1.7},
            "potato": {"calories": 77, "carbs_g": 17, "protein_g": 2, "fat_g": 0.1, "fiber_g": 2.2, "sodium_mg": 6, "sugars_g": 0.8},
            "pumpkin": {"calories": 26, "carbs_g": 6.5, "protein_g": 1, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 1, "sugars_g": 2.8},
            "alu posto": {"calories": 180, "carbs_g": 20, "protein_g": 5, "fat_g": 9, "fiber_g": 3, "sodium_mg": 350, "sugars_g": 2},

            # === FRUITS ===
            "banana": {"calories": 89, "carbs_g": 23, "protein_g": 1.1, "fat_g": 0.3, "fiber_g": 2.6, "sodium_mg": 1, "sugars_g": 12},
            "bananas": {"calories": 89, "carbs_g": 23, "protein_g": 1.1, "fat_g": 0.3, "fiber_g": 2.6, "sodium_mg": 1, "sugars_g": 12},
            "apple": {"calories": 52, "carbs_g": 14, "protein_g": 0.3, "fat_g": 0.2, "fiber_g": 2.4, "sodium_mg": 1, "sugars_g": 10},
            "water apple": {"calories": 25, "carbs_g": 6, "protein_g": 0.6, "fat_g": 0.1, "fiber_g": 0.9, "sodium_mg": 7, "sugars_g": 4.5},
            "watermelon": {"calories": 30, "carbs_g": 8, "protein_g": 0.6, "fat_g": 0.2, "fiber_g": 0.4, "sodium_mg": 1, "sugars_g": 6},
            "mosambi": {"calories": 43, "carbs_g": 9, "protein_g": 0.7, "fat_g": 0.2, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 8},
            "mousumbi": {"calories": 43, "carbs_g": 9, "protein_g": 0.7, "fat_g": 0.2, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 8},
            "lemon": {"calories": 29, "carbs_g": 9, "protein_g": 1.1, "fat_g": 0.3, "fiber_g": 2.8, "sodium_mg": 2, "sugars_g": 2.5},

            # === SNACKS ===
            "chips": {"calories": 540, "carbs_g": 47, "protein_g": 6, "fat_g": 37, "fiber_g": 4, "sodium_mg": 850, "sugars_g": 0.5},
            "potato chips": {"calories": 540, "carbs_g": 47, "protein_g": 6, "fat_g": 37, "fiber_g": 4, "sodium_mg": 850, "sugars_g": 0.5},

            # === CURRIES ===
            "pav bhaji": {"calories": 200, "carbs_g": 25, "protein_g": 4, "fat_g": 8, "fiber_g": 2, "sodium_mg": 400, "sugars_g": 3},
            "dal": {"calories": 116, "carbs_g": 20, "protein_g": 9, "fat_g": 0.4, "fiber_g": 8, "sodium_mg": 238, "sugars_g": 2},
            "vegetable soup": {"calories": 67, "carbs_g": 12, "protein_g": 3.4, "fat_g": 0.7, "fiber_g": 3, "sodium_mg": 450, "sugars_g": 5},
        }

    # ... rest of translator logic
```

**Impact**: Now covers 40+ common Indian foods instead of 3

---

### PHASE 3: Signature Design Improvements (MEDIUM FIX)

**Problem in V1**: Signatures don't guide LLM well enough

**V2 Fix**: Enhance signature descriptions

```python
class PortionExtractor(dspy.Signature):
    """Extract food name and portion size from user input.

    CRITICAL: You MUST extract both fields. Never return None.
    If uncertain, make your best guess from the description.
    """
    food_description = dspy.InputField(
        desc="Food item with quantity (e.g., '60 gram rohu fish', '2 cucumbers')"
    )
    food_name = dspy.OutputField(
        desc="ONLY the food name without quantity (e.g., 'rohu fish', 'cucumbers'). "
             "REQUIRED: Cannot be None or empty. Extract the main food item."
    )
    portion_size = dspy.OutputField(
        desc="ONLY the portion with units (e.g., '60 gram', '2 cucumbers'). "
             "REQUIRED: Cannot be None or empty. Extract the quantity and unit."
    )
```

**Why**: Better descriptions → better LLM outputs → fewer None values

---

### PHASE 4: Add LLM-Based Inference Fallback (NEW CAPABILITY)

**Problem in V1**: When all APIs fail → returns None

**V2 Solution**: Use LLM to estimate nutrition from food name

```python
class NutritionEstimator(dspy.Signature):
    """Estimate nutritional values when database lookup fails.

    Use your knowledge of similar foods to provide reasonable estimates.
    Better to provide educated guess than no data.
    """
    food_name = dspy.InputField(desc="Name of food item")
    portion_description = dspy.InputField(desc="Portion size (e.g., '100g', '1 plate')")
    similar_foods_data = dspy.InputField(desc="JSON of similar foods from domain knowledge")

    estimated_nutrition = dspy.OutputField(
        desc="Estimated nutrition per 100g as JSON: {calories, carbs_g, protein_g, fat_g, fiber_g, sodium_mg, sugars_g}"
    )
    reasoning = dspy.OutputField(
        desc="Explain which similar foods you used and why"
    )
    confidence_score = dspy.OutputField(
        desc="0-100: How confident in this estimate?"
    )
```

**Integration Point**: In MedicalNutritionAgent.forward()

```python
# After trying all sources
if all_sources_empty:
    # Find similar foods in domain KB
    similar_foods = self._find_similar_foods(food_name)

    # Use LLM to estimate
    estimator = dspy.ChainOfThought(NutritionEstimator)
    estimate = estimator(
        food_name=food_name,
        portion_description=portion,
        similar_foods_data=json.dumps(similar_foods)
    )

    # Parse and use estimate
    estimated_data = json.loads(estimate.estimated_nutrition)
    # ... continue with estimated data
```

**Impact**: System ALWAYS returns some data, never completely empty

---

## NEW PITFALLS & EDGE CASES (V2 DISCOVERIES)

### PITFALL 11: LLM Non-Determinism at Temperature > 0

**What Goes Wrong**:
```
Run 1: food_name="rohu fish", portion="60 gram"
Run 2: food_name=None, portion=None  ← RANDOM FAILURE
Run 3: food_name="rohu", portion="60 gram piece"
```

**Why It Occurs**:
- temperature=0.3 introduces randomness
- LLM occasionally "forgets" to generate required fields
- No validation catches this until runtime crash

**How to Fix**:

1. **Set temperature=0.0 for extraction tasks**
```python
# For extraction/routing modules
llm_extraction = dspy.LM('ollama/qwen3:8b', temperature=0.0)

# For reasoning/creative tasks
llm_reasoning = dspy.LM('ollama/qwen3:8b', temperature=0.5)
```

2. **Add assertions** (see Phase 0.3)

3. **Use .get() with defaults**
```python
# ❌ UNSAFE
food_name = result.food_name

# ✅ SAFE
food_name = result.get('food_name', 'unknown_food')
```

**How to Test**:
```bash
# Run 10 times, must get same output
for i in {1..10}; do
    python test_pot.py | grep "Food name:"
done
# All outputs should be identical
```

---

### PITFALL 12: API Rate Limiting & Timeouts

**What Goes Wrong**:
```
OpenFoodFacts API: 100 requests/minute limit
After 100 foods: HTTP 429 "Too Many Requests"
System crashes instead of gracefully degrading
```

**Why It Occurs**:
- No rate limiting in V1
- No retry logic with exponential backoff
- No caching of API responses

**How to Fix**:

1. **Add caching**
```python
import functools
from cachetools import TTLCache

# Cache API responses for 24 hours
api_cache = TTLCache(maxsize=1000, ttl=86400)

@functools.lru_cache(maxsize=500)
def _query_openfoodfacts_cached(self, food_name: str) -> dict:
    cache_key = f"off_{food_name.lower()}"
    if cache_key in api_cache:
        return api_cache[cache_key]

    result = self._query_openfoodfacts(food_name, "")
    api_cache[cache_key] = result
    return result
```

2. **Add retry with exponential backoff**
```python
import time

def _query_openfoodfacts_with_retry(self, food_name: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            return self._query_openfoodfacts(food_name, "")
        except requests.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = (2 ** attempt) + random.random()
                print(f"  Rate limited, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                raise
    return {}  # All retries failed
```

**How to Test**:
```python
# Rapid-fire 150 requests
foods = ["food_" + str(i) for i in range(150)]
for food in foods:
    result = agent._query_openfoodfacts(food, "100g")
# Should handle rate limits gracefully
```

---

### PITFALL 13: Ambiguous Food Names (NEW)

**What Goes Wrong**:
```
Input: "2 mousumbi lemons"
OpenFoodFacts search: Returns Mexican limes
Expected: Indian sweet lime (mosambi)

Input: "water apples"
Returns: Data for apples (92 cal)
Expected: Rose apple/jambu (25 cal)
```

**Why It Occurs**:
- Regional food names not in global databases
- Spelling variations (mosambi vs mousumbi)
- Multiple foods with similar names

**How to Fix**:

1. **Add regional food mapping**
```python
class RegionalFoodMapper:
    REGIONAL_MAPPINGS = {
        "mousumbi": ["mosambi", "sweet lime", "citrus limetta"],
        "alu posto": ["aloo posto", "potato poppy seed curry"],
        "water apple": ["rose apple", "jambu", "syzygium aqueum"],
        "rohu": ["rohu fish", "labeo rohita", "rui fish"],
    }

    def normalize_food_name(self, input_name: str) -> list[str]:
        """Return list of search terms to try"""
        input_lower = input_name.lower()

        # Check mappings
        for canonical, variants in self.REGIONAL_MAPPINGS.items():
            if canonical in input_lower or any(v in input_lower for v in variants):
                return [canonical] + variants

        return [input_name]
```

2. **Try multiple search terms**
```python
def _query_openfoodfacts(self, food_name: str):
    mapper = RegionalFoodMapper()
    search_terms = mapper.normalize_food_name(food_name)

    for term in search_terms:
        result = self._api_search(term)
        if result:  # Found data
            return result

    return {}  # All terms failed
```

**How to Test**:
```python
test_cases = [
    ("mousumbi lemons", "mosambi"),
    ("water apples", "rose apple"),
    ("alu posto", "potato poppy")
]

for input_name, expected_match in test_cases:
    result = agent(food_name=input_name, portion="100g")
    assert expected_match in result.get('reasoning', '').lower()
```

---

### PITFALL 14: Portion Size Ambiguity

**What Goes Wrong**:
```
Input: "1 plate pav bhaji"
System estimates: 300g
User's actual plate: 500g (restaurant size)
Calorie error: 67% off!

Input: "2 bananas"
System estimates: 100g each (200g total)
User's bananas: 60g each (small variety)
Calorie error: 70% over!
```

**Why It Occurs**:
- "Plate" varies: 200g (small) to 500g (restaurant)
- "1 banana" varies: 60g (small) to 150g (large)
- No user confirmation of portion estimate

**How to Fix**:

1. **Return portion range, not single value**
```python
class PortionScaling(dspy.Signature):
    nutrition_per_100g = dspy.InputField(desc="Per 100g values")
    user_portion = dspy.InputField(desc="'1 plate', '2 bananas', etc")
    food_name = dspy.InputField(desc="Food for density estimate")

    # ✅ V2: Return ranges
    estimated_grams_min = dspy.OutputField(desc="Minimum grams in portion")
    estimated_grams_typical = dspy.OutputField(desc="Typical grams in portion")
    estimated_grams_max = dspy.OutputField(desc="Maximum grams in portion")

    # Nutrition for all three estimates
    scaled_nutrition_range = dspy.OutputField(
        desc="JSON with min/typical/max nutrition values"
    )
```

2. **Ask user for confirmation (interactive mode)**
```python
print(f"\nEstimated portion size: {typical_grams}g (range: {min_g}-{max_g}g)")
user_input = input("Is this correct? (y/n or enter actual grams): ")

if user_input.lower() == 'n' or user_input.isdigit():
    actual_grams = int(user_input) if user_input.isdigit() else None
    if actual_grams:
        # Recalculate with user's actual portion
        ...
```

**How to Test**:
```python
test_cases = [
    ("1 plate pav bhaji", 200, 300, 500),  # min, typical, max
    ("2 bananas", 120, 200, 300),
    ("1 cup rice", 150, 200, 250)
]

for portion, min_exp, typ_exp, max_exp in test_cases:
    result = scaler(portion=portion, food="test")
    assert min_exp <= result['estimated_grams_min'] <= min_exp * 1.2
    assert typ_exp <= result['estimated_grams_typical'] <= typ_exp * 1.2
```

---

### PITFALL 15: Medical Condition Overfitting

**What Goes Wrong**:
```
Input condition: "I have non alcoholic fatty liver, I am skinny fat,
                  I am an active sedentary person with regular gym but
                  I cannot show fitness on the ground..."

LLM output: Focuses ONLY on NAFLD, ignores cardiovascular issues

Expected: Should flag both liver stress AND cardio limitations
```

**Why It Occurs**:
- Complex medical descriptions get summarized
- LLM picks "most prominent" condition
- Misses interconnected health factors

**How to Fix**:

1. **Parse complex conditions into structured format**
```python
class MedicalConditionParser(dspy.Signature):
    """Parse complex medical description into structured conditions."""
    raw_description = dspy.InputField(
        desc="User's medical condition description"
    )

    primary_conditions = dspy.OutputField(
        desc="List of main medical conditions (e.g., ['NAFLD', 'hypertension'])"
    )
    secondary_factors = dspy.OutputField(
        desc="List of relevant factors (e.g., ['sedentary', 'heat intolerance'])"
    )
    dietary_goals = dspy.OutputField(
        desc="List of dietary goals (e.g., ['reduce liver fat', 'improve stamina'])"
    )
```

2. **Multi-condition medical adapter**
```python
def forward(self, nutrition_data, medical_description, food_name):
    # Parse complex description
    parser = dspy.ChainOfThought(MedicalConditionParser)
    parsed = parser(raw_description=medical_description)

    # Get advice for EACH condition
    all_warnings = []
    all_recommendations = []

    for condition in parsed.primary_conditions:
        advice = self._get_condition_advice(
            nutrition_data, condition, food_name
        )
        all_warnings.extend(advice['warnings'])
        all_recommendations.extend(advice['recommendations'])

    # Combine and prioritize
    return {
        'warnings': self._prioritize_warnings(all_warnings),
        'recommendations': all_recommendations
    }
```

**How to Test**:
```python
complex_condition = """
I have non alcoholic fatty liver, I am skinny fat,
I heat up and sweat very easily,
I cannot support my muscles with my heart and lungs for more than 10 minutes
"""

result = medical_adapter(
    nutrition_data={'carbs_g': 50, 'fat_g': 10},
    medical_description=complex_condition,
    food_name="pav bhaji"
)

# Must address BOTH liver AND cardiovascular
assert 'liver' in result['warnings'].lower()
assert any(word in result['warnings'].lower()
          for word in ['heart', 'cardiovascular', 'stamina', 'exercise'])
```

---

## V2 IMPLEMENTATION CHECKLIST

### Phase 0: Critical Fixes (DO THIS FIRST)
- [ ] Change temperature to 0.0 in test_pot.py
- [ ] Fix module calling: `.forward()` → `()`
- [ ] Add SafePortionExtractor with assertions
- [ ] Activate assertions: `.activate_assertions()`
- [ ] Test: Run 10 times, verify deterministic output

### Phase 1: Real API Integration
- [ ] Implement real OpenFoodFacts HTTP calls
- [ ] Implement real SearXNG integration
- [ ] Add caching with TTLCache
- [ ] Add retry logic with exponential backoff
- [ ] Test: Query 50 foods, verify data returned

### Phase 2: Expand Domain KB
- [ ] Add 40+ Indian foods to domain KB
- [ ] Add regional food name mapping
- [ ] Test: All test foods from user's example covered

### Phase 3: LLM-Based Fallback
- [ ] Create NutritionEstimator signature
- [ ] Integrate into MedicalNutritionAgent
- [ ] Test: Unknown food returns estimated data

### Phase 4: Portion Range Estimation
- [ ] Modify PortionScaling to return min/typical/max
- [ ] Add user confirmation in interactive mode
- [ ] Test: Portion estimates within 20% of actual

### Phase 5: Medical Condition Parsing
- [ ] Create MedicalConditionParser
- [ ] Update MedicalAdapterAgent for multi-condition
- [ ] Test: Complex conditions addressed fully

### Phase 6: End-to-End Validation
- [ ] Run full test_pot.py with real user input
- [ ] Verify: No None values in output
- [ ] Verify: Total calories reasonable (1000-2000 for meal)
- [ ] Verify: Medical warnings specific to conditions

---

## SUCCESS CRITERIA (V2)

Your implementation is PRODUCTION READY when:

1. **No None Values**
   ```bash
   python test_pot.py
   # Check output: ZERO instances of "None" in nutrition data
   ```

2. **Realistic Calorie Totals**
   ```
   User meal with rice + fish + vegetables + fruits
   Expected total: 1200-1800 calories
   NOT 1 calorie (V1 bug)
   ```

3. **Deterministic Extraction**
   ```bash
   for i in {1..10}; do python test_pot.py | grep "Food name"; done
   # All 10 runs: same food names extracted
   ```

4. **API Integration Working**
   ```bash
   python test_pot.py 2>&1 | grep "OpenFoodFacts"
   # Should show successful API calls, not "Mock implementation"
   ```

5. **Medical Warnings Specific**
   ```
   NAFLD patient eating rice (high carbs)
   Expected: Warning about carbs + liver fat
   NOT generic "eat healthy" advice
   ```

---

## REFERENCE: WHERE TO FIND ANSWERS (V2)

### For DSPy Best Practices
- **Module calling**: https://dspy.ai/api/modules/Module/
- **Assertions**: https://dspy.ai/learn/programming/7-assertions/
- **Temperature strategy**: https://dspy.ai/cheatsheet/
- **Prediction access**: https://dspy.ai/api/primitives/Prediction/

### For V1 Code to Modify
- **PortionExtractor**: test_pot.py lines 48-52
- **Module calling bug**: test_pot.py line 133
- **Temperature setting**: test_pot.py line 242
- **Mock API methods**: agents.py lines 188-202
- **Domain KB**: translators.py lines 189-253

### For Pitfall Solutions
- **Pitfall 11 (Non-determinism)**: V2 Phase 0
- **Pitfall 12 (Rate limiting)**: V2 Phase 1
- **Pitfall 13 (Ambiguous names)**: V2 Phase 2
- **Pitfall 14 (Portion ambiguity)**: V2 Phase 4
- **Pitfall 15 (Medical overfitting)**: V2 Phase 5

---

## ESTIMATED TIME (V2 FIXES ONLY)

| Phase | Task | Time |
|-------|------|------|
| 0 | Critical Fixes | 1-2 hours |
| 1 | Real API Integration | 2-3 hours |
| 2 | Expand Domain KB | 1 hour |
| 3 | LLM Fallback | 1-2 hours |
| 4 | Portion Ranges | 1-2 hours |
| 5 | Medical Parsing | 1-2 hours |
| **Total** | **V1 → V2 Upgrade** | **~8-12 hours** |

---

**V2 SUMMARY**: The V1 implementation had correct architecture but critical execution flaws. V2 fixes focus on:
1. Real data retrieval (not mocks)
2. Output validation (assertions)
3. Correct DSPy patterns (module calling, temperature)
4. Comprehensive fallback logic
5. Real-world edge cases (ambiguous foods, portion ranges, complex medical conditions)

These fixes transform the system from "architecturally correct but practically broken" to "production-ready nutrition analysis system."
