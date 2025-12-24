# agent_api/views.py
# from django.shortcuts import render
from __future__ import annotations

import json
from datetime import datetime, date
from typing import Any, Dict, List

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from email_fetcher import fetch_recent_messages
from llm_client import LLMClient
from prompts import EMAIL_SUMMARY_PROMPT, RESUME_TAILOR_PROMPT
from log_storage import EncryptedLogStore
from log_storage import LogEntry  # import dataclass

# Simple in-process password state (works for `runserver` single process)
LOG_PASSWORD: str | None = None
LOG_STORE = EncryptedLogStore()


def _json_body(request: HttpRequest) -> Dict[str, Any]:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1]
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _serialize_log(entries: List[LogEntry]) -> List[Dict[str, Any]]:
    """Attach an index id to each log entry for deletion."""
    out: List[Dict[str, Any]] = []
    for idx, e in enumerate(entries):
        out.append(
            {
                "id": idx,
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "meta": e.meta,
                "preview": e.preview,
            }
        )
    return out


@csrf_exempt
def summarize_emails(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    data = _json_body(request)
    count = int(data.get("count", 3))

    try:
        messages = fetch_recent_messages(count)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    client = LLMClient()
    results = []

    for m in messages:
        prompt = EMAIL_SUMMARY_PROMPT.format(email=m.get("snippet", ""))
        try:
            summary_text = client.generate(prompt, max_tokens=256, task_type="email")
        except Exception as e:
            summary_text = f"[Error generating summary: {e}]"
        results.append(
            {
                "subject": m.get("subject", ""),
                "snippet": m.get("snippet", ""),
                "summary_raw": summary_text,
            }
        )

    # Append to logs if password set
    global LOG_PASSWORD
    if LOG_PASSWORD:
        combined = "\n\n".join(
            f"Subject: {r['subject']}\n{r['summary_raw']}" for r in results
        )
        entry = LOG_STORE.create_entry(
            event_type="email_summary",
            meta={"count": len(results)},
            preview=combined[:2000],
        )
        try:
            LOG_STORE.append_log(entry, LOG_PASSWORD)
        except Exception:
            # Don't fail the API if logging fails
            pass

    return JsonResponse({"results": results})


@csrf_exempt
def tailor_resume(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    data = _json_body(request)
    job_text = (data.get("job_text") or "").strip()
    resume_text = (data.get("resume_text") or "").strip()

    if not job_text or not resume_text:
        return JsonResponse(
            {"error": "job_text and resume_text are required"},
            status=400,
        )

    client = LLMClient()
    prompt = RESUME_TAILOR_PROMPT.format(job_text=job_text, resume_text=resume_text)

    try:
        raw_output = client.generate(
            prompt,
            max_tokens=1024,
            temperature=0.4,
            task_type="resume",
        )
    except Exception as e:
        return JsonResponse({"error": f"LLM call failed: {e}"}, status=500)

    try:
        data_out = json.loads(raw_output)
    except json.JSONDecodeError:
        # Return raw output so frontend can show + allow manual salvage
        return JsonResponse(
            {"error": "Could not parse JSON from model", "raw_output": raw_output},
            status=502,
        )

    profile = data_out.get("profile", "")
    bullets = data_out.get("bullets", []) or []
    cover_letter = data_out.get("cover_letter", "")

    # Log event if password set
    global LOG_PASSWORD
    if LOG_PASSWORD:
        preview = (
            "PROFILE:\n"
            + profile
            + "\n\nBULLETS:\n"
            + "\n".join(f"- {b}" for b in bullets)
            + "\n\nCOVER LETTER:\n"
            + cover_letter
        )
        entry = LOG_STORE.create_entry(
            event_type="resume_tailor",
            meta={"bullet_count": len(bullets)},
            preview=preview[:3000],
        )
        try:
            LOG_STORE.append_log(entry, LOG_PASSWORD)
        except Exception:
            pass

    return JsonResponse(
        {
            "profile": profile,
            "bullets": bullets,
            "cover_letter": cover_letter,
        }
    )


@csrf_exempt
def unlock_logs(request: HttpRequest) -> JsonResponse:
    """
    POST { "password": "..." }

    - If log file exists, tries to decrypt with given password.
    - If success: stores password in memory and returns all logs.
    - If file does not exist: initializes empty logs with that password.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    data = _json_body(request)
    password = data.get("password") or ""
    if not password:
        return JsonResponse({"error": "password is required"}, status=400)

    try:
        entries = LOG_STORE.load_logs(password)
    except ValueError:
        return JsonResponse(
            {"error": "Incorrect password or corrupted log file"},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Save password in memory
    global LOG_PASSWORD
    LOG_PASSWORD = password

    return JsonResponse({"logs": _serialize_log(entries)})


def _filter_logs(entries: List[LogEntry], log_type: str | None, start_str: str, end_str: str) -> List[LogEntry]:
    log_type = (log_type or "").strip()
    start_date: date | None = None
    end_date: date | None = None

    if start_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    if end_str:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    out: List[LogEntry] = []
    for e in entries:
        if log_type and log_type != "All" and e.event_type != log_type:
            continue

        dt = _parse_iso(e.timestamp)
        if dt:
            d = dt.date()
            if start_date and d < start_date:
                continue
            if end_date and d > end_date:
                continue

        out.append(e)
    return out


def list_logs(request: HttpRequest) -> JsonResponse:
    """
    GET /api/logs/?type=email_summary&start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    global LOG_PASSWORD
    if LOG_PASSWORD is None:
        return JsonResponse({"error": "Logs are locked"}, status=403)

    log_type = request.GET.get("type", "")
    start_str = request.GET.get("start", "")
    end_str = request.GET.get("end", "")

    try:
        entries = LOG_STORE.load_logs(LOG_PASSWORD)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    filtered = _filter_logs(entries, log_type, start_str, end_str)
    # NOTE: we still need original indices from full list, so we rebuild against full `entries`
    indexed = _serialize_log(entries)
    # Keep only IDs that are in filtered subset
    filtered_ids = {entries.index(e) for e in filtered}
    out = [item for item in indexed if item["id"] in filtered_ids]

    return JsonResponse({"logs": out})


@csrf_exempt
def delete_log(request: HttpRequest) -> JsonResponse:
    """
    POST { "id": <log_index> }
    """
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    global LOG_PASSWORD
    if LOG_PASSWORD is None:
        return JsonResponse({"error": "Logs are locked"}, status=403)

    data = _json_body(request)
    try:
        idx = int(data.get("id"))
    except Exception:
        return JsonResponse({"error": "id must be an integer"}, status=400)

    try:
        entries = LOG_STORE.load_logs(LOG_PASSWORD)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    if idx < 0 or idx >= len(entries):
        return JsonResponse({"error": "invalid id"}, status=400)

    # Remove that entry
    del entries[idx]

    try:
        LOG_STORE.save_logs(entries, LOG_PASSWORD)
    except Exception as e:
        return JsonResponse({"error": f"failed to save logs: {e}"}, status=500)

    return JsonResponse({"logs": _serialize_log(entries)})
