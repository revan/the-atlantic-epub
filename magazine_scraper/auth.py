import os

from dotenv import load_dotenv
from playwright.sync_api import Browser, sync_playwright


def login() -> Browser:
    """Launch a browser and log in using credentials from .env.

    Returns a Browser instance with an authenticated session.
    """
    load_dotenv()
    email = os.environ["LOGIN_EMAIL"]
    password = os.environ["LOGIN_PASSWORD"]

    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page()

    page.goto("https://accounts.theatlantic.com/login/", wait_until="networkidle")

    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    page.close()
    return browser
