# JavaScript Rendering Guide for Job Scrapers

## Overview

Some job sites use Single Page Applications (SPAs) that require JavaScript to load content. This guide covers the best approaches for handling these sites.

## Options Comparison

### 1. **Playwright** (Recommended) ⭐

**Pros:**
- Modern, fast, and well-maintained
- Excellent Python bindings
- Supports Chromium, Firefox, and WebKit
- Better performance than Selenium
- Built-in waiting mechanisms
- Good documentation
- Can run headless or with browser visible
- Better handling of modern web features

**Cons:**
- Requires browser binaries (auto-downloaded on first use)
- Slightly larger dependency footprint
- Newer than Selenium (smaller community)

**Best for:** Modern Python projects, performance-critical scraping

### 2. **Selenium**

**Pros:**
- Most established, large community
- Extensive documentation and tutorials
- Works with multiple browsers
- Many third-party tools and extensions

**Cons:**
- Slower than Playwright
- More resource-intensive
- Requires separate browser driver management
- More verbose API

**Best for:** Projects already using Selenium, or when you need maximum compatibility

### 3. **Requests-HTML**

**Pros:**
- Lightweight Python library
- Simple API
- Uses PyQt5's QWebEngine internally

**Cons:**
- Less powerful than Playwright/Selenium
- Limited browser support
- Less maintained
- May not handle complex SPAs well

**Best for:** Simple cases, minimal dependencies

## Recommendation: Playwright

For this job scraper project, **Playwright** is the best choice because:
1. Better performance (important when scraping many sites)
2. Modern API that's easier to use
3. Better handling of modern web features
4. Active development and maintenance
5. Good Python integration

## Implementation Approach

### Option A: Hybrid Approach (Recommended)

Create a helper function that can use either `requests` (for static sites) or `Playwright` (for SPAs), allowing gradual migration:

```python
# sources/browser_utils.py
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("JobScraper.BrowserUtils")

def fetch_html_with_browser(url, use_js=False, wait_selector=None, timeout=30000):
    """
    Fetch HTML content, optionally using JavaScript rendering.
    
    Args:
        url: URL to fetch
        use_js: If True, use Playwright for JavaScript rendering
        wait_selector: CSS selector to wait for (for JS rendering)
        timeout: Timeout in milliseconds (for JS rendering)
    
    Returns:
        HTML content as string, or None on error
    """
    if not use_js:
        # Use requests for static sites (faster)
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-NZ,en;q=0.9",
            }
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            return res.text
        except Exception as e:
            logger.warning(f"Error fetching {url} with requests: {e}")
            return None
    else:
        # Use Playwright for JavaScript rendering
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set realistic viewport and user agent
                page.set_viewport_size({"width": 1920, "height": 1080})
                page.set_extra_http_headers({
                    "Accept-Language": "en-NZ,en;q=0.9",
                })
                
                # Navigate to page
                page.goto(url, wait_until="networkidle", timeout=timeout)
                
                # Wait for specific selector if provided
                if wait_selector:
                    page.wait_for_selector(wait_selector, timeout=timeout)
                
                # Get rendered HTML
                html = page.content()
                
                browser.close()
                return html
        except Exception as e:
            logger.warning(f"Error fetching {url} with Playwright: {e}")
            return None
```

### Option B: Per-Site Configuration

Mark which sites need JavaScript rendering and handle them accordingly:

```python
# In daily_run.py or a config file
JS_REQUIRED_SITES = [
    "Trade Me",
    "Matchstiq",
    "Unicorn Factory",
    "Zealancer",
    "Toptal",
    "Turing",
    "Trimble",
]
```

## Example: Updating a Scraper to Use Playwright

### Before (requests only):
```python
def fetch_trademe_jobs():
    url = f"{BASE_URL}?{urlencode(params)}"
    res = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    # ... parse jobs
```

### After (with Playwright support):
```python
from sources.browser_utils import fetch_html_with_browser

def fetch_trademe_jobs():
    url = f"{BASE_URL}?{urlencode(params)}"
    
    # Try with JavaScript rendering
    html = fetch_html_with_browser(
        url, 
        use_js=True,
        wait_selector="tm-search-card-wrapper",  # Wait for job cards to load
        timeout=30000
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    # ... parse jobs (same as before)
```

## Installation

Add to `requirements.txt`:
```txt
playwright>=1.40.0
```

Install and setup:
```bash
pip install playwright
playwright install chromium  # Install browser binaries
```

## Performance Considerations

1. **Use JavaScript rendering only when needed**: Static sites should still use `requests` for speed
2. **Reuse browser instances**: For multiple sites, consider keeping browser open
3. **Set appropriate timeouts**: Don't wait too long for slow sites
4. **Use headless mode**: Faster and uses less resources
5. **Consider rate limiting**: JavaScript rendering is slower, so add delays between requests

## Example: Browser Reuse Pattern

For better performance when scraping multiple JS sites:

```python
class BrowserScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def fetch_html(self, url, wait_selector=None):
        page = self.browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=30000)
            return page.content()
        finally:
            page.close()

# Usage:
# with BrowserScraper() as scraper:
#     html1 = scraper.fetch_html(url1)
#     html2 = scraper.fetch_html(url2)
```

## Migration Strategy

1. **Phase 1**: Add Playwright to requirements, create browser_utils.py
2. **Phase 2**: Identify which sites need JS (test with Playwright)
3. **Phase 3**: Update scrapers one by one, starting with highest priority
4. **Phase 4**: Add configuration to enable/disable JS per site

## Sites Likely Needing JavaScript

Based on testing:
- **Trade Me** - Uses custom web components
- **Matchstiq** - Appears to be SPA
- **Unicorn Factory** - Likely SPA
- **Zealancer** - May need JS
- **Toptal** - Likely SPA
- **Turing** - Likely SPA
- **Trimble** - Uses Eightfold.ai (likely SPA)
- **Absolute IT** - Has iframe, may need JS

## Alternative: API First

Before implementing JavaScript rendering, check if sites offer APIs:
- **Trade Me** - Has API (already have credentials in .env)
- Some sites may have hidden API endpoints
- Check network tab in browser DevTools for API calls

## Cost-Benefit Analysis

**JavaScript Rendering Pros:**
- Can scrape modern SPAs
- Handles dynamic content
- More reliable for complex sites

**JavaScript Rendering Cons:**
- Slower (2-5x slower than requests)
- More resource-intensive (CPU, memory)
- Requires browser binaries
- More complex error handling
- May still be blocked by anti-bot measures

**Recommendation**: Use JavaScript rendering selectively, only for sites that truly need it.