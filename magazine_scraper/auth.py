import os

from dotenv import load_dotenv
from playwright.sync_api import Browser, sync_playwright


def login() -> Browser:
    """Launch a browser and log in using credentials from .env.

    Returns a Browser instance with an authenticated session.
    """
    load_dotenv()
    _email = os.environ["LOGIN_EMAIL"]
    _password = os.environ["LOGIN_PASSWORD"]

    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    # TODO: implement actual login flow using email and password
    return browser
