# main.py
"""
Orchestrator demo: fetches recent emails, summarizes using the LLM, and provides hooks to run site-specific Playwright connectors.
"""
from llm_client import LLMClient
from prompts import EMAIL_SUMMARY_PROMPT
from email_fetcher import fetch_recent_messages
from playwright_apply import apply_linkedin, apply_jobright, apply_simplyfy


def summarize_emails_demo(n=3):
    client = LLMClient()
    msgs = fetch_recent_messages(n)
    for m in msgs:
        prompt = EMAIL_SUMMARY_PROMPT.format(email=m['snippet'])
        summary = client.generate(prompt)
        print('---')
        print(f"Subject: {m['subject']}")
        print(summary)


if __name__ == '__main__':
    print('Fetching & summarizing emails...')
    try:
        summarize_emails_demo(3)
    except Exception as e:
        print('Email demo failed (have you run --init-auth?):', e)

    print('\nPlaywright connectors are available in playwright_apply.py.\n')
    print('To run a connector manually, import and call apply_linkedin/apply_jobright/apply_simplyfy with the job URL and resume path.')
