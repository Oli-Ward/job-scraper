"""
Browser utilities for fetching HTML content with optional JavaScript rendering.

This module provides functions to fetch HTML content from websites, with support
for both static sites (using requests) and JavaScript-rendered sites (using Playwright).
"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("JobScraper.BrowserUtils")

# Try to import Playwright, but make it optional
try:
    from playwright.sync_api import sync_playwright, Browser, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. JavaScript rendering will not be available.")


def get_default_headers() -> Dict[str, str]:
    """Get default browser headers for requests."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-NZ,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def fetch_html_static(url: str, timeout: int = 15, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Fetch HTML content from a static website using requests.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        headers: Optional custom headers (defaults to get_default_headers())
    
    Returns:
        HTML content as string, or None on error
    """
    if headers is None:
        headers = get_default_headers()
    
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        res.raise_for_status()
        return res.text
    except requests.Timeout:
        logger.warning(f"Timeout fetching {url} (static)")
        return None
    except requests.RequestException as e:
        logger.warning(f"Error fetching {url} (static): {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error fetching {url} (static): {e}")
        return None


def fetch_html_with_playwright(
    url: str,
    wait_selector: Optional[str] = None,
    timeout: int = 30000,
    wait_until: str = "networkidle",
    headless: bool = True,
) -> Optional[str]:
    """
    Fetch HTML content from a JavaScript-rendered website using Playwright.
    
    Args:
        url: URL to fetch
        wait_selector: Optional CSS selector to wait for before extracting HTML
        timeout: Timeout in milliseconds
        wait_until: When to consider navigation successful ("load", "domcontentloaded", "networkidle")
        headless: Whether to run browser in headless mode
    
    Returns:
        HTML content as string, or None on error
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright not available. Cannot fetch with JavaScript rendering.")
        return None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            try:
                # Set realistic viewport and user agent
                page.set_viewport_size({"width": 1920, "height": 1080})
                page.set_extra_http_headers({
                    "Accept-Language": "en-NZ,en;q=0.9",
                })
                
                # Handle download events - cancel them to prevent errors
                # Set up download handler before navigation
                download_occurred = False
                
                def handle_download(download):
                    nonlocal download_occurred
                    download_occurred = True
                    try:
                        download.cancel()
                    except:
                        pass
                
                page.on("download", handle_download)
                
                # Navigate to page
                try:
                    response = page.goto(url, wait_until=wait_until, timeout=timeout)
                    # If response indicates a download, wait a bit and try to get content
                    if response and response.headers.get('content-type', '').startswith('application/'):
                        logger.debug(f"Download content-type detected for {url}, waiting for page")
                        page.wait_for_timeout(3000)
                except Exception as e:
                    # If download error, wait and try to get content anyway
                    error_str = str(e)
                    if "Download is starting" in error_str or "download" in error_str.lower():
                        logger.debug(f"Download detected for {url}, waiting and attempting to get content")
                        # Wait for page to potentially load
                        try:
                            page.wait_for_timeout(3000)
                            # Try to evaluate if page has loaded
                            page.evaluate("document.readyState")
                        except:
                            pass
                    else:
                        raise
                
                # Wait for specific selector if provided
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=timeout)
                    except Exception as e:
                        logger.debug(f"Selector {wait_selector} not found or timeout: {e}")
                        # Continue anyway - page might still have content
                
                # Get rendered HTML
                html = page.content()
                
                return html
            finally:
                page.close()
                browser.close()
                
    except Exception as e:
        logger.warning(f"Error fetching {url} with Playwright: {e}")
        return None


def fetch_html(
    url: str,
    use_js: bool = False,
    wait_selector: Optional[str] = None,
    timeout: int = 15,
    headers: Optional[Dict[str, str]] = None,
    **playwright_kwargs: Any,
) -> Optional[str]:
    """
    Fetch HTML content from a URL, with optional JavaScript rendering.
    
    This is the main function to use. It automatically chooses between
    static fetching (requests) and JavaScript rendering (Playwright).
    
    Args:
        url: URL to fetch
        use_js: If True, use Playwright for JavaScript rendering
        wait_selector: CSS selector to wait for (only used with use_js=True)
        timeout: Timeout in seconds (for static) or milliseconds (for JS)
        headers: Custom headers (only used for static fetching)
        **playwright_kwargs: Additional kwargs passed to fetch_html_with_playwright
    
    Returns:
        HTML content as string, or None on error
    
    Example:
        # Static site (fast)
        html = fetch_html("https://example.com/jobs")
        
        # JavaScript-rendered site
        html = fetch_html(
            "https://example.com/jobs",
            use_js=True,
            wait_selector=".job-card",
            timeout=30000
        )
    """
    if use_js:
        # Convert timeout from seconds to milliseconds for Playwright
        playwright_timeout = playwright_kwargs.pop('timeout', timeout * 1000)
        return fetch_html_with_playwright(
            url,
            wait_selector=wait_selector,
            timeout=playwright_timeout,
            **playwright_kwargs
        )
    else:
        return fetch_html_static(url, timeout=timeout, headers=headers)


class BrowserScraper:
    """
    Context manager for reusing a browser instance across multiple requests.
    
    This is more efficient when scraping multiple JavaScript-rendered sites,
    as it avoids the overhead of starting/stopping the browser for each site.
    
    Example:
        with BrowserScraper() as scraper:
            html1 = scraper.fetch_html(url1, wait_selector=".jobs")
            html2 = scraper.fetch_html(url2, wait_selector=".listings")
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the browser scraper.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
    
    def __enter__(self):
        """Start the browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available. Install with: pip install playwright && playwright install chromium")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def fetch_html(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        timeout: int = 30000,
        wait_until: str = "networkidle",
    ) -> Optional[str]:
        """
        Fetch HTML from a URL using the shared browser instance.
        
        Args:
            url: URL to fetch
            wait_selector: Optional CSS selector to wait for
            timeout: Timeout in milliseconds
            wait_until: When to consider navigation successful
        
        Returns:
            HTML content as string, or None on error
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Use BrowserScraper as context manager.")
        
        page = self.browser.new_page()
        try:
            # Set realistic viewport and user agent
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.set_extra_http_headers({
                "Accept-Language": "en-NZ,en;q=0.9",
            })
            
            # Navigate to page
            page.goto(url, wait_until=wait_until, timeout=timeout)
            
            # Wait for specific selector if provided
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=timeout)
                except Exception as e:
                    logger.debug(f"Selector {wait_selector} not found or timeout: {e}")
                    # Continue anyway
            
            # Get rendered HTML
            return page.content()
        except Exception as e:
            logger.warning(f"Error fetching {url} with shared browser: {e}")
            return None
        finally:
            page.close()
