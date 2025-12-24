# agent_api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("email/summarize/", views.summarize_emails, name="summarize_emails"),
    path("resume/tailor/", views.tailor_resume, name="tailor_resume"),
    path("logs/unlock/", views.unlock_logs, name="unlock_logs"),
    path("logs/", views.list_logs, name="list_logs"),
    path("logs/delete/", views.delete_log, name="delete_log"),
]
