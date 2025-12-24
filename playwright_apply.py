# playwright_apply.py
"""
Demo Playwright script: opens a URL, tries to fill common fields (name/email),
attaches a file, pauses for human review, then optionally clicks submit.

This is a demonstration: real sites require custom selectors and respecting
each site's Terms of Service.
"""
from typing import Optional

from playwright.sync_api import sync_playwright


def apply_form_demo(
    url: str,
    resume_path: str,
    applicant_name: str,
    applicant_email: str,
    auto_submit: bool = False,
) -> None:
    """
    Open a browser and attempt to fill an application-like form.

    Args:
        url: URL of the application form.
        resume_path: Path to your resume file (PDF, DOCX, etc.).
        applicant_name: Your full name.
        applicant_email: Your email address.
        auto_submit: If True, click the detected submit button automatically.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"🌐 Navigating to: {url}")
        page.goto(url, timeout=30000)

        # Heuristic attempts to fill common name/email fields
        selectors = [
            ('input[name*="name"]', applicant_name),
            ('input[name*="full_name"]', applicant_name),
            ('input[name*="firstname"]', applicant_name.split(" ")[0]),
            ('input[name*="lastname"]', applicant_name.split(" ")[-1]),
            ('input[name*="email"]', applicant_email),
            ('input[type="email"]', applicant_email),
        ]

        for sel, val in selectors:
            try:
                input_el = page.query_selector(sel)
                if input_el:
                    page.fill(sel, val)
                    print(f"  ✓ Filled {sel!r} with {val!r}")
            except Exception:
                # Ignore individual selector failures; keep going.
                pass

        # Attempt to set file input for resume upload
        try:
            file_input = page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(resume_path)
                print(f"  ✓ Attached resume file: {resume_path}")
            else:
                print("  ℹ️ No file input found on page.")
        except Exception as e:
            print(f"  ⚠️ Failed to attach file: {e}")

        print("\nForm filled (best-effort). Review in the browser window.")
        if not auto_submit:
            try:
                input("Press Enter to attempt submit (or Ctrl+C to abort)... ")
            except KeyboardInterrupt:
                print("\n🚫 Submission aborted by user.")
                browser.close()
                return

        # Try to click the submit button
        try:
            submit_button = page.query_selector('button[type="submit"]')
            if submit_button:
                submit_button.click()
                print("  ✅ Clicked submit button (best-effort).")
            else:
                print("  ℹ️ No submit button auto-detected. Submit manually in the browser.")
        except Exception as e:
            print(f"  ⚠️ Submit failed: {e}")

        print("✅ Playwright demo finished. You can now close the browser.")
        browser.close()


if __name__ == "__main__":
    # Example usage
    apply_form_demo(
        "https://example.com/apply",
        resume_path="resume.pdf",
        applicant_name="Alice Example",
        applicant_email="alice@example.com",
    )
