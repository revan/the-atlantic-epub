"""Browser context used for scraping.

There is deliberately no login here.  Two facts make one unnecessary and
one impossible:

* The Atlantic's paywall is a *client-side* metered overlay — full article
  HTML is server-rendered on every request, and ``scrape_article`` reads the
  raw DOM with BeautifulSoup, so the overlay never applies.  An anonymous
  context returns complete articles.
* The sign-in form is protected by reCAPTCHA, which rejects the submission
  with ``invalid_recaptcha`` under headless *and* headed Playwright.  A
  credential flow cannot be made to work from automation.
"""

from collections.abc import Generator
from contextlib import contextmanager

from playwright.sync_api import BrowserContext, sync_playwright


@contextmanager
def browser_context() -> Generator[BrowserContext, None, None]:
    """Launch a browser and yield a context for scraping.

    Use as a context manager so the browser and Playwright subprocess are
    always cleaned up::

        with browser_context() as ctx:
            ...
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    try:
        yield browser.new_context()
    finally:
        browser.close()
        pw.stop()
