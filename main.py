# main.py
"""
Orchestrator CLI for the local agent.

Menu options:
1) Summarize recent emails
2) Tailor resume for a job
3) Run Playwright job application demo
4) Quit
"""
from __future__ import annotations

import datetime as _dt
import json
import os

from llm_client import LLMClient
from prompts import EMAIL_SUMMARY_PROMPT, RESUME_TAILOR_PROMPT
from email_fetcher import fetch_recent_messages
from playwright_apply import apply_form_demo


# ---------- Helpers ----------


def _read_multiline(prompt: str) -> str:
    """
    Read multi-line input from the user until a line equal to 'END' is entered.
    """
    print(prompt)
    print("Paste your text below. When you're done, type 'END' on a new line and press Enter.")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _save_artifact(prefix: str, content: str, ext: str = "txt") -> str:
    """
    Save content into the `outputs/` directory with a timestamped filename.
    Returns the file path.
    """
    os.makedirs("outputs", exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.{ext}"
    path = os.path.join("outputs", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------- Flows ----------


def summarize_emails_demo(n: int = 3) -> None:
    """
    Fetch and summarize the most recent emails using the LLM.
    """
    client = LLMClient()
    print(f"\n📨 Fetching and summarizing your {n} most recent emails...\n")
    try:
        msgs = fetch_recent_messages(n)
    except Exception as e:
        print("❌ Email demo failed:", e)
        print("   Have you run `python email_fetcher.py --init-auth` first?")
        return

    if not msgs:
        print("No messages found.")
        return

    for m in msgs:
        prompt = EMAIL_SUMMARY_PROMPT.format(email=m["snippet"])
        summary = client.generate(prompt, max_tokens=256)
        print("\n---")
        print(f"Subject: {m['subject']}")
        print(summary)


def tailor_resume_for_job() -> None:
    """
    Tailor a resume and cover letter to a job posting using the LLM.
    """
    client = LLMClient()

    job_text = _read_multiline("\n🧾 Paste the job description.")
    if not job_text:
        print("⚠️ No job description provided. Aborting.")
        return

    resume_text = _read_multiline(
        "\n📄 Paste your current resume as plain text "
        "(you can copy from your PDF/Word file)."
    )
    if not resume_text:
        print("⚠️ No resume text provided. Aborting.")
        return

    print("\n🤖 Generating tailored profile, bullets, and cover letter...")
    prompt = RESUME_TAILOR_PROMPT.format(
        job_text=job_text,
        resume_text=resume_text,
    )
    raw_output = client.generate(prompt, max_tokens=1024, temperature=0.4)

    # Try to parse JSON
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        print("\n⚠️ Could not parse JSON from model output. Here is the raw response:\n")
        print(raw_output)
        print("\nYou may need to copy/edit this manually.")
        return

    profile = data.get("profile", "")
    bullets = data.get("bullets", []) or []
    cover_letter = data.get("cover_letter", "")

    print("\n====== PROFILE SUMMARY ======")
    print(profile)

    print("\n====== BULLETS ======")
    for b in bullets:
        print(f"• {b}")

    print("\n====== COVER LETTER ======")
    print(cover_letter)

    # Save JSON artifact
    pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
    path = _save_artifact("tailored_resume", pretty_json, ext="json")
    print(f"\n💾 Saved tailored resume+cover letter JSON to: {path}")


def run_playwright_demo() -> None:
    """
    Run the Playwright job application demo with interactive input.
    """
    print("\n🧪 Playwright job application demo")

    url = input("Job application URL [default: https://example.com/apply]: ").strip()
    if not url:
        url = "https://example.com/apply"

    resume_path = input("Path to your resume file [default: resume.pdf]: ").strip()
    if not resume_path:
        resume_path = "resume.pdf"

    name = input("Your full name [default: Your Name]: ").strip()
    if not name:
        name = "Your Name"

    email = input("Your email address [default: you@example.com]: ").strip()
    if not email:
        email = "you@example.com"

    auto_submit_str = input("Auto-click submit after review? [y/N]: ").strip().lower()
    auto_submit = auto_submit_str in ("y", "yes")

    print("\nLaunching browser...")
    apply_form_demo(
        url=url,
        resume_path=resume_path,
        applicant_name=name,
        applicant_email=email,
        auto_submit=auto_submit,
    )


# ---------- CLI Menu ----------


def main() -> None:
    while True:
        print("\n=== Local Agent ===")
        print("1) Summarize recent emails")
        print("2) Tailor resume for a job")
        print("3) Run Playwright job application demo")
        print("4) Quit")

        choice = input("Choose an option [1-4]: ").strip()

        if choice == "1":
            summarize_emails_demo()
        elif choice == "2":
            tailor_resume_for_job()
        elif choice == "3":
            run_playwright_demo()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice, please enter 1–4.")


if __name__ == "__main__":
    main()
