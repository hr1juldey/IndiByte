#!/bin/bash
# Backend Test Script
# Tests all critical components before starting the server

set -e  # Exit on error

echo "======================================================================"
echo "Bytelense Backend Test Script"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Testing: $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Change to backend directory
cd "$(dirname "$0")"

echo "[1/7] Checking Python Dependencies"
echo "-----------------------------------"
run_test "FastAPI" "python -c 'import fastapi'"
run_test "Socket.IO" "python -c 'import socketio'"
run_test "Pydantic v2" "python -c 'import pydantic; assert pydantic.VERSION.startswith(\"2\")'"
run_test "httpx" "python -c 'import httpx'"
run_test "aiofiles" "python -c 'import aiofiles'"
echo ""

echo "[2/7] Checking External Services"
echo "-----------------------------------"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama is running"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Ollama is NOT running (http://localhost:11434)"
    echo "   Start with: ollama serve"
    ((TESTS_FAILED++))
fi

if curl -s "http://192.168.1.4/search?q=test&format=json" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} SearXNG is accessible"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} SearXNG is NOT accessible (http://192.168.1.4)"
    echo "   This is OK for simplified testing"
fi
echo ""

echo "[3/7] Checking Configuration"
echo "-----------------------------------"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} .env file missing"
    echo "   Copy from .env.example"
    ((TESTS_FAILED++))
fi

if [ -d "data/profiles" ]; then
    PROFILE_COUNT=$(ls -1 data/profiles/*.json 2>/dev/null | wc -l)
    echo -e "${GREEN}✓${NC} Profile directory exists (${PROFILE_COUNT} profiles)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Profile directory missing"
    echo "   Create with: mkdir -p data/profiles"
    ((TESTS_FAILED++))
fi
echo ""

echo "[4/7] Validating Python Modules"
echo "-----------------------------------"
run_test "schemas.py" "python -c 'from app.models.schemas import DetailedAssessment'"
run_test "health_modeling.py" "python -c 'from app.services.health_modeling import health_modeling_engine'"
run_test "scan_simple.py" "python -c 'from app.api import scan_simple'"
run_test "main.py" "python -c 'from app.main import app, sio'"
echo ""

echo "[5/7] Testing Health Modeling Engine"
echo "-----------------------------------"
python << 'PYEOF'
from app.models.schemas import Demographics, LifestyleHabits, HealthGoals
from app.services.health_modeling import health_modeling_engine
import asyncio

async def test():
    demo = Demographics(age=30, gender="male", height_cm=175, weight_kg=75)
    lifestyle = LifestyleHabits(
        sleep_hours=7, work_style="desk_job", exercise_frequency="3-4_times_week",
        commute_type="bike", smoking="no", alcohol="light", meals_per_day=3
    )
    goals = HealthGoals(
        fitness_goal="weight_loss", target_weight_kg=70,
        dietary_restrictions=[], condition_focus=[]
    )

    metrics, targets = await health_modeling_engine.calculate_metrics(demo, lifestyle, goals)

    assert metrics.bmi > 0
    assert metrics.bmr > 0
    assert targets.calories > 0
    print(f"BMI: {metrics.bmi}, BMR: {metrics.bmr}, Target Calories: {targets.calories}")
    print("✓ HealthModelingEngine working")

asyncio.run(test())
PYEOF
((TESTS_PASSED++))
echo ""

echo "[6/7] Checking Server Start Capability"
echo "-----------------------------------"
echo "Attempting to import FastAPI app..."
if python -c "from app.main import socket_app; print('✓ App imports successfully')" 2>&1; then
    echo -e "${GREEN}✓${NC} Server can be started"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Server import failed"
    ((TESTS_FAILED++))
fi
echo ""

echo "[7/7] Summary"
echo "======================================================================"
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Backend is ready.${NC}"
    echo ""
    echo "To start the server, run:"
    echo "  cd backend"
    echo "  uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    echo "Or use the run script:"
    echo "  python -m app.main"
    exit 0
else
    echo -e "${RED}Some tests failed. Please fix the issues above.${NC}"
    exit 1
fi
