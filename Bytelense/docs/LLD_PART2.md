# Bytelense - Low-Level Design Document (Part 2)

**Continuation of LLD.md**

---

## 5. Enhanced OCR Processing Pipeline

### 5.1 Overview

The OCR pipeline transforms raw image text into structured nutritional data through a multi-stage process:

1. **Raw OCR Extraction** (Chandra) → Full text with confidence
2. **DSPy Structural Extraction** → Parse text into entities
3. **Missing Data Identification** → Detect incomplete information
4. **Market Search Augmentation** (if needed) → Size/price estimation
5. **OpenFoodFacts Validation** → Cross-reference with database
6. **Final Structured Output** → Complete NutritionData object

**Key Design Principle**: Each stage can be bypassed if data is already complete. Stages are independent and can be tested/debugged separately.

### 5.2 Stage 1: Raw OCR Extraction

**Module**: `backend/app/services/ocr/raw_extraction.py`

**Responsibility**: Extract all visible text from food package image using Chandra OCR.

**Input Contract**:
```python
RawOCRRequest:
    image_bytes: bytes
    image_format: Literal["jpeg", "png", "jpg"]
    preprocessing_level: Literal["none", "basic", "aggressive"] = "basic"
```

**Output Contract**:
```python
RawOCRExtraction:
    full_text: str                          # Complete extracted text
    confidence: float                       # Overall OCR confidence (0-1)
    processing_time_ms: int

    # Optional structured regions (if OCR provides)
    text_blocks: List[Dict[str, Any]]       # [{"text": "...", "bbox": [...], "confidence": 0.9}]

    # Preprocessing metadata
    image_preprocessed: bool
    preprocessing_applied: List[str]        # ["denoise", "contrast", "rotate"]
```

**Processing Steps**:

1. **Image Preprocessing** (if enabled):
   - Convert to grayscale
   - Adaptive thresholding for text clarity
   - Denoise (bilateral filter)
   - Deskew (correct rotation up to ±15°)
   - Contrast enhancement (CLAHE)

2. **Chandra OCR Invocation**:
   ```python
   # Chandra OCR usage pattern
   from chandra_ocr import ChandraOCR

   ocr = ChandraOCR()  # Loads transformers model: datalab-to/chandra

   result = ocr.extract(pil_image)
   # Returns: {"text": str, "confidence": float, "blocks": [...]}
   ```

3. **Post-processing**:
   - Remove noise characters (control chars, excessive whitespace)
   - Normalize encoding (UTF-8)
   - Detect and merge split words (e.g., "CA LORIES" → "CALORIES")

**Error Handling**:
- If Chandra fails → retry with aggressive preprocessing
- If still fails → return empty text with confidence=0.0
- Log failure for monitoring

**Performance Target**: < 2s for 1920x1080 image

**Decoupling**: This module has ZERO dependencies on other services. Can be tested with any image independently.

---

### 5.3 Stage 2: DSPy Structural Extraction

**Module**: `backend/app/services/ocr/structured_extraction.py`

**Responsibility**: Parse unstructured OCR text into structured nutritional entities using DSPy.

**Why DSPy**: Raw text from labels is messy. Regex patterns fail on:
- Typos: "Calorles" instead of "Calories"
- Non-standard formatting: "per 100 gm serving"
- Missing units: "Sugar 10" (is it 10g? 10mg?)
- Multilingual labels: "Sodium/सोडियम 250mg"

DSPy LLM can handle ambiguity and extract intent even from messy text.

**DSPy Signature Definition**:

```python
class ExtractNutritionalEntities(dspy.Signature):
    """
    Extract structured nutritional information from OCR text of food label.

    Handle:
    - Typos and OCR errors
    - Non-standard formatting
    - Multilingual text
    - Missing units (infer from context)
    - Per-serving vs per-100g values
    """

    ocr_text: str = dspy.InputField(
        desc="Raw OCR text extracted from food package label"
    )

    # Outputs
    product_name: str = dspy.OutputField(
        desc="Product name/brand (e.g., 'Lay's Classic Potato Chips')"
    )

    brand: Optional[str] = dspy.OutputField(
        desc="Brand name if separately identifiable"
    )

    net_quantity: Optional[str] = dspy.OutputField(
        desc="Net quantity with unit (e.g., '52g', '500ml', '1kg')"
    )

    serving_size: Optional[str] = dspy.OutputField(
        desc="Serving size mentioned (e.g., '28g', '1 cup', '2 biscuits')"
    )

    nutrients_per_100g: Dict[str, float] = dspy.OutputField(
        desc="""
        Nutrients per 100g/100ml as JSON dict.
        Keys: 'energy_kcal', 'protein_g', 'carbs_g', 'fat_g', 'sugar_g', 'sodium_mg', 'fiber_g'
        Only include if explicitly stated in text.
        """
    )

    nutrients_per_serving: Dict[str, float] = dspy.OutputField(
        desc="""
        Nutrients per serving as JSON dict (same keys as per_100g).
        Only include if explicitly stated.
        """
    )

    ingredients_list: List[str] = dspy.OutputField(
        desc="List of ingredients in order. Empty list if not found."
    )

    allergen_warnings: List[str] = dspy.OutputField(
        desc="Allergens mentioned (e.g., ['milk', 'soy', 'nuts']). Empty if none."
    )

    package_indicators: List[str] = dspy.OutputField(
        desc="""
        Price/size indicators for market search (e.g., ['₹20', '40g pack', '500ml bottle']).
        Extract any text that helps identify product variant in market.
        """
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in extraction quality (0.0 to 1.0)"
    )

    missing_critical_info: List[str] = dspy.OutputField(
        desc="""
        List of critical missing information.
        Options: ['product_name', 'net_quantity', 'nutritional_values', 'ingredients']
        """
    )
```

**DSPy Module Implementation Pattern**:

```python
class NutritionalEntityExtractor(dspy.Module):
    """DSPy module for extracting structured data from OCR text."""

    def __init__(self, model: str = "qwen3:8b"):
        super().__init__()

        # Use smaller, faster model for extraction (not reasoning)
        lm = dspy.LM(f'ollama_chat/{model}', api_base='http://localhost:11434')
        dspy.configure(lm=lm)

        # Use ChainOfThought for reasoning through messy text
        self.extractor = dspy.ChainOfThought(ExtractNutritionalEntities)

    async def forward(self, ocr_text: str) -> dspy.Prediction:
        """
        Extract entities from OCR text.

        Returns DSPy Prediction object with all output fields.
        """
        result = await self.extractor(ocr_text=ocr_text)
        return result
```

**Usage Pattern** (Async):

```python
# In calling code
from app.services.ocr.structured_extraction import NutritionalEntityExtractor

extractor = NutritionalEntityExtractor()

result = await extractor.forward(ocr_text="NUTRITION FACTS per 100g...")

# Access fields
product_name = result.product_name
nutrients = result.nutrients_per_100g  # Dict
missing = result.missing_critical_info  # List
```

**When LLM Call is Needed**:
- OCR text is present but messy
- Standard regex patterns fail
- Units are ambiguous
- Multilingual text
- Non-standard formatting

**When LLM Call is NOT Needed**:
- OCR completely failed (empty text) → skip
- Text is perfectly structured (rare) → simple regex

**Performance Target**: < 3s (includes LLM inference)

**Fallback Strategy**:
- If DSPy fails → attempt regex-based extraction
- If regex fails → return partial data with low confidence
- Always return a result (never throw exception)

---

### 5.4 Stage 3: Missing Data Identification

**Module**: `backend/app/services/ocr/gap_analyzer.py`

**Responsibility**: Analyze extracted data to identify what's missing and how critical it is.

**Input**:
```python
StructuredNutritionExtraction  # From Stage 2
```

**Output**:
```python
DataGapAnalysis:
    completeness_score: float               # 0-1 (1 = all critical data present)

    missing_fields: List[str]              # ['net_quantity', 'sugar_g']

    critical_gaps: List[str]               # Blocking issues: ['product_name', 'calories']
    non_critical_gaps: List[str]           # Nice-to-have: ['fiber_g', 'brand']

    can_proceed_without_search: bool       # True if we have enough data
    requires_market_search: bool           # True if we need size/price estimation
    requires_openfoodfacts: bool           # True if we need database augmentation

    suggested_search_query: Optional[str]  # Best query for market search
```

**Decision Logic** (Rule-Based, No LLM Needed):

```python
def analyze_gaps(extraction: StructuredNutritionExtraction) -> DataGapAnalysis:
    """
    Analyze data completeness and determine next steps.

    Critical fields (must have at least ONE):
    - product_name OR brand
    - calories OR energy_kcal
    - serving_size OR net_quantity

    Non-critical (nice to have):
    - protein, carbs, fat, fiber
    - ingredients
    - allergens
    """

    critical_present = []
    critical_missing = []

    # Check product identification
    if extraction.product_name:
        critical_present.append('product_name')
    else:
        critical_missing.append('product_name')

    # Check calorie data
    has_calories = (
        'energy_kcal' in extraction.nutrients_per_100g or
        'calories' in extraction.nutrients_per_serving
    )

    if has_calories:
        critical_present.append('calories')
    else:
        critical_missing.append('calories')

    # Check quantity (for portion calculation)
    if extraction.net_quantity or extraction.serving_size:
        critical_present.append('quantity')
    else:
        critical_missing.append('quantity')

    # Calculate completeness
    completeness = len(critical_present) / (len(critical_present) + len(critical_missing))

    # Determine next steps
    can_proceed = len(critical_missing) == 0
    needs_search = ('quantity' in critical_missing or
                    'product_name' in critical_missing)
    needs_off = ('calories' in critical_missing)

    return DataGapAnalysis(
        completeness_score=completeness,
        critical_gaps=critical_missing,
        can_proceed_without_search=can_proceed,
        requires_market_search=needs_search,
        requires_openfoodfacts=needs_off,
        suggested_search_query=_build_search_query(extraction)
    )
```

**No LLM Needed**: Simple rule-based logic.

---

### 5.5 Stage 4: Market Search Augmentation

**Module**: `backend/app/services/ocr/market_augmentation.py`

**Responsibility**: If net quantity or product variants are missing, search market to estimate size/price.

**Trigger Condition**: `DataGapAnalysis.requires_market_search == True`

**Why This Stage Exists**:
- OCR might read "Lay's Chips" but miss "52g Net Wt."
- Knowing pack size is critical for calculating total nutritional load
- Market search can find: "Lay's Classic: ₹10 (25g), ₹20 (52g), ₹40 (100g)"

**Search Strategy**:

1. **Build Search Query** from available data:
   ```python
   query_parts = []

   if product_name:
       query_parts.append(product_name)
   if brand:
       query_parts.append(brand)
   if package_indicators:  # e.g., ["₹20", "blue pack"]
       query_parts.extend(package_indicators)

   query = " ".join(query_parts) + " buy online price size variants"
   ```

2. **Delegate to Search Intern Agent** (Section 6):
   ```python
   from app.agents.search_intern import SearchInternAgent

   intern = SearchInternAgent()

   task = {
       "objective": "Find available sizes and prices for this product",
       "product_name": extraction.product_name,
       "hints": extraction.package_indicators
   }

   report = await intern.execute_task(task)
   # Returns: InternAgentReport with available_sizes, prices, sources
   ```

3. **Extract Size Variants**:
   - Parse results for common patterns: "25g", "52g", "100g", "500ml"
   - Associate with prices: "₹10", "₹20", "₹40"
   - Match OCR hints to most likely variant

4. **Estimate Net Quantity**:
   ```python
   # If OCR found "₹20" in package_indicators
   # And search found {"₹20": "52g"}
   # → estimated_net_quantity = "52g"
   ```

**Output**:
```python
ProductSizeEstimate:
    available_sizes: List[Dict]  # [{"price": "₹20", "size": "52g", "source": "url"}]
    best_match: Dict             # Most likely variant based on hints
    confidence: float            # How confident the match is
```

**Performance Target**: < 5s (includes search intern agent)

**Fallback**: If search fails, ask user to manually enter pack size via chat.

---

### 5.6 Stage 5: OpenFoodFacts Validation

**Module**: `backend/app/services/ocr/openfoodfacts_validation.py`

**Responsibility**: Cross-reference extracted data with OpenFoodFacts database to:
- Fill missing nutritional values
- Validate OCR-extracted values
- Get authoritative allergen info

**When to Use**:
- `DataGapAnalysis.requires_openfoodfacts == True`, OR
- Extracted nutritional data has low confidence, OR
- Always (as validation step)

**Search Strategy**:

1. **Try Barcode First** (if available from image):
   ```python
   if barcode:
       url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
       response = await httpx_client.get(url)
       # Parse and extract nutrition
   ```

2. **Fallback to Text Search**:
   ```python
   search_url = "https://world.openfoodfacts.org/cgi/search.pl"
   params = {
       "search_terms": f"{product_name} {brand}",
       "search_simple": 1,
       "json": 1,
       "page_size": 5
   }
   response = await httpx_client.get(search_url, params=params)
   products = response.json()["products"]

   # Pick best match (Section 5.7)
   ```

3. **Data Merging**:
   - OCR data is PRIMARY (it's what user is actually holding)
   - OpenFoodFacts data is SECONDARY (for filling gaps/validation)
   - Merge strategy:
     ```python
     merged = ocr_data.copy()

     for field in ['protein_g', 'carbs_g', 'fat_g', 'fiber_g']:
         if field not in merged or merged[field] is None:
             merged[field] = off_data.get(field)

     # Always prefer OCR ingredients (fresher data)
     # But use OFF allergens if OCR missed them
     if not merged['allergens']:
         merged['allergens'] = off_data.get('allergens', [])
     ```

**Output**: Enhanced `StructuredNutritionExtraction` with filled gaps.

---

### 5.7 Product Matching (OpenFoodFacts Results)

**Challenge**: When text search returns 5 products, which one matches the scanned item?

**Solution**: DSPy-based matching with similarity scoring.

**DSPy Signature**:

```python
class MatchProduct(dspy.Signature):
    """
    Determine which OpenFoodFacts product best matches the scanned item.
    """

    scanned_product_info: str = dspy.InputField(
        desc="""
        Information from scanned product: name, brand, package size, price hints.
        Format as JSON string.
        """
    )

    candidate_products: str = dspy.InputField(
        desc="""
        List of candidate products from OpenFoodFacts as JSON array.
        Each with: name, brand, size, barcode.
        """
    )

    best_match_index: int = dspy.OutputField(
        desc="Index (0-based) of best matching product. -1 if no good match."
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in match (0-1)"
    )

    reasoning: str = dspy.OutputField(
        desc="Why this product was selected"
    )
```

**Usage**:

```python
class ProductMatcher(dspy.Module):
    def __init__(self):
        super().__init__()
        self.matcher = dspy.ChainOfThought(MatchProduct)

    async def find_best_match(
        self,
        scanned_info: Dict,
        candidates: List[Dict]
    ) -> int:
        result = await self.matcher(
            scanned_product_info=json.dumps(scanned_info),
            candidate_products=json.dumps(candidates)
        )
        return int(result.best_match_index)
```

**When LLM Needed**: Multiple search results with ambiguous matches.

**When NOT Needed**: Exact barcode match (index=0, confidence=1.0).

---

### 5.8 Final Assembly

**Module**: `backend/app/services/ocr/pipeline.py`

**Responsibility**: Orchestrate all stages and produce final `NutritionData` object.

**Async Pipeline Execution**:

```python
class OCREnhancementPipeline:
    """
    Orchestrates 5-stage OCR enhancement pipeline.

    Each stage is independent and can be bypassed.
    """

    def __init__(self):
        self.raw_extractor = RawOCRExtractor()
        self.entity_extractor = NutritionalEntityExtractor()
        self.gap_analyzer = DataGapAnalyzer()
        self.market_augmenter = MarketAugmenter()
        self.off_validator = OpenFoodFactsValidator()

    async def process(
        self,
        image_bytes: bytes,
        barcode: Optional[str] = None
    ) -> NutritionData:
        """
        Run full pipeline asynchronously.

        Returns complete NutritionData or raises exception with partial data.
        """

        # Stage 1: Raw OCR
        raw_ocr = await self.raw_extractor.extract(image_bytes)

        if not raw_ocr.full_text or raw_ocr.confidence < 0.5:
            raise OCRFailedException("OCR extraction failed", partial_data=None)

        # Stage 2: Structured extraction
        structured = await self.entity_extractor.forward(raw_ocr.full_text)

        # Stage 3: Gap analysis
        gaps = self.gap_analyzer.analyze_gaps(structured)

        # Stage 4: Market augmentation (if needed)
        if gaps.requires_market_search:
            size_estimate = await self.market_augmenter.estimate_size(structured)
            structured.net_quantity = size_estimate.best_match.get('size')

        # Stage 5: OpenFoodFacts validation
        if barcode or gaps.requires_openfoodfacts:
            enhanced = await self.off_validator.validate_and_enhance(
                structured, barcode
            )
        else:
            enhanced = structured

        # Convert to NutritionData
        nutrition_data = self._to_nutrition_data(enhanced, gaps)

        return nutrition_data

    def _to_nutrition_data(
        self,
        extraction: StructuredNutritionExtraction,
        gaps: DataGapAnalysis
    ) -> NutritionData:
        """Convert structured extraction to final NutritionData model."""
        # Implementation maps fields
        pass
```

**Error Handling Strategy**:
- Each stage logs its output
- If any stage fails, proceed with partial data + low confidence flag
- Never fail the entire scan unless Stage 1 (raw OCR) completely fails

**Performance Targets**:
- Stage 1 (OCR): < 2s
- Stage 2 (Extraction): < 3s
- Stage 3 (Gap Analysis): < 0.1s (rule-based)
- Stage 4 (Market Search): < 5s (if needed)
- Stage 5 (OFF Validation): < 3s (if needed)
- **Total**: < 13s worst case, < 5s typical case

---

## 6. SearXNG ReAct "Intern" Agent

### 6.1 Overview - The "Intern" Metaphor

This is the **most critical intelligent component** of the system.

**Metaphor**: The main food scoring thread is like a senior analyst. It knows WHAT data it needs but not HOW to search the messy internet for it. It delegates search tasks to an "intern" - a specialized ReAct agent that:

1. **Understands the task** (e.g., "Find available sizes of Lay's chips")
2. **Plans multiple search strategies** (keyword variations, different phrasings)
3. **Executes searches** via SearXNG with query variations
4. **Aggregates results** from multiple queries
5. **Cleans and structures data**
6. **Reports back** with links for traceability

**Key Insight**: This agent doesn't just fetch web results - it **makes sense of them**. It's an active researcher, not a passive API caller.

### 6.2 Architecture

**Module**: `backend/app/agents/search_intern.py`

**Technology**: DSPy ReAct module with custom tools

**Ollama Model**: Use reasoning-optimized model (deepseek-r1:8b or qwen3:30b)

**Core Components**:
1. **Task Parser** - Understands what's being asked
2. **Query Planner** - Generates multiple search strategies
3. **Search Executor** - Runs queries via SearXNG
4. **Result Aggregator** - Merges and deduplicates results
5. **Data Extractor** - Parses structured data from web snippets
6. **Report Generator** - Formats findings with citations

### 6.3 DSPy Signature for Search Intern

```python
class SearchInternTask(dspy.Signature):
    """
    You are a research intern. Your job is to search the web for specific information
    about food products and compile a detailed report with source links.

    You have access to tools:
    - search_web(query, max_results): Query SearXNG, returns results
    - extract_from_snippet(snippet, data_type): Extract structured data from text
    - validate_url(url): Check if URL is accessible

    Your approach:
    1. Analyze the task to understand what data is needed
    2. Generate 3-5 different search queries (keyword variations)
    3. Execute each query and collect results
    4. Aggregate findings from all queries
    5. Extract structured data (e.g., sizes, prices, nutrition facts)
    6. Compile report with all source URLs

    Be thorough but efficient. Max 10 total queries.
    """

    task_description: str = dspy.InputField(
        desc="""
        What you need to find. Examples:
        - "Find available package sizes and prices for Lay's Classic chips"
        - "Get nutrition facts for Oreo cookies if not in OpenFoodFacts"
        - "Find WHO guidelines for daily sodium intake for heart health"
        """
    )

    product_hints: Dict[str, Any] = dspy.InputField(
        desc="""
        Any hints about the product (name, brand, price seen on package, etc.)
        Format as JSON dict. Can be empty if task is general (like guidelines).
        """
    )

    data_type: str = dspy.InputField(
        desc="""
        Type of data expected:
        - 'product_variants' (sizes, prices)
        - 'nutrition_facts'
        - 'health_guidelines'
        - 'similar_products'
        - 'ingredients_info'
        """
    )

    # Outputs

    queries_executed: List[str] = dspy.OutputField(
        desc="List of all search queries you ran (for transparency)"
    )

    total_results_found: int = dspy.OutputField(
        desc="Total number of raw results across all queries"
    )

    relevant_results: List[Dict] = dspy.OutputField(
        desc="""
        Filtered relevant results as JSON array.
        Each: {"url": "...", "title": "...", "snippet": "...", "extracted_data": {...}}
        """
    )

    summary: str = dspy.OutputField(
        desc="""
        Natural language summary of findings.
        E.g., "Found 3 size variants: 25g (₹10), 52g (₹20), 100g (₹40).
        Most popular size is 52g based on search frequency."
        """
    )

    structured_data: Dict[str, Any] = dspy.OutputField(
        desc="""
        Extracted structured data as JSON.
        Format depends on data_type:
        - product_variants: {"sizes": [...], "prices": [...]}
        - nutrition_facts: {"per_100g": {...}, "source": "url"}
        - health_guidelines: {"recommendation": "...", "source": "WHO/FDA/USDA"}
        """
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in data quality (0-1)"
    )

    sources: List[Dict] = dspy.OutputField(
        desc="""
        All source URLs with metadata for citations.
        [{"url": "...", "title": "...", "snippet": "...", "accessed": "timestamp"}]
        """
    )
```

### 6.4 Tool Definitions for ReAct Agent

**Tools Available to Intern Agent** (via FastMCP):

```python
# File: backend/app/agents/search_intern_tools.py

from fastmcp import FastMCP

mcp = FastMCP("Search Intern Tools")


@mcp.tool()
async def search_web(
    query: str,
    max_results: int = 10,
    categories: str = "general"
) -> Dict:
    """
    Search the web using SearXNG.

    Args:
        query: Search query string
        max_results: Max results to return (default 10)
        categories: SearXNG categories (default "general")

    Returns:
        Dict with:
        - query: str (query that was executed)
        - num_results: int
        - results: List[Dict] with url, title, content, engine
        - search_time_ms: int
    """
    import httpx
    from app.core.config import settings

    url = f"{settings.searxng_api_base}/search"
    params = {
        "q": query,
        "format": "json",
        "categories": categories,
        "lang": "en"
    }

    start = time.time()

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url, params=params)
        data = response.json()

    elapsed_ms = int((time.time() - start) * 1000)

    results = []
    for r in data.get("results", [])[:max_results]:
        results.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "content": r.get("content", "")[:500],  # Limit snippet length
            "engine": r.get("engine", "unknown"),
            "score": r.get("score", 0)
        })

    return {
        "query": query,
        "num_results": len(results),
        "results": results,
        "search_time_ms": elapsed_ms
    }


@mcp.tool()
async def extract_prices_and_sizes(snippet: str) -> Dict:
    """
    Extract price and size information from text snippet.

    Uses regex + LLM fallback for messy text.

    Args:
        snippet: Text snippet from search result

    Returns:
        Dict with:
        - prices: List[str] (e.g., ["₹20", "$5"])
        - sizes: List[str] (e.g., ["52g", "500ml"])
        - confidence: float
    """
    import re

    # Regex patterns for common price/size formats
    price_patterns = [
        r'₹\s*\d+',          # ₹20
        r'\$\s*\d+\.?\d*',   # $5.99
        r'Rs\.?\s*\d+',      # Rs 20
        r'\d+\s*rupees?',    # 20 rupees
    ]

    size_patterns = [
        r'\d+\.?\d*\s*g(?:rams?)?',  # 52g, 100 grams
        r'\d+\.?\d*\s*kg',           # 1kg
        r'\d+\.?\d*\s*ml',           # 500ml
        r'\d+\.?\d*\s*l(?:iters?)?', # 1 liter
    ]

    prices = []
    for pattern in price_patterns:
        prices.extend(re.findall(pattern, snippet, re.IGNORECASE))

    sizes = []
    for pattern in size_patterns:
        sizes.extend(re.findall(pattern, snippet, re.IGNORECASE))

    # Clean up
    prices = list(set(prices))
    sizes = list(set(sizes))

    confidence = 1.0 if (prices and sizes) else 0.5

    return {
        "prices": prices,
        "sizes": sizes,
        "confidence": confidence
    }


@mcp.tool()
async def extract_nutrition_facts(snippet: str) -> Dict:
    """
    Extract nutritional values from text snippet.

    Args:
        snippet: Text snippet mentioning nutrition

    Returns:
        Dict with nutrients found and confidence
    """
    import re

    nutrients = {}

    # Patterns: "Calories: 150", "Protein 5g", "Sugar: 10 grams"
    patterns = {
        'calories': r'calories?:?\s*(\d+\.?\d*)',
        'protein': r'protein:?\s*(\d+\.?\d*)\s*g',
        'carbs': r'carb(?:ohydrate)?s?:?\s*(\d+\.?\d*)\s*g',
        'fat': r'fat:?\s*(\d+\.?\d*)\s*g',
        'sugar': r'sugar:?\s*(\d+\.?\d*)\s*g',
        'sodium': r'sodium:?\s*(\d+\.?\d*)\s*mg',
        'fiber': r'fiber:?\s*(\d+\.?\d*)\s*g',
    }

    for nutrient, pattern in patterns.items():
        match = re.search(pattern, snippet, re.IGNORECASE)
        if match:
            nutrients[nutrient] = float(match.group(1))

    return {
        "nutrients": nutrients,
        "confidence": len(nutrients) / len(patterns)  # How many we found
    }


@mcp.tool()
async def validate_source_authority(url: str) -> Dict:
    """
    Assess the authority/credibility of a source URL.

    Args:
        url: URL to assess

    Returns:
        Dict with authority_score (0-1) and reason
    """
    from urllib.parse import urlparse

    domain = urlparse(url).netloc.lower()

    # Authoritative sources
    high_authority = [
        'who.int',          # World Health Organization
        'fda.gov',          # US FDA
        'usda.gov',         # USDA
        'nih.gov',          # National Institutes of Health
        'nhs.uk',           # UK National Health Service
        'health.harvard.edu', # Harvard Health
        'mayoclinic.org',   # Mayo Clinic
    ]

    medium_authority = [
        'eatthis.com',
        'healthline.com',
        'webmd.com',
        'medicalnewstoday.com',
    ]

    if any(auth in domain for auth in high_authority):
        return {"authority_score": 0.95, "reason": "Official health authority"}

    elif any(auth in domain for auth in medium_authority):
        return {"authority_score": 0.7, "reason": "Reputable health website"}

    elif 'amazon' in domain or 'flipkart' in domain or 'bigbasket' in domain:
        return {"authority_score": 0.6, "reason": "E-commerce (product info may be accurate)"}

    else:
        return {"authority_score": 0.4, "reason": "Unknown source"}
```

### 6.5 ReAct Agent Implementation

```python
# File: backend/app/agents/search_intern.py

import dspy
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SearchInternAgent(dspy.Module):
    """
    Autonomous ReAct agent that researches information on the web.

    Uses tools:
    - search_web()
    - extract_prices_and_sizes()
    - extract_nutrition_facts()
    - validate_source_authority()

    Follows ReAct pattern: Thought → Action → Observation → Repeat
    """

    def __init__(self, model: str = "deepseek-r1:8b", max_iterations: int = 10):
        super().__init__()

        # Use reasoning-optimized model
        lm = dspy.LM(
            f'ollama_chat/{model}',
            api_base='http://localhost:11434',
            api_key=''
        )
        dspy.configure(lm=lm)

        # Import tools
        from app.agents.search_intern_tools import (
            search_web,
            extract_prices_and_sizes,
            extract_nutrition_facts,
            validate_source_authority
        )

        # Create ReAct agent with tools
        self.agent = dspy.ReAct(
            signature=SearchInternTask,
            tools=[
                search_web,
                extract_prices_and_sizes,
                extract_nutrition_facts,
                validate_source_authority
            ],
            max_iters=max_iterations
        )

        logger.info(f"SearchInternAgent initialized with {model}, max_iters={max_iterations}")

    async def execute_task(
        self,
        task_description: str,
        product_hints: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Execute a search research task.

        Args:
            task_description: What to search for
            product_hints: Product info (name, brand, price hints, etc.)
            data_type: Type of data expected (product_variants, nutrition_facts, etc.)

        Returns:
            Dict with:
            - summary: str
            - structured_data: Dict
            - sources: List[Dict]
            - queries_executed: List[str]
            - confidence: float
        """
        logger.info(f"SearchIntern executing task: {task_description}")

        try:
            # Run ReAct agent
            result = await self.agent(
                task_description=task_description,
                product_hints=product_hints,
                data_type=data_type
            )

            # Parse outputs
            return {
                "summary": result.summary,
                "structured_data": result.structured_data,
                "sources": result.sources,
                "queries_executed": result.queries_executed,
                "total_results": result.total_results_found,
                "confidence": result.confidence
            }

        except Exception as e:
            logger.error(f"SearchIntern error: {e}", exc_info=True)

            # Fallback: single direct search
            from app.agents.search_intern_tools import search_web

            fallback_query = f"{product_hints.get('product_name', '')} {data_type}".strip()
            fallback_results = await search_web(fallback_query, max_results=5)

            return {
                "summary": f"Fallback search executed: {fallback_query}",
                "structured_data": {},
                "sources": fallback_results["results"],
                "queries_executed": [fallback_query],
                "total_results": fallback_results["num_results"],
                "confidence": 0.3  # Low confidence for fallback
            }
```

### 6.6 Example ReAct Agent Reasoning Flow

**Task**: "Find available package sizes and prices for Lay's Classic chips"

**Product Hints**: `{"product_name": "Lay's Classic", "brand": "Lay's", "price_hint": "₹20"}`

**Expected ReAct Trace**:

```
Iteration 1:
  Thought: "I need to find different sizes of Lay's Classic chips. Let me start with a broad search."
  Action: search_web("Lay's Classic chips sizes available India", max_results=10)
  Observation: Found 10 results, many from e-commerce sites.

Iteration 2:
  Thought: "I see multiple e-commerce results. Let me try a more specific query for small packs."
  Action: search_web("Lay's Classic 20 rupees pack size", max_results=5)
  Observation: Found results mentioning "₹20 pack is 52g"

Iteration 3:
  Thought: "Good! I found one size. Let me search for other price points."
  Action: search_web("Lay's Classic 10 rupees 40 rupees pack size", max_results=5)
  Observation: Found "₹10 = 25g", "₹40 = 90g" in snippets

Iteration 4:
  Thought: "Now I have multiple sizes. Let me extract structured data from these snippets."
  Action: extract_prices_and_sizes("Lay's Classic chips: ₹10 for 25g pack, ₹20 for 52g...")
  Observation: {"prices": ["₹10", "₹20", "₹40"], "sizes": ["25g", "52g", "90g"]}

Iteration 5:
  Thought: "I should validate the authority of my sources."
  Action: validate_source_authority("https://www.amazon.in/...")
  Observation: {"authority_score": 0.6, "reason": "E-commerce"}

Iteration 6:
  Thought: "I have enough information. Let me compile the report."
  Action: FINISH

Final Output:
  summary: "Found 3 size variants for Lay's Classic chips in India market: 25g (₹10), 52g (₹20), 90g (₹40). Based on the price hint (₹20), the scanned product is most likely the 52g variant."
  structured_data: {
    "sizes": ["25g", "52g", "90g"],
    "prices": ["₹10", "₹20", "₹40"],
    "best_match": {"price": "₹20", "size": "52g"}
  }
  sources: [
    {"url": "https://amazon.in/...", "title": "Lay's Classic 52g"},
    {"url": "https://bigbasket.com/...", "title": "Lay's Chips variants"}
  ]
  queries_executed: [
    "Lay's Classic chips sizes available India",
    "Lay's Classic 20 rupees pack size",
    "Lay's Classic 10 rupees 40 rupees pack size"
  ]
  confidence: 0.85
```

**Key Features**:
1. **Multi-query strategy**: Doesn't rely on single search
2. **Query variation**: Tries different phrasings
3. **Tool usage**: Uses extract_* tools to parse data
4. **Source validation**: Checks authority of sources
5. **Reasoning transparency**: All steps logged
6. **Source linking**: Every finding has URL citation

### 6.7 Async Execution Pattern

**Critical**: This agent must run **asynchronously** without blocking the main food scanning pipeline.

**Pattern** (from DSPy async tutorial):

```python
# In calling code (e.g., OCR pipeline Stage 4)

import asyncio
from app.agents.search_intern import SearchInternAgent

# Create agent instance
intern = SearchInternAgent(model="deepseek-r1:8b", max_iterations=10)

# Run as async task
async def main():
    task = {
        "task_description": "Find sizes for Lay's chips",
        "product_hints": {"product_name": "Lay's Classic"},
        "data_type": "product_variants"
    }

    # This runs in background, doesn't block
    result = await intern.execute_task(**task)

    print(result["summary"])
    print(result["structured_data"])

# Execute
asyncio.run(main())
```

**Timeout Handling**:
- Agent has max 10 iterations (configurable)
- Each search has 5s timeout
- Total agent timeout: 60s
- If timeout exceeded, return partial results with low confidence

### 6.8 Performance Optimization

**Latency Concerns**:
- Each LLM call: ~2-5s (with deepseek-r1:8b on good hardware)
- 10 iterations max = potentially 50s
- Search queries: ~1s each

**Optimization Strategies**:

1. **Reduce Iterations**:
   - For simple tasks (product size): max 5 iterations
   - For complex tasks (nutrition research): max 10 iterations

2. **Parallel Search Queries**:
   ```python
   # Instead of sequential searches, run in parallel
   queries = ["query1", "query2", "query3"]

   results = await asyncio.gather(*[
       search_web(q) for q in queries
   ])
   ```

3. **Cache Common Searches**:
   - If searching for "Lay's Classic sizes", cache result
   - Store in Redis with 24h TTL
   - Key: hash(product_name + task_type)

4. **Use Smaller Model for Simple Tasks**:
   - Product size search: qwen3:8b (faster)
   - Health guidelines: qwen3:30b (better reasoning)

**Target Performance**:
- Simple product search: < 10s
- Complex nutrition research: < 30s
- Cached results: < 1s

---

## 7. Food History Tracking System

### 7.1 Overview

Track user's food consumption over time to enable **context-aware scoring**.

**Key Principle**: The same food can be "good" or "bad" depending on:
- What user already ate today
- Time of day
- How often they eat this item
- Current moderation level

**Example**:
- Chocolate at 9 AM after healthy breakfast → Score: 7/10 (treat is fine)
- Chocolate at 9 PM after 3 sugary items → Score: 3/10 (sugar overload)

### 7.2 Data Storage Structure

**Location**: `backend/data/scan_history/{username}/`

**Files**:
- `2025-11-14.json` - Today's scans
- `2025-11-week46.json` - This week's summary
- `2025-11.json` - This month's summary (optional)

**Daily File Schema**:
```json
{
  "date": "2025-11-14",
  "user_name": "john",
  "scans": [
    {
      "scan_id": "uuid",
      "timestamp": "2025-11-14T09:30:00Z",
      "product_name": "Lay's Classic Chips",
      "brand": "Lay's",
      "serving_size": "52g",
      "servings_consumed": 1.0,

      "calories": 273,
      "protein_g": 3.5,
      "carbs_g": 31.2,
      "fat_g": 15.6,
      "sugar_g": 1.0,
      "sodium_mg": 312,
      "fiber_g": 2.6,

      "time_of_day": "morning",
      "meal_type": "snack",

      "score": 6.5,
      "verdict": "moderate",

      "moderation_level": "within"
    }
  ],

  "daily_totals": {
    "calories": 1450,
    "protein_g": 45.2,
    "carbs_g": 180.5,
    "fat_g": 52.3,
    "sugar_g": 28.5,
    "sodium_mg": 1850,
    "fiber_g": 18.2
  },

  "vs_targets": {
    "calories": 0.725,
    "sugar_g": 1.14,
    "sodium_mg": 0.82
  },

  "flags": {
    "exceeded_sugar": true,
    "exceeded_sodium": false,
    "exceeded_calories": false
  }
}
```

### 7.3 History Tracker Module

**File**: `backend/app/services/history/tracker.py`

```python
"""
Food scan history tracker.

Responsibilities:
- Record each scan
- Calculate daily totals
- Track moderation levels
- Provide context for scoring
"""

import aiofiles
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.models.schemas import FoodScanRecord, DailySummary, WeeklySummary


class HistoryTracker:
    """Manages food scan history for users."""

    def __init__(self, history_dir: str = "./data/scan_history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_dir(self, user_name: str) -> Path:
        """Get user's history directory."""
        user_dir = self.history_dir / user_name
        user_dir.mkdir(exist_ok=True)
        return user_dir

    def _get_daily_file(self, user_name: str, date_str: str) -> Path:
        """Get path to daily history file."""
        user_dir = self._get_user_dir(user_name)
        return user_dir / f"{date_str}.json"

    async def record_scan(
        self,
        user_name: str,
        scan_record: FoodScanRecord
    ) -> DailySummary:
        """
        Record a food scan and update daily summary.

        Args:
            user_name: Username
            scan_record: Scan details

        Returns:
            Updated daily summary
        """
        date_str = scan_record.timestamp.strftime("%Y-%m-%d")
        daily_file = self._get_daily_file(user_name, date_str)

        # Load existing or create new
        if daily_file.exists():
            async with aiofiles.open(daily_file, 'r') as f:
                content = await f.read()
                daily_data = json.loads(content)
                daily_summary = DailySummary(**daily_data)
        else:
            daily_summary = DailySummary(
                date=date_str,
                user_name=user_name
            )

        # Add scan
        daily_summary.scans.append(scan_record)

        # Recalculate totals
        daily_summary = self._calculate_daily_totals(daily_summary)

        # Save
        async with aiofiles.open(daily_file, 'w') as f:
            await f.write(daily_summary.model_dump_json(indent=2))

        return daily_summary

    def _calculate_daily_totals(self, summary: DailySummary) -> DailySummary:
        """Calculate totals from all scans."""
        summary.total_calories = sum(
            scan.calories * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_protein_g = sum(
            scan.protein_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_carbs_g = sum(
            scan.carbs_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_fat_g = sum(
            scan.fat_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_sugar_g = sum(
            scan.sugar_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_sodium_mg = sum(
            scan.sodium_mg * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_fiber_g = sum(
            (scan.fiber_g or 0) * scan.servings_consumed
            for scan in summary.scans
        )

        return summary

    async def get_today_summary(self, user_name: str) -> Optional[DailySummary]:
        """Get today's consumption summary."""
        today_str = date.today().strftime("%Y-%m-%d")
        daily_file = self._get_daily_file(user_name, today_str)

        if not daily_file.exists():
            return None

        async with aiofiles.open(daily_file, 'r') as f:
            content = await f.read()
            return DailySummary(**json.loads(content))

    async def get_week_summary(
        self,
        user_name: str,
        weeks_back: int = 0
    ) -> WeeklySummary:
        """
        Get weekly consumption summary.

        Args:
            user_name: Username
            weeks_back: How many weeks back (0 = current week)

        Returns:
            Weekly summary with daily breakdowns
        """
        # Calculate week start date
        today = date.today()
        week_start = today - timedelta(days=today.weekday() + (weeks_back * 7))

        daily_summaries = []

        for i in range(7):
            day = week_start + timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")

            daily_file = self._get_daily_file(user_name, day_str)

            if daily_file.exists():
                async with aiofiles.open(daily_file, 'r') as f:
                    content = await f.read()
                    daily_summaries.append(DailySummary(**json.loads(content)))

        # Calculate weekly stats
        weekly = WeeklySummary(
            week_start=week_start.strftime("%Y-%m-%d"),
            user_name=user_name,
            daily_summaries=daily_summaries
        )

        if daily_summaries:
            weekly.avg_daily_calories = sum(
                d.total_calories for d in daily_summaries
            ) / len(daily_summaries)

            weekly.avg_daily_sugar_g = sum(
                d.total_sugar_g for d in daily_summaries
            ) / len(daily_summaries)

            weekly.avg_daily_sodium_mg = sum(
                d.total_sodium_mg for d in daily_summaries
            ) / len(daily_summaries)

        return weekly

    async def calculate_moderation_level(
        self,
        user_name: str,
        new_scan: FoodScanRecord,
        user_targets: Dict[str, float]
    ) -> str:
        """
        Calculate if user is within/approaching/exceeding moderation.

        Args:
            user_name: Username
            new_scan: The scan being evaluated
            user_targets: Daily nutritional targets

        Returns:
            "within", "approaching", or "exceeding"
        """
        # Get today's summary (before adding new scan)
        today = await self.get_today_summary(user_name)

        if not today:
            # First scan of the day
            return "within"

        # Calculate what totals would be AFTER this scan
        projected_calories = today.total_calories + (
            new_scan.calories * new_scan.servings_consumed
        )
        projected_sugar = today.total_sugar_g + (
            new_scan.sugar_g * new_scan.servings_consumed
        )
        projected_sodium = today.total_sodium_mg + (
            new_scan.sodium_mg * new_scan.servings_consumed
        )

        # Check against targets
        calories_pct = projected_calories / user_targets.get("calories", 2000)
        sugar_pct = projected_sugar / user_targets.get("sugar_g", 30)
        sodium_pct = projected_sodium / user_targets.get("sodium_mg", 2300)

        # Determine moderation level
        max_pct = max(calories_pct, sugar_pct, sodium_pct)

        if max_pct < 0.8:
            return "within"
        elif max_pct < 1.0:
            return "approaching"
        else:
            return "exceeding"


# Global instance
history_tracker = HistoryTracker()
```

### 7.4 Context Retrieval for Scoring

**Function**: `get_consumption_context()`

**Purpose**: Provide scoring engine with today's and week's context.

```python
async def get_consumption_context(
    user_name: str,
    scan_time: datetime
) -> Dict[str, Any]:
    """
    Get consumption context for scoring.

    Returns:
        Dict with:
        - today_summary: DailySummary
        - week_summary: WeeklySummary
        - time_of_day: str (morning/afternoon/evening/night)
        - recent_scans: List[FoodScanRecord] (last 3)
    """
    from app.services.history.tracker import history_tracker

    today = await history_tracker.get_today_summary(user_name)
    week = await history_tracker.get_week_summary(user_name, weeks_back=0)

    # Determine time of day
    hour = scan_time.hour
    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 21:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    # Get recent scans (for pattern detection)
    recent_scans = today.scans[-3:] if today else []

    return {
        "today_summary": today.model_dump() if today else None,
        "week_summary": week.model_dump(),
        "time_of_day": time_of_day,
        "recent_scans": [s.model_dump() for s in recent_scans]
    }
```

**Usage in Scoring**:
```python
# In scoring engine
context = await get_consumption_context(user_name, datetime.now())

# Pass to DSPy scoring agent
scoring_result = await scoring_agent.score(
    nutrition_data=nutrition_data,
    user_profile=user_profile,
    consumption_context=context  # <-- CONTEXT HERE
)
```

---

## 8. Context-Aware Scoring Engine

### 8.1 Overview

The scoring engine must consider:
1. **Intrinsic nutritional quality** of the food
2. **User's health profile** (goals, risks)
3. **Consumption context** (today's intake, time, patterns)
4. **Moderation principle** (anything is OK in moderation)

**Base Assumption**: Unless toxic/addictive, ALL foods are permitted in moderation. The system guides, not restricts.

### 8.2 Scoring Formula

```
Final Score = Base Score × Context Multiplier × Time Multiplier

Where:
- Base Score (0-10): Intrinsic quality + goal alignment
- Context Multiplier (0.5-1.5): Based on today's consumption
- Time Multiplier (0.8-1.2): Based on time of day appropriateness
```

**Example**:
- Chocolate bar: Base Score = 6.0 (moderate sugar, some enjoyment value)
- Context: User already had 25g sugar today (target: 30g)
  - Context Multiplier = 0.7 (approaching limit)
- Time: 9 PM (late for sugar)
  - Time Multiplier = 0.8
- **Final Score = 6.0 × 0.7 × 0.8 = 3.36 → Verdict: "avoid" (for now)**

But same chocolate at 10 AM with only 5g sugar consumed:
- **Final Score = 6.0 × 1.2 × 1.0 = 7.2 → Verdict: "good" (enjoy!)**

### 8.3 DSPy Signature for Context-Aware Scoring

```python
class ContextAwareNutritionScoring(dspy.Signature):
    """
    Score food item against user's health profile AND consumption context.

    Philosophy:
    - Everything is OK in moderation
    - Context matters: same food can be good or bad depending on what user already ate
    - Time matters: breakfast foods vs dinner foods
    - Pattern matters: frequency of consumption affects recommendation

    Output a score (0-10) and verdict (good/moderate/avoid) with reasoning.
    """

    # Inputs

    nutrition_data: str = dspy.InputField(
        desc="Nutritional data of scanned food as JSON string"
    )

    user_profile: str = dspy.InputField(
        desc="""
        User health profile as JSON:
        - goals (weight_loss, muscle_building, diabetes, etc.)
        - daily_targets (calories, sugar, sodium, etc.)
        - health_risks (diabetes_risk, cardiovascular_risk, etc.)
        - allergies
        """
    )

    consumption_context: str = dspy.InputField(
        desc="""
        Today's and week's consumption context as JSON:
        - today_summary: {total_calories, total_sugar_g, total_sodium_mg, ...}
        - time_of_day: morning/afternoon/evening/night
        - recent_scans: last 3 items eaten
        - moderation_level: within/approaching/exceeding
        """
    )

    # Outputs

    base_score: float = dspy.OutputField(
        desc="Intrinsic nutritional quality score (0-10), ignoring context"
    )

    context_adjustment: str = dspy.OutputField(
        desc="""
        How context affects score. Format as reasoning:
        "User already consumed X calories (Y% of target). Sugar at Z (W% of target).
        Therefore, adjusting score down/up by N points."
        """
    )

    final_score: float = dspy.OutputField(
        desc="Final score (0-10) after context adjustment"
    )

    verdict: str = dspy.OutputField(
        desc="Overall verdict: 'good', 'moderate', or 'avoid'"
    )

    reasoning: str = dspy.OutputField(
        desc="""
        Complete reasoning in natural language with citations.
        Format: "This product has X calories and Y sugar [1]. Given your goal of Z,
        and that you've already consumed A calories today, this would bring you to B%
        of your target [2]. Recommendation: ..."
        """
    )

    warnings: List[str] = dspy.OutputField(
        desc="""
        Specific warnings as JSON array.
        Format: ["High sodium (350mg) - you've already had 1200mg today", ...]
        Max 3 warnings.
        """
    )

    highlights: List[str] = dspy.OutputField(
        desc="""
        Positive aspects as JSON array.
        Format: ["Good protein source (12g)", "Low sugar", ...]
        Max 3 highlights.
        """
    )

    moderation_message: str = dspy.OutputField(
        desc="""
        Message about moderation status.
        Examples:
        - "You're well within your limits. Enjoy!"
        - "You're approaching your daily sugar limit. Consider this your last sweet treat today."
        - "You've exceeded your sodium target. Skip salty snacks for the rest of the day."
        """
    )

    timing_recommendation: str = dspy.OutputField(
        desc="""
        Time-based recommendation.
        Examples:
        - "Great breakfast choice! High protein to start your day."
        - "This is quite heavy for late night. Consider a lighter option."
        - "Perfect afternoon snack timing."
        """
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in scoring (0-1)"
    )
```

### 8.4 Scoring Module Implementation

```python
# File: backend/app/services/scoring/context_aware_scorer.py

import dspy
from typing import Dict, Any
import json

from app.models.schemas import (
    NutritionData, EnhancedUserProfile, DetailedAssessment, ShortAssessment
)
from app.services.history.context import get_consumption_context
from app.services.citation_manager import CitationManager


class ContextAwareScoringEngine(dspy.Module):
    """
    Context-aware nutrition scoring using DSPy.

    Considers:
    - Intrinsic nutrition quality
    - User goals and health profile
    - Today's consumption
    - Time of day
    - Recent eating patterns
    """

    def __init__(self, model: str = "qwen3:30b"):
        super().__init__()

        # Use best model for reasoning
        lm = dspy.LM(f'ollama_chat/{model}', api_base='http://localhost:11434')
        dspy.configure(lm=lm)

        # Use ChainOfThought for step-by-step reasoning
        self.scorer = dspy.ChainOfThought(ContextAwareNutritionScoring)

        self.citation_manager = CitationManager()

    async def score(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile,
        scan_time: datetime
    ) -> DetailedAssessment:
        """
        Score food with full context awareness.

        Args:
            nutrition_data: Food nutritional data
            user_profile: User health profile
            scan_time: When scan occurred

        Returns:
            Detailed assessment with context-adjusted score
        """
        # 1. Get consumption context
        context = await get_consumption_context(user_profile.name, scan_time)

        # 2. Check for allergens (immediate block)
        if self._has_allergen_violation(nutrition_data, user_profile):
            return self._create_allergen_block_assessment(
                nutrition_data, user_profile, context
            )

        # 3. Run DSPy scoring
        result = await self.scorer(
            nutrition_data=nutrition_data.model_dump_json(),
            user_profile=user_profile.model_dump_json(),
            consumption_context=json.dumps(context)
        )

        # 4. Parse and structure result
        assessment = DetailedAssessment(
            product_name=nutrition_data.product_name,
            brand=nutrition_data.brand,
            user_name=user_profile.name,

            consumption_context=context,

            base_score=float(result.base_score),
            context_adjusted_score=float(result.final_score),
            final_score=float(result.final_score),

            verdict=self._parse_verdict(result.verdict),

            reasoning_steps=[result.context_adjustment, result.reasoning],
            scientific_rationale=result.reasoning,

            moderation_impact=result.moderation_message,
            time_of_day_impact=result.timing_recommendation,

            moderate_warnings=self._parse_list(result.warnings),
            positive_highlights=self._parse_list(result.highlights),

            citations=self.citation_manager.generate_citation_objects(),

            confidence=float(result.confidence)
        )

        return assessment

    def _has_allergen_violation(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile
    ) -> bool:
        """Check if food contains user's allergens."""
        user_allergens = [a.lower() for a in user_profile.allergies]
        food_allergens = [a.lower() for a in nutrition_data.allergens]

        for allergen in user_allergens:
            if any(allergen in fa for fa in food_allergens):
                return True

            # Also check ingredients
            ingredients_text = " ".join(nutrition_data.ingredients).lower()
            if allergen in ingredients_text:
                return True

        return False

    def _create_allergen_block_assessment(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile,
        context: Dict
    ) -> DetailedAssessment:
        """Create assessment for allergen violation (auto-block)."""
        matching_allergens = []

        for allergen in user_profile.allergies:
            if any(allergen.lower() in a.lower() for a in nutrition_data.allergens):
                matching_allergens.append(allergen)

        return DetailedAssessment(
            product_name=nutrition_data.product_name,
            brand=nutrition_data.brand,
            user_name=user_profile.name,
            consumption_context=context,

            base_score=0.0,
            context_adjusted_score=0.0,
            final_score=0.0,
            verdict="avoid",

            reasoning_steps=["Allergen check: FAILED"],
            scientific_rationale=f"This product contains allergens you're allergic to: {', '.join(matching_allergens)}. Do NOT consume.",

            critical_warnings=[f"⚠️ ALLERGEN ALERT: Contains {allergen}" for allergen in matching_allergens],

            moderation_impact="N/A - Safety issue",
            time_of_day_impact="N/A - Safety issue",

            citations=[],
            confidence=1.0
        )

    def _parse_verdict(self, verdict_str: str) -> str:
        """Parse verdict from LLM output."""
        v = verdict_str.lower()
        if "good" in v:
            return "good"
        elif "avoid" in v:
            return "avoid"
        else:
            return "moderate"

    def _parse_list(self, list_str: str) -> List[str]:
        """Parse list from LLM output (JSON or comma-separated)."""
        try:
            return json.loads(list_str)
        except:
            return [item.strip() for item in list_str.split(",") if item.strip()]


# Global instance
context_aware_scorer = ContextAwareScoringEngine()
```

---

**This document continues in LLD_PART3.md with:**

- Section 9: Assessment Generation System (Detailed + Short forms)
- Section 10: API Contracts (All endpoints with request/response)
- Section 11: Async Flow Diagrams
- Section 12: Module Decoupling Strategy
- Section 13: Threading & Concurrency Patterns
- Section 14: Function-Level Specifications

**Current progress**: ~3,500 lines across LLD.md + LLD_PART2.md

Shall I continue with Part 3?
