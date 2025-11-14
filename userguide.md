# SearXNG User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Independent Operation](#independent-operation)
3. [Quick Start](#quick-start)
4. [Accessing SearXNG](#accessing-searxng)
5. [Using the Web Interface](#using-the-web-interface)
6. [Using the JSON API](#using-the-json-api)
7. [Integration with AI Applications](#integration-with-ai-applications)
8. [Ollama MCP Server Integration](#ollama-mcp-server-integration)
9. [CLI Helper Script](#cli-helper-script)
10. [Service Management](#service-management)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance](#maintenance)
13. [Quick Reference](#quick-reference)

---

## Introduction

### What is SearXNG?

SearXNG is a privacy-respecting metasearch engine that aggregates results from over 70 search engines without tracking you. Your instance is now running 24/7 on your home network.

### Your Setup

- **Server**: Your PC (192.168.1.4)
- **Access**: All devices on home WiFi network
- **Protocol**: HTTP (local network only, HTTPS not available/needed)
- **Auto-start**: Enabled (starts automatically when PC boots)
- **Privacy**: All searches stay on your local network
- **External Access**: Not available (ISP blocks port 80, by design for security)
- **Docker**: Runs on System Docker, not Docker Desktop

### Key Features

✅ **Private**: No tracking, no data collection
✅ **Fast**: Local network = instant results
✅ **Always Available**: Runs 24/7 on your PC
✅ **No Rate Limits**: Use as much as you want
✅ **JSON API**: Perfect for AI applications
✅ **Multi-Device**: Access from any device on your network

---

## Independent Operation

### SearXNG Runs Independently

**Important:** SearXNG is running as a **systemd service**, which means:

✅ **Runs independently** of any IDE (VSCode, PyCharm, etc.)
✅ **Stays running** after you close all applications
✅ **Survives** terminal/shell closures
✅ **Auto-starts** when your PC boots
✅ **Runs 24/7** as a background daemon service

### You Can Close VSCode/Terminal

After setup, you can:

- Close VSCode
- Close all terminal windows
- Log out and back in
- Restart your PC (service auto-starts)

**SearXNG will keep running!**

### Verification

Test that it's running independently:

```bash
# Check service status (runs without VSCode)
systemctl is-active searxng-docker.service
# Output: active

# Test from browser (works without VSCode)
http://192.168.1.4/search?q=test&format=json

# Test from command line (works without VSCode)
curl "http://localhost/search?q=test&format=json"
```

### Service Architecture

```bash
┌─────────────────────────────────────┐
│       Your PC (Always Running)      │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐   │
│  │  systemd (System Manager)    │   │
│  │                              │   │
│  │  ├─ searxng-docker.service   │   │
│  │  │   (Auto-starts on boot)   │   │
│  │  │                           │   │
│  │  │   ├─ Docker Daemon        │   │
│  │  │   │   ├─ Caddy (HTTP)     │   │
│  │  │   │   ├─ SearXNG          │   │
│  │  │   │   └─ Redis (Cache)    │   │
│  └──────────────────────────────┘   │
│                                     │
│  ▲ Service runs independently       │
│  ▲ No dependency on IDE/Terminal    │
│  ▲ Survives all app closures        │
└─────────────────────────────────────┘
```

### What This Means

**For Development:**

- Develop your AI apps in any IDE
- Close the IDE when done
- SearXNG keeps running for your apps

**For Production:**

- No need to keep terminal open
- No need to remember to start service
- Works immediately after PC reboot

**For Daily Use:**

- Access from phone while PC is in another room
- Use from laptop while PC runs headless
- Integrate with automation scripts that run 24/7

---

## Quick Start

### 30 Second Test

1. **From This PC**:
   - Open browser → Go to `http://localhost/` (with trailing slash)
   - Type "python" → Press Enter
   - See results! ✅

2. **From Your Phone**:
   - Connect to home WiFi
   - Open browser → Go to `http://192.168.1.4/` (with trailing slash)
   - Search for anything
   - Works! ✅

**Important:** Use `http://192.168.1.4/` (with slash) for the web interface, NOT `/search`

### First-Time Setup Checklist

- [x] SearXNG installed and configured
- [x] Service running and auto-start enabled
- [x] Accessible on home network
- [x] JSON API enabled
- [x] Helper scripts created
- [x] Documentation complete

**You're all set!** Everything is already working.

---

## Accessing SearXNG

### From Different Devices

#### 🖥️ This PC (Server)

**Web Browser:**

```bash
http://localhost
http://192.168.1.4
```

**Command Line:**

```bash
curl http://localhost
```

#### 📱 Phone (Android/iOS)

1. **Connect to home WiFi**
2. **Open any browser** (Chrome, Safari, Firefox)
3. **Enter URL**: `http://192.168.1.4/` (with trailing slash)
4. **Search away!**

**Common Mistake:**

- ❌ Don't use: `http://192.168.1.4/search` (this is the API endpoint)
- ✅ Use: `http://192.168.1.4/` (this is the web interface)

**Pro Tip**: Add to home screen for quick access:

- Android: Menu (⋮) → Add to Home Screen
- iPhone: Share (⎙) → Add to Home Screen

#### 💻 Laptop (Windows/Mac/Linux)

**Browser:**

- Open any browser
- Go to: `http://192.168.1.4`

**Command Line:**

```bash
# Windows PowerShell
Invoke-RestMethod -Uri "http://192.168.1.4/search?q=test&format=json"

# Mac/Linux
curl "http://192.168.1.4/search?q=test&format=json"
```

#### 📺 Tablet/Smart TV

1. Connect to home WiFi
2. Open browser app
3. Go to: `http://192.168.1.4`

### Access URLs Summary

| Device Type | URL | Notes |
|-------------|-----|-------|
| This PC (Web UI) | `http://localhost/` or `http://192.168.1.4/` | Just `/` not `/search` |
| Phone/Tablet (Web UI) | `http://192.168.1.4/` | Must be on same WiFi |
| JSON API | `http://192.168.1.4/search?q={query}&format=json` | For apps/scripts |

**IMPORTANT:**

- For the **web interface**, use just `/` (e.g., `http://192.168.1.4/`)
- The `/search` endpoint is for the **JSON API** only
- If you go to `/search` in a browser, it may show JSON instead of the search page

---

## Using the Web Interface

### Basic Search

1. **Go to**: `http://192.168.1.4`
2. **Type your query** in the search box
3. **Press Enter** or click search
4. **View results** from multiple search engines

### Advanced Search Options

#### Categories

Click the category icons to search specific types of content:

- **General** - Web pages (default)
- **Images** - Image search
- **Videos** - Video search
- **News** - News articles
- **Maps** - Map search
- **Music** - Music and audio
- **IT** - Technology and programming
- **Science** - Scientific articles
- **Files** - File search

#### Preferences

Click **Preferences** (gear icon) to customize:

- **Search engines**: Enable/disable specific engines
- **Language**: Set your preferred language
- **Theme**: Change appearance
- **Autocomplete**: Enable search suggestions
- **Results per page**: Adjust number of results

#### Search Syntax

Use these operators for better results:

```bash
"exact phrase"           - Search exact phrase
site:example.com python  - Search within specific site
python -java            - Exclude term (search python, not java)
filetype:pdf guide      - Search specific file types
python OR java          - Either term
```

### Search Examples

**Basic:**

```bash
machine learning
```

**Exact phrase:**

```bash
"artificial intelligence"
```

**Site-specific:**

```bash
site:github.com python libraries
```

**Exclude term:**

```bash
python tutorial -java
```

**File type:**

```bash
machine learning filetype:pdf
```

---

## Using the JSON API

### Why Use the API?

- **Integrate with applications**: Build search into your apps
- **Automate searches**: Script batch searches
- **AI applications**: Feed search results to AI models
- **Custom interfaces**: Build your own search UI

### API Endpoint

```bash
http://192.168.1.4/search
```

### Basic Usage

#### Simple Search

```bash
curl "http://192.168.1.4/search?q=python&format=json"
```

#### Response Format

```json
{
  "query": "python",
  "number_of_results": 25,
  "results": [
    {
      "url": "https://www.python.org/",
      "title": "Welcome to Python.org",
      "content": "The official home of the Python Programming Language",
      "engine": "google",
      "score": 1.0
    },
    ...
  ]
}
```

### API Parameters

#### Required

| Parameter | Description | Example |
|-----------|-------------|---------|
| `q` | Search query | `q=python` |
| `format` | Response format (use `json`) | `format=json` |

#### Optional

| Parameter | Description | Values | Example |
|-----------|-------------|--------|---------|
| `categories` | Search category | `general`, `images`, `videos`, `news`, `it` | `categories=images` |
| `engines` | Specific engines to use | Comma-separated engine names | `engines=google,bing` |
| `language` | Search language | Language code (e.g., `en`, `es`) | `language=en` |
| `pageno` | Page number | Number (default: 1) | `pageno=2` |
| `time_range` | Time filter | `day`, `week`, `month`, `year` | `time_range=week` |
| `safesearch` | Safe search level | `0`, `1`, `2` | `safesearch=1` |

### API Examples

#### Basic Search with Pretty Print

```bash
curl "http://192.168.1.4/search?q=python&format=json" | jq .
```

#### Search Images

```bash
curl "http://192.168.1.4/search?q=cats&format=json&categories=images"
```

#### Search with Specific Engines

```bash
curl "http://192.168.1.4/search?q=news&format=json&engines=google,duckduckgo"
```

#### Recent Results (Last Week)

```bash
curl "http://192.168.1.4/search?q=ai&format=json&time_range=week"
```

#### Get Only URLs

```bash
curl "http://192.168.1.4/search?q=python&format=json" | jq -r '.results[].url'
```

#### Get Titles and URLs

```bash
curl "http://192.168.1.4/search?q=python&format=json" | jq -r '.results[] | "\(.title)\n\(.url)\n"'
```

#### Count Results

```bash
curl "http://192.168.1.4/search?q=test&format=json" | jq '.results | length'
```

#### Extract Specific Fields

```bash
# Get top 5 titles
curl "http://192.168.1.4/search?q=python&format=json" | jq -r '.results[:5] | .[] | .title'

# Get URLs and scores
curl "http://192.168.1.4/search?q=python&format=json" | jq -r '.results[] | "\(.url) - Score: \(.score)"'
```

---

## Integration with AI Applications

### Python Integration

#### Simple Function

```python
import requests

def search_web(query):
    """Search SearXNG and return results"""
    url = "http://192.168.1.4/search"
    params = {
        "q": query,
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()["results"]

# Usage
results = search_web("machine learning")
for result in results[:5]:
    print(f"{result['title']}: {result['url']}")
```

#### Advanced Class

```python
import requests
from typing import List, Dict, Optional

class SearXNG:
    def __init__(self, base_url: str = "http://192.168.1.4"):
        self.base_url = base_url
        self.search_endpoint = f"{base_url}/search"

    def search(self,
               query: str,
               category: Optional[str] = None,
               engines: Optional[List[str]] = None,
               num_results: Optional[int] = None) -> List[Dict]:
        """
        Search SearXNG with advanced options

        Args:
            query: Search query
            category: Category to search (images, videos, news, etc.)
            engines: List of engines to use
            num_results: Number of results to return

        Returns:
            List of search results
        """
        params = {
            "q": query,
            "format": "json"
        }

        if category:
            params["categories"] = category

        if engines:
            params["engines"] = ",".join(engines)

        response = requests.get(self.search_endpoint, params=params)
        response.raise_for_status()

        results = response.json()["results"]

        if num_results:
            return results[:num_results]

        return results

    def search_images(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search for images"""
        return self.search(query, category="images", num_results=num_results)

    def search_news(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search for news"""
        return self.search(query, category="news", num_results=num_results)

# Usage
searxng = SearXNG()

# Basic search
results = searxng.search("python programming")

# Image search
images = searxng.search_images("cats", num_results=5)

# News search with specific engines
news = searxng.search("AI", category="news", engines=["google", "bing"])

# Print results
for result in results[:5]:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Snippet: {result['content'][:100]}...")
    print("-" * 80)
```

#### Integration with LangChain

```python
from langchain.tools import Tool
import requests

def search_searxng(query: str) -> str:
    """Search the web using SearXNG"""
    url = "http://192.168.1.4/search"
    params = {"q": query, "format": "json"}
    response = requests.get(url, params=params)
    results = response.json()["results"][:5]

    formatted_results = []
    for r in results:
        formatted_results.append(
            f"Title: {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Snippet: {r['content']}\n"
        )

    return "\n\n".join(formatted_results)

# Create LangChain tool
search_tool = Tool(
    name="Web Search",
    func=search_searxng,
    description="Useful for searching the web for current information"
)
```

### Node.js Integration

#### Simple Functions

```javascript
const axios = require('axios');

async function searchWeb(query) {
    const response = await axios.get('http://192.168.1.4/search', {
        params: {
            q: query,
            format: 'json'
        }
    });
    return response.data.results;
}

// Usage
searchWeb('machine learning').then(results => {
    results.slice(0, 5).forEach(result => {
        console.log(`${result.title}: ${result.url}`);
    });
});
```

#### Advanced Classes

```javascript
const axios = require('axios');

class SearXNG {
    constructor(baseURL = 'http://192.168.1.4') {
        this.baseURL = baseURL;
        this.searchEndpoint = `${baseURL}/search`;
    }

    async search(query, options = {}) {
        const params = {
            q: query,
            format: 'json',
            ...options
        };

        const response = await axios.get(this.searchEndpoint, { params });
        return response.data.results;
    }

    async searchImages(query, numResults = 10) {
        const results = await this.search(query, { categories: 'images' });
        return results.slice(0, numResults);
    }

    async searchNews(query, numResults = 10) {
        const results = await this.search(query, { categories: 'news' });
        return results.slice(0, numResults);
    }
}

// Usage
const searxng = new SearXNG();

// Basic search
searxng.search('python programming').then(results => {
    results.slice(0, 5).forEach(result => {
        console.log(`Title: ${result.title}`);
        console.log(`URL: ${result.url}`);
        console.log(`Snippet: ${result.content.substring(0, 100)}...`);
        console.log('-'.repeat(80));
    });
});
```

### Shell Script Integration

```bash
#!/bin/bash
# search_and_process.sh

QUERY="$1"
API_URL="http://192.168.1.4/search"

# Perform search
RESULTS=$(curl -s "${API_URL}?q=${QUERY}&format=json")

# Extract URLs
echo "$RESULTS" | jq -r '.results[].url' > urls.txt

# Extract titles and URLs
echo "$RESULTS" | jq -r '.results[] | "\(.title)\n\(.url)\n"' > results.txt

# Count results
COUNT=$(echo "$RESULTS" | jq '.results | length')
echo "Found $COUNT results for: $QUERY"

# Get top 5 results
echo "$RESULTS" | jq -r '.results[:5] | .[] | "[\(.engine)] \(.title)\n    \(.url)\n"'
```

---

## Ollama MCP Server Integration

### Overview

SearXNG works perfectly with Ollama-based MCP (Model Context Protocol) servers. Since SearXNG runs as an independent systemd service, your MCP server can access it 24/7 without any IDE or terminal running.

### Why This Works

✅ **Independent Operation**: SearXNG runs separately from your development environment
✅ **Always Available**: Service is always running and auto-starts on boot
✅ **Local Network**: Fast, private access from same machine or network
✅ **No Authentication**: Simple HTTP access (secure on local network)
✅ **Standard HTTP API**: Works with any HTTP client library

### Basic MCP Tool Configuration

#### Endpoint Configuration

Your MCP server should use one of these endpoints:

```python
# If MCP server runs on same machine as SearXNG
SEARXNG_ENDPOINT = "http://localhost/search"

# If MCP server runs on different machine (same network)
SEARXNG_ENDPOINT = "http://192.168.1.4/search"
```

#### Simple MCP Tool Example

```python
import requests
from typing import Dict, List

class SearXNGTool:
    """Web search tool for MCP server using local SearXNG"""

    def __init__(self, endpoint: str = "http://localhost/search"):
        self.endpoint = endpoint

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search the web using SearXNG

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of search results with title, url, and content
        """
        try:
            response = requests.get(
                self.endpoint,
                params={
                    "q": query,
                    "format": "json"
                },
                timeout=10
            )
            response.raise_for_status()

            results = response.json().get("results", [])
            return results[:num_results]

        except requests.RequestException as e:
            return {"error": f"Search failed: {str(e)}"}

    def format_results(self, results: List[Dict]) -> str:
        """Format results for LLM consumption"""
        if isinstance(results, dict) and "error" in results:
            return results["error"]

        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"{i}. {result.get('title', 'No title')}\n"
                f"   URL: {result.get('url', 'No URL')}\n"
                f"   Summary: {result.get('content', 'No description')[:200]}...\n"
            )

        return "\n".join(formatted)

# Usage in MCP server
searxng_tool = SearXNGTool()
results = searxng_tool.search("python best practices")
formatted_output = searxng_tool.format_results(results)
```

#### Advanced MCP Tool with Error Handling

```python
import requests
from typing import Dict, List, Optional
import logging

class RobustSearXNGTool:
    """Production-ready SearXNG tool for MCP servers"""

    def __init__(
        self,
        endpoint: str = "http://localhost/search",
        timeout: int = 10,
        retry_attempts: int = 2
    ):
        self.endpoint = endpoint
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.logger = logging.getLogger(__name__)

    def search(
        self,
        query: str,
        num_results: int = 5,
        category: Optional[str] = None,
        engines: Optional[List[str]] = None
    ) -> Dict:
        """
        Advanced search with retry logic

        Args:
            query: Search query
            num_results: Number of results to return
            category: Search category (images, news, videos, etc.)
            engines: List of specific engines to use

        Returns:
            Dict with results or error information
        """
        params = {
            "q": query,
            "format": "json"
        }

        if category:
            params["categories"] = category

        if engines:
            params["engines"] = ",".join(engines)

        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(
                    self.endpoint,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()
                results = data.get("results", [])[:num_results]

                return {
                    "success": True,
                    "query": query,
                    "num_results": len(results),
                    "results": results
                }

            except requests.Timeout:
                self.logger.warning(f"Search timeout (attempt {attempt + 1})")
                if attempt == self.retry_attempts - 1:
                    return {
                        "success": False,
                        "error": "Search timed out after multiple attempts"
                    }

            except requests.RequestException as e:
                self.logger.error(f"Search error: {e}")
                return {
                    "success": False,
                    "error": f"Search failed: {str(e)}"
                }

        return {
            "success": False,
            "error": "Search failed after retries"
        }

    def health_check(self) -> bool:
        """Check if SearXNG is accessible"""
        try:
            response = requests.get(
                self.endpoint.replace("/search", ""),
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

# Usage
tool = RobustSearXNGTool()

# Check health before using
if tool.health_check():
    result = tool.search("AI agents", num_results=3)
    if result["success"]:
        print(f"Found {result['num_results']} results")
    else:
        print(f"Error: {result['error']}")
else:
    print("SearXNG service is not accessible")
```

### Integration with Ollama

#### Example: Ollama Function Calling

```python
import ollama
import requests

def search_web(query: str) -> str:
    """Search the web for information"""
    response = requests.get(
        "http://localhost/search",
        params={"q": query, "format": "json"}
    )
    results = response.json()["results"][:3]

    output = []
    for r in results:
        output.append(f"Title: {r['title']}\nURL: {r['url']}\nSummary: {r['content'][:150]}\n")

    return "\n---\n".join(output)

# Define tool for Ollama
tools = [{
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the web for current information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
}]

# Use with Ollama
response = ollama.chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'What are the latest AI developments?'}],
    tools=tools
)
```

### Testing the Integration

#### Verify SearXNG is Accessible

```python
import requests

def test_searxng():
    """Test SearXNG connectivity"""
    try:
        # Test endpoint
        response = requests.get("http://localhost")
        print(f"✅ Web UI accessible: HTTP {response.status_code}")

        # Test API
        api_response = requests.get(
            "http://localhost/search",
            params={"q": "test", "format": "json"}
        )
        results = api_response.json().get("results", [])
        print(f"✅ API accessible: {len(results)} results returned")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Run test
if __name__ == "__main__":
    test_searxng()
```

#### Expected Output

```bash
✅ Web UI accessible: HTTP 200
✅ API accessible: 27 results returned
```

### Browser Verification

You can verify it works by opening this URL in your browser:

```bash
http://192.168.1.4/search?q=test&format=json
```

This will return JSON results, confirming the API is working.

### Configuration Tips

#### For Same Machine

```python
# MCP server on same machine as SearXNG
SEARXNG_CONFIG = {
    "endpoint": "http://localhost/search",
    "timeout": 10,
    "max_results": 5
}
```

#### For Network Access

```python
# MCP server on different machine (same network)
SEARXNG_CONFIG = {
    "endpoint": "http://192.168.1.4/search",
    "timeout": 15,  # Slightly higher timeout for network
    "max_results": 5
}
```

### Common Issues

#### "Connection refused"

**Problem**: MCP server can't reach SearXNG

**Solutions**:

1. Check service is running: `systemctl status searxng-docker.service`
2. Verify URL is correct: `http://localhost/search` or `http://192.168.1.4/search`
3. Test with curl: `curl http://localhost/search?q=test&format=json`

#### Slow responses

**Problem**: Searches taking too long

**Solutions**:

1. Increase timeout in MCP tool (default: 10s, try 15-20s)
2. Reduce `num_results` requested
3. Check your internet connection

#### Empty results

**Problem**: Search returns no results

**Solutions**:

1. Test query in browser first
2. Check if search engines are enabled in SearXNG preferences
3. Verify internet connectivity from server

### Complete Example

Here's a complete working example:

```python
# complete_mcp_searxng.py
import requests
from typing import Dict, List

class MCPSearXNG:
    """Complete SearXNG integration for MCP servers"""

    def __init__(self):
        self.endpoint = "http://localhost/search"
        self.timeout = 10

    def search(self, query: str, limit: int = 5) -> Dict:
        """Execute web search"""
        try:
            response = requests.get(
                self.endpoint,
                params={"q": query, "format": "json"},
                timeout=self.timeout
            )
            response.raise_for_status()

            results = response.json()["results"][:limit]

            return {
                "success": True,
                "results": [
                    {
                        "title": r["title"],
                        "url": r["url"],
                        "snippet": r.get("content", "")[:200]
                    }
                    for r in results
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Test it
if __name__ == "__main__":
    searcher = MCPSearXNG()
    result = searcher.search("python programming")

    if result["success"]:
        print(f"Found {len(result['results'])} results:")
        for i, r in enumerate(result["results"], 1):
            print(f"\n{i}. {r['title']}")
            print(f"   {r['url']}")
    else:
        print(f"Error: {result['error']}")
```

Save this file and run it to verify your setup works!

### Summary

**What You Get:**

- ✅ Always-available search API for your MCP server
- ✅ No external API keys needed
- ✅ Privacy-respecting (searches stay local)
- ✅ Fast (local network speed)
- ✅ Works 24/7 without manual intervention

**How to Use:**

1. Your MCP server calls `http://localhost/search`
2. SearXNG returns JSON results
3. Your MCP server processes and returns results to Ollama
4. Everything works even when VSCode is closed!

---

## CLI Helper Script

### Using search.sh

A helper script has been created for easy CLI searches.

#### Basic Usage Example

```bash
./search.sh "your search query"
```

#### Options

| Option | Description |
|--------|-------------|
| `--raw` | Output raw JSON (default) |
| `--pretty` | Pretty print JSON |
| `--urls` | Show only URLs |
| `--titles` | Show titles and URLs |
| `--count` | Show number of results |
| `--category=X` | Search specific category |
| `--engines=X` | Use specific engines |

#### Examples

**Basic search:**

```bash
./search.sh "python tutorial"
```

**Pretty print:**

```bash
./search.sh "machine learning" --pretty
```

**Get only URLs:**

```bash
./search.sh "best practices" --urls
```

**Show titles and URLs:**

```bash
./search.sh "linux commands" --titles
```

**Count results:**

```bash
./search.sh "artificial intelligence" --count
```

**Search images:**

```bash
./search.sh "cats" --category=images --urls
```

**Use specific engines:**

```bash
./search.sh "latest news" --engines=google,bing --titles
```

### Make Script Available Globally

To use the script from anywhere:

```bash
# Copy to system path
sudo cp search.sh /usr/local/bin/searxng-search
sudo chmod +x /usr/local/bin/searxng-search

# Now use from anywhere
searxng-search "your query" --pretty
```

---

## Service Management

### Systemd Commands

#### Check Status

```bash
sudo systemctl status searxng-docker.service
```

**Expected output:**

```bash
● searxng-docker.service - SearXNG service
     Loaded: loaded (... enabled ...)
     Active: active (running) since ...
```

#### Start Service

```bash
sudo systemctl start searxng-docker.service
```

#### Stop Service

```bash
sudo systemctl stop searxng-docker.service
```

#### Restart Service

```bash
sudo systemctl restart searxng-docker.service
```

#### View Logs

```bash
# Follow logs in real-time
sudo journalctl -u searxng-docker.service -f

# View last 50 lines
sudo journalctl -u searxng-docker.service -n 50

# View logs from today
sudo journalctl -u searxng-docker.service --since today
```

### Docker Commands

#### Check Running Containers

```bash
docker ps
```

**Expected output:**

```bash
NAMES     STATUS         PORTS
searxng   Up X minutes   127.0.0.1:8080->8080/tcp
redis     Up X minutes   6379/tcp
caddy     Up X minutes
```

#### View Docker Logs

```bash
# All containers
docker compose logs -f

# Specific container
docker compose logs -f searxng
docker compose logs -f caddy
docker compose logs -f redis

# Last 50 lines
docker compose logs --tail=50
```

#### Restart Containers

```bash
# Restart all
docker compose restart

# Restart specific container
docker compose restart searxng
```

### Service Auto-Start

**Verify auto-start is enabled:**

```bash
systemctl is-enabled searxng-docker.service
```

Should return: `enabled`

**Test auto-start:**

1. Restart your PC
2. Wait 1-2 minutes after boot
3. Check if service is running:

   ```bash
   sudo systemctl status searxng-docker.service
   ```

---

## Common Issues and Solutions

### "I see JSON instead of the search page!"

**Problem:** Browser shows JSON data instead of the search interface

**Solution:** You're using the wrong URL!

```bash
❌ WRONG: http://192.168.1.4/search
✅ RIGHT: http://192.168.1.4/
```

The `/search` endpoint is for the JSON API. For the web interface, just use the IP address with a trailing slash.

### Mobile browser won't let me search

**Problem:** Page loads but search doesn't work on phone

**Solution:** This was a Content Security Policy issue that has been fixed. If you still experience it:

1. **Clear browser cache** on mobile
2. **Force refresh** the page
3. Try **private/incognito mode**
4. Make sure you're using `http://192.168.1.4/` not `https://`

### Docker Desktop doesn't show containers

**Problem:** Docker Desktop GUI shows no containers but SearXNG is working

**Explanation:** You have two separate Docker installations:

- **System Docker** - Where SearXNG runs (`/var/run/docker.sock`)
- **Docker Desktop** - Separate daemon (`~/.docker/desktop/docker.sock`)

**Solution:** Use command line to manage containers:

```bash
# Switch to system Docker context
docker context use default

# Now you can see containers
docker ps

# Manage containers
docker compose logs -f
sudo systemctl status searxng-docker.service
```

Docker Desktop and System Docker are completely separate and cannot share containers. Your SearXNG runs on System Docker, which is correct for server applications.

### DuckDNS domain doesn't work

**Problem:** `https://indibyte.duckdns.org` doesn't load

**Explanation:** This is expected for local-only setup:

- Your ISP/router blocks port 80 from external access
- Can't get SSL certificate without port 80/443 accessible
- Setup is configured for **local network only**

**Solution:** This is by design for home network use. Access options:

```bash
✅ WORKS - Local network:
   http://192.168.1.4/

❌ DOESN'T WORK - Internet:
   https://indibyte.duckdns.org
   (Requires port forwarding - not needed for your use case)
```

For your AI apps running on the home network, local access is perfect and more secure!

## Troubleshooting

### Service Not Responding

**Symptoms:** Can't access `http://192.168.1.4`

**Solutions:**

1. **Check if service is running:**

   ```bash
   sudo systemctl status searxng-docker.service
   ```

2. **Check containers:**

   ```bash
   docker ps
   ```

3. **Restart service:**

   ```bash
   sudo systemctl restart searxng-docker.service
   ```

4. **Check logs for errors:**

   ```bash
   sudo journalctl -u searxng-docker.service -n 50
   ```

### Can't Access from Other Devices

**Symptoms:** Works on server PC but not on phone/laptop

**Solutions:**

1. **Verify device is on same WiFi:**
   - Check WiFi name on both devices
   - Must be on same network (not guest network)

2. **Check server IP:**

   ```bash
   hostname -I
   ```

   First IP should be `192.168.1.4`

3. **Test from server:**

   ```bash
   curl http://192.168.1.4
   ```

4. **Check firewall (if enabled):**

   ```bash
   sudo ufw status
   ```

### Slow Search Results

**Symptoms:** Searches taking too long

**Solutions:**

1. **Check internet connection:**

   ```bash
   ping -c 4 google.com
   ```

2. **Check system resources:**

   ```bash
   docker stats
   ```

3. **Restart containers:**

   ```bash
   docker compose restart
   ```

4. **Clear cache:**

   ```bash
   docker compose restart redis
   ```

### Service Won't Start

**Symptoms:** Service fails to start

**Solutions:**

1. **Check error messages:**

   ```bash
   sudo journalctl -u searxng-docker.service -n 50
   ```

2. **Check if ports are in use:**

   ```bash
   sudo netstat -tlnp | grep -E ':(80|8080|6379)'
   ```

3. **Manually start with Docker:**

   ```bash
   cd /home/riju279/Documents/Tools/SearchXNG/searxng-docker
   docker compose up
   ```

4. **Check disk space:**

   ```bash
   df -h
   ```

### IP Address Changed

**Symptoms:** IP changed from 192.168.1.4

**Solutions:**

1. **Find new IP:**

   ```bash
   hostname -I
   ```

2. **Update Caddyfile** with new IP (or set static IP in router)

3. **Reserve IP in router:**
   - Access router settings (usually 192.168.1.1)
   - Find DHCP settings
   - Reserve IP for this PC's MAC address

### Search Returns No Results

**Symptoms:** All searches return empty results

**Solutions:**

1. **Check internet connection:**

   ```bash
   curl https://www.google.com
   ```

2. **Test different search engines:**
   - Go to Preferences
   - Enable different engines
   - Save and try again

3. **Check SearXNG logs:**

   ```bash
   docker compose logs searxng | grep -i error
   ```

### Port 80 Already in Use

**Symptoms:** Can't start Caddy, port 80 conflict

**Solutions:**

1. **Find what's using port 80:**

   ```bash
   sudo lsof -i :80
   ```

2. **Stop conflicting service:**

   ```bash
   # If Apache
   sudo systemctl stop apache2

   # If Nginx
   sudo systemctl stop nginx
   ```

3. **Restart SearXNG:**

   ```bash
   sudo systemctl restart searxng-docker.service
   ```

---

## Maintenance

### Regular Maintenance

#### Weekly

**Check service health:**

```bash
# Check if service is running
sudo systemctl status searxng-docker.service

# Test search
curl "http://192.168.1.4/search?q=test&format=json" | jq '.results | length'
```

#### Monthly

**Update SearXNG:**

```bash
cd /home/riju279/Documents/Tools/SearchXNG/searxng-docker
git pull
docker compose pull
sudo systemctl restart searxng-docker.service
```

**Check disk space:**

```bash
df -h /home
```

**Review logs:**

```bash
sudo journalctl -u searxng-docker.service --since "1 week ago" | grep -i error
```

### Backup Configuration

**Backup important files:**

```bash
# Create backup directory
mkdir -p ~/searxng-backups/$(date +%Y-%m-%d)

# Backup configuration files
cp .env ~/searxng-backups/$(date +%Y-%m-%d)/
cp Caddyfile ~/searxng-backups/$(date +%Y-%m-%d)/
cp -r searxng ~/searxng-backups/$(date +%Y-%m-%d)/
```

### Update SearXNG

**Full update process:**

```bash
# 1. Navigate to directory
cd /home/riju279/Documents/Tools/SearchXNG/searxng-docker

# 2. Backup current configuration
mkdir -p ~/searxng-backups/$(date +%Y-%m-%d)
cp -r searxng ~/searxng-backups/$(date +%Y-%m-%d)/

# 3. Pull latest changes
git pull

# 4. Update Docker images
docker compose pull

# 5. Restart service
sudo systemctl restart searxng-docker.service

# 6. Verify it's working
sleep 10
curl http://localhost
```

### Clean Up

**Remove old Docker images:**

```bash
# See disk usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

**Clear logs:**

```bash
# Rotate systemd logs
sudo journalctl --vacuum-time=30d

# Clear Docker logs
docker compose down
docker compose up -d
```

---

## Quick Reference

### Access URLs

```bash
From This PC:      http://localhost
                   http://192.168.1.4

From Other Devices: http://192.168.1.4

JSON API:          http://192.168.1.4/search?q={query}&format=json
```

### Common Commands

```bash
# Check status
sudo systemctl status searxng-docker.service

# Restart service
sudo systemctl restart searxng-docker.service

# View logs
sudo journalctl -u searxng-docker.service -f

# Test search
curl "http://192.168.1.4/search?q=test&format=json" | jq .

# Update SearXNG
cd /home/riju279/Documents/Tools/SearchXNG/searxng-docker
git pull && docker compose pull && sudo systemctl restart searxng-docker.service
```

### API Quick Reference

```bash
# Basic search
curl "http://192.168.1.4/search?q=python&format=json"

# Images
curl "http://192.168.1.4/search?q=cats&format=json&categories=images"

# News
curl "http://192.168.1.4/search?q=tech&format=json&categories=news"

# Get URLs only
curl "http://192.168.1.4/search?q=test&format=json" | jq -r '.results[].url'

# Count results
curl "http://192.168.1.4/search?q=test&format=json" | jq '.results | length'
```

### Configuration Files

```bash
.env                     - Environment variables
searxng/settings.yml     - SearXNG configuration
Caddyfile               - Reverse proxy config
docker-compose.yaml      - Docker services
searxng-docker.service   - Systemd service file
```

### Helpful Scripts

```bash
./search.sh             - CLI search helper
./check-dns.sh          - DNS propagation checker
./monitor-ssl.sh        - SSL certificate monitor
```

### Support Resources

- SearXNG Documentation: <https://docs.searxng.org/>
- SearXNG GitHub: <https://github.com/searxng/searxng>
- Docker Setup: <https://github.com/searxng/searxng-docker>

---

## Appendix

### System Information

**Installation Directory:**

```bash
/home/riju279/Documents/Tools/SearchXNG/searxng-docker
```

**Server Details:**

- **IP Address**: 192.168.1.4
- **OS**: Linux 6.17.4-76061704-generic
- **Docker Compose**: v2.x
- **SearXNG Version**: 2025.11.10

**Service Configuration:**

- **Service Name**: searxng-docker.service
- **Auto-start**: Enabled
- **User**: riju279

### Port Information

| Service | Port | Access |
|---------|------|--------|
| Caddy (HTTP) | 80 | External (LAN) |
| SearXNG | 8080 | Internal only |
| Redis | 6379 | Internal only |

### Search Engines Available

SearXNG aggregates results from 70+ search engines including:

- Google
- Bing
- DuckDuckGo
- Yahoo
- Wikipedia
- GitHub
- Stack Overflow
- Reddit
- YouTube
- And many more...

### File Locations

```bash
Configuration:
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/.env
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/searxng/settings.yml
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/Caddyfile

Service:
  /etc/systemd/system/searxng-docker.service

Scripts:
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/search.sh
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/check-dns.sh
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/monitor-ssl.sh

Documentation:
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/userguide.md
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/HOME-NETWORK-ACCESS.md
  /home/riju279/Documents/Tools/SearchXNG/searxng-docker/SETUP.md
```

---

**Version**: 1.0
**Last Updated**: November 13, 2025
**Author**: Automated setup for riju279

---
