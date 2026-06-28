from functools import lru_cache

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InterviewLoop-v2"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: PostgresDsn = "postgresql+psycopg://interviewloop:interviewloop@postgres:5432/interviewloop"
    redis_url: RedisDsn = "redis://redis:6379/0"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: float = 20.0
    ollama_retry_attempts: int = 3
    interview_memory_window: int = 8
    adaptive_score_window: int = 3
    deepgram_api_key: str | None = None
    deepgram_ws_url: str = "wss://api.deepgram.com/v1/listen"
    deepgram_model: str = "nova-2"
    deepgram_language: str = "en-US"
    deepgram_encoding: str = "linear16"
    deepgram_sample_rate: int = 16000
    deepgram_timeout_seconds: float = 20.0
    deepgram_reconnect_attempts: int = 3
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "InterviewLoop"
    smtp_use_tls: bool = True
    code_execution_timeout_seconds: int = 5
    code_execution_memory_limit: str = "128m"
    code_execution_cpu_limit: float = 0.5
    code_execution_pids_limit: int = 64
    report_storage_dir: str = "storage/reports"
    report_signature_private_key: str | None = None
    report_signature_public_key: str | None = None
    cleanup_soft_deleted_days: int = 30
    celery_task_max_retries: int = 3
    celery_task_retry_backoff_seconds: int = 5
    websocket_heartbeat_seconds: int = 25
    websocket_event_history_limit: int = 50
    websocket_max_reconnect_attempts: int = 5
    jwt_private_key: str | None = None
    jwt_public_key: str | None = None
    jwt_algorithm: str = "RS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    otp_ttl_minutes: int = 10
    auth_rate_limit_attempts: int = 5
    auth_rate_limit_window_seconds: int = 300
    face_match_threshold: float = 0.35
    liveness_min_blinks: int = 1
    liveness_eye_closed_frames: int = 2
    totp_issuer_name: str = "InterviewLoop-v2"
    totp_secret_encryption_key: str | None = None
    totp_recovery_code_count: int = 10
    totp_recovery_code_bytes: int = 6
    totp_valid_window: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
