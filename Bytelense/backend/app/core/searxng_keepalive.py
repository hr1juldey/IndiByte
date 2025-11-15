"""
SearXNG Keep-Alive Background Task

Pings SearXNG every 600 seconds (10 minutes) to prevent the Docker container
from sleeping and causing slow first requests.
"""

import asyncio
import logging
import httpx
import random
from typing import Optional

logger = logging.getLogger(__name__)


class SearXNGKeepAlive:
    """Background task to keep SearXNG container awake."""

    def __init__(self, searxng_url: str, interval_seconds: int = 600):
        """
        Initialize keep-alive task.

        Args:
            searxng_url: Base URL of SearXNG instance
            interval_seconds: How often to ping (default: 600 = 10 minutes)
        """
        self.searxng_url = searxng_url
        self.interval_seconds = interval_seconds
        self.task: Optional[asyncio.Task] = None
        self._running = False

    async def _ping(self) -> bool:
        """
        Send a lightweight ping to SearXNG.

        Returns:
            True if ping successful, False otherwise
        """
        test_words= ["JC_BOSE","mcp","Fastapi"]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.searxng_url}/search",
                    params={"q": f"{random.choice(test_words)}", "format": "json", "categories": "general"},
                )
                if response.status_code == 200:
                    logger.debug(f"SearXNG keep-alive ping successful: See results{response.request}")
                    return True
                else:
                    logger.warning(f"SearXNG ping returned {response.status_code}")
                    return False
        except Exception as e:
            logger.warning(f"SearXNG keep-alive ping failed: {e}")
            return False

    async def _run_loop(self):
        """Main keep-alive loop."""
        logger.info(
            f"Starting SearXNG keep-alive (pinging every {self.interval_seconds}s)"
        )

        while self._running:
            try:
                await self._ping()
            except Exception as e:
                logger.error(f"Error in keep-alive loop: {e}")

            # Wait for next ping
            await asyncio.sleep(self.interval_seconds)

        logger.info("SearXNG keep-alive stopped")

    def start(self):
        """Start the keep-alive background task."""
        if self._running:
            logger.warning("Keep-alive already running")
            return

        self._running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("SearXNG keep-alive task started")

    async def stop(self):
        """Stop the keep-alive background task."""
        if not self._running:
            return

        self._running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("SearXNG keep-alive task stopped")


# Global instance (initialized in main.py)
searxng_keepalive: Optional[SearXNGKeepAlive] = None


def init_keepalive(searxng_url: str) -> SearXNGKeepAlive:
    """
    Initialize and start the global keep-alive instance.

    Args:
        searxng_url: Base URL of SearXNG instance

    Returns:
        SearXNGKeepAlive instance
    """
    global searxng_keepalive
    searxng_keepalive = SearXNGKeepAlive(searxng_url)
    searxng_keepalive.start()
    return searxng_keepalive


async def shutdown_keepalive():
    """Shutdown the global keep-alive instance."""
    global searxng_keepalive
    if searxng_keepalive:
        await searxng_keepalive.stop()
