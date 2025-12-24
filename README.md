# Local Agent Starter (Local-First, Free LLMs)

A local-first Python agent that can:

- Read and summarize recent Gmail emails.
- Tailor your resume and cover letter to a specific job posting using an LLM.
- Open a job application page in a real browser and pre-fill the form (with your approval).

By default, it uses **Ollama** and local models (like `llama3.1:8b`) so you can run
everything **100% free on your machine**. You can optionally point it at OpenAI
cloud if you want.

---

## Features

- ✅ **Email summarization**
  - Fetches your most recent Gmail messages.
  - Summarizes each email in 2 sentences and extracts up to 3 action items.

- ✅ **Resume tailoring**
  - You paste a job description and your current resume (plain text).
  - The agent generates:
    - A 2-line profile summary tailored to the job.
    - Six accomplishment-based bullets.
    - A short 3-paragraph cover letter.
  - The result is saved as JSON under `outputs/`.

- ✅ **Job application automation (demo)**
  - Launches a Playwright-controlled Chromium browser.
  - Navigates to a job application URL.
  - Attempts to fill name, email, and upload a resume file.
  - Pauses for your review, then optionally clicks “submit”.

---

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── oauth_setup.md
├── LLM_SETUP.md
├── storage.py
├── utils.py
├── email_fetcher.py
├── prompts.py
├── llm_client.py
├── playwright_apply.py
└── main.py
```

## Desktop App (encrypted logs + UI)

We provide a simple cross-platform desktop GUI (`desktop_app.py`) which:

- Lets you run key flows (summarize emails, tailor resume, Playwright demo) from a GUI.
- Stores all actions and outputs in an **encrypted local store** that requires a password to unlock.
- Stores encrypted files at `~/.local_agent_secure/{salt.bin,logs.bin}`.

### Quickstart

1. Install extra deps:

```bash
pip install PySimpleGUI cryptography
```



### Encrypted logs (with filters & delete)

In the **“Logs”** tab:

1. Enter your password and click **“Unlock Logs”**:
   - First time: any password creates a new encrypted log file.
   - Later: you must reuse the same password to decrypt existing logs.
2. Use the **Filter** box:
   - **Type**: `All`, `email_summary`, `resume_tailor`, or `other`
   - **Start Date / End Date**: optional `YYYY-MM-DD` range filter
   - Click **Apply Filter** to narrow logs, or **Clear Filter** to reset.
3. Click on a row in the **log table** (left side) to see full details on the right:
   - Timestamp
   - Type
   - Metadata
   - Full preview text
4. To remove a log entry permanently:
   - Select it in the table
   - Click **“Delete Selected Log”**
   - Confirm in the dialog

All logs are stored in a single encrypted file in your home directory:

```text
~/.local_agent_history.enc
```


## Web UI (Django + React)

This project includes a small web backend (Django) and a React frontend.

### Backend (Django API)

From the repo root:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver  # http://localhost:8000
```