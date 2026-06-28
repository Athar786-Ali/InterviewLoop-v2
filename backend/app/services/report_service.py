import hashlib
import json
from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import utc_now
from app.models.report import Report
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.report import ReportVerificationResponse
from app.services.report_crypto import ReportSignatureService
from app.services.report_pdf import ReportPdfRenderer


class ReportService:
    def __init__(
        self,
        reports: ReportRepository,
        audit_logs: AuditLogRepository,
        sessions: SessionRepository,
        signer: ReportSignatureService,
        pdf_renderer: ReportPdfRenderer,
        storage_dir: str | None = None,
    ) -> None:
        self.reports = reports
        self.audit_logs = audit_logs
        self.sessions = sessions
        self.signer = signer
        self.pdf_renderer = pdf_renderer
        self.storage_dir = Path(storage_dir or settings.report_storage_dir)

    def generate(self, user: User, session_id: UUID, report_type: str) -> Report:
        session = self.sessions.get_for_user(session_id=session_id, user_id=user.id)
        if not session:
            raise AppError("SESSION_NOT_FOUND", "Session was not found.", 404)

        payload = self._payload(user, session, report_type)
        json_bytes = json.dumps(payload, sort_keys=True, default=str, indent=2).encode("utf-8")
        content_hash = self._sha256(json_bytes)
        signature = self.signer.sign(json_bytes)

        report_dir = self.storage_dir / str(user.id) / str(session.id)
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / "report.json"
        pdf_path = report_dir / "report.pdf"
        json_path.write_bytes(json_bytes)
        pdf_path.write_bytes(self.pdf_renderer.render(payload | {"content_hash": content_hash}))

        report = self.reports.create(
            user_id=user.id,
            session_id=session.id,
            report_type=report_type,
            storage_path=str(report_dir),
            content_hash=content_hash,
            signature=signature,
            generated_at=utc_now(),
        )
        self._audit(user.id, session.id, "report.generated", {"report_id": str(report.id), "content_hash": content_hash})
        return report

    def list_reports(self, user: User) -> list[Report]:
        return self.reports.list_for_user(user.id)

    def verify(self, user: User, report_id: UUID) -> ReportVerificationResponse:
        report = self._get_report(user, report_id)
        json_bytes = self._json_path(report).read_bytes()
        content_hash = self._sha256(json_bytes)
        hash_matches = content_hash == report.content_hash
        signature_valid = self.signer.verify(json_bytes, report.signature or "")
        self._audit(
            user.id,
            report.session_id,
            "report.verified",
            {"report_id": str(report.id), "hash_matches": hash_matches, "signature_valid": signature_valid},
        )
        return ReportVerificationResponse(
            report_id=report.id,
            is_valid=hash_matches and signature_valid,
            content_hash=content_hash,
            signature_valid=signature_valid,
            hash_matches=hash_matches,
        )

    def download_path(self, user: User, report_id: UUID, file_type: str) -> Path:
        report = self._get_report(user, report_id)
        if file_type == "json":
            path = self._json_path(report)
        elif file_type == "pdf":
            path = self._pdf_path(report)
        else:
            raise AppError("UNSUPPORTED_REPORT_FORMAT", "Report format must be json or pdf.", 422)
        if not path.exists():
            raise AppError("REPORT_FILE_NOT_FOUND", "Report file was not found.", 404)
        self._audit(user.id, report.session_id, "report.downloaded", {"report_id": str(report.id), "format": file_type})
        return path

    def _payload(self, user: User, session, report_type: str) -> dict:
        scores = [
            question.score
            for question in session.question_logs
            if question.deleted_at is None and question.score is not None
        ]
        average_score = round(sum(scores) / len(scores), 2) if scores else 0
        return {
            "report_type": report_type,
            "user_id": str(user.id),
            "email": user.email,
            "session_id": str(session.id),
            "external_session_id": session.session_id,
            "interview_type": session.interview_type,
            "status": session.status,
            "average_score": average_score,
            "question_count": len(scores),
            "generated_at": utc_now().isoformat(),
        }

    def _audit(self, user_id: UUID, session_id: UUID, action: str, metadata: dict) -> None:
        previous = self.audit_logs.get_latest_for_user(user_id)
        previous_hash = previous.metadata_json.get("hash_chain") if previous and previous.metadata_json else None
        chain_payload = json.dumps({"previous_hash": previous_hash, "action": action, "metadata": metadata}, sort_keys=True)
        hash_chain = self._sha256(chain_payload.encode("utf-8"))
        self.audit_logs.create(
            user_id=user_id,
            session_id=session_id,
            action=action,
            metadata_json=metadata | {"previous_hash": previous_hash, "hash_chain": hash_chain},
        )

    def _get_report(self, user: User, report_id: UUID) -> Report:
        report = self.reports.get_for_user(report_id=report_id, user_id=user.id)
        if not report:
            raise AppError("REPORT_NOT_FOUND", "Report was not found.", 404)
        return report

    def _json_path(self, report: Report) -> Path:
        return Path(report.storage_path or "") / "report.json"

    def _pdf_path(self, report: Report) -> Path:
        return Path(report.storage_path or "") / "report.pdf"

    def _sha256(self, value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()
