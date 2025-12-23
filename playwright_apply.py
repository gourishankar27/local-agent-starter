# playwright_apply.py
"""
Demo Playwright script with site-specific connectors for:
- LinkedIn
- JobRight AI (hypothetical example)
- SimplyFy (hypothetical example)

NOTES:
- These are best-effort selectors and flows. Real sites change their DOM frequently and often require authentication.
- LinkedIn in particular has strict terms of service against scraping/automation. Use with caution and your own account risk.
- Login handling is NOT implemented here; the simplest approach is to run Playwright in headed mode, navigate to the site, log in manually, then run the connector functions.
"""
from playwright.sync_api import sync_playwright, Page
import time


def open_browser(headless=False):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    ctx = browser.new_context()
    page = ctx.new_page()
    return p, browser, ctx, page


def close_browser(p, browser):
    try:
        browser.close()
    finally:
        try:
            p.stop()
        except Exception:
            pass


# ---------------------- LinkedIn connector ----------------------
def apply_linkedin(job_url: str, resume_path: str, applicant_name: str, applicant_email: str, auto_submit=False):
    """
    Best-effort flow for LinkedIn "Easy Apply" postings.
    Requirements:
      - You must be logged into LinkedIn in the opened browser/context.
      - Selectors here are heuristics and will need tweaking.
    """
    p, browser, ctx, page = open_browser(headless=False)
    try:
        page.goto(job_url, timeout=60000)
        time.sleep(2)
        # Click Easy Apply button if present
        try:
            ea = page.query_selector('button[aria-label*="Easy apply"]') or page.query_selector('button:has-text("Easy apply")')
            if ea:
                ea.click()
                time.sleep(1)
        except Exception:
            pass

        # Fill name/email if fields exist
        try:
            if page.query_selector('input[name*="email"]'):
                page.fill('input[name*="email"]', applicant_email)
        except Exception:
            pass

        # Attach resume if file input exists
        try:
            file_input = page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(resume_path)
        except Exception:
            pass

        print('LinkedIn form filled (best-effort). Please review the dialog in the browser.')
        if not auto_submit:
            input('Press Enter to submit (or Ctrl+C to abort)...')

        # Try to click the final submit / done button
        try:
            done_btn = page.query_selector('button[aria-label*="Submit application"]') or page.query_selector('button:has-text("Submit application")') or page.query_selector('button:has-text("Done")')
            if done_btn:
                done_btn.click()
                print('Clicked submit (best-effort).')
            else:
                print('Could not auto-detect final submit button. Submit manually.')
        except Exception as e:
            print('Submit failed:', e)

        time.sleep(2)
    finally:
        close_browser(p, browser)


# ---------------------- JobRight AI connector (hypothetical) ----------------------
def apply_jobright(job_url: str, resume_path: str, applicant_name: str, applicant_email: str, auto_submit=False):
    """
    Example connector for JobRight AI. This is a placeholder to show how to write site-specific logic.
    Update selectors after inspecting the site's form structure.
    """
    p, browser, ctx, page = open_browser(headless=False)
    try:
        page.goto(job_url, timeout=60000)
        time.sleep(2)
        # Example: fill name/email
        for selector in ['input[name="name"]', 'input#name', 'input[name*="full_name"]']:
            try:
                if page.query_selector(selector):
                    page.fill(selector, applicant_name)
            except Exception:
                pass
        for selector in ['input[name="email"]', 'input#email']:
            try:
                if page.query_selector(selector):
                    page.fill(selector, applicant_email)
            except Exception:
                pass
        # Attach resume
        try:
            file_input = page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(resume_path)
        except Exception:
            pass

        print('JobRight form filled (best-effort). Please review browser.')
        if not auto_submit:
            input('Press Enter to submit (or Ctrl+C to abort)...')

        try:
            submit = page.query_selector('button[type="submit"]') or page.query_selector('button:has-text("Apply")')
            if submit:
                submit.click()
                print('Clicked submit (best-effort).')
            else:
                print('Submit button not found; submit manually.')
        except Exception as e:
            print('Submit failed:', e)

        time.sleep(2)
    finally:
        close_browser(p, browser)


# ---------------------- SimplyFy connector (hypothetical) ----------------------
def apply_simplyfy(job_url: str, resume_path: str, applicant_name: str, applicant_email: str, auto_submit=False):
    """
    Example connector for SimplyFy. Placeholder selectors — update per real site.
    """
    p, browser, ctx, page = open_browser(headless=False)
    try:
        page.goto(job_url, timeout=60000)
        time.sleep(2)
        # Try to click an "Apply" link
        try:
            apply_link = page.query_selector('a:has-text("Apply")')
            if apply_link:
                apply_link.click()
                time.sleep(1)
        except Exception:
            pass

        # Fill fields
        try:
            if page.query_selector('input[name="applicant_name"]'):
                page.fill('input[name="applicant_name"]', applicant_name)
        except Exception:
            pass

        try:
            if page.query_selector('input[name="applicant_email"]'):
                page.fill('input[name="applicant_email"]', applicant_email)
        except Exception:
            pass

        # Attach resume
        try:
            file_input = page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(resume_path)
        except Exception:
            pass

        print('SimplyFy form filled (best-effort). Review browser.')
        if not auto_submit:
            input('Press Enter to submit (or Ctrl+C to abort)...')

        try:
            submit = page.query_selector('button[type="submit"]')
            if submit:
                submit.click()
                print('Clicked submit (best-effort).')
            else:
                print('No submit detected; submit manually in the browser.')
        except Exception as e:
            print('Submit failed:', e)

        time.sleep(2)
    finally:
        close_browser(p, browser)


if __name__ == '__main__':
    # Small interactive demo: you can call one of the connectors here
    print('This script contains connectors: apply_linkedin, apply_jobright, apply_simplyfy')
    print('Edit __main__ to call the desired connector with a job URL and resume path.')
