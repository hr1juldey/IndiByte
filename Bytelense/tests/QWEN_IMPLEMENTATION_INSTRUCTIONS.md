# Instructions for Qwen: Implement Medical Nutrition Agentic System

**Start Here**: Read this file first. It tells you exactly what to do and where to find answers.

---

## QUICK START (Read This First)

### Your Job

Build a medical nutrition analysis system using DSPy with three layers:

1. **Thin Layer** - Orchestration & routing
2. **Translation Layers** - Convert API data to standard format
3. **Deep Layer** - Reasoning agents for missing data & conflicts

### Where Everything Is Located

```bash
/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/tests/
├── HLD_MEDICAL_NUTRITION_AGENT.md          ← READ THIS FIRST (full design)
├── QWEN_IMPLEMENTATION_INSTRUCTIONS.md     ← You are here
├── test_pot.py                             ← Your target to integrate with
├── agents.py                               ← YOU WILL CREATE THIS
├── translators.py                          ← YOU WILL CREATE THIS
└── test_agents.py                          ← YOU WILL CREATE THIS
```

### What You Need to Do (High Level)

1. Create translation layers for API data normalization
2. Create thin orchestration agent for routing
3. Create deep reasoning agents for inference/reconciliation/scaling/medical
4. Integrate with test_pot.py (replace NutritionalSearch with new agents)
5. Write tests to verify everything works
6. Check off the sign-off checklist

### Expected Time

- Translation layers: 2-3 hours
- Thin agent: 1 hour
- Deep agents: 3-4 hours
- Integration: 1-2 hours
- Testing: 2-3 hours
- **Total: ~12-15 hours**

---

## DETAILED IMPLEMENTATION ROADMAP

### PHASE 1: Translation Layers (Start Here)

**Purpose**: Convert raw API responses into standard format

**What to Create**: File `translators.py`

**Reference**: HLD Section "TRANSLATION LAYERS: REQUEST & RESPONSE" (Lines 167-256)

**Step 1.1: OpenFoodFacts Request Translator**

- Location: HLD line 172-213
- Copy the code template from HLD
- Implement `translate()` method
- Implement `_estimate_grams()` helper

**Step 1.2: OpenFoodFacts Response Translator**

- Location: HLD line 218-256
- Implement `translate()` method
- Implement `_calc_completeness()` helper
- Implement `_get_missing()` helper
- **IMPORTANT**: Handle None values (see PITFALL 2 in HLD line 601-648)

**Step 1.3: SearXNG Response Translator**

- Location: HLD (similar pattern to OpenFoodFacts)
- Parse web search results into standard format
- Extract numeric values using regex
- Identify conflicting values
- Return standardized output

**Step 1.4: Domain Knowledge Base Translator**

- Location: HLD (for fallback data)
- Map food names to categories
- Provide typical nutritional ranges
- Mark uncertainty levels

**Testing**: Run the tests from HLD line 627-648

```bash
cd /Bytelense/tests
python -m pytest test_agents.py::test_response_translator_validation -v
```

**How to Know It's Working**:

- No crashes on malformed data
- All required fields present in output
- Completeness score calculated correctly
- Missing fields identified
- Error messages helpful

---

### PHASE 2: Thin Orchestration Agent (1-2 hours)

**Purpose**: Route to simple_cot vs hybrid vs deep_reasoning based on data quality

**What to Create**: First part of `agents.py`

**Reference**: HLD Section "LAYER 1: THIN ORCHESTRATION AGENT" (Lines 107-163)

**Step 2.1: Define DataQualityAssessment Signature**

- Location: HLD line 116-139
- Copy the signature definition
- Add all InputField and OutputField definitions

**Step 2.2: Implement ThinOrchestrationAgent**

- Location: HLD line 144-162
- Create `__init__()` method with dspy.Predict(DataQualityAssessment)
- Implement `forward()` method
- Add routing logic:
  - If conflict_severity > 70 → "deep_reasoning"
  - Elif completeness_score > 80 → "simple_cot"
  - Else → "hybrid"

**Testing**: Run test from HLD line 680-688

```bash
python -m pytest test_agents.py::test_thin_agent_determinism -v
```

**How to Know It's Working**:

- Same input always produces same output (run 10 times)
- All three paths (simple/hybrid/deep) can be triggered with right input
- Scores between 0-100

**CRITICAL PITFALL**: See HLD line 652-697 (Pitfall #3 - Routing Conflicts)

- Must handle multiple sources with different quality levels
- Use weighted scoring if multiple sources
- Always deterministic (temperature=0.0)

---

### PHASE 3: Deep Reasoning Agents (3-4 hours)

**Purpose**: Infer missing data, reconcile conflicts, scale portions, adapt for medical conditions

**What to Create**: Rest of `agents.py`

**Reference**: HLD Section "LAYER 2: DEEP REASONING AGENTS" (Lines 260-372)

**Step 3.1: Data Inference & Reconciliation Agent**

- Location: HLD line 265-301
- Define `DataInferenceAndReconciliation` signature (line 265-284)
- Implement `DeepInferenceAgent` (line 286-301)
- Use `dspy.ChainOfThought` for reasoning steps
- **CRITICAL PITFALL**: See HLD line 701-748 (Pitfall #4 - Hallucination)
  - Require "CANNOT_INFER" when confidence low
  - Require "BASIS:" citations for inferences
  - Set confidence=0 for pure guesses

**Step 3.2: Portion Scaling Agent**

- Location: HLD line 307-341
- Define `PortionScaling` signature (line 307-315)
- Implement `PortionScalingAgent` (line 317-341)
- **CRITICAL PITFALL**: See HLD line 752-798 (Pitfall #5 - Wrong Estimates)
  - Return range (min/typical/max), not single value
  - Account for food density variations
  - Quantify uncertainty

**Step 3.3: Medical Context Adapter Agent**

- Location: HLD line 347-371
- Define `MedicalContextAdapter` signature (line 347-358)
- Implement `MedicalAdapterAgent` (line 360-371)
- **CRITICAL PITFALL**: See HLD line 802-849 (Pitfall #6 - Generic Advice)
  - Hard-code medical thresholds (WHO, ADA guidelines)
  - Make advice CONDITION-SPECIFIC (diabetes ≠ hypertension)
  - Add liability disclaimers

**Testing**: Run tests from HLD line 1079-1095

```bash
python -m pytest test_agents.py::test_inference_agent_no_hallucination -v
python -m pytest test_agents.py::test_portion_scaling_uncertainty -v
python -m pytest test_agents.py::test_medical_adapter_specificity -v
```

**How to Know It's Working**:

- Inference: Only infers when BASIS can be cited
- Scaling: Returns range with confidence interval
- Medical: Same food gets different advice per condition

---

### PHASE 4: Main Orchestration (1-2 hours)

**Purpose**: Tie everything together

**What to Create**: `MedicalNutritionAgent` class in `agents.py`

**Reference**: HLD Section "MAIN ORCHESTRATION FLOW" (Lines 379-486)

**Step 4.1: Initialize All Components**

- Location: HLD line 380-395
- Create instances of all agents
- Create instances of all translators
- Set up LLM configuration (temperature=0.0, seed=42)

**Step 4.2: Implement Forward Method**

- Location: HLD line 397-471
- Step 1: Fetch from all sources (parallel if possible)
- Step 2: Translate responses to standard format
- Step 3: Assess quality
- Step 4: Route to appropriate complexity
- Step 5: Return reasoned output

**Step 4.3: Implement Helper Methods**

- `_simple_path()` - Return best source directly
- `_merge_sources()` - Combine data from multiple sources
- `_query_openfoodfacts()` - Call OpenFoodFacts API with retry
- `_query_searxng()` - Call SearXNG with error handling
- `_query_domain_kb()` - Lookup domain knowledge

**Testing**: Run end-to-end tests

```bash
python -m pytest test_agents.py::test_e2e_tea_simple_path -v
python -m pytest test_agents.py::test_e2e_chips_hybrid_path -v
python -m pytest test_agents.py::test_e2e_pav_bhaji_deep_path -v
```

**How to Know It's Working**:

- Tea → simple_cot → 2-20 kcal, >90% confidence
- Chips → hybrid → sodium/sugars inferred, 70-80% confidence
- Pav Bhaji → deep_reasoning → 406-490 reconciled to 450, medical warning

**CRITICAL PITFALL**: See HLD line 853-901 (Pitfall #7 - Integration Failures)

- Define strict data contracts (TypedDict)
- Validate at component boundaries
- Type check with mypy before testing

---

### PHASE 5: Integration with test_pot.py (1-2 hours)

**Purpose**: Replace old NutritionalSearch with new agents

**What to Modify**: `/Bytelense/tests/test_pot.py`

**Current Code** (Lines 149-154):

```python
search_result = self.search_react(food_item=food_name)
nutritional_info_str = getattr(search_result, 'nutritional_info', '...')
nutritional_data[food_name] = nutritional_info_str
```

**Replace With**:

```python
# Use new MedicalNutritionAgent
nutrition_result = self.nutrition_agent.forward(
    food_name=food_name,
    portion=portion_size,
    condition=medical_condition  # Add from user input
)
nutritional_data[food_name] = nutrition_result
```

**Steps**:

1. Import MedicalNutritionAgent at top of test_pot.py
2. In CalorieQualityProgram.**init**, create:

   ```python
   self.nutrition_agent = MedicalNutritionAgent()
   ```

3. Replace NutritionalSearch logic with nutrition_agent.forward()
4. Add medical_condition parameter to main function
5. Test that it still works

**Testing**: Run full test_pot.py

```bash
cd /Bytelense/tests
python test_pot.py
# Should show improved output for tea, chips, pav bhaji
```

---

### PHASE 6: Write Tests (2-3 hours)

**Purpose**: Verify all 10 pitfalls are handled

**What to Create**: File `test_agents.py`

**Reference**: HLD Section "COMPREHENSIVE TESTING CHECKLIST" (Lines 1058-1143)

**Required Tests** (10 unit + 3 integration = 13 minimum):

```python
# Unit Tests
def test_translation_layer_timeout_retry():
    # From HLD line 581-590
    pass

def test_response_translator_validation():
    # From HLD line 627-648
    pass

def test_thin_agent_determinism():
    # From HLD line 680-688
    pass

def test_inference_agent_no_hallucination():
    # From HLD line 727-748
    pass

def test_portion_scaling_uncertainty():
    # From HLD line 781-798
    pass

def test_medical_adapter_specificity():
    # From HLD line 830-842
    pass

def test_integration_full_pipeline():
    # From HLD line 1097-1101
    pass

def test_edge_cases_unknown_food():
    # From HLD line 1103-1107
    pass

def test_performance_response_time():
    # From HLD line 1109-1113
    pass

def test_medical_safety_liability():
    # From HLD line 1115-1119
    pass

# Integration Tests
def test_e2e_tea_simple_path():
    # From HLD line 1125-1129
    pass

def test_e2e_chips_hybrid_path():
    # From HLD line 1131-1135
    pass

def test_e2e_pav_bhaji_deep_path():
    # From HLD line 1137-1142
    pass
```

**How to Run**:

```bash
cd /Bytelense/tests
python -m pytest test_agents.py -v --tb=short
# Target: All 13 tests pass
# Target: >80% code coverage
```

---

## WHERE TO FIND ANSWERS

### For Design Questions

**File**: `/Bytelense/tests/HLD_MEDICAL_NUTRITION_AGENT.md`

- "How should routing work?" → Section "LAYER 1" (line 107-163)
- "What is translation layer?" → Section "TRANSLATION LAYERS" (line 167-256)
- "How do inference agents work?" → Section "LAYER 2" (line 260-372)
- "What are example flows?" → Section "EXAMPLE FLOWS" (line 491-533)

### For Code Templates

**File**: Same HLD document, code blocks in each section

- `class DataQualityAssessment(dspy.Signature):` → Line 116-139
- `class ThinOrchestrationAgent(dspy.Module):` → Line 144-162
- `class OpenFoodFactsRequestTranslator:` → Line 172-213
- All other classes follow same pattern

### For Edge Cases & How to Handle Them

**File**: `/Bytelense/tests/HLD_MEDICAL_NUTRITION_AGENT.md` Section "IMPLEMENTATION PITFALLS & EDGE CASES"

- API timeouts? → Pitfall #1 (line 555-597)
- Invalid data? → Pitfall #2 (line 601-648)
- Routing conflicts? → Pitfall #3 (line 652-697)
- LLM hallucination? → Pitfall #4 (line 701-748)
- Portion estimates wrong? → Pitfall #5 (line 752-798)
- Generic medical advice? → Pitfall #6 (line 802-849)
- Type mismatches? → Pitfall #7 (line 853-901)
- Slow responses? → Pitfall #8 (line 905-954)
- Non-deterministic? → Pitfall #9 (line 958-1005)
- Medical liability? → Pitfall #10 (line 1009-1054)

**For each pitfall, document shows**:

- What goes wrong
- Why it occurs
- How to fix
- Test code to verify it's fixed

### For Testing

**File**: `/Bytelense/tests/HLD_MEDICAL_NUTRITION_AGENT.md` Section "COMPREHENSIVE TESTING CHECKLIST"

- Unit test templates → Line 1063-1120
- Integration test templates → Line 1125-1142
- Sign-off checklist → Line 1147-1191

### For Current Code to Understand

**File**: `/Bytelense/tests/test_pot.py`

- How PortionExtractor works → Line 56-60
- How NutritionalSearch signature works → Line 62-65
- How ReAct is used → Line 99-103
- Where to integrate new agents → Line 149-154

### For Medical Guidelines

- Diabetes: ADA (American Diabetes Association) guidelines
  - Daily carbs: 130g recommended
  - Per meal: max 50g
- Hypertension: AHA guidelines
  - Daily sodium: <2300mg
  - Per meal: <600mg
- Kidney disease: KDIGO guidelines
  - Varies by stage (1-5)
  - Consult nephrologist for exact limits

---

## HOW TO RUN YOUR CODE

### Before You Start

1. Make sure Ollama is running:

   ```bash
   ollama serve
   # Should show "listening on 127.0.0.1:11434"
   ```

2. Make sure SearXNG is running:

   ```bash
   sudo systemctl status searxng-docker
   # Should show "active (running)"
   ```

### While Developing (Test Individual Components)

```bash
# Test translations layer
python -c "from translators import OpenFoodFactsResponseTranslator; t = OpenFoodFactsResponseTranslator(); print('OK')"

# Test thin agent
python -c "from agents import ThinOrchestrationAgent; a = ThinOrchestrationAgent(); print('OK')"

# Test full pipeline
python -c "from agents import MedicalNutritionAgent; a = MedicalNutritionAgent(); result = a.forward('tea', '1 cup'); print(result)"
```

### After Implementation (Run Tests)

```bash
cd /Bytelense/tests

# Run all tests
python -m pytest test_agents.py -v

# Run specific test
python -m pytest test_agents.py::test_thin_agent_determinism -v

# Run with coverage
python -m pytest test_agents.py --cov=. --cov-report=html
```

### Final Integration (Run Full System)

```bash
cd /Bytelense/tests

# Should work without modification
timeout 60 python test_pot.py

# Expected output:
# Total Calories: 450-500 (for pav bhaji)
# Quality Score: 3-5/10
# Key Health Factors: [condition-specific warnings]
```

---

## STEP-BY-STEP CHECKLIST

### Before You Start

- [ ] Read this file (QWEN_IMPLEMENTATION_INSTRUCTIONS.md)
- [ ] Read HLD_MEDICAL_NUTRITION_AGENT.md (full design)
- [ ] Make sure Ollama is running
- [ ] Make sure SearXNG is running
- [ ] cd /Bytelense/tests

### Phase 1: Translation Layers

- [ ] Create translators.py
- [ ] Implement OpenFoodFactsRequestTranslator
- [ ] Implement OpenFoodFactsResponseTranslator
- [ ] Implement SearXNGResponseTranslator
- [ ] Implement DomainKBResponseTranslator
- [ ] Test: `python -m pytest test_agents.py::test_response_translator_validation -v`

### Phase 2: Thin Orchestration

- [ ] Create agents.py
- [ ] Define DataQualityAssessment signature
- [ ] Implement ThinOrchestrationAgent
- [ ] Test: `python -m pytest test_agents.py::test_thin_agent_determinism -v`

### Phase 3: Deep Reasoning Agents

- [ ] Define & implement DataInferenceAndReconciliation
- [ ] Define & implement PortionScaling agent
- [ ] Define & implement MedicalContextAdapter
- [ ] Test: `python -m pytest test_agents.py -k "inference or scaling or medical" -v`

### Phase 4: Main Orchestration

- [ ] Implement MedicalNutritionAgent.**init**()
- [ ] Implement MedicalNutritionAgent.forward()
- [ ] Implement helper methods (_simple_path, _merge_sources, etc)
- [ ] Test: `python -m pytest test_agents.py -k "e2e" -v`

### Phase 5: Integration

- [ ] Modify test_pot.py to use new agents
- [ ] Remove old NutritionalSearch code
- [ ] Add medical_condition parameter
- [ ] Test: `timeout 60 python test_pot.py`

### Phase 6: Write Tests

- [ ] Write 10 unit tests
- [ ] Write 3 integration tests
- [ ] Achieve >80% coverage
- [ ] All 13 tests pass

### Phase 7: Sign-Off

- [ ] Code Quality Checklist (5 items)
- [ ] Testing Checklist (5 items)
- [ ] Performance Checklist (5 items)
- [ ] Medical Safety Checklist (5 items)
- [ ] Documentation Checklist (5 items)
- [ ] Deployment Checklist (5 items)

---

## COMMON QUESTIONS

**Q: What if OpenFoodFacts API is slow?**
A: See PITFALL #1 (HLD line 555-597) for timeout retry logic

**Q: What if LLM gives wrong answer?**
A: See PITFALL #4 (HLD line 701-748) for hallucination detection

**Q: What if different sources disagree on calories?**
A: See PITFALL #3 (HLD line 652-697) for conflict resolution via Inference Agent

**Q: How do I know if my code is correct?**
A: Use the test code from HLD. All tests must pass + Sign-off checklist complete

**Q: What's the most important pitfall to fix first?**
A: #4 (Hallucination) and #10 (Liability) - medical safety critical

**Q: Can I use temperature > 0 in DSPy?**
A: NO - see PITFALL #9 (line 958-1005). Must be temperature=0.0 for routing

**Q: Do I need to modify test_pot.py CalorieCalculator?**
A: NO - keep it as is. Only replace NutritionalSearch with new agents.

---

## SUCCESS CRITERIA

Your implementation is DONE when:

1. **All 13 tests pass**

   ```bash
   python -m pytest test_agents.py -v
   # All 13: PASSED
   # Coverage: >80%
   ```

2. **Full test_pot.py works**

   ```bash
   python test_pot.py
   # Better output for tea, chips, pav bhaji
   # Shows reasoning and confidence
   ```

3. **All sign-off items checked**
   - Code Quality: 5/5 ✓
   - Testing: 5/5 ✓
   - Performance: 5/5 ✓
   - Medical Safety: 5/5 ✓
   - Documentation: 5/5 ✓
   - Deployment: 5/5 ✓

4. **All 10 pitfalls handled**
   - Each pitfall has fix implemented
   - Each pitfall has test verifying fix
   - Each pitfall documented in code comments

---

## ESTIMATED TIME PER PHASE

| Phase | Task | Time |
|-------|------|------|
| 1 | Translation Layers | 2-3 hours |
| 2 | Thin Agent | 1 hour |
| 3 | Deep Agents | 3-4 hours |
| 4 | Main Orchestration | 1-2 hours |
| 5 | Integration | 1-2 hours |
| 6 | Tests | 2-3 hours |
| **Total** | **Full Implementation** | **~12-15 hours** |

---

**Now you're ready. Start with Phase 1. If you get stuck, re-read the relevant section of HLD_MEDICAL_NUTRITION_AGENT.md**
