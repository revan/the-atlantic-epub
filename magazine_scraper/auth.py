import os
from collections.abc import Generator
from contextlib import contextmanager

from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Error, sync_playwright


@contextmanager
def login() -> Generator[BrowserContext, None, None]:
    """Launch a browser and yield an authenticated BrowserContext.

    When the ``LOGIN_COOKIE`` env-var is set the interactive login is
    skipped and the cookie is injected directly.  Otherwise the full
    email/password flow is executed.

    Use as a context manager so the browser and Playwright subprocess
    are always cleaned up::

        with login() as ctx:
            ...
    """
    load_dotenv()

    pw = sync_playwright().start()
    browser = pw.chromium.launch()

    try:
        login_cookie = os.environ.get("LOGIN_COOKIE", "")
        if login_cookie:
            context = browser.new_context()
            context.add_cookies(
                [
                    {
                        "name": "atljwt",
                        "value": login_cookie,
                        "domain": ".theatlantic.com",
                        "path": "/",
                    }
                ]
            )
            yield context
            return

        email = os.environ["LOGIN_EMAIL"]
        password = os.environ["LOGIN_PASSWORD"]

        context = browser.new_context()
        page = context.new_page()

        page.goto("https://accounts.theatlantic.com/login/", wait_until="networkidle")

        page.fill('input[name="username"]', email)
        page.click('button[type="submit"]')
        try:
            page.frame_locator('title="reCAPTCHA"').locator(
                'span[class="recaptcha-checkbox"]'
            ).click(timeout=8_000)
        except Error:
            pass
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_load_state("domcontentloaded")

        page.close()
        yield context
    finally:
        browser.close()
        pw.stop()
