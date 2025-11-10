import asyncio
import os
import hashlib
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import DomainFilter, FilterChain
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


OUTPUT_DIR = "crawl_output"


def safe_filename(url: str) -> str:
    """Generate a clean, unique, short filename for each URL."""
    h = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
    # Strip protocol and sanitize
    name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    # Truncate to stay under 200 chars (255 is FS limit, keep buffer)
    if len(name) > 200:
        name = name[:200]
    return f"{name}_{h}.md"


async def crawl_site():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filter_chain = FilterChain(
        [DomainFilter(allowed_domains=["sustainablecampus.cornell.edu"])]
    )

    strategy = BFSDeepCrawlStrategy(
        max_depth=5, include_external=False, filter_chain=filter_chain
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True,
    )

    metadata = []

    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(
            "https://sustainablecampus.cornell.edu", config=config
        ):
            if not result or not result.markdown:
                continue

            # Save markdown
            filename = safe_filename(result.url)
            path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(result.markdown)

            # Collect metadata for summary
            metadata.append(
                {
                    "url": result.url,
                    "filename": filename,
                    "depth": result.metadata.get("depth", 0),
                    "status": result.metadata.get("status_code", None),
                }
            )
            print(f"Saved: {result.url}")

    # Save crawl summary
    with open(os.path.join(OUTPUT_DIR, "crawl_index.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Crawl completed. {len(metadata)} pages saved to '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    asyncio.run(crawl_site())
