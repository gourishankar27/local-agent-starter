# prompts.py

EMAIL_SUMMARY_PROMPT = '''
You are a helpful assistant. Summarize the following email in 2 sentences and list up to 3 action items (short bullet points).

Email:
{email}

Result:
1) Summary:
- <two-sentence summary>
2) Actions:
- <action 1>
- <action 2>
'''

RESUME_TAILOR_PROMPT = '''
You are an expert resume writer. The job posting is below and the candidate's current resume is below.
Produce:
- A 2-line profile summary tailored to the job.
- 6 concise accomplishment-based bullets for the most relevant experience, formatted as resume bullets.
- A short 3-paragraph cover letter.

Job Posting:
{job_text}

Resume:
{resume_text}

Output JSON with keys: profile, bullets (array), cover_letter
'''
