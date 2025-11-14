# Bytelense Backend

AI-powered food scanning and nutritional analysis backend built with FastAPI, DSPy, and Ollama.

## Architecture

- **FastAPI**: Async web framework
- **Socket.IO**: Real-time WebSocket communication
- **DSPy + Ollama**: Local LLM reasoning with ReAct agents
- **OpenFoodFacts**: Primary nutrition database
- **SearXNG**: Fallback web search via FastMCP
- **Chandra OCR**: Text extraction from labels
- **pyzbar**: Barcode detection

## Prerequisites

1. **Python 3.12+**
2. **Ollama** installed and running:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama pull qwen3:30b  # or qwen3:8b for development
   ```

3. **SearXNG** - Already running at http://192.168.1.4
   - Verify: `curl "http://192.168.1.4/search?q=test&format=json"`
   - JSON format is enabled and working ✅

4. **pyzbar dependencies** (for barcode detection):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libzbar0

   # macOS
   brew install zbar
   ```

## Setup

1. **Install dependencies**:
   ```bash
   cd backend
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r ../requirements.txt
   pip install pyzbar  # Not in requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

3. **Run server**:
   ```bash
   python -m app.main
   # Or with uvicorn:
   uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
   ```

4. **Verify**:
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

## API Endpoints

### REST APIs

- `POST /api/auth/login` - Check if user exists
- `POST /api/auth/onboard` - Create new user profile
- `GET /api/profile/{name}` - Get user profile
- `PATCH /api/profile/{name}` - Update profile
- `GET /health` - Health check
- `GET /api/config` - Client configuration

### WebSocket Events

**Namespace**: `/`

**Client → Server**:
- `connect` - Establish connection
- `start_scan` - Initiate food scan with image data

**Server → Client**:
- `scan_progress` - Progress updates (10%, 30%, 60%, 85%)
- `scan_complete` - Final result with verdict and UI schema
- `scan_error` - Error notification

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + SocketIO
│   ├── core/
│   │   ├── config.py           # Settings management
│   │   └── profile_store.py   # User profile storage (JSON)
│   ├── models/
│   │   ├── schemas.py          # Pydantic models
│   │   └── dspy_modules.py     # DSPy ReAct agents
│   ├── services/
│   │   ├── image_processing.py # Barcode + OCR
│   │   ├── nutrition_api.py    # OpenFoodFacts client
│   │   ├── scoring.py          # AI scoring service
│   │   ├── citation_manager.py # Perplexity-style citations
│   │   └── ui_generator.py     # Generative UI schemas
│   ├── mcp/
│   │   └── searxng_tools.py    # FastMCP tools for DSPy
│   └── api/
│       ├── auth.py             # Auth endpoints
│       └── scan.py             # WebSocket scan handler
├── data/
│   └── profiles/               # User profile JSON files
├── .env.example
└── README.md
```

## Scanning Flow

1. **Client** sends image via WebSocket `start_scan` event
2. **Image Processing**: Detect barcode or extract text (OCR)
3. **Nutrition Retrieval**: Query OpenFoodFacts → fallback to SearXNG
4. **AI Scoring**: DSPy ReAct agent with Ollama analyzes nutrition vs user profile
   - Calls tools: `search_nutrition_database`, `get_health_guidelines`, `compare_similar_products`
   - Generates score (0-10), verdict (good/moderate/avoid), reasoning with citations
5. **UI Generation**: Backend creates component schema for frontend
6. **Response**: Send complete result with UI schema back to client

## Development

### Testing Authentication

```bash
# Login (new user)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "john"}'

# Onboard
curl -X POST http://localhost:8000/api/auth/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john",
    "age": 30,
    "goals": ["weight_loss"],
    "allergies": ["dairy"],
    "nutritional_focus": ["sugar", "calories"]
  }'
```

### Testing WebSocket (Python client)

```python
import socketio
import base64

sio = socketio.Client()
sio.connect('http://localhost:8000')

# Read image file
with open('food_label.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Start scan
sio.emit('start_scan', {
    'user': 'john',
    'image_data': image_data,
    'source': 'upload',
    'format': 'jpeg'
})

# Listen for progress
@sio.on('scan_progress')
def on_progress(data):
    print(f"Progress: {data['progress']}% - {data['message']}")

@sio.on('scan_complete')
def on_complete(data):
    print(f"Complete! Score: {data['result']['scoring']['score']}")
    print(f"Verdict: {data['result']['scoring']['verdict']}")

sio.wait()
```

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
systemctl restart ollama  # Linux with systemd
```

### SearXNG not accessible
```bash
# Check if SearXNG is running
curl http://localhost:8888/search?q=test&format=json

# Enable JSON format in settings.yml
# Restart container
```

### Chandra OCR errors
```bash
# Reinstall transformers
pip install --upgrade transformers
pip install --upgrade chandra-ocr
```

### Barcode detection not working
```bash
# Install zbar system library
sudo apt-get install libzbar0  # Debian/Ubuntu
brew install zbar              # macOS

# Reinstall pyzbar
pip uninstall pyzbar
pip install pyzbar
```

## Performance Notes

- **Ollama inference time**: 2-10s with GPU, 30-60s CPU-only
- **Model recommendations**:
  - Development: `qwen3:8b` (5.2GB, fast)
  - Testing: `deepseek-r1:8b` (5.2GB, good reasoning)
  - Production: `qwen3:30b` (18GB, best quality)
- **RAM requirements**:
  - qwen3:8b: 10GB minimum
  - qwen3:30b: 24GB minimum
- **GPU**: Highly recommended (10x speedup)

## Next Steps

1. Implement frontend (React + Vite + shadcn/ui)
2. Create dynamic UI renderer for component schemas
3. Add WebSocket client for real-time updates
4. Build camera capture and image upload components
5. Implement citation UI (Perplexity-style references)

## License

MIT
