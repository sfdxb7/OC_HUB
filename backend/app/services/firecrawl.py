"""
Firecrawl service for scraping web content.
Uses self-hosted Firecrawl at myfirecrawl.alfalasi.io
"""
import json
from typing import Optional
from dataclasses import dataclass
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScrapedContent:
    """Scraped article content."""
    url: str
    title: str
    content: str  # Markdown content
    author: Optional[str] = None
    published_date: Optional[str] = None
    source_domain: str = ""
    word_count: int = 0


class FirecrawlService:
    """Service for scraping web content using Firecrawl."""
    
    def __init__(self):
        self.base_url = settings.firecrawl_url.rstrip("/")
        self.api_key = settings.firecrawl_api_key
        self.timeout = 60.0  # Scraping can be slow
    
    async def scrape_url(self, url: str) -> ScrapedContent:
        """
        Scrape content from a URL using Firecrawl.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapedContent with markdown content
        """
        logger.info("Scraping URL", url=url)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/scrape",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "formats": ["markdown"],
                        "onlyMainContent": True,
                        "waitFor": 2000  # Wait for JS rendering
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse Firecrawl response
                if not data.get("success"):
                    raise Exception(f"Firecrawl error: {data.get('error', 'Unknown error')}")
                
                result = data.get("data", {})
                metadata = result.get("metadata", {})
                
                content = result.get("markdown", "")
                if not content:
                    content = result.get("content", "")
                
                # Extract domain from URL
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                
                scraped = ScrapedContent(
                    url=url,
                    title=metadata.get("title", metadata.get("ogTitle", "Untitled")),
                    content=content,
                    author=metadata.get("author"),
                    published_date=metadata.get("publishedTime"),
                    source_domain=domain,
                    word_count=len(content.split()) if content else 0
                )
                
                logger.info(
                    "Scraping complete",
                    url=url,
                    title=scraped.title[:50],
                    word_count=scraped.word_count
                )
                
                return scraped
                
            except httpx.HTTPStatusError as e:
                logger.error("Firecrawl HTTP error", url=url, status=e.response.status_code)
                raise Exception(f"Failed to scrape URL: HTTP {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error("Firecrawl request error", url=url, error=str(e))
                raise Exception(f"Failed to connect to Firecrawl: {str(e)}")
            except Exception as e:
                logger.error("Firecrawl error", url=url, error=str(e))
                raise


# Singleton instance
_firecrawl_service: Optional[FirecrawlService] = None


def get_firecrawl_service() -> FirecrawlService:
    """Get singleton Firecrawl service instance."""
    global _firecrawl_service
    if _firecrawl_service is None:
        _firecrawl_service = FirecrawlService()
    return _firecrawl_service
