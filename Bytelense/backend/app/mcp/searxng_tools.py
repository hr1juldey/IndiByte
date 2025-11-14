"""SearXNG integration via FastMCP for DSPy ReAct agent."""

import logging
from typing import List, Dict, Optional
import httpx
from fastmcp import FastMCP

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Bytelense SearXNG Tools")


@mcp.tool()
async def search_nutrition_database(
    product_name: str,
    barcode: Optional[str] = None
) -> Dict:
    """
    Search OpenFoodFacts and SearXNG for nutritional information.

    This tool is called by the DSPy ReAct agent to gather nutrition data.

    Args:
        product_name: Name of the product to search
        barcode: Optional barcode for exact lookup

    Returns:
        Dict containing nutrition data and source URLs for citations
    """
    # First try OpenFoodFacts (already handled by nutrition_api)
    # This tool focuses on SearXNG web search fallback

    results = await _searxng_search(f"{product_name} nutrition facts")

    if not results:
        return {
            "found": False,
            "product_name": product_name,
            "sources": []
        }

    return {
        "found": True,
        "product_name": product_name,
        "sources": results,
        "citation_hint": "Use these sources for citations"
    }


@mcp.tool()
async def compare_similar_products(
    product_name: str,
    category: str
) -> List[Dict]:
    """
    Find similar products for comparison and context.

    Helps the agent understand if the product is better or worse than alternatives.

    Args:
        product_name: Current product name
        category: Food category (e.g., "cereal", "snack", "yogurt")

    Returns:
        List of similar products with basic nutrition info
    """
    query = f"{category} {product_name} alternatives comparison nutrition"
    results = await _searxng_search(query, max_results=3)

    return results


@mcp.tool()
async def get_health_guidelines(
    nutrient: str,
    user_goal: str
) -> Dict:
    """
    Retrieve official health guidelines for specific nutrients.

    Searches for WHO, FDA, or USDA guidelines to support reasoning with authoritative sources.

    Args:
        nutrient: Nutrient name (e.g., "sodium", "sugar", "protein")
        user_goal: User health goal (e.g., "weight_loss", "diabetes", "heart_health")

    Returns:
        Guidelines with citations to authoritative sources
    """
    query = f"{nutrient} daily limit {user_goal} WHO FDA USDA guidelines"
    results = await _searxng_search(query, max_results=2)

    if not results:
        return {
            "found": False,
            "nutrient": nutrient,
            "user_goal": user_goal
        }

    return {
        "found": True,
        "nutrient": nutrient,
        "user_goal": user_goal,
        "guidelines": results
    }


async def _searxng_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Internal helper to query SearXNG API.

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        List of search results with title, url, snippet
    """
    url = f"{settings.searxng_api_base}/search"
    params = {
        "q": query,
        "format": "json",
        "categories": "general",
        "lang": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                results = []

                for result in data.get("results", [])[:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("content", "")[:200],
                        "source_type": "searxng"
                    })

                logger.info(f"SearXNG search returned {len(results)} results for: {query}")
                return results

            logger.warning(f"SearXNG returned status {response.status_code}")
            return []

    except Exception as e:
        logger.error(f"SearXNG search error: {e}")
        return []


# Export MCP server for integration
__all__ = ["mcp", "search_nutrition_database", "compare_similar_products", "get_health_guidelines"]
