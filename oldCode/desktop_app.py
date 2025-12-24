# desktop_app.py
"""
Desktop UI for the Local Agent using Tkinter.

Features:
- Run email summarization via a button.
- Run resume tailoring via a UI form.
- Save all actions to an encrypted log file.
- View logs only after entering your password.
- Filter logs by type and date range.
- Delete specific logs from history (still encrypted on disk).

Run this file directly:

    python desktop_app.py
"""

from __future__ import annotations

import json
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from email_fetcher import fetch_recent_messages
from llm_client import LLMClient
from log_storage import EncryptedLogStore
from prompts import EMAIL_SUMMARY_PROMPT, RESUME_TAILOR_PROMPT


def _parse_iso_timestamp(ts: str) -> datetime | None:
    """
    Parse our ISO-like timestamps of the form 'YYYY-MM-DDTHH:MM:SSZ'.

    Returns a datetime or None if parsing fails.
    """
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1]
        return datetime.fromisoformat(ts)
    except Exception:
        return None


class LocalAgentApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Local Agent Desktop")
        self.geometry("1200x800")

        # Log-related
        self.log_store = EncryptedLogStore()
        self.log_password: str | None = None  # set after successful unlock
        self._all_logs: list = []             # full decrypted list
        self._filtered_logs: list = []        # filtered subset

        self._build_ui()

    # ---------- UI construction ----------

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # Agent tab
        agent_frame = ttk.Frame(notebook, padding=10)
        notebook.add(agent_frame, text="Agent")

        self._build_agent_tab(agent_frame)

        # Logs tab
        logs_frame = ttk.Frame(notebook, padding=10)
        notebook.add(logs_frame, text="Logs")

        self._build_logs_tab(logs_frame)

    def _build_agent_tab(self, parent: ttk.Frame):
        # ---- Email summarization section ----
        email_frame = ttk.LabelFrame(parent, text="Summarize Recent Emails", padding=10)
        email_frame.pack(fill="x", expand=False, pady=(0, 10))

        ttk.Label(email_frame, text="Number of emails to summarize:").grid(
            row=0, column=0, sticky="w"
        )
        self.email_count_var = tk.StringVar(value="3")
        email_count_entry = ttk.Entry(email_frame, width=5, textvariable=self.email_count_var)
        email_count_entry.grid(row=0, column=1, sticky="w", padx=(5, 10))

        self.email_run_button = ttk.Button(
            email_frame,
            text="Run",
            command=self.run_email_summary,
        )
        self.email_run_button.grid(row=0, column=2, padx=5)

        self.email_output = ScrolledText(email_frame, height=10, wrap="word")
        self.email_output.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(8, 0))

        email_frame.grid_columnconfigure(0, weight=1)
        email_frame.grid_rowconfigure(1, weight=1)

        # ---- Resume tailoring section ----
        resume_frame = ttk.LabelFrame(parent, text="Tailor Resume for Job", padding=10)
        resume_frame.pack(fill="both", expand=True)

        # Job description
        ttk.Label(resume_frame, text="Job Description:").grid(
            row=0, column=0, sticky="w"
        )
        self.job_text_widget = ScrolledText(resume_frame, height=8, wrap="word")
        self.job_text_widget.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(2, 8))

        # Resume text
        ttk.Label(resume_frame, text="Your Resume (plain text):").grid(
            row=2, column=0, sticky="w"
        )
        self.resume_text_widget = ScrolledText(resume_frame, height=8, wrap="word")
        self.resume_text_widget.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(2, 8))

        # Run button + output
        self.resume_run_button = ttk.Button(
            resume_frame,
            text="Generate Tailored Profile & Cover Letter",
            command=self.run_resume_tailor,
        )
        self.resume_run_button.grid(row=4, column=0, sticky="w", pady=(4, 4))

        self.resume_output = ScrolledText(resume_frame, height=10, wrap="word")
        self.resume_output.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(4, 0))

        resume_frame.grid_columnconfigure(0, weight=1)
        resume_frame.grid_rowconfigure(1, weight=1)
        resume_frame.grid_rowconfigure(3, weight=1)
        resume_frame.grid_rowconfigure(5, weight=1)

    def _build_logs_tab(self, parent: ttk.Frame):
        # ---- Password row ----
        pw_frame = ttk.Frame(parent)
        pw_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(pw_frame, text="Log Password:").pack(side="left")
        self.log_password_var = tk.StringVar()
        pw_entry = ttk.Entry(pw_frame, textvariable=self.log_password_var, show="*")
        pw_entry.pack(side="left", padx=(5, 5), fill="x", expand=True)

        unlock_btn = ttk.Button(pw_frame, text="Unlock Logs", command=self.unlock_logs)
        unlock_btn.pack(side="left", padx=(5, 0))

        # Info label
        info_text = (
            "Enter your password to decrypt logs.\n"
            "- If this is your first time, any password you choose will be used to encrypt new logs.\n"
            "- If logs already exist, you must enter the same password you used before."
        )
        ttk.Label(parent, text=info_text, wraplength=800, justify="left").pack(
            fill="x", pady=(0, 8)
        )

        # ---- Filter row ----
        filter_frame = ttk.LabelFrame(parent, text="Filter", padding=8)
        filter_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=0, sticky="w")
        self.log_type_var = tk.StringVar(value="All")
        self.log_type_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.log_type_var,
            state="readonly",
            values=["All", "email_summary", "resume_tailor", "other"],
            width=18,
        )
        self.log_type_combo.grid(row=0, column=1, sticky="w", padx=(4, 10))

        ttk.Label(filter_frame, text="Start Date (YYYY-MM-DD):").grid(
            row=0, column=2, sticky="w"
        )
        self.log_start_date_var = tk.StringVar()
        start_entry = ttk.Entry(filter_frame, textvariable=self.log_start_date_var, width=14)
        start_entry.grid(row=0, column=3, sticky="w", padx=(4, 10))

        ttk.Label(filter_frame, text="End Date (YYYY-MM-DD):").grid(
            row=0, column=4, sticky="w"
        )
        self.log_end_date_var = tk.StringVar()
        end_entry = ttk.Entry(filter_frame, textvariable=self.log_end_date_var, width=14)
        end_entry.grid(row=0, column=5, sticky="w", padx=(4, 10))

        apply_btn = ttk.Button(filter_frame, text="Apply Filter", command=self.apply_log_filter)
        apply_btn.grid(row=0, column=6, sticky="w", padx=(4, 4))

        clear_btn = ttk.Button(filter_frame, text="Clear Filter", command=self.clear_log_filter)
        clear_btn.grid(row=0, column=7, sticky="w", padx=(4, 0))

        for c in range(8):
            filter_frame.grid_columnconfigure(c, weight=0)
        filter_frame.grid_columnconfigure(1, weight=1)

        # ---- Logs list + preview (split) ----
        body_frame = ttk.Frame(parent)
        body_frame.pack(fill="both", expand=True)

        # Left: table of logs
        self.logs_tree = ttk.Treeview(
            body_frame,
            columns=("time", "type", "meta"),
            show="headings",
            selectmode="browse",
            height=15,
        )
        self.logs_tree.heading("time", text="Time")
        self.logs_tree.heading("type", text="Type")
        self.logs_tree.heading("meta", text="Meta Preview")

        self.logs_tree.column("time", width=200, anchor="w")
        self.logs_tree.column("type", width=120, anchor="w")
        self.logs_tree.column("meta", width=400, anchor="w")

        self.logs_tree.bind("<<TreeviewSelect>>", self.on_log_selected)

        tree_scroll_y = ttk.Scrollbar(body_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=tree_scroll_y.set)

        self.logs_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")

        # Right: preview pane
        preview_frame = ttk.Frame(body_frame)
        preview_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        ttk.Label(preview_frame, text="Selected Log Details:").pack(anchor="w")
        self.logs_preview = ScrolledText(preview_frame, height=25, wrap="word", state="normal")
        self.logs_preview.pack(fill="both", expand=True)

        delete_btn = ttk.Button(
            preview_frame,
            text="Delete Selected Log",
            command=self.delete_selected_log,
        )
        delete_btn.pack(anchor="e", pady=(6, 0))

        body_frame.grid_columnconfigure(0, weight=1)
        body_frame.grid_columnconfigure(2, weight=1)
        body_frame.grid_rowconfigure(0, weight=1)

    # ---------- Agent actions ----------

    def run_email_summary(self):
        """
        Summarize recent emails and display the result in the UI.
        Also append to encrypted logs if a log password is set.
        """
        try:
            n = int(self.email_count_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of emails.")
            return

        self.email_output.delete("1.0", tk.END)
        self.email_output.insert(tk.END, "Fetching emails and generating summaries...\n")
        self.email_run_button.config(state="disabled")
        self.update_idletasks()

        try:
            client = LLMClient()
            msgs = fetch_recent_messages(n)
        except Exception as e:
            self.email_output.insert(tk.END, f"\n❌ Failed: {e}\n")
            self.email_run_button.config(state="normal")
            return

        if not msgs:
            self.email_output.insert(tk.END, "\nNo messages found.\n")
            self.email_run_button.config(state="normal")
            return

        full_text_parts = []
        for m in msgs:
            prompt = EMAIL_SUMMARY_PROMPT.format(email=m["snippet"])
            try:
                summary = client.generate(prompt, max_tokens=256, task_type="email")
            except Exception as e:
                summary = f"[Error generating summary: {e}]"

            block = f"---\nSubject: {m['subject']}\n{summary}\n"
            full_text_parts.append(block)

        result = "\n".join(full_text_parts)
        self.email_output.delete("1.0", tk.END)
        self.email_output.insert(tk.END, result)

        # Log event (if log password is set)
        if self.log_password:
            preview = result[:1500]
            entry = self.log_store.create_entry(
                event_type="email_summary",
                meta={"count": len(msgs)},
                preview=preview,
            )
            try:
                self.log_store.append_log(entry, self.log_password)
                # Refresh in-memory logs if already unlocked
                self._reload_logs_in_memory()
            except Exception as e:
                messagebox.showwarning(
                    "Log Error",
                    f"Could not write to encrypted log file:\n{e}",
                )

        self.email_run_button.config(state="normal")

    def run_resume_tailor(self):
        """
        Run resume tailoring using the job description and resume text
        from the UI. Show formatted results and log the event.
        """
        job_text = self.job_text_widget.get("1.0", tk.END).strip()
        resume_text = self.resume_text_widget.get("1.0", tk.END).strip()

        if not job_text:
            messagebox.showerror("Missing Job Description", "Please enter a job description.")
            return
        if not resume_text:
            messagebox.showerror("Missing Resume", "Please paste your resume text.")
            return

        self.resume_output.delete("1.0", tk.END)
        self.resume_output.insert(tk.END, "Generating tailored profile, bullets, and cover letter...\n")
        self.resume_run_button.config(state="disabled")
        self.update_idletasks()

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
            self.resume_output.insert(tk.END, f"\n❌ Failed to call LLM: {e}\n")
            self.resume_run_button.config(state="normal")
            return

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # Show raw output to the user for manual salvage
            self.resume_output.delete("1.0", tk.END)
            self.resume_output.insert(
                tk.END,
                "⚠️ Could not parse JSON from model output. Raw response:\n\n"
            )
            self.resume_output.insert(tk.END, raw_output)
            self.resume_run_button.config(state="normal")
            return

        profile = data.get("profile", "")
        bullets = data.get("bullets", []) or []
        cover_letter = data.get("cover_letter", "")

        # Format nicely
        formatted = ["====== PROFILE SUMMARY ======\n", profile, "\n\n"]
        formatted.append("====== BULLETS ======\n")
        for b in bullets:
            formatted.append(f"• {b}\n")
        formatted.append("\n====== COVER LETTER ======\n")
        formatted.append(cover_letter)

        final_text = "".join(formatted)
        self.resume_output.delete("1.0", tk.END)
        self.resume_output.insert(tk.END, final_text)

        # Log event (if log password is set)
        if self.log_password:
            preview = final_text[:2000]
            entry = self.log_store.create_entry(
                event_type="resume_tailor",
                meta={"bullet_count": len(bullets)},
                preview=preview,
            )
            try:
                self.log_store.append_log(entry, self.log_password)
                self._reload_logs_in_memory()
            except Exception as e:
                messagebox.showwarning(
                    "Log Error",
                    f"Could not write to encrypted log file:\n{e}",
                )

        self.resume_run_button.config(state="normal")

    # ---------- Log loading / filtering / selection ----------

    def unlock_logs(self):
        """
        Attempt to unlock logs with the password from the UI.

        - If no log file exists, we accept the password and treat this as
          initializing a new log file (empty for now).
        - If a log file exists, we attempt to decrypt it. On failure, we show
          an error and do not set the password.
        """
        pw = self.log_password_var.get()
        if not pw:
            messagebox.showerror("Missing Password", "Please enter a password.")
            return

        try:
            entries = self.log_store.load_logs(pw)
        except ValueError:
            messagebox.showerror(
                "Incorrect Password",
                "Could not decrypt logs. Incorrect password or corrupted file.",
            )
            return
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Unexpected error reading log file:\n{e}",
            )
            return

        # At this point, password is valid (or no file existed yet)
        self.log_password = pw
        self._all_logs = entries
        self.apply_log_filter()
        messagebox.showinfo("Logs Unlocked", "Logs unlocked successfully.")

    def _reload_logs_in_memory(self):
        """
        Reloads logs from disk into memory, if password is known.
        Useful after appending or deleting logs.
        """
        if not self.log_password:
            return
        try:
            self._all_logs = self.log_store.load_logs(self.log_password)
            self.apply_log_filter()
        except Exception:
            # If this fails silently, worst case user can re-unlock manually.
            pass

    def apply_log_filter(self):
        """
        Filter logs by type and optional date range, then refresh the UI.
        """
        log_type = self.log_type_var.get() or "All"
        start_str = self.log_start_date_var.get().strip()
        end_str = self.log_end_date_var.get().strip()

        start_date: date | None = None
        end_date: date | None = None

        if start_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror(
                    "Invalid Start Date",
                    "Start date must be in YYYY-MM-DD format.",
                )
                return

        if end_str:
            try:
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror(
                    "Invalid End Date",
                    "End date must be in YYYY-MM-DD format.",
                )
                return

        results = []
        for e in self._all_logs:
            # Type filter
            if log_type != "All" and e.event_type != log_type:
                continue

            # Date filter
            dt = _parse_iso_timestamp(e.timestamp)
            if dt is None:
                # If timestamp is weird, show it only when no date filters
                if not start_date and not end_date:
                    results.append(e)
                continue

            d = dt.date()
            if start_date and d < start_date:
                continue
            if end_date and d > end_date:
                continue

            results.append(e)

        self._filtered_logs = results
        self._refresh_logs_view()

    def clear_log_filter(self):
        """
        Clear filters and show all logs.
        """
        self.log_type_var.set("All")
        self.log_start_date_var.set("")
        self.log_end_date_var.set("")
        self._filtered_logs = list(self._all_logs)
        self._refresh_logs_view()

    def _refresh_logs_view(self):
        """
        Re-render the Treeview based on self._filtered_logs.
        """
        # Clear selection & preview
        self.logs_tree.delete(*self.logs_tree.get_children())
        self.logs_preview.config(state="normal")
        self.logs_preview.delete("1.0", tk.END)
        self.logs_preview.insert(tk.END, "Select a log on the left to view details.\n")

        if not self._filtered_logs:
            self.logs_preview.insert(tk.END, "\nNo logs match the current filter.\n")
            self.logs_preview.config(state="disabled")
            return

        for idx, e in enumerate(self._filtered_logs):
            meta_str = json.dumps(e.meta, ensure_ascii=False)
            if len(meta_str) > 80:
                meta_str = meta_str[:77] + "..."
            self.logs_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(e.timestamp, e.event_type, meta_str),
            )

        self.logs_preview.config(state="disabled")

    def on_log_selected(self, event):
        """
        When a log is selected in the Treeview, show its full details in the preview pane.
        """
        selection = self.logs_tree.selection()
        if not selection:
            return
        idx_str = selection[0]
        try:
            idx = int(idx_str)
        except ValueError:
            return

        if idx < 0 or idx >= len(self._filtered_logs):
            return

        e = self._filtered_logs[idx]

        self.logs_preview.config(state="normal")
        self.logs_preview.delete("1.0", tk.END)
        self.logs_preview.insert(
            tk.END,
            f"Time: {e.timestamp}\n"
            f"Type: {e.event_type}\n"
            f"Meta: {json.dumps(e.meta, ensure_ascii=False, indent=2)}\n\n"
            f"Preview:\n{e.preview}\n",
        )
        self.logs_preview.config(state="disabled")

    def delete_selected_log(self):
        """
        Delete the selected log from history (encrypted file and in-memory state).
        """
        if not self.log_password:
            messagebox.showerror(
                "Locked",
                "You must unlock logs with your password before deleting entries.",
            )
            return

        selection = self.logs_tree.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a log entry to delete.",
            )
            return

        idx_str = selection[0]
        try:
            idx = int(idx_str)
        except ValueError:
            return

        if idx < 0 or idx >= len(self._filtered_logs):
            return

        entry_to_delete = self._filtered_logs[idx]

        answer = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to permanently delete this log entry?",
        )
        if not answer:
            return

        # Remove from _all_logs by identity
        new_all = []
        for e in self._all_logs:
            if e is entry_to_delete:
                continue
            new_all.append(e)
        self._all_logs = new_all

        try:
            self.log_store.save_logs(self._all_logs, self.log_password)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save logs after deletion:\n{e}",
            )
            return

        # Re-apply filter and refresh view
        self.apply_log_filter()
        messagebox.showinfo("Deleted", "Log entry deleted successfully.")


if __name__ == "__main__":
    app = LocalAgentApp()
    app.mainloop()
