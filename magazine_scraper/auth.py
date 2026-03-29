import os

from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Error, sync_playwright


def login() -> BrowserContext:
    """Launch a browser and return an authenticated BrowserContext.

    When the ``LOGIN_COOKIE`` env-var is set the interactive login is
    skipped and the cookie is injected directly.  Otherwise the full
    email/password flow is executed.
    """
    load_dotenv()

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)

    login_cookie = os.environ.get("LOGIN_COOKIE", "")
    if login_cookie:
        context = browser.new_context()
        context.add_cookies(
            [
                {
                    "name": "atljwt",
                    "value": login_cookie,
                    "url": "https://accounts.theatlantic.com/",
                }
            ]
        )
        return context

    email = os.environ["LOGIN_EMAIL"]
    password = os.environ["LOGIN_PASSWORD"]

    context = browser.new_context()
    page = context.new_page()

    page.goto("https://accounts.theatlantic.com/login/", wait_until="networkidle")

    page.fill('input[name="username"]', email)
    page.click('button[type="submit"]')
    try:
        page.frame_locator('title="reCAPTCHA"').locator('span[class="recaptcha-checkbox"]').click(
            timeout=8_000
        )
    except Error:
        pass
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")

    page.close()
    return context
