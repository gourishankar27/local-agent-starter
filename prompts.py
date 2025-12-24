# prompts.py
"""
Prompt templates for the local agent.
"""


EMAIL_SUMMARY_PROMPT = """
You are a helpful assistant. Summarize the following email in 2 sentences and
list up to 3 action items (short bullet points).

Email:
{email}

Result:
1) Summary:
- <two-sentence summary>

2) Actions:
- <action 1 or 'None'>
- <action 2 or 'None'>
- <action 3 or 'None'>
""".strip()


RESUME_TAILOR_PROMPT = """
You are an expert resume and cover letter writer.

You will receive:
- A job posting
- A candidate's current resume (plain text)

Your tasks:
1. Write a 2-line profile summary tailored to the job.
2. Write 6 concise accomplishment-based bullets for the most relevant experience.
3. Write a short 3-paragraph cover letter tailored to the job.

Return your answer as VALID JSON ONLY with this exact structure:

{
  "profile": "<2-line profile summary>",
  "bullets": [
    "<bullet 1>",
    "<bullet 2>",
    "<bullet 3>",
    "<bullet 4>",
    "<bullet 5>",
    "<bullet 6>"
  ],
  "cover_letter": "<3-paragraph cover letter>"
}

Important:
- Do NOT include any text before or after the JSON.
- Do NOT include comments.
- Ensure the JSON is syntactically valid.

Job Posting:
{job_text}

Resume:
{resume_text}
""".strip()
