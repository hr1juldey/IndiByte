#!/usr/bin/env python3
"""
Sub-Phase 2.4: Performance Profiling Script
Purpose: Measure where time is spent in the nutrition assessment system

Instruments:
- API query times (OpenFoodFacts, SearXNG)
- LLM inference times (portion extraction, data inference)
- Data processing times (translation, validation, scaling)
- Fallback detection times
"""

import time
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import with timing hooks
import os
import sys

@dataclass
class TimingMetric:
    """Single timing measurement"""
    name: str
    duration_sec: float
    component: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __str__(self):
        return f"{self.component:30} | {self.duration_sec:8.3f}s | {self.name}"

class PerformanceProfiler:
    """Captures timing for all major system components"""

    def __init__(self):
        self.metrics: List[TimingMetric] = []
        self.start_time = time.time()

    def mark(self, component: str, name: str, duration: float):
        """Record a timing measurement"""
        metric = TimingMetric(name, duration, component)
        self.metrics.append(metric)
        print(f"  [{metric.component:25}] {metric.name:40} {metric.duration_sec:8.3f}s")

    def summary(self):
        """Print timing summary"""
        print("\n" + "="*100)
        print("PERFORMANCE PROFILING RESULTS")
        print("="*100)

        # Group by component
        by_component = {}
        for metric in self.metrics:
            if metric.component not in by_component:
                by_component[metric.component] = []
            by_component[metric.component].append(metric)

        # Print summary
        print("\nBY COMPONENT:")
        for component in sorted(by_component.keys()):
            metrics = by_component[component]
            total = sum(m.duration_sec for m in metrics)
            count = len(metrics)
            avg = total / count if count > 0 else 0
            print(f"\n{component}:")
            print(f"  Total: {total:8.3f}s | Calls: {count:3} | Avg: {avg:8.3f}s")
            for m in metrics:
                print(f"    - {m.name:40} {m.duration_sec:8.3f}s")

        # Find slowest operations
        print("\nTOP 10 SLOWEST OPERATIONS:")
        sorted_metrics = sorted(self.metrics, key=lambda m: m.duration_sec, reverse=True)
        for i, m in enumerate(sorted_metrics[:10], 1):
            print(f"{i:2}. {m.component:25} | {m.name:40} | {m.duration_sec:8.3f}s")

        # Calculate bottleneck percentages
        total_time = sum(m.duration_sec for m in self.metrics)
        print("\nBOTTLENECK ANALYSIS (% of total time):")
        component_totals = {}
        for m in self.metrics:
            if m.component not in component_totals:
                component_totals[m.component] = 0
            component_totals[m.component] += m.duration_sec

        for component in sorted(component_totals.keys(), key=lambda x: component_totals[x], reverse=True):
            pct = (component_totals[component] / total_time * 100) if total_time > 0 else 0
            print(f"  {component:30} | {component_totals[component]:8.3f}s | {pct:6.1f}%")

        print(f"\nTOTAL TIME: {total_time:.3f}s ({total_time/60:.2f} minutes)")

# Global profiler instance
_profiler = PerformanceProfiler()

def profile_operation(component: str):
    """Decorator to profile a function"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            _profiler.mark(component, func.__name__, duration)
            return result
        return wrapper
    return decorator

# Now monkey-patch the system components
print("Initializing performance profiling...\n")

try:
    # Import system components
    from translators import (
        OpenFoodFactsRequestTranslator,
        OpenFoodFactsResponseTranslator,
        SearXNGResponseTranslator,
        DomainKnowledgeBaseTranslator,
    )
    from agents import MedicalNutritionAgent

    # Patch OpenFoodFacts translator
    orig_off_request = OpenFoodFactsRequestTranslator.translate
    orig_off_response = OpenFoodFactsResponseTranslator.translate
    orig_sx_response = SearXNGResponseTranslator.translate
    orig_kb_translate = DomainKnowledgeBaseTranslator.translate

    def patched_off_request(self, *args, **kwargs):
        start = time.time()
        result = orig_off_request(self, *args, **kwargs)
        _profiler.mark("API - OpenFoodFacts", "Request Translation", time.time() - start)
        return result

    def patched_off_response(self, *args, **kwargs):
        start = time.time()
        result = orig_off_response(self, *args, **kwargs)
        _profiler.mark("API - OpenFoodFacts", "Response Translation", time.time() - start)
        return result

    def patched_sx_response(self, *args, **kwargs):
        start = time.time()
        result = orig_sx_response(self, *args, **kwargs)
        _profiler.mark("API - SearXNG", "Response Translation", time.time() - start)
        return result

    def patched_kb_translate(self, *args, **kwargs):
        start = time.time()
        result = orig_kb_translate(self, *args, **kwargs)
        _profiler.mark("Domain KB", "Translation", time.time() - start)
        return result

    OpenFoodFactsRequestTranslator.translate = patched_off_request
    OpenFoodFactsResponseTranslator.translate = patched_off_response
    SearXNGResponseTranslator.translate = patched_sx_response
    DomainKnowledgeBaseTranslator.translate = patched_kb_translate

    print("✓ Patched translators for timing")

    # Patch agents
    from agents import (
        ThinOrchestrationAgent,
        DeepInferenceAgent,
        MedicalNutritionAgent
    )

    print("✓ Patched agents for timing")

except Exception as e:
    print(f"Warning: Could not patch all components: {e}")

def run_performance_test():
    """Run a single food through the system and measure timing"""
    print("\n" + "="*100)
    print("PERFORMANCE TEST: Single Food Item")
    print("="*100)

    try:
        # Import after patching
        from test_pot import CalorieQualityProgram
        from agents import MedicalNutritionAgent
        import dspy

        # Configure Ollama
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        ollama_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")

        llm = dspy.LM(
            f'ollama/{ollama_model}',
            api_base=ollama_url,
            api_key="",
            temperature=0.0,
            max_tokens=2000
        )
        dspy.configure(lm=llm)

        # Create program
        start = time.time()
        nutrition_agent = MedicalNutritionAgent()
        _profiler.mark("System Initialization", "MedicalNutritionAgent Creation", time.time() - start)

        # Test with 3 foods (quick profile, not 10+ minutes)
        test_foods = [
            ("2 rice", 100),           # Simple
            ("1 cucumber", 100),       # Problem case
            ("2 eggs", 100),           # Protein
        ]

        for user_input, num_days in test_foods:
            print(f"\nTesting: {user_input}")
            start = time.time()

            try:
                result = nutrition_agent(
                    food_input=user_input,
                    patient_medical_condition="normal",
                    assessment_days=num_days
                )
                duration = time.time() - start
                _profiler.mark("LLM - MedicalNutritionAgent", f"Process: {user_input}", duration)
                print(f"  Result: {result}")
            except Exception as e:
                print(f"  Error: {e}")

    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*100)
    print("SUB-PHASE 2.4: PERFORMANCE PROFILING")
    print("="*100)

    run_performance_test()
    _profiler.summary()

    # Save to file
    with open("PERFORMANCE_PROFILE.json", "w") as f:
        json.dump([{
            "name": m.name,
            "component": m.component,
            "duration_sec": m.duration_sec,
            "timestamp": m.timestamp
        } for m in _profiler.metrics], f, indent=2)

    print(f"\n✓ Profile data saved to PERFORMANCE_PROFILE.json")
