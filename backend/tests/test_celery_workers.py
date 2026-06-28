from app.workers.celery_app import celery_app
from app.workers.tasks import analytics_tasks, cleanup_tasks, email_tasks, report_tasks


def test_celery_uses_redis_broker_and_named_queues():
    assert celery_app.conf.broker_url.startswith("redis://")
    queue_names = {queue.name for queue in celery_app.conf.task_queues}
    assert {"default", "analytics", "email", "maintenance", "reports"}.issubset(queue_names)
    assert celery_app.conf.task_routes["reports.*"]["queue"] == "reports"
    assert celery_app.conf.task_routes["email.*"]["queue"] == "email"


def test_celery_beat_schedules_cleanup_and_analytics_refresh():
    schedule = celery_app.conf.beat_schedule

    assert schedule["cleanup-soft-deleted-records-daily"]["task"] == "cleanup.soft_deleted_records"
    assert schedule["refresh-analytics-hourly"]["task"] == "analytics.refresh_all_users"


def test_worker_tasks_are_registered_after_import():
    task_names = celery_app.tasks.keys()

    assert "email.send" in task_names
    assert "email.send_otp" in task_names
    assert "reports.generate_pdf" in task_names
    assert "analytics.update_user" in task_names
    assert "analytics.refresh_all_users" in task_names
    assert "cleanup.soft_deleted_records" in task_names


def test_email_task_uses_email_service(monkeypatch):
    sent = {}

    def fake_send_email(self, to_email, subject, body):
        sent["to_email"] = to_email
        sent["subject"] = subject
        sent["body"] = body

    monkeypatch.setattr("app.services.email_service.EmailService.send_email", fake_send_email)

    result = email_tasks.send_email_task.run("candidate@example.com", "Report ready", "Your PDF is ready.")

    assert result == {"status": "sent", "to_email": "candidate@example.com"}
    assert sent == {
        "to_email": "candidate@example.com",
        "subject": "Report ready",
        "body": "Your PDF is ready.",
    }


def test_tasks_define_retry_policy():
    assert email_tasks.send_email_task.autoretry_for == (Exception,)
    assert report_tasks.generate_pdf_report_task.autoretry_for == (Exception,)
    assert analytics_tasks.update_user_analytics_task.autoretry_for == (Exception,)
    assert cleanup_tasks.cleanup_soft_deleted_records_task.autoretry_for == (Exception,)
