# Bytelense Project Context

## Project Overview

Bytelense is a scanning and analysis component of the IndiByte platform. It allows users to scan food items via app/web UI, analyzes food labels or objects using OCR capabilities, compares against user dietary profiles, rates food components with a multi-factor scoring system, and generates dynamic UI responses with verdicts. The system integrates with text-to-speech services for accessibility.

## Purpose and Functionality

The core purpose of Bytelense is to solve the challenge of eating healthy by making diet and calorie tracking easier. Instead of requiring users to manually read labels and make dietary decisions, Bytelense allows users to simply scan food items. The system then:

- Runs a quick search on food labels or food objects (for unpackaged items)
- Uses SearXNG as a service/MCP to get results
- Compares results to user profiles and standard food profiles
- Rates components using a multi-factor scoring system
- Writes verdicts based on the analysis
- Creates dynamic UI responses
- Converts verdict text to audio via TTS services like IndexTTS2
- Shows results to the user in the app/webapp

## Technical Architecture

### Backend

- FastAPI with FastMCP server, all asynchronous with micro tooling
- Handles OCR processing and food analysis
- Integrates with SearXNG for search capabilities
- Manages user profiles and eating records

### Frontend

- Built with shadcn components
- Implements generative UI principles
- Handles dynamic UI assembly based on backend verdicts

### Key Technical Challenges

- IndexTTS2 is resource-intensive (even in FP16 mode)
- Service must be called, used, and terminated efficiently
- Multiple components (UI assembly, LLM agent, video camera, audio stream) compete for VRAM
- All operations run asynchronously, requiring careful resource management
- Integration between DSPy, Ollama agents, and dynamic UI generation

## Project Structure

```bash
Bytelense/
├── backend/                # FastAPI + FastMCP server
├── frontend/               # React-based UI with shadcn components  
├── docs/                   # Technical documentation
│   └── UI/                 # UI-specific documentation
├── ReadMe.md              # Component overview
├── QWEN_FRONTEND_PROMPT.md # Frontend development prompt
├── IMPLEMENTATION_STATUS.md # Current development status
└── VALIDATION_RESULTS.md    # Validation test results
```

## Key Technologies

- **Backend**: FastAPI, FastMCP (async architecture)
- **Frontend**: shadcn UI components, React
- **OCR**: Integration with Chandra-OCR (via main IndiByte dependencies)
- **Search**: SearXNG integration for food information retrieval
- **AI/ML**: DSPy for AI orchestration, Ollama for local inference
- **TTS**: Integration with IndexTTS2 for audio feedback
- **STT**: OpenAI Whisper for speech-to-text processing
- **UI Generation**: Generative UI techniques for dynamic interfaces

## Core Workflow

1. User scans food item via camera in app/web UI
2. OCR processes the food label or identifies the food object
3. System searches for food information using SearXNG
4. Results compared to user's dietary profile
5. Multi-factor scoring system evaluates components
6. Verdict generated based on comparison
7. Dynamic UI assembled based on verdict
8. Verdict text converted to speech
9. Audio + visual response presented to user
10. Information stored in user's eating record

## Key Development Considerations

- VRAM management across multiple competing processes (UI, LLM, camera, audio)
- Asynchronous handling in live user sessions
- Efficient DSPy and Ollama agent integration for UI assembly
- Tool-calling optimization to reduce LLM decision burden
- Real-time processing requirements for user experience

## Integration Points

- Connects to main IndiByte database for food information
- Uses SearXNG for external search capabilities  
- Integrates with TTS/STT services for accessibility
- Stores user profiles and dietary records
- Works with camera hardware for food scanning
