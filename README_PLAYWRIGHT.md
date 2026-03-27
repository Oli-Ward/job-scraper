# Playwright Setup Instructions

## Installation

Playwright has been added to `requirements.txt`. To complete the setup:

1. **Install Python package** (already done):
   ```bash
   pip install playwright
   ```

2. **Install browser binaries**:
   ```bash
   playwright install chromium
   ```
   
   This downloads the Chromium browser (~160MB) and may take a few minutes.

## Usage

The browser utility is available in `sources/browser_utils.py`:

### Basic Usage

```python
from sources.browser_utils import fetch_html

# Static site (fast, uses requests)
html = fetch_html("https://example.com/jobs")

# JavaScript-rendered site (slower, uses Playwright)
html = fetch_html(
    "https://example.com/jobs",
    use_js=True,
    wait_selector=".job-card",  # Wait for job cards to load
    timeout=30000  # 30 seconds
)
```

### Using BrowserScraper (for multiple JS sites)

```python
from sources.browser_utils import BrowserScraper

# Reuse browser instance for better performance
with BrowserScraper() as scraper:
    html1 = scraper.fetch_html(url1, wait_selector=".jobs")
    html2 = scraper.fetch_html(url2, wait_selector=".listings")
```

### Updating a Scraper to Use JavaScript

Example: Updating Trade Me scraper:

```python
from sources.browser_utils import fetch_html
from bs4 import BeautifulSoup

def fetch_trademe_jobs():
    url = "https://www.trademe.co.nz/a/jobs?search_string=software"
    
    # Use JavaScript rendering
    html = fetch_html(
        url,
        use_js=True,
        wait_selector="tm-search-card-wrapper",  # Wait for job cards
        timeout=30000
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    # ... rest of parsing logic stays the same
```

## Notes

- Static sites should continue using `requests` (faster)
- Only use JavaScript rendering for sites that need it
- Browser binaries are stored in `~/Library/Caches/ms-playwright/` (macOS)
- The first run may be slower as browser initializes
