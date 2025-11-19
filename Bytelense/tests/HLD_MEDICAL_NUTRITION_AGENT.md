# Medical Nutrition Agentic System - High-Level Design

**Framework**: DSPy with Thin/Deep Agentic Layers
**Location**: `/Bytelense/tests/`
**Status**: Design & Implementation Planning

---

## EXECUTIVE SUMMARY

Build an **agentic nutrition system** that:

1. **Fetches** nutritional data from multiple sources (OpenFoodFacts, SearXNG, Domain Knowledge)
2. **Translates** raw API responses into standardized format
3. **Assesses** data quality (completeness, conflicts, reliability)
4. **Routes** to appropriate complexity level:
   - **Simple Path**: Good data → Simple CoT → Return result
   - **Hybrid Path**: Partial data → Infer missing → Return result
   - **Deep Path**: Conflicting data → Reason → Reconcile → Return result
5. **Personalizes** for medical conditions (diabetes, hypertension, etc.)

**Key Innovation**: Complexity is **data-driven**, not architecture-driven.

---

## PROBLEM STATEMENT: Current Output Issues

Your test run showed:

```bash
Tea:       ERROR - "No specific nutritional data found"
Chips:     EMPTY - {}
Pav Bhaji: CONFLICT - 406 vs 490 calories (no resolution)
```

**Root Cause**: No reasoning layer to:

- Infer missing data ("Tea = ~2 kcal black tea")
- Reconcile conflicts ("406 = shallow-fried, 490 = deep-fried")
- Adapt to context ("For diabetic, high carbs = warning")

---

## ARCHITECTURE: THREE-LAYER SYSTEM

```bash
┌─────────────────────────────────────────────────────────┐
│  USER: "1 plate pav bhaji" (diabetic)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  LAYER 1: THIN ORCHESTRATION AGENT                      │
│  • Parse input → Route to sources                       │
│  • Assess data quality                                  │
│  • Decide: simple_cot vs hybrid vs deep_reasoning       │
└────────────────────┬────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌──────────┐  ┌──────────────┐  ┌────────────────┐
│OpenFood  │  │SearXNG       │  │DomainKB        │
│Facts API │  │Search API    │  │(Category data) │
└─────┬────┘  └──────┬───────┘  └────────┬───────┘
      │              │                   │
      └──────────────┼───────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │ TRANSLATION LAYER (Response)    │
    │ • Normalize field names         │
    │ • Validate ranges               │
    │ • Identify missing fields       │
    │ • Detect conflicts              │
    └────────────────┬────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  LAYER 2: DEEP REASONING AGENTS                         │
│                                                         │
│  [Data Quality Agent]      → Assess completeness        │
│     ↓                                                   │
│  [Inference Agent]         → Infer missing values       │
│     ↓                                                   │
│  [Reconciliation Agent]    → Resolve conflicts          │
│     ↓                                                   │
│  [Scaling Agent]           → 100g → user portion        │
│     ↓                                                   │
│  [Medical Adapter Agent]   → Condition-specific         │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  OUTPUT: Reasoned Nutritional Data                      │
│  {                                                      │
│    "food": "pav bhaji",                                 │
│    "calories": 450,                                     │
│    "calories_range": [406, 490],                        │
│    "reasoning": "406=shallow-fried, 490=deep-fried.     │
│                  Selected 450 (medium estimate)",       │
│    "diabetes_warning": "High carbs (176g)",             │
│    "confidence": 0.72                                   │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

---

## LAYER 1: THIN ORCHESTRATION AGENT

### Purpose

Route data fetching and decide complexity level based on data quality.

### Signature

```python
class DataQualityAssessment(dspy.Signature):
    """Assess quality of raw nutritional data from all sources"""
    raw_sources = dspy.InputField(
        desc="Raw data from OpenFoodFacts, SearXNG, DomainKB"
    )
    food_name = dspy.InputField(desc="Food item (e.g., 'pav bhaji')")

    completeness_score = dspy.OutputField(
        desc="0-100: % of required fields present"
    )
    conflict_severity = dspy.OutputField(
        desc="0-100: How severe are data conflicts? "
             "100=major (406 vs 490), 0=none"
    )
    missing_fields = dspy.OutputField(
        desc="List of critical missing fields"
    )
    conflicts_found = dspy.OutputField(
        desc="List of conflicting values and sources"
    )
    recommended_path = dspy.OutputField(
        desc="'simple_cot' | 'hybrid' | 'deep_reasoning'"
    )
```

### Agent Implementation

```python
class ThinOrchestrationAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.assessor = dspy.Predict(DataQualityAssessment)

    def forward(self, raw_sources: list, food_name: str):
        """Decide routing based on data quality"""
        assessment = self.assessor(
            raw_sources=json.dumps(raw_sources),
            food_name=food_name
        )

        # Route decision
        if assessment.conflict_severity > 70:
            return {"path": "deep_reasoning", "reason": "High conflicts"}
        elif assessment.completeness_score > 80:
            return {"path": "simple_cot", "reason": "Complete data"}
        else:
            return {"path": "hybrid", "reason": "Partial data"}
```

---

## TRANSLATION LAYERS: REQUEST & RESPONSE

### REQUEST Translation (What to Ask)

```python
class OpenFoodFactsRequestTranslator:
    """Convert user input to OpenFoodFacts API call"""

    def translate(self, food_name: str, portion: str) -> dict:
        """
        Input: "pav bhaji", "1 plate"
        Output: API call parameters
        """
        return {
            "method": "text_search",
            "query": food_name,
            "fields": [
                "product_name",
                "energy_kcal_100g",
                "carbohydrates_100g",
                "proteins_100g",
                "fat_100g",
                "fiber_100g",
                "sodium_100g",
                "sugars_100g",
                "nutrition_grades"
            ],
            "context": {
                "portion_size": portion,
                "estimated_grams": self._estimate_grams(portion)
            }
        }

    def _estimate_grams(self, portion: str) -> int:
        """Convert portion description to grams"""
        estimates = {
            "plate": 300,
            "cup": 240,
            "bowl": 200,
            "packet": 35,
            "slice": 50
        }
        for key, grams in estimates.items():
            if key in portion.lower():
                return grams
        return 100  # default
```

### RESPONSE Translation (What We Got)

```python
class OpenFoodFactsResponseTranslator:
    """Convert raw API response to standardized format"""

    def translate(self, api_response: dict) -> dict:
        """
        Input: Raw OFF API response
        Output: Standardized nutrition schema
        """
        return {
            "source": "OpenFoodFacts",
            "product_name": api_response.get("product_name"),
            "nutrition_per_100g": {
                "calories": api_response.get("energy_kcal_100g"),
                "carbs_g": api_response.get("carbohydrates_100g"),
                "protein_g": api_response.get("proteins_100g"),
                "fat_g": api_response.get("fat_100g"),
                "fiber_g": api_response.get("fiber_100g"),
                "sodium_mg": api_response.get("sodium_100g") * 1000,
                "sugars_g": api_response.get("sugars_100g")
            },
            "metadata": {
                "completeness": self._calc_completeness(api_response),
                "missing_fields": self._get_missing(api_response),
                "reliability": 0.85  # Database source
            }
        }

    def _calc_completeness(self, data: dict) -> float:
        """% of expected fields present"""
        required = ["energy_kcal_100g", "carbohydrates_100g",
                    "proteins_100g", "fat_100g"]
        found = sum(1 for f in required if data.get(f))
        return (found / len(required)) * 100

    def _get_missing(self, data: dict) -> list:
        """List fields not in response"""
        required = ["sodium_100g", "sugars_100g", "fiber_100g"]
        return [f for f in required if not data.get(f)]
```

---

## LAYER 2: DEEP REASONING AGENTS

### Agent 1: Data Inference & Reconciliation

```python
class DataInferenceAndReconciliation(dspy.Signature):
    """Infer missing values and reconcile conflicts"""
    available_data = dspy.InputField(desc="What we have")
    missing_nutrients = dspy.InputField(desc="What's missing")
    food_name = dspy.InputField(desc="Food item")
    conflicting_values = dspy.InputField(desc="If conflicts exist")

    inferred_nutrition = dspy.OutputField(
        desc="Complete nutrition with inferred values marked"
    )
    inference_reasoning = dspy.OutputField(
        desc="Explain how missing values were estimated"
    )
    conflict_resolution = dspy.OutputField(
        desc="Which value chosen and why"
    )
    uncertainty = dspy.OutputField(
        desc="What remains uncertain?"
    )
    confidence = dspy.OutputField(desc="0-100 confidence")

class DeepInferenceAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.reasoner = dspy.ChainOfThought(
            DataInferenceAndReconciliation
        )

    def forward(self, available: dict, missing: list,
                food_name: str, conflicts: list):
        """Reason through missing data and conflicts"""
        return self.reasoner(
            available_data=json.dumps(available),
            missing_nutrients=json.dumps(missing),
            food_name=food_name,
            conflicting_values=json.dumps(conflicts)
        )
```

### Agent 2: Portion Scaling

```python
class PortionScaling(dspy.Signature):
    """Scale 100g data to user portion"""
    nutrition_per_100g = dspy.InputField(desc="Per 100g values")
    user_portion = dspy.InputField(desc="'1 plate', '1 cup', etc")
    food_name = dspy.InputField(desc="Food for density estimate")

    estimated_grams = dspy.OutputField(desc="How many grams in portion")
    scaled_nutrition = dspy.OutputField(desc="Nutrition in user portion")
    confidence = dspy.OutputField(desc="0-100 confidence in estimate")

class PortionScalingAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.scaler = dspy.Predict(PortionScaling)

    def forward(self, nutrition_100g: dict, portion: str, food: str):
        """Scale nutrition to user portion"""
        result = self.scaler(
            nutrition_per_100g=json.dumps(nutrition_100g),
            user_portion=portion,
            food_name=food
        )

        # Calculate scaled values
        scale_factor = float(result.estimated_grams) / 100.0
        scaled = {
            k: v * scale_factor if isinstance(v, (int, float)) else v
            for k, v in nutrition_100g.items()
        }

        return {
            "portion_grams": result.estimated_grams,
            "nutrition": scaled,
            "confidence": result.confidence
        }
```

### Agent 3: Medical Context Adaptation

```python
class MedicalContextAdapter(dspy.Signature):
    """Highlight health implications for condition"""
    nutrition_data = dspy.InputField(desc="Complete nutrition")
    food_name = dspy.InputField(desc="Food item")
    medical_condition = dspy.InputField(desc="'diabetes', 'hypertension', etc")

    relevant_nutrients = dspy.OutputField(
        desc="What matters for this condition"
    )
    warnings = dspy.OutputField(desc="Any concerning values")
    recommendations = dspy.OutputField(desc="How to make safer for this person")
    portion_suitability = dspy.OutputField(desc="Is portion size OK?")

class MedicalAdapterAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.adapter = dspy.Predict(MedicalContextAdapter)

    def forward(self, nutrition: dict, food: str, condition: str):
        """Adapt for medical context"""
        return self.adapter(
            nutrition_data=json.dumps(nutrition),
            food_name=food,
            medical_condition=condition
        )
```

---

## MAIN ORCHESTRATION FLOW

```python
class MedicalNutritionAgent(dspy.Module):
    def __init__(self):
        super().__init__()

        # Thin layer
        self.thin_assessor = ThinOrchestrationAgent()

        # Deep layer agents
        self.inference_agent = DeepInferenceAgent()
        self.scaling_agent = PortionScalingAgent()
        self.medical_agent = MedicalAdapterAgent()

        # Tool translators
        self.off_req = OpenFoodFactsRequestTranslator()
        self.off_res = OpenFoodFactsResponseTranslator()
        self.sxng_res = SearXNGResponseTranslator()
        self.kb_res = DomainKBResponseTranslator()

    def forward(self, food_name: str, portion: str,
                condition: str = None):
        """Main reasoning pipeline"""

        # STEP 1: Fetch from all sources
        print(f"Fetching data for: {food_name} ({portion})")
        sources = []

        # Try OpenFoodFacts
        try:
            off_req = self.off_req.translate(food_name, portion)
            off_raw = self._query_openfoodfacts(off_req)
            off_data = self.off_res.translate(off_raw)
            sources.append(off_data)
        except Exception as e:
            print(f"OpenFoodFacts error: {e}")

        # Try SearXNG
        try:
            sxng_raw = self._query_searxng(food_name)
            sxng_data = self.sxng_res.translate(sxng_raw)
            sources.append(sxng_data)
        except Exception as e:
            print(f"SearXNG error: {e}")

        # Try Domain KB
        try:
            kb_data = self._query_domain_kb(food_name)
            sources.append(kb_data)
        except Exception as e:
            print(f"Domain KB error: {e}")

        # STEP 2: Assess quality
        quality = self.thin_assessor.forward(sources, food_name)

        print(f"Data quality: {quality}")

        # STEP 3: Route based on quality
        if quality["path"] == "simple_cot":
            # Use best source directly
            return self._simple_path(sources)

        elif quality["path"] == "hybrid":
            # Infer missing + scale
            inferred = self.inference_agent.forward(
                available=sources[0],
                missing=quality.get("missing_fields", []),
                food_name=food_name,
                conflicts=quality.get("conflicts_found", [])
            )
            scaled = self.scaling_agent.forward(
                inferred.inferred_nutrition, portion, food_name
            )
            return scaled

        else:  # deep_reasoning
            # Full reasoning pipeline
            inferred = self.inference_agent.forward(
                available=self._merge_sources(sources),
                missing=quality.get("missing_fields", []),
                food_name=food_name,
                conflicts=quality.get("conflicts_found", [])
            )

            scaled = self.scaling_agent.forward(
                inferred.inferred_nutrition, portion, food_name
            )

            if condition:
                medical = self.medical_agent.forward(
                    scaled["nutrition"], food_name, condition
                )
                scaled["medical_context"] = medical

            return scaled

    def _simple_path(self, sources: list) -> dict:
        """Return best source data directly"""
        best = max(sources,
                   key=lambda x: x.get("metadata", {}).get("completeness", 0))
        return best

    def _merge_sources(self, sources: list) -> dict:
        """Combine data from multiple sources"""
        merged = {}
        for source in sources:
            for key, val in source.get("nutrition_per_100g", {}).items():
                if val and key not in merged:
                    merged[key] = val
        return merged
```

---

## EXAMPLE FLOWS

### Example 1: Tea (Simple Path)

```bash
Input: "1 cup tea" → Quality Assessment: completeness=95, conflicts=0
                 → Path: "simple_cot"

Flow:
- OpenFoodFacts: "black tea" → 1 kcal per 100ml
- Scale: 1 cup (240ml) → 2.4 kcal
- Return: {"calories": 2, "confidence": 0.95}
```

### Example 2: Chips (Hybrid Path)

```bash
Input: "1 packet chips" → Quality Assessment: completeness=50, conflicts=0
                       → Path: "hybrid"

Flow:
- OpenFoodFacts: calories=530 kcal/100g, sodium=missing, sugars=missing
- Inference Agent: infer sodium (~400mg per packet), sugars (~1g per packet)
- Scaling Agent: 35g packet → scale all values
- Return: {"calories": 185, "sodium": 400, "sugars": 1, "confidence": 0.75}
```

### Example 3: Pav Bhaji (Deep Path)

```bash
Input: "1 plate pav bhaji", condition="diabetic"
     → Quality Assessment: completeness=75, conflicts=HIGH
                        → Path: "deep_reasoning"

Flow:
- Multiple sources: OpenFoodFacts (350 kcal/100g),
                   SearXNG (406 vs 490 cal per plate)
- Inference Agent: "406=shallow-fried, 490=deep-fried.
                    Select 450 (middle). Infer sodium."
- Scaling Agent: 300g plate → scale all values
- Medical Adapter: "High carbs, warn diabetic, recommend fiber"
- Return: Complete reasoned output with warnings
```

---

## NEXT STEPS

1. **Create translation layer modules** in `/Bytelense/tests/`
2. **Implement deep reasoning agents** (DSPy modules)
3. **Build main orchestration** (ThinOrchestrationAgent)
4. **Integrate with test_pot.py** (replace nutrition search)
5. **Test with real examples** (tea, chips, pav bhaji)
6. **Optimize with DSPy optimizers** (if needed)

---

**Created**: 2025-11-19
**Purpose**: Design reference for implementation

---

## IMPLEMENTATION PITFALLS & EDGE CASES

### PITFALL 1: Translation Layer API Failures (Network Timeouts)

**What Goes Wrong**:

```bash
OpenFoodFactsRequestTranslator.translate() succeeds (creates request)
  → But API call times out (20+ seconds or connection error)
  → ResponseTranslator receives None or empty response
  → _calc_completeness() crashes on None values
  → Entire pipeline fails silently
```

**Why It Occurs**:

- Network latency in poor connections (3G, distant servers)
- API rate limiting (100+ requests/day from single IP)
- Food not in database (regional/local foods)
- OpenFoodFacts API downtime or version mismatch
- Ollama model responding slowly (>5 seconds)

**How to Find & Fix**:

1. Add explicit timeout handling with retry logic
2. Implement exponential backoff (wait 1s, 2s, 4s)
3. Mock API responses in unit tests
4. Test with artificially slow network (tc command)

**Testing It's Solved** (Not Just Patched):

```bash
# Test 1: Verify retry happens
python -c "
from unittest.mock import patch
from requests import Timeout
import timeout
translator = OpenFoodFactsRequestTranslator()
with patch('requests.get', side_effect=Timeout):
    result = translator.translate_with_retry('food', '1 plate')
assert result.get('error') == 'API timeout after 3 attempts'
"

# Test 2: Check it doesn't hang entire pipeline
timeout 10 python test_pot.py  # Must complete in 10s even with network issues

# Test 3: Verify graceful degradation (falls back to next source)
# See other sources used in output, not just error
```

---

### PITFALL 2: Response Validation - Null/Invalid Data

**What Goes Wrong**:

```bash
API returns: {"product_name": "Pav Bhaji"}  // Missing calories!
ResponseTranslator.translate() succeeds
  → nutrition_per_100g["calories"] = None
  → Later: PortionScalingAgent tries None * 3.0
  → TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'
  → System crashes
```

**Why It Occurs**:

- Database has incomplete entries (15-30% of food items)
- Different API versions return different schemas
- Data corruption in upstream database
- Type mismatch (string "350" vs int 350)
- Range violations (calories = -100 or 9999)

**How to Find & Fix**:

1. Validate required fields before processing
2. Coerce types safely (str→float with error handling)
3. Check numeric ranges (0-900 kcal/100g is valid)
4. Return error with raw response for debugging

**Testing It's Solved**:

```bash
# Test 1: Malformed response handling
python -c "
translator = OpenFoodFactsResponseTranslator()
malformed = {'product_name': 'Food'}  # No calories
result = translator.translate(malformed)
assert 'error' in result and 'Missing critical fields' in result['error']
"

# Test 2: Type coercion
malformed_types = {
    'product_name': 123,  # should be string
    'energy_kcal_100g': 'three hundred',  # should be numeric
}
# Must not crash, must log/report error gracefully

# Test 3: Fuzzing - random invalid data
for _ in range(100):
    random_data = {k: random.randint(-1000, 10000) for k in ['energy_kcal_100g']}
    result = translator.translate(random_data)
    # Must never crash, always return error or valid data
```

---

### PITFALL 3: Routing Logic - Multiple Source Conflicts

**What Goes Wrong**:

```bash
source1 = {completeness: 95, conflicts: 0}      → "simple_cot"
source2 = {completeness: 40, conflicts: 100}    → "deep_reasoning"
source3 = {completeness: 60, conflicts: 20}     → "hybrid"

ThinOrchestrationAgent must choose ONE path
But current code assesses each source individually!
Result: Non-deterministic routing (different path on different runs)
```

**Why It Occurs**:

- Design assumes one quality assessment, but multiple sources have different qualities
- No prioritization (OFF > SearXNG > KB)
- DSPy LLM response varies (temperature > 0)
- No deterministic tie-breaking logic
- No version control on routing prompts

**How to Find & Fix**:

1. Sort sources by reliability (priority: OFF > SearXNG > KB)
2. Calculate weighted quality score
3. Use temperature=0 for deterministic routing
4. Version control all prompts explicitly
5. Add unit tests for determinism

**Testing It's Solved**:

```bash
# Test 1: Determinism - Same input → Same output
python -c "
results = set()
for i in range(10):
    result = agent.forward(sources, 'pav bhaji')
    results.add(result['path'])
assert len(results) == 1, f'Non-deterministic: {results}'
"

# Test 2: Weighted scoring
# Low quality source1 + High quality source2 should follow source2
# Must not flip-flop between paths

# Test 3: Source priority
# When all sources have same quality, should pick highest priority
# OFF > SearXNG > KB
```

---

### PITFALL 4: Deep Inference Agent - LLM Hallucination

**What Goes Wrong**:

```bash
Input: food_name="xyz_fictional_food"
LLM invents: "Based on similar foods, xyz probably has 300 kcal/100g"
Output contains made-up data, not reasoning!

Result: Patient gets fake nutritional info → health risk
```

**Why It Occurs**:

- LLM tries to be helpful, fills gaps with plausible-sounding data
- No grounding mechanism to validate inferences
- Confidence scores not penalized for pure invention
- Instructions don't explicitly forbid fabrication
- No domain knowledge base to check against

**How to Find & Fix**:

1. Add explicit "CANNOT_INFER" markers when confidence low
2. Require LLM to cite BASIS ("similar to apple")
3. Validate inferences against domain knowledge
4. Set confidence=0 for pure guesses
5. Use ChainOfThought to show reasoning steps

**Testing It's Solved**:

```bash
# Test 1: Hallucination detection
python -c "
agent = DeepInferenceAgent()
result = agent.forward(
    available={},
    missing=['fiber'],
    food_name='xyz_fictional_12345',
    category='unknown'
)
# Should have 'CANNOT_INFER', not invented number
assert 'CANNOT_INFER' in str(result) or result['confidence'] == 0
"

# Test 2: Cite basis
# Every inferred value must show why (e.g., 'similar to apple')
output = str(result)
assert 'BASIS:' in output or 'similar' in output.lower()

# Test 3: Validation against domain KB
# Inferred values should be within known ranges for food category
```

---

### PITFALL 5: Portion Scaling - Wrong Gram Estimates

**What Goes Wrong**:

```bash
User: "1 plate pav bhaji"
System estimates: 300g (reasonable)
Actual user portion: 500g (generous) or 150g (light)

Result: Calories off by 50-200%!
  "50g": 225 kcal
  "300g": 1350 kcal  ← 6x difference!
  "500g": 2250 kcal
```

**Why It Occurs**:

- "Plate" size varies: US plate ≠ Indian thali ≠ restaurant plate
- Cultural differences in portion sizes
- No feedback loop to correct estimates
- System has no way to know user's actual portion
- Fried foods denser than expected

**How to Find & Fix**:

1. Use range estimates, not point estimates (min/typical/max)
2. Collect real data on portion sizes (crowd-source)
3. Ask user for confirmation post-calculation
4. Account for food-specific density adjustments
5. Show uncertainty bounds in output

**Testing It's Solved**:

```bash
# Test 1: Range accuracy
python -c "
agent = PortionScalingAgent()
result = agent.forward({'calories': 100}, '1 plate', 'pav bhaji')
# Output must have portion_range, not single estimate
assert 'portion_range' in result
assert result['portion_range'][0] < result['portion_range'][1]
"

# Test 2: Compare against measured data
# Collect 50 real user portion sizes for common items
# System estimate must be within 20% of actual median

# Test 3: User feedback loop
# After calculation, ask "Is 300g correct?"
# Track corrections and update estimates
```

---

### PITFALL 6: Medical Adapter - Generic Advice Not Condition-Specific

**What Goes Wrong**:

```bash
Input: condition="diabetic", carbs=175g
Bad output: "This is a healthy food with good nutrients"
Good output: "HIGH CARB WARNING for diabetic.
            175g carbs = 3x daily recommended (60g).
            Risk of blood sugar spike."

Result: Patient ignores warning, has medical emergency
```

**Why It Occurs**:

- LLM doesn't understand medical thresholds
- No integration with guidelines (WHO, ADA, etc)
- Condition term is vague (type 1 vs 2 diabetes? Mild vs severe?)
- No severity level specified
- Generic nutrition advice doesn't translate to medical advice

**How to Find & Fix**:

1. Hard-code medical guideline thresholds
2. Require condition severity level (mild/moderate/severe)
3. Cross-reference against medical databases
4. Add medical review step
5. Include liability disclaimers everywhere

**Testing It's Solved**:

```bash
# Test 1: Condition-specific advice
python -c "
agent = MedicalAdapterAgent()
nutrition = {'carbs_g': 175, 'sodium_mg': 500}

result_diabetic = agent.forward(nutrition, 'pav bhaji', 'diabetes')
result_hyper = agent.forward(nutrition, 'pav bhaji', 'hypertension')

# Same food, different conditions = different warnings
assert 'carbs' in str(result_diabetic).lower()
assert 'carbs' not in str(result_hyper).lower()
"

# Test 2: Medical review
# Doctor validates all recommendations

# Test 3: Threshold accuracy
# Check against published guidelines (ADA, WHO)
```

---

### PITFALL 7: Integration Test Failures - Type Mismatches

**What Goes Wrong**:

```bash
ThinOrchestrationAgent output: {"path": "hybrid", ...}
DeepInferenceAgent expects: dict with nutrition_per_100g
But receives: DeepInferenceAgent expects: dict with nutrition_per_100g
But receives: NutritionData object (type mismatch!)

PortionScalingAgent tries: float(nutrition[key])
But receives: None (type error!)

MedicalAdapterAgent crashes on unexpected input format
```

**Why It Occurs**:

- No shared data schema across components
- Components developed independently
- Output format of one ≠ input format of next
- No serialization/deserialization tests
- Type hints missing or incorrect

**How to Find & Fix**:

1. Define strict data contracts (TypedDict, Pydantic)
2. Validate at component boundaries
3. Add comprehensive integration tests
4. Use adapter pattern if schemas differ
5. Type-check with mypy

**Testing It's Solved**:

```bash
# Test 1: Contract validation
python -c "
from typing import TypedDict
class NutritionData(TypedDict):
    calories: float
    carbs_g: float | None

# Each component must validate output matches contract
agent1_output = agent1.forward(...)
validate_contract(agent1_output, NutritionData)
"

# Test 2: Full pipeline integration
python test_integration.py  # 100 runs, all components together

# Test 3: Type checking
mypy --strict bytelense/tests/agents.py  # 0 errors
```

---

### PITFALL 8: Performance Degradation - Slow Response Time

**What Goes Wrong**:

```bash
Sequential API calls:
  OpenFoodFacts: 5s
  SearXNG: 5s
  Domain KB: 1s
  Total: 11 seconds per food item!

User waiting > 10s is unacceptable for real-time nutrition app
```

**Why It Occurs**:

- Current design fetches from all sources sequentially
- No early exit (stop after good data found)
- LLM inference adds 2-5 seconds per call
- No caching mechanism
- No parallelization

**How to Find & Fix**:

1. Parallelize API calls (asyncio, ThreadPoolExecutor)
2. Implement early exit (stop if confidence > 90%)
3. Add result caching (with TTL)
4. Profile bottlenecks (cProfile)
5. Async/await for concurrent operations

**Testing It's Solved**:

```bash
# Test 1: Performance benchmark
python -c "
import time
start = time.time()
result = agent.forward('tea', '1 cup')
elapsed = time.time() - start
assert elapsed < 3.0, f'Response took {elapsed}s, goal is <3s'
"

# Test 2: Load test
python -c "
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(agent.forward, foods * 10)
    # All 100 requests complete, no timeouts
"

# Test 3: Profile to identify bottleneck
python -m cProfile -s cumtime test_pot.py
# Shows which function takes longest
```

---

### PITFALL 9: DSPy Configuration Drift - Non-Determinism

**What Goes Wrong**:

```bash
Run 1: ThinOrchestrationAgent("pav bhaji") → "deep_reasoning"
Run 2: Same input → "simple_cot"
Run 3: Same input → "hybrid"

Result: Same food processed differently each time!
Unreproducible and unpredictable.
```

**Why It Occurs**:

- temperature > 0 introduces randomness
- Prompt wording changes affect LLM output
- Model version updates change behavior
- No seed/version control on prompts
- Missing configuration documentation

**How to Find & Fix**:

1. Use temperature=0.0 for deterministic routing
2. Explicitly seed random generators
3. Version control all prompts
4. Document configuration
5. Test for consistency across runs

**Testing It's Solved**:

```bash
# Test 1: Determinism verification
python -c "
results = []
for i in range(10):
    result = agent.forward('pav bhaji', '1 plate')
    results.append(result['path'])

unique_paths = set(results)
assert len(unique_paths) == 1, f'Non-deterministic: {unique_paths}'
print(f'✓ All 10 runs returned: {results[0]}')
"

# Test 2: Version control
# git log bytelense/tests/agents.py
# Every change to signature must be documented

# Test 3: Configuration lock
# LLM config = temperature:0.0, seed:42, model:version-X
# Document and test against changes
```

---

### PITFALL 10: Medical Data Liability - Dangerous Advice

**What Goes Wrong**:

```bash
System: "Your meal has 50mg sodium, safe for hypertensive"
Reality: Patient is on dialysis stage 5 (limit: <1000mg/day!)
Result: Patient ignores doctor's strict diet, has medical emergency

Legal consequence: Bytelense faces lawsuit for medical liability
```

**Why It Occurs**:

- System doesn't know condition severity (stage 1 vs 5 kidney disease)
- No understanding of drug interactions
- Generic guidelines don't apply to all patients
- No integration with patient's actual medical records
- Assumption of "one size fits all" nutrition advice

**How to Find & Fix**:

1. NEVER give absolute medical advice
2. Require patient context (medications, test results, condition stage)
3. Add LIABILITY DISCLAIMERS everywhere
4. Flag conditions requiring professional guidance
5. Integrate with medical databases (CMS, FDA)
6. Get legal review before deployment

**Testing It's Solved**:

```bash
# Test 1: Serious conditions require professional review
python -c "
agent = MedicalAdapterAgent()
result = agent.forward({}, 'food', 'kidney_disease')
assert 'REQUIRES_PROFESSIONAL_REVIEW' in str(result)
assert 'healthcare provider' in str(result).lower()
"

# Test 2: Liability disclaimer present
# Every output must include disclaimer language

# Test 3: Medication interaction check
result = agent.forward({}, 'food', 'diabetes', medications=['metformin'])
# Must flag potassium interaction with certain foods

# Test 4: Legal review
# Lawyer reads all outputs, confirms disclaimer adequacy
```

---

## COMPREHENSIVE TESTING CHECKLIST

### Unit Tests (Individual Components)

```bash
✓ test_translation_layer_timeout_retry.py
  - API timeout triggers retry
  - Exponential backoff works
  - Fallback to next source after 3 failures

✓ test_response_translator_validation.py
  - Missing required fields detected
  - Type coercion handled safely
  - Invalid ranges rejected
  - Error messages helpful

✓ test_thin_agent_determinism.py
  - 10 runs same input = same output
  - All paths (simple/hybrid/deep) testable
  - Source priority respected (OFF > SearXNG > KB)

✓ test_inference_agent_no_hallucination.py
  - "CANNOT_INFER" used for unknowns
  - Inferences cite basis
  - Confidence scores realistic
  - Domain knowledge validates estimates

✓ test_portion_scaling_uncertainty.py
  - Range estimates provided (min/typical/max)
  - Uncertainty quantified
  - Food-specific adjustments applied
  - User feedback loop works

✓ test_medical_adapter_specificity.py
  - Same food → different advice per condition
  - Warnings condition-specific, not generic
  - Thresholds match medical guidelines
  - Disclaimers present

✓ test_integration_full_pipeline.py
  - 100 runs through entire pipeline
  - No crashes, all outputs valid
  - Data contracts validated
  - Type errors caught

✓ test_edge_cases_unknown_food.py
  - Fictional food handled gracefully
  - No crashes, clear error messages
  - Fallback to next source
  - Reasonable confidence scores

✓ test_performance_response_time.py
  - Response < 3 seconds
  - Parallelization working
  - No bottlenecks
  - Load test passes (10 concurrent)

✓ test_medical_safety_liability.py
  - All disclaimers present
  - No absolute medical claims
  - Serious conditions flagged
  - Legal language reviewed
```

### Integration Tests (Full Flows)

```bash
✓ test_e2e_tea_simple_path.py
  - Input: "1 cup tea"
  - Path: "simple_cot"
  - Output: 2-20 kcal (reasonable range for tea)
  - Confidence: >90%

✓ test_e2e_chips_hybrid_path.py
  - Input: "1 packet chips"
  - Path: "hybrid" (partial data)
  - Inferred: sodium, sugars
  - Confidence: 70-80%

✓ test_e2e_pav_bhaji_deep_path.py
  - Input: "1 plate pav bhaji", diabetes
  - Path: "deep_reasoning" (conflicts: 406 vs 490)
  - Reconciled to: 450 kcal
  - Medical: high carbs warning
  - Confidence: 65-75%
```

---

## SIGN-OFF CHECKLIST FOR IMPLEMENTERS

**Before marking implementation DONE, verify ALL below**:

### Code Quality

- [ ] All functions have docstrings (format: Google style)
- [ ] Type hints used throughout (Python 3.9+ syntax)
- [ ] No TODO comments left
- [ ] Linting: `flake8 --max-line-length=120` passes
- [ ] Style: `black --line-length=120` formatted

### Testing

- [ ] Unit tests: 10/10 passing
- [ ] Integration tests: 3/3 passing
- [ ] Code coverage: >80% (check with `coverage.py`)
- [ ] Edge cases documented
- [ ] No silent failures (all errors logged)

### Performance

- [ ] Response time: <3 seconds per food
- [ ] API calls: parallelized (not sequential)
- [ ] Caching: implemented with TTL
- [ ] Memory: profiled, no leaks
- [ ] Load: 10 concurrent requests OK

### Medical Safety

- [ ] All outputs include disclaimers
- [ ] No absolute medical claims
- [ ] Serious conditions: "REQUIRES_PROFESSIONAL_REVIEW"
- [ ] Drug interactions: checked
- [ ] Legal review: completed by lawyer

### Documentation

- [ ] All signatures documented
- [ ] Error messages: helpful and specific
- [ ] Examples: 3+ for each path
- [ ] README: updated with usage
- [ ] This HLD: updated with actual findings

### Deployment Ready

- [ ] Environment variables: configured
- [ ] API keys: secure (no hardcoded)
- [ ] Logging: structured, searchable
- [ ] Error monitoring: enabled (Sentry/DataDog)
- [ ] Rollback plan: documented

---

**Last Updated**: 2025-11-19
**Purpose**: Pitfalls & testing guide for implementers
