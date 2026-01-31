**Role:** Senior Backend Engineer & Web Scraping Specialist
**Task:** Upgrade [FirecrawlClient](cci:2://file:///Users/yizu/Desktop/clear-bill/backend/firecrawl_client.py:58:0-505:48) to extract LIVE wait times from facility websites.

**Context:**
We are building a healthcare price transparency app for a hackathon. We currently scrape prices, but valid "Wait Time" data is a missing "killer feature" that proves our agent is accessing real-time data. We need to modify our Firecrawl client to specifically hunt for and extract wait time indicators.

**Target File:** [backend/firecrawl_client.py](cci:7://file:///Users/yizu/Desktop/clear-bill/backend/firecrawl_client.py:0:0-0:0)

**Objectives:**
1.  **Update Search Strategy**: Modify [_search_pricing_pages](cci:1://file:///Users/yizu/Desktop/clear-bill/backend/firecrawl_client.py:260:4-292:13) to also find booking/status pages.
    *   *Current Query:* `"urgent care self pay price cost {location}"`
    *   *New Query:* `"urgent care wait time current status price cost {location}"`

2.  **Enhance Extraction Logic**: Rename [_extract_pricing_from_markdown](cci:1://file:///Users/yizu/Desktop/clear-bill/backend/firecrawl_client.py:369:4-388:43) to `_extract_facility_data` and add regex support for time indicators.
    *   *Patterns to detect:*
        *   Explicit times: `Wait time: (\d+) min`
        *   Availability: `Next available: (\d+:\d+\s*[AP]M)`
        *   Status: `Walk-ins welcome`, `On schedule`, `High volume`
    *   *Output:* Return a dictionary containing both [pricing](cci:1://file:///Users/yizu/Desktop/clear-bill/backend/firecrawl_client.py:445:4-451:9) and `wait_time_data`.

3.  **Update Enrichment**: Modify [_enrich_with_pricing](cci:1://file:///Users/yizu/Desktop/clear-bill/backend/firecrawl_client.py:323:4-367:9) to merge this new `wait_time` data into the facility object.
    *   If a live wait time is found, set `wait_time` field and mark `wait_time_source` as "verified_live".
    *   If no time is found, keep the existing default/estimate logic but verify the field exists.

4.  **Refine "Mock" Data**: Update the [_mock_facilities](cci:1://file:///Users/yizu/Desktop/clear-bill/backend/firecrawl_client.py:462:4-492:9) method to include realistic wait time strings (e.g., "15 min", "45 min", "No wait") so the frontend can display them immediately even if the scrape misses.

**Constraints:**
*   Do not break existing pricing extraction.
*   Ensure the regex is case-insensitive.
*   Keep the function signatures compatible with `search_and_enrich`.